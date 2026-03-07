"""
Infrastructure Analysis Response Parser

Parses structured infrastructure intelligence from LLM responses including:
- Building inventory with classifications
- Road network assessment
- Utility infrastructure
- Bridges and structural elements
- Signage analysis
- Strategic assessment
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class InfrastructureAnalysisResponseParser:
    """Parse structured infrastructure intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract infrastructure intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed infrastructure intelligence data
        """
        return {
            "summary": self._parse_summary(text),
            "buildings": self._parse_buildings(text),
            "roads": self._parse_roads(text),
            "utilities": self._parse_utilities(text),
            "bridges": self._parse_bridges(text),
            "signage": self._parse_signage(text),
            "strategic_assessment": self._parse_strategic_assessment(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract infrastructure analysis summary."""
        match = re.search(
            r"RESUMEN\s*DE\s*INFRAESTRUCTURA:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_buildings(self, text: str) -> list[dict[str, Any]]:
        """Extract individual building entries."""
        buildings: list[dict[str, Any]] = []

        pattern = re.compile(
            r"\*\*Edificio\s*(\d+):\*\*\s*(.*?)(?=\*\*Edificio\s*\d+|###|RED\s*VIAL|$)",
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(text):
            building_num = int(match.group(1))
            block = match.group(2)

            building: dict[str, Any] = {
                "id": building_num,
                "type": self._extract_field(block, "Tipo"),
                "stories": self._extract_field(block, "Pisos"),
                "condition": self._extract_field(block, "Condición"),
                "age": self._extract_field(block, "Antigüedad"),
                "strategic_value": self._extract_field(block, "Valor estratégico"),
            }
            buildings.append(building)

        return buildings

    def _extract_field(self, block: str, field_name: str) -> str | None:
        """Extract a named field from a block."""
        pattern = rf"-\s*{field_name}:\s*\[?([^\]\n]+)\]?"
        match = re.search(pattern, block, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value.lower() in ["n/a", "no visible", "no aplica", "no determinable", "-"]:
                return None
            return value
        return None

    def _parse_roads(self, text: str) -> list[dict[str, Any]]:
        """Extract road entries."""
        roads: list[dict[str, Any]] = []

        pattern = re.compile(
            r"\*\*Vía\s*(\d+):\*\*\s*(.*?)(?=\*\*Vía\s*\d+|###|SERVICIOS|$)",
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(text):
            road_num = int(match.group(1))
            block = match.group(2)

            road: dict[str, Any] = {
                "id": road_num,
                "type": self._extract_field(block, "Tipo"),
                "surface": self._extract_field(block, "Superficie"),
                "lanes": self._extract_field(block, "Carriles"),
                "capacity": self._extract_field(block, "Capacidad"),
            }
            roads.append(road)

        return roads

    def _parse_utilities(self, text: str) -> list[str]:
        """Extract utility infrastructure entries."""
        section_match = re.search(
            r"SERVICIOS:\s*(.*?)(?=###|PUENTES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno|ninguna|no\s+se\s+detectan|no\s+aplica|no\s+se\s+identifican",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:20]

    def _parse_bridges(self, text: str) -> list[str]:
        """Extract bridge and structure entries."""
        section_match = re.search(
            r"PUENTES:\s*(.*?)(?=###|SEÑALIZACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno|ninguna|no\s+se\s+detectan|no\s+aplica|no\s+se\s+identifican",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]

    def _parse_signage(self, text: str) -> list[str]:
        """Extract signage entries."""
        section_match = re.search(
            r"SEÑALIZACIÓN:\s*(.*?)(?=###|EVALUACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno|ninguna|no\s+se\s+detectan|no\s+aplica|no\s+se\s+identifican",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:20]

    def _parse_strategic_assessment(self, text: str) -> dict[str, Any]:
        """Extract strategic assessment data."""
        assessment: dict[str, Any] = {
            "critical_infrastructure": None,
            "vulnerability_points": None,
            "military_significance": None,
        }

        # Critical infrastructure
        critical_match = re.search(
            r"Infraestructura\s*crítica:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if critical_match:
            value = critical_match.group(1).strip()
            if value.lower() not in ["ninguna", "no identificada", "no", "-"]:
                assessment["critical_infrastructure"] = value

        # Vulnerability points
        vuln_match = re.search(
            r"Puntos\s*de\s*vulnerabilidad:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if vuln_match:
            value = vuln_match.group(1).strip()
            if value.lower() not in ["ninguno", "no identificados", "no", "-"]:
                assessment["vulnerability_points"] = value

        # Military significance
        mil_match = re.search(
            r"Significancia\s*militar:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if mil_match:
            value = mil_match.group(1).strip()
            if value.lower() not in ["ninguna", "no", "-"]:
                assessment["military_significance"] = value

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
