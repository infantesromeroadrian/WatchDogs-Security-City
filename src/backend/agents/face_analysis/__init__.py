"""
Face Analysis Agent Module - CIA-Level OSINT Person Identification

This module provides forensic-level analysis of faces and persons in images,
including:
- Detailed facial feature extraction
- Body and posture analysis
- Clothing and accessories identification
- Distinguishing marks (scars, tattoos, birthmarks)
- Age, gender, and ethnicity estimation
"""

from .face_agent import FaceAnalysisAgent
from .prompts import FACE_ANALYSIS_PROMPT
from .response_parser import FaceAnalysisResponseParser

__all__ = [
    "FaceAnalysisAgent",
    "FACE_ANALYSIS_PROMPT",
    "FaceAnalysisResponseParser",
]
