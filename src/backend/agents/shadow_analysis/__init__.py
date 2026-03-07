"""
Shadow/Sun Analysis Agent Module - Military Intelligence

This module provides military-grade shadow and sun analysis including:
- Sun position estimation (azimuth, elevation)
- Shadow angle measurement and consistency check
- Time-of-day estimation from shadow geometry
- Season inference from sun elevation patterns
- Geographic hemisphere determination
- Artificial vs natural lighting distinction
"""

from .prompts import SHADOW_ANALYSIS_PROMPT
from .response_parser import ShadowAnalysisResponseParser
from .shadow_analysis_agent import ShadowAnalysisAgent

__all__ = [
    "SHADOW_ANALYSIS_PROMPT",
    "ShadowAnalysisAgent",
    "ShadowAnalysisResponseParser",
]
