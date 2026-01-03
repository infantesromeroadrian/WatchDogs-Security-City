"""
Geolocation Module - Supporting components for GeolocationAgent
Single Responsibility: Provide prompts and parsing utilities
"""

from .prompts import GEOLOCATION_PROMPT
from .response_parser import GeolocationResponseParser

__all__ = ["GEOLOCATION_PROMPT", "GeolocationResponseParser"]
