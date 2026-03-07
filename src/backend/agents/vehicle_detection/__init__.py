"""
Vehicle Detection & ALPR Agent Module - Military Intelligence

This module provides military-grade vehicle intelligence including:
- Vehicle type classification (civilian, military, emergency, commercial)
- Color identification and condition assessment
- License plate recognition (ALPR) with partial plate inference
- Military markings, unit identifiers, and convoy patterns
- Tactical vehicle movement analysis
"""

from .prompts import VEHICLE_DETECTION_PROMPT
from .response_parser import VehicleDetectionResponseParser
from .vehicle_detection_agent import VehicleDetectionAgent

__all__ = [
    "VEHICLE_DETECTION_PROMPT",
    "VehicleDetectionAgent",
    "VehicleDetectionResponseParser",
]
