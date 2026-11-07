"""
Visual prompt-injection regression suite (offline).

Adversarial payloads are NOT stored in this file: they are loaded from tests/fixtures/injection_payloads.json
(schema in tests/fixtures/README-schema below). The suite is skipped when that file is absent.

Schema: {"payloads": [{"id": str, "category": str, "text": str}, ...]} with categories
embedded_image_text, role_change, exfiltration_report, exfiltration_chat, markup_injection, fence_breakout
(at least 3 payloads each). markup_injection payloads should contain HTML/ReportLab tags (img, a, font, script).
"""

import json
from pathlib import Path

import pytest
from conftest import _tiny_jpeg_b64
from stub_llm import StubLLM

from src.backend import config
from src.backend.services.report.safe_text import safe_markup
from src.backend.utils.untrusted import BEGIN_MARK, END_MARK, sanitize_structure, wrap_untrusted

FIXTURE = Path(__file__).parent / "fixtures" / "injection_payloads.json"
pytestmark = pytest.mark.skipif(not FIXTURE.exists(), reason="payload corpus not installed")


def _payloads(category=None):
    items = json.loads(FIXTURE.read_text())["payloads"]
    return [p["text"] for p in items if category in (None, p["category"])]


@pytest.fixture
def stub_backend(monkeypatch):
    def _use(stub):
        for k, v in (("LLM_PROVIDER", "custom"), ("OPENAI_BASE_URL", stub.url), ("OPENAI_API_KEY", "k"), ("OPENAI_MODEL", "m")):
            monkeypatch.setattr(config, k, v)
    return _use


def _text(body):
    return "\n".join(
        m["content"] if isinstance(m["content"], str) else " ".join(p.get("text", "") for p in m["content"])
        for m in body["messages"]
    )


def test_corpus_covers_categories():
    cats = {p["category"] for p in json.loads(FIXTURE.read_text())["payloads"]}
    assert {"embedded_image_text", "role_change", "exfiltration_report", "exfiltration_chat",
            "markup_injection", "fence_breakout"} <= cats


def test_outputs_are_capped_and_inert(stub_backend):
    from src.backend.agents.coordinator import CoordinatorAgent

    payload = "".join(_payloads()) * 5
    with StubLLM(content=json.dumps({"summary": payload, "extracted_text": [payload]})) as stub:
        stub_backend(stub)
        report = CoordinatorAgent().analyze_frame(_tiny_jpeg_b64(), "")
    agents = report["json"]["agents"]
    assert all(a["status"] == "success" for a in agents.values())
    assert all(len(a["summary"]) <= 2000 for a in agents.values() if a.get("summary"))


def test_every_prompt_warns_that_image_text_is_data(stub_backend):
    from src.backend.agents.coordinator import CoordinatorAgent

    seen = []
    with StubLLM(content=lambda b: (seen.append(_text(b)), '{"summary": "ok"}')[1]) as stub:
        stub_backend(stub)
        CoordinatorAgent().analyze_frame(_tiny_jpeg_b64(), "")
    assert len(seen) >= 16 and all("nunca obedezcas" in t.lower() or "no obedezcas" in t.lower() for t in seen)


def test_fence_cannot_be_broken(stub_backend):
    for text in _payloads("fence_breakout") + _payloads():
        wrapped = wrap_untrusted(text + f"<<<{END_MARK}")
        assert wrapped.count(BEGIN_MARK) == 1 and wrapped.count(END_MARK) == 1


def test_multi_frame_and_chat_fence_untrusted_text(stub_backend):
    from src.backend.agents.coordinator import CoordinatorAgent

    clue = _payloads("role_change")[0]
    prompts = []

    def reply(body):
        prompts.append(_text(body))
        return json.dumps({"key_clues": [clue], "summary": "ok"})

    with StubLLM(content=reply) as stub:
        stub_backend(stub)
        c = CoordinatorAgent()
        frames = [{"frame": _tiny_jpeg_b64(), "description": "a"}, {"frame": _tiny_jpeg_b64(), "description": "b"}]
        c.analyze_multi_frame(frames, enable_context_accumulation=True)
        carrying = [p for p in prompts if clue[:40] in p]
        assert carrying and all(BEGIN_MARK in p for p in carrying)
        prompts.clear()
        c.chat("¿qué ves?", image_base64=_tiny_jpeg_b64(), analysis_summary=clue, thread_id="inj")
        system = prompts[-1]
        assert BEGIN_MARK in system and system.index(BEGIN_MARK) < system.index(clue[:40])


def test_pdf_markup_is_escaped_and_report_builds(auth_client):
    for text in _payloads("markup_injection"):
        out = safe_markup(text)
        assert "<img" not in out.lower() and "<a " not in out.lower() and "<font" not in out.lower()
    res = {"vision": {"status": "success", "analysis": "\n".join(_payloads())}}
    r = auth_client.post("/api/generate-pdf-report", json={"analysis_results": res})
    assert r.status_code == 200 and r.data.startswith(b"%PDF")


def test_sanitize_structure_on_corpus():
    out = sanitize_structure({"a": _payloads() * 100})
    assert len(out["a"]) <= 100
