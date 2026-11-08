"""Service-level probe: concurrency and memory of the production gunicorn setup (no real LLM).

Starts a stub OpenAI-compatible LLM (fixed per-call delay), launches gunicorn with the Render flags
(1 worker x 4 threads, --preload, MALLOC_ARENA_MAX=2), logs in, fires concurrent full analyses
(16 agents each) and records latency and the worker's resident memory.

    python -m eval.service_probe [--out metrics.json]   # merges a "service" section into metrics.json
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import secrets
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from stub_llm import StubLLM, make_password  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PORT = 15099
CONCURRENCY, ROUNDS, STUB_DELAY = 4, 2, 0.5


def _rss_mb(pid: int) -> float:
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("VmRSS"):
            return round(int(line.split()[1]) / 1024, 1)
    return 0.0


def _worker_pid(master: int) -> int:
    children = Path(f"/proc/{master}/task/{master}/children").read_text().split()
    return int(children[0])


def _frame() -> str:
    img = Image.effect_noise((640, 480), 40).convert("RGB")  # ~incompressible noise: realistic payload size
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="metrics.json")
    args = ap.parse_args()
    password = make_password()
    tmp = tempfile.mkdtemp(prefix="wd-probe-")
    with StubLLM(delay=STUB_DELAY) as stub:
        env = {
            **os.environ, "PYTHONPATH": str(ROOT), "FLASK_ENV": "production", "MALLOC_ARENA_MAX": "2",
            "LLM_PROVIDER": "custom", "OPENAI_BASE_URL": stub.url, "OPENAI_API_KEY": "stub", "OPENAI_MODEL": "stub",
            "ADMIN_USERNAME": "probe", "ADMIN_PASSWORD": password, "FLASK_SECRET_KEY": secrets.token_hex(32),
            "AUTH_STORAGE_FILE": f"{tmp}/auth.json", "LLM_BUDGET_DB": f"{tmp}/budget.sqlite3",
            "CACHE_ENABLED": "false", "AGENT_TIMEOUT_SECONDS": "180",
        }
        server = subprocess.Popen(
            [sys.executable, "-m", "gunicorn", "--bind", f"127.0.0.1:{PORT}", "--workers", "1", "--threads", "4",
             "--timeout", "300", "--preload", "--max-requests", "50", "--max-requests-jitter", "10", "src.backend.app:app"],
            env=env, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{PORT}"
            for _ in range(60):
                try:
                    urllib.request.urlopen(f"{base}/api/health", timeout=2)
                    break
                except OSError:
                    time.sleep(1)
            worker = _worker_pid(server.pid)
            idle_mb = _rss_mb(worker)
            opener = urllib.request.build_opener()
            login = opener.open(urllib.request.Request(
                f"{base}/api/auth/login", json.dumps({"username": "probe", "password": password}).encode(),
                {"Content-Type": "application/json"}), timeout=60)
            token = json.load(login)["session_token"]  # the cookie is Secure: over plain http use Bearer
            frame = _frame()
            body = json.dumps({"frame": frame}).encode()
            latencies: list[float] = []
            ok = 0

            def one() -> None:
                nonlocal ok
                t0 = time.perf_counter()
                resp = opener.open(urllib.request.Request(
                    f"{base}/api/analyze-frame", body,
                    {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}), timeout=280)
                data = json.load(resp)
                agents = data["results"]["json"]["agents"]
                latencies.append(time.perf_counter() - t0)
                ok += all(a["status"] == "success" for a in agents.values()) and len(agents) == 16

            for _ in range(ROUNDS):
                threads = [threading.Thread(target=one) for _ in range(CONCURRENCY)]
                [t.start() for t in threads]
                [t.join() for t in threads]
            peak_mb = _rss_mb(worker)
            section = {
                "setup": f"gunicorn 1 worker x 4 threads, MALLOC_ARENA_MAX=2, stub LLM with {STUB_DELAY}s per call",
                "concurrent_analyses": CONCURRENCY, "rounds": ROUNDS, "frame_bytes": len(frame) * 3 // 4,
                "analyses_16_of_16_agents_ok": f"{ok}/{CONCURRENCY * ROUNDS}",
                "median_latency_s": round(statistics.median(latencies), 2),
                "max_latency_s": round(max(latencies), 2),
                "worker_rss_idle_mb": idle_mb, "worker_rss_after_load_mb": peak_mb,
                "render_free_plan_limit_mb": 512,
            }
        finally:
            server.terminate()
            server.wait(timeout=20)
    path = Path(args.out)
    doc = json.loads(path.read_text()) if path.exists() else {}
    doc["service"] = section
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(section, indent=1))
    return 0 if ok == CONCURRENCY * ROUNDS else 1


if __name__ == "__main__":
    sys.exit(main())
