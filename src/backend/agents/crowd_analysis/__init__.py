"""
Crowd Analysis Agent Module - Military Intelligence

This module provides military-grade crowd analysis including:
- Crowd density estimation (persons per area)
- Demographic composition analysis
- Movement patterns and flow detection
- Anomalous behavior identification
- Group formation analysis
- Panic/distress indicators
"""

from .crowd_analysis_agent import CrowdAnalysisAgent
from .prompts import CROWD_ANALYSIS_PROMPT
from .response_parser import CrowdAnalysisResponseParser

__all__ = [
    "CROWD_ANALYSIS_PROMPT",
    "CrowdAnalysisAgent",
    "CrowdAnalysisResponseParser",
]
