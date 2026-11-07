"""Minimal OpenAI-compatible chat-completions stub for tests (no network, no keys)."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class StubLLM:
    """Threaded HTTP server that mimics ``POST /v1/chat/completions``.

    Args:
        content: reply text (str) or callable(request_json) -> str
        delay: seconds to sleep before replying
        fail_first: number of initial requests answered with HTTP 500
        finish_reason: finish_reason reported in every reply ("length" simulates a token cap)
    """

    def __init__(self, content: Any = '{"summary": "stub"}', delay: float = 0.0, fail_first: int = 0, port: int = 0,
                 finish_reason: str = "stop"):
        self.content = content
        self.delay = delay
        self.fail_first = fail_first
        self.finish_reason = finish_reason
        self.requests = 0
        self.max_concurrent = 0
        self._active = 0
        self._lock = threading.Lock()
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:  # silence
                pass

            def do_POST(self) -> None:  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                with stub._lock:
                    stub.requests += 1
                    n = stub.requests
                    stub._active += 1
                    stub.max_concurrent = max(stub.max_concurrent, stub._active)
                try:
                    time.sleep(stub.delay)
                    if n <= stub.fail_first:
                        self.send_response(500)
                        self.end_headers()
                        self.wfile.write(b'{"error": {"message": "boom"}}')
                        return
                    text = stub.content(body) if callable(stub.content) else stub.content
                    payload = json.dumps(
                        {
                            "id": "stub",
                            "object": "chat.completion",
                            "created": 0,
                            "model": body.get("model", "stub"),
                            "choices": [
                                {
                                    "index": 0,
                                    "finish_reason": stub.finish_reason,
                                    "message": {"role": "assistant", "content": text},
                                }
                            ],
                            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        }
                    ).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # client timed out and closed the socket
                finally:
                    with stub._lock:
                        stub._active -= 1

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/v1"
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> StubLLM:
        self._thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.server.shutdown()
        self.server.server_close()


if __name__ == "__main__":  # standalone, for gunicorn load tests
    import os

    with StubLLM(delay=float(os.getenv("STUB_DELAY", "0.5")), port=int(os.getenv("STUB_PORT", "18080"))) as stub:
        print("stub listening on", stub.url, flush=True)
        threading.Event().wait()
