"""Provider abstraction, structured outputs, timeouts/retries and graph fan-out (offline, stub LLM)."""

import base64
import io
import json
import threading
import time

import pytest
from PIL import Image
from stub_llm import StubLLM

from src.backend import config
from src.backend.llm import StructuredOutputError, StructuredParser, build_chat_model
from src.backend.llm.provider import get_provider_settings
from src.backend.llm.structured import extract_json, render_markdown
from src.backend.models.structured import (
    ForensicSchema,
    GeolocationSchema,
    OcrSchema,
    WeaponSchema,
)


def _image_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 160, 200)).save(buf, "JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def use_stub(monkeypatch):
    """Point the provider at a stub server."""

    def _use(stub: StubLLM, timeout: float = 30.0):
        monkeypatch.setattr(config, "LLM_PROVIDER", "custom")
        monkeypatch.setattr(config, "OPENAI_BASE_URL", stub.url)
        monkeypatch.setattr(config, "OPENAI_API_KEY", "test")
        monkeypatch.setattr(config, "OPENAI_MODEL", "stub-model")
        monkeypatch.setattr(config, "LLM_TIMEOUT_SECONDS", timeout)

    return _use


# ------------------------------------------------------------------ provider
class TestProvider:
    def test_default_is_groq(self, monkeypatch):
        monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
        monkeypatch.setattr(config, "OPENAI_BASE_URL", None)
        monkeypatch.setattr(config, "OPENAI_MODEL", None)
        s = get_provider_settings()
        assert s.base_url == "https://api.groq.com/openai/v1"
        assert "llama-4-scout" in s.model

    def test_env_overrides_preset(self, monkeypatch):
        monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(config, "OPENAI_MODEL", "other:tag")
        monkeypatch.setattr(config, "OPENAI_BASE_URL", None)
        s = get_provider_settings()
        assert s.model == "other:tag"
        assert s.base_url.startswith("http://localhost:11434")

    def test_custom_requires_url(self, monkeypatch):
        monkeypatch.setattr(config, "LLM_PROVIDER", "custom")
        monkeypatch.setattr(config, "OPENAI_BASE_URL", None)
        with pytest.raises(ValueError):
            get_provider_settings()

    def test_unknown_provider(self, monkeypatch):
        monkeypatch.setattr(config, "LLM_PROVIDER", "nope")
        with pytest.raises(ValueError):
            get_provider_settings()


# ---------------------------------------------------------------- structured
class TestStructured:
    def test_extract_json_variants(self):
        assert extract_json('{"a": 1}') == {"a": 1}
        assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
        assert extract_json('<think>hmm {x}</think>{"a": 1}') == {"a": 1}
        assert extract_json('Aquí va: {"a": {"b": 2}} fin') == {"a": {"b": 2}}
        assert extract_json("sin json") is None
        assert extract_json("[1, 2]") is None

    def test_lenient_scalar_coercion(self):
        data = WeaponSchema.model_validate(
            {"summary": 5, "weapon_count": "2", "weapons": {"type": "fusil"}, "limitations": "una"}
        ).model_dump()
        assert data["summary"] == "5"
        assert data["weapon_count"] == 2
        assert data["weapons"][0]["type"] == "fusil"
        assert data["limitations"] == ["una"]

    def test_nulls_use_defaults(self):
        data = GeolocationSchema.model_validate(
            {"location": None, "coordinates": {"lat": "38.7", "lon": -9.1}, "key_clues": None}
        ).model_dump()
        assert data["coordinates"]["lat"] == 38.7
        assert data["location"]["city"] is None
        assert data["key_clues"] == []

    def test_parse_json_reply(self):
        parser = StructuredParser(OcrSchema)
        data, text = parser.parse_with_text('{"has_text": true, "extracted_text": ["ABC 123"]}')
        assert data["extracted_text"] == ["ABC 123"]
        assert "ABC 123" in text

    def test_garbage_raises_for_retry(self):
        with pytest.raises(StructuredOutputError):
            StructuredParser(OcrSchema).parse("esto no es json")

    def test_legacy_fallback(self):
        class Legacy:
            def parse(self, text):
                return {"summary": "from regex"}

        data, text = StructuredParser(WeaponSchema, Legacy()).parse_with_text("texto libre")
        assert data["summary"] == "from regex"
        assert text == "texto libre"

    def test_render_markdown_skips_empty(self):
        md = render_markdown({"summary": "ok", "empty": None, "items": ["a", ""], "n": {"x": 1}})
        assert "ok" in md and "empty" not in md and "- a" in md


class TestForensicParserRegression:
    """The old regex let ``\\s*`` cross the newline and shifted every 'details' by one line."""

    def test_manipulation_details_not_shifted(self):
        from src.backend.agents.forensic_analysis.response_parser import ForensicResponseParser

        text = (
            "MANIPULACIONES ESPECÍFICAS:\n"
            "- Copy-paste: No detectado\n"
            "- Splicing: Detectado - borde irregular\n"
            "- Retoque: No detectado\n"
            "- Generación IA: No detectado\n"
        )
        manip = ForensicResponseParser()._parse_manipulation_specific(text)
        assert manip["copy_paste"] == {"detected": False, "details": None}
        assert manip["splicing"] == {"detected": True, "details": "borde irregular"}
        assert manip["retouching"]["details"] is None
        assert manip["ai_generated"]["details"] is None

    def test_schema_roundtrip(self):
        out = ForensicSchema.model_validate({"integrity_score": "90"}).model_dump()
        assert out["integrity_score"] == 90


# ------------------------------------------------------ timeouts and retries
class TestTimeoutsAndRetries:
    def test_http_timeout_closes_connection(self, use_stub):
        from openai import APITimeoutError

        with StubLLM(delay=3.0) as stub:
            use_stub(stub, timeout=0.5)
            llm = build_chat_model()
            t = time.time()
            with pytest.raises(APITimeoutError):
                llm.invoke("hola")
            assert time.time() - t < 2.5

    def test_retry_recovers_from_transient_error(self, use_stub):
        from src.backend.agents.weapon_detection import WeaponDetectionAgent

        with StubLLM(content='{"summary": "0 armas"}', fail_first=1) as stub:
            use_stub(stub)
            agent = WeaponDetectionAgent()
            agent.breaker = None
            result = agent.analyze(_image_b64())
            assert result["status"] == "success"
            assert result["summary"] == "0 armas"
            assert stub.requests == 2

    def test_unparsable_reply_reports_error_after_retries(self, use_stub):
        from src.backend.agents.weapon_detection import WeaponDetectionAgent

        with StubLLM(content="no soy json") as stub:
            use_stub(stub)
            agent = WeaponDetectionAgent()
            agent.breaker = None
            result = agent.analyze(_image_b64())
            assert result["status"] == "error"
            assert stub.requests == config.AGENT_RETRY_MAX_ATTEMPTS


# -------------------------------------------------------------------- fan-out
class TestFanOut:
    def test_sixteen_agents_run_in_parallel_threads(self, use_stub):
        from src.backend.agents.coordinator import CoordinatorAgent

        with StubLLM(delay=0.4) as stub:
            use_stub(stub)
            coordinator = CoordinatorAgent()
            for runner_agent in vars(coordinator.agent_runners).values():
                if hasattr(runner_agent, "breaker"):
                    runner_agent.breaker = None
            t = time.time()
            report = coordinator.analyze_frame(_image_b64(), "")
            elapsed = time.time() - t
        agents = report["json"]["agents"]
        assert len(agents) == 16
        assert all(a["status"] == "success" for a in agents.values()), {
            k: v["status"] for k, v in agents.items()
        }
        assert stub.max_concurrent >= 8
        assert elapsed < 16 * 0.4  # strictly better than sequential

    def test_concurrent_requests_do_not_mix_results(self, use_stub):
        from src.backend.agents.coordinator import CoordinatorAgent

        def reply(body):
            return json.dumps({"summary": "stub", "has_text": False})

        with StubLLM(content=reply, delay=0.1) as stub:
            use_stub(stub)
            coordinator = CoordinatorAgent()
            results: list = []

            def run(i):
                results.append(coordinator.analyze_frame(_image_b64(), f"ctx {i}", thread_id=f"t{i}"))

            threads = [threading.Thread(target=run, args=(i,)) for i in range(4)]
            [t.start() for t in threads]
            [t.join(60) for t in threads]
        assert len(results) == 4
        assert all(len(r["json"]["agents"]) == 16 for r in results)


class TestOutputCap:
    """Ollama ignores ``max_completion_tokens``; the cap must reach it as ``max_tokens``."""

    @pytest.mark.parametrize("provider", ["ollama", "groq", "custom"])
    def test_classic_max_tokens_for_compatible_servers(self, use_stub, monkeypatch, provider):
        seen: list[dict] = []
        with StubLLM(content=lambda body: (seen.append(body), "ok")[1]) as stub:
            use_stub(stub)
            monkeypatch.setattr(config, "LLM_PROVIDER", provider)
            monkeypatch.setattr(config, "OPENAI_MAX_TOKENS", 123)
            build_chat_model().invoke("hola")
        assert seen[0]["max_tokens"] == 123 and "max_completion_tokens" not in seen[0]

    def test_openai_gets_max_completion_tokens(self, use_stub, monkeypatch):
        seen: list[dict] = []
        with StubLLM(content=lambda body: (seen.append(body), "ok")[1]) as stub:
            use_stub(stub)
            monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
            monkeypatch.setattr(config, "OPENAI_MAX_TOKENS", 321)
            build_chat_model().invoke("hola")
        assert seen[0]["max_completion_tokens"] == 321


class TestPlaceholders:
    def test_null_island_is_not_a_prediction(self):
        data = GeolocationSchema.model_validate(
            {"coordinates": {"lat": 0, "lon": 0, "confidence_radius_meters": 0}}
        ).model_dump()
        assert data["coordinates"] is None
        kept = GeolocationSchema.model_validate({"coordinates": {"lat": 0, "lon": 12.5}}).model_dump()
        assert kept["coordinates"]["lon"] == 12.5

    def test_skeleton_contains_no_literal_zero_defaults(self):
        from src.backend.llm.structured import format_instructions

        text = format_instructions(GeolocationSchema)
        assert '"lat": 0' not in text and '"lat": "<número o null>"' in text


class TestTruncatedOutput:
    def test_length_finish_reason_becomes_structured_output_error(self, use_stub, monkeypatch):
        """A reply cut at the token cap must be retryable, not an unhandled client exception."""
        from src.backend.agents.weapon_detection import WeaponDetectionAgent

        calls = {"n": 0}

        def truncated(body):
            calls["n"] += 1
            return '{"summary": "se corta'  # invalid JSON, as after a token cap

        with StubLLM(content=truncated, finish_reason="length") as stub:
            use_stub(stub)
            agent = WeaponDetectionAgent()
            agent.breaker = None
            result = agent.analyze(_image_b64())
        assert result["status"] == "error"
        assert calls["n"] == config.AGENT_RETRY_MAX_ATTEMPTS


class TestNoEthnicity:
    def test_face_output_has_no_ethnicity_key(self, use_stub):
        from src.backend.agents.face_analysis import FaceAnalysisAgent

        reply = '{"persons": [{"person_id": 1, "demographics": {"age_range": "30-40", "gender": "hombre", "ethnicity_description": "x"}}]}'
        with StubLLM(content=reply) as stub:
            use_stub(stub)
            agent = FaceAnalysisAgent()
            agent.breaker = None
            result = agent.analyze(_image_b64())
        assert result["status"] == "success"
        assert "ethnic" not in json.dumps(result).lower().replace("(no ethnicity inference)", "")
