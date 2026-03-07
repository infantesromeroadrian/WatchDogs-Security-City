"""
Night Vision Enhancement Agent Module - Military Intelligence Block 2

This module provides military-grade night/low-light image analysis including:
- Low-light scene enhancement and interpretation
- Light source identification and classification
- Infrared/thermal signature inference
- Night activity pattern detection
- Visibility assessment and distance estimation
- Covert activity indicators
"""

from .night_vision_agent import NightVisionAgent
from .prompts import NIGHT_VISION_PROMPT
from .response_parser import NightVisionResponseParser

__all__ = [
    "NIGHT_VISION_PROMPT",
    "NightVisionAgent",
    "NightVisionResponseParser",
]
