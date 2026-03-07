"""
State Management - TypedDict definitions for LangGraph
Single Responsibility: Define state structures only

Military-Grade OSINT Analysis State with 12 parallel agents:

Original CIA-Level (7):
- vision, ocr, detection, geolocation
- face_analysis, forensic_analysis, context_intel

Military Intelligence Block 1 (5):
- vehicle_detection, weapon_detection, crowd_analysis
- shadow_analysis, infrastructure_analysis

Privacy controls are loaded from config to allow disabling sensitive agents.
"""

from typing import Any, Literal, TypedDict

from ...config import (
    CONTEXT_INTEL_ENABLED,
    CROWD_ANALYSIS_ENABLED,
    FACE_ANALYSIS_ENABLED,
    FORENSIC_ANALYSIS_ENABLED,
    INFRASTRUCTURE_ANALYSIS_ENABLED,
    PRIVACY_MODE,
    SHADOW_ANALYSIS_ENABLED,
    VEHICLE_DETECTION_ENABLED,
    WEAPON_DETECTION_ENABLED,
)

# Type alias for all available agents
AgentType = Literal[
    # Original 7
    "vision",
    "ocr",
    "detection",
    "geolocation",
    "face_analysis",
    "forensic_analysis",
    "context_intel",
    # Military Intelligence Block 1
    "vehicle_detection",
    "weapon_detection",
    "crowd_analysis",
    "shadow_analysis",
    "infrastructure_analysis",
]


def get_enabled_agents() -> list[AgentType]:
    """
    Return list of enabled agents based on privacy configuration.

    Respects PRIVACY_MODE and individual agent flags from config.
    """
    # Core agents always enabled
    agents: list[AgentType] = ["vision", "ocr", "detection", "geolocation"]

    # Privacy mode disables ALL sensitive agents (but not military intel)
    if not PRIVACY_MODE:
        if FACE_ANALYSIS_ENABLED:
            agents.append("face_analysis")
        if FORENSIC_ANALYSIS_ENABLED:
            agents.append("forensic_analysis")
        if CONTEXT_INTEL_ENABLED:
            agents.append("context_intel")

    # Military Intelligence Block 1 (always available, controlled individually)
    if VEHICLE_DETECTION_ENABLED:
        agents.append("vehicle_detection")
    if WEAPON_DETECTION_ENABLED:
        agents.append("weapon_detection")
    if CROWD_ANALYSIS_ENABLED:
        agents.append("crowd_analysis")
    if SHADOW_ANALYSIS_ENABLED:
        agents.append("shadow_analysis")
    if INFRASTRUCTURE_ANALYSIS_ENABLED:
        agents.append("infrastructure_analysis")

    return agents


# Default agents to run (respects privacy config)
DEFAULT_AGENTS: list[AgentType] = get_enabled_agents()


class AnalysisState(TypedDict):
    """State structure for analysis graph with 12 agents."""

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
    # Military Intelligence Block 1
    vehicle_detection_result: dict[str, Any] | None
    weapon_detection_result: dict[str, Any] | None
    crowd_analysis_result: dict[str, Any] | None
    shadow_analysis_result: dict[str, Any] | None
    infrastructure_analysis_result: dict[str, Any] | None
    # Final output
    final_report: dict[str, Any] | None
