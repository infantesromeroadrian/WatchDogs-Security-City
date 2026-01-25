"""
Context Intelligence Agent Module - Temporal and Cultural Inference

This module provides CIA-level contextual intelligence extraction including:
- Temporal analysis (time, day, season, era, specific dates)
- Cultural and socioeconomic indicators
- Event and activity classification
- Environmental conditions
- Anomaly detection
- Key inferences with confidence levels
"""

from .context_intel_agent import ContextIntelAgent
from .prompts import CONTEXT_INTEL_PROMPT
from .response_parser import ContextIntelResponseParser

__all__ = [
    "CONTEXT_INTEL_PROMPT",
    "ContextIntelAgent",
    "ContextIntelResponseParser",
]
