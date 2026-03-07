"""
Temporal Comparison Agent Module - Military Intelligence Block 2

This module provides military-grade temporal change detection including:
- Scene change detection between current and reference imagery
- New construction, removal, or modification of structures
- Vehicle/personnel movement pattern changes
- Terrain and vegetation temporal shifts
- Strategic posture changes (fortification, withdrawal, buildup)
"""

from .prompts import TEMPORAL_COMPARISON_PROMPT
from .response_parser import TemporalComparisonResponseParser
from .temporal_comparison_agent import TemporalComparisonAgent

__all__ = [
    "TEMPORAL_COMPARISON_PROMPT",
    "TemporalComparisonAgent",
    "TemporalComparisonResponseParser",
]
