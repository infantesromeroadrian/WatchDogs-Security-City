"""
State Management - TypedDict definitions for LangGraph
Single Responsibility: Define state structures only
Max: 100 lines

CIA-Level OSINT Analysis State with 7 parallel agents:
- vision: General scene analysis
- ocr: Text extraction
- detection: Object/person detection
- geolocation: Location identification
- face_analysis: Person identification (GDPR-sensitive)
- forensic_analysis: Image authenticity verification
- context_intel: Temporal and cultural inference

Privacy controls are loaded from config to allow disabling sensitive agents.
"""

from typing import Any, Literal, TypedDict

from ...config import (
    CONTEXT_INTEL_ENABLED,
    FACE_ANALYSIS_ENABLED,
    FORENSIC_ANALYSIS_ENABLED,
    PRIVACY_MODE,
)

# Type alias for all available agents
AgentType = Literal[
    "vision",
    "ocr",
    "detection",
    "geolocation",
    "face_analysis",
    "forensic_analysis",
    "context_intel",
]


def get_enabled_agents() -> list[AgentType]:
    """
    Return list of enabled agents based on privacy configuration.

    Respects PRIVACY_MODE and individual agent flags from config.
    """
    # Core agents always enabled
    agents: list[AgentType] = ["vision", "ocr", "detection", "geolocation"]

    # Privacy mode disables ALL sensitive agents
    if PRIVACY_MODE:
        return agents

    # Add CIA-level agents if enabled
    if FACE_ANALYSIS_ENABLED:
        agents.append("face_analysis")
    if FORENSIC_ANALYSIS_ENABLED:
        agents.append("forensic_analysis")
    if CONTEXT_INTEL_ENABLED:
        agents.append("context_intel")

    return agents


# Default agents to run (respects privacy config)
DEFAULT_AGENTS: list[AgentType] = get_enabled_agents()


class AnalysisState(TypedDict):
    """State structure for single-frame analysis graph with 7 agents."""

    image_base64: str
    context: str
    agents_to_run: list[AgentType]
    # Original 4 agents
    vision_result: dict[str, Any] | None
    ocr_result: dict[str, Any] | None
    detection_result: dict[str, Any] | None
    geolocation_result: dict[str, Any] | None
    # CIA-level agents
    face_analysis_result: dict[str, Any] | None
    forensic_analysis_result: dict[str, Any] | None
    context_intel_result: dict[str, Any] | None
    # Final output
    final_report: dict[str, Any] | None
