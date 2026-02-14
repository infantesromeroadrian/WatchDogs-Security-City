"""Tests for multi-frame handler sequential and parallel routes."""

from __future__ import annotations

from typing import Any

from src.backend.agents.coordinator.multi_frame_handler import MultiFrameHandler


def _build_analyzer_with_trace(trace: list[str]):
    """Create analyzer that records contexts and returns deterministic payload."""

    def analyzer(frame_base64: str, context: str) -> dict[str, Any]:
        trace.append(context)
        frame_id = frame_base64.split(":")[-1]
        return {
            "json": {
                "agents": {
                    "geolocation": {
                        "key_clues": [f"geo-{frame_id}"],
                        "location": {"country": "Spain", "city": "Madrid"},
                        "confidence": "HIGH",
                    },
                    "ocr": {
                        "status": "success",
                        "has_text": True,
                        "analysis": f"Texto detectado {frame_id} para acumulacion de contexto",
                    },
                    "detection": {
                        "status": "success",
                        "analysis": f"Objeto detectado {frame_id} para acumulacion",
                    },
                }
            }
        }

    return analyzer


def test_analyze_multi_frame_sequential_accumulates_context() -> None:
    """Sequential mode should pass accumulated clues to following frames."""
    contexts: list[str] = []
    handler = MultiFrameHandler(_build_analyzer_with_trace(contexts))
    frames = [
        {"frame": "img:1", "description": "Cruce"},
        {"frame": "img:2", "description": "Semaforo"},
        {"frame": "img:3", "description": "Escaparate"},
    ]

    response = handler.analyze_multi_frame(frames, enable_context_accumulation=True)

    assert response["json"]["context_accumulation_enabled"] is True
    assert response["json"]["total_frames"] == 3
    assert len(response["json"]["individual_results"]) == 3
    assert "PISTAS ACUMULADAS" not in contexts[0]
    assert "PISTAS ACUMULADAS" in contexts[1]
    assert "PISTAS ACUMULADAS" in contexts[2]


def test_analyze_multi_frame_parallel_uses_independent_context() -> None:
    """Parallel mode should use per-frame context without accumulation."""
    contexts: list[str] = []
    handler = MultiFrameHandler(_build_analyzer_with_trace(contexts))
    frames = [
        {"frame": "img:1", "description": "Entrada"},
        {"frame": "img:2", "description": "Salida"},
        {"frame": "img:3", "description": "Avenida"},
    ]

    response = handler.analyze_multi_frame(frames, enable_context_accumulation=False)

    assert response["json"]["context_accumulation_enabled"] is False
    assert response["json"]["total_frames"] == 3
    assert len(response["json"]["individual_results"]) == 3
    assert contexts == ["Entrada", "Salida", "Avenida"]


def test_analyze_multi_frame_returns_identical_schema_for_both_modes() -> None:
    """Sequential and parallel routes must return the same response schema."""
    handler = MultiFrameHandler(_build_analyzer_with_trace([]))
    frames = [{"frame": "img:1", "description": "Plaza"}]

    sequential = handler.analyze_multi_frame(frames, enable_context_accumulation=True)
    parallel = handler.analyze_multi_frame(frames, enable_context_accumulation=False)

    assert set(sequential.keys()) == {"text", "json"}
    assert set(parallel.keys()) == {"text", "json"}
    assert set(sequential["json"].keys()) == {
        "individual_results",
        "combined_geolocation",
        "total_frames",
        "context_accumulation_enabled",
    }
    assert set(parallel["json"].keys()) == set(sequential["json"].keys())
