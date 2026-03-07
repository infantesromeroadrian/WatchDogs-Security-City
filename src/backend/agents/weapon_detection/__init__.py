"""
Weapon/Threat Detection Agent Module - Military Intelligence

This module provides military-grade weapon and threat detection including:
- Firearm identification (type, caliber, condition)
- Bladed weapon detection
- Explosive device indicators (IED components, bomb-making materials)
- Military equipment (missiles, launchers, artillery)
- Chemical/biological threat indicators
- Improvised weapon identification
"""

from .prompts import WEAPON_DETECTION_PROMPT
from .response_parser import WeaponDetectionResponseParser
from .weapon_detection_agent import WeaponDetectionAgent

__all__ = [
    "WEAPON_DETECTION_PROMPT",
    "WeaponDetectionAgent",
    "WeaponDetectionResponseParser",
]
