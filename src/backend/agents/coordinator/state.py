"""
State Management - TypedDict definitions for LangGraph
Single Responsibility: Define state structures only
Max: 50 lines
"""

from typing import Dict, Any, TypedDict, Literal


class AnalysisState(TypedDict):
    """State structure for single-frame analysis graph"""

    image_base64: str
    context: str
    agents_to_run: list[Literal["vision", "ocr", "detection", "geolocation"]]
    vision_result: Dict[str, Any] | None
    ocr_result: Dict[str, Any] | None
    detection_result: Dict[str, Any] | None
    geolocation_result: Dict[str, Any] | None
    final_report: Dict[str, Any] | None


class MultiFrameState(TypedDict):
    """State structure for multi-frame analysis"""

    frames: list[Dict[str, str]]
    current_frame_index: int
    individual_results: list[Dict[str, Any]]
    combined_geolocation: Dict[str, Any] | None
    summary: str | None
