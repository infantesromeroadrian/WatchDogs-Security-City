"""
Forensic Analysis Agent Module - Image Authenticity and Manipulation Detection

This module provides forensic-level analysis of images for:
- Manipulation detection (copy-paste, splicing, retouching)
- Compression artifact analysis (re-save detection)
- Lighting and shadow consistency
- Perspective and geometry analysis
- Digital fingerprint analysis
- Source device estimation
"""

from .forensic_agent import ForensicAnalysisAgent
from .prompts import FORENSIC_ANALYSIS_PROMPT
from .response_parser import ForensicResponseParser

__all__ = [
    "FORENSIC_ANALYSIS_PROMPT",
    "ForensicAnalysisAgent",
    "ForensicResponseParser",
]
