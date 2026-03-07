"""
Weapon/Threat Detection Response Parser

Parses structured weapon and threat intelligence from LLM responses including:
- Weapon inventory with classifications
- Explosive device indicators
- Military equipment
- Threat assessment with escalation risk
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class WeaponDetectionResponseParser:
    """Parse structured weapon and threat intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract weapon and threat intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed weapon intelligence data
        """
        return {
            "summary": self._parse_summary(text),
            "weapons": self._parse_weapons(text),
            "weapon_count": len(self._parse_weapons(text)),
            "explosive_indicators": self._parse_explosive_indicators(text),
            "military_equipment": self._parse_military_equipment(text),
            "threat_assessment": self._parse_threat_assessment(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract weapon detection summary."""
        match = re.search(
            r"RESUMEN\s*DE\s*ARMAMENTO:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_weapons(self, text: str) -> list[dict[str, Any]]:
        """Extract individual weapon entries."""
        weapons: list[dict[str, Any]] = []

        pattern = re.compile(
            r"\*\*Arma\s*(\d+):\*\*\s*(.*?)(?=\*\*Arma\s*\d+|###|INDICADORES|$)",
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(text):
            weapon_num = int(match.group(1))
            block = match.group(2)

            weapon: dict[str, Any] = {
                "id": weapon_num,
                "type": self._extract_field(block, "Tipo"),
                "subtype": self._extract_field(block, "Subtipo"),
                "caliber": self._extract_field(block, "Calibre"),
                "make_model": self._extract_field(block, "Marca/Modelo"),
                "condition": self._extract_field(block, "Condición"),
                "operational_status": self._extract_field(block, "Estado operativo"),
                "threat_level": self._extract_field(block, "Nivel de amenaza"),
            }
            weapons.append(weapon)

        return weapons

    def _extract_field(self, block: str, field_name: str) -> str | None:
        """Extract a named field from a weapon block."""
        pattern = rf"-\s*{field_name}:\s*\[?([^\]\n]+)\]?"
        match = re.search(pattern, block, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value.lower() in ["n/a", "no visible", "no aplica", "no identificable", "-"]:
                return None
            return value
        return None

    def _parse_explosive_indicators(self, text: str) -> list[str]:
        """Extract explosive device indicators."""
        section_match = re.search(
            r"INDICADORES\s*EXPLOSIVOS:\s*(.*?)(?=###|EQUIPAMIENTO\s*MILITAR|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno|ninguna|no\s+se\s+detectan|no\s+aplica|no\s+se\s+observan",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:15]

    def _parse_military_equipment(self, text: str) -> list[str]:
        """Extract military equipment entries."""
        section_match = re.search(
            r"EQUIPAMIENTO\s*MILITAR:\s*(.*?)(?=###|EVALUACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno|ninguna|no\s+se\s+detecta|no\s+aplica|no\s+se\s+observa",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:15]

    def _parse_threat_assessment(self, text: str) -> dict[str, Any]:
        """Extract threat assessment data."""
        assessment: dict[str, Any] = {
            "threat_level": None,
            "immediate_threats": None,
            "escalation_risk": None,
        }

        # Threat level
        threat_match = re.search(
            r"Nivel\s*de\s*amenaza:\*\*\s*\[?(NINGUNO|BAJO|MEDIO|ALTO|CRÍTICO)\]?",
            text,
            re.IGNORECASE,
        )
        if threat_match:
            assessment["threat_level"] = threat_match.group(1).strip().upper()

        # Immediate threats
        immediate_match = re.search(
            r"Amenazas\s*inmediatas:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if immediate_match:
            value = immediate_match.group(1).strip()
            if value.lower() not in ["ninguna", "ninguno", "no", "-"]:
                assessment["immediate_threats"] = value

        # Escalation risk
        escalation_match = re.search(
            r"Riesgo\s*de\s*escalada:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if escalation_match:
            value = escalation_match.group(1).strip()
            if value.lower() not in ["ninguno", "ninguna", "no", "-"]:
                assessment["escalation_risk"] = value

        return assessment

    def _parse_limitations(self, text: str) -> list[str]:
        """Extract analysis limitations."""
        section_match = re.search(
            r"LIMITACIONES:\s*(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]
