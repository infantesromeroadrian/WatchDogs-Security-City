"""
Vehicle Detection & ALPR Response Parser

Parses structured vehicle intelligence from LLM responses including:
- Vehicle inventory with classifications
- License plate readings
- Military markings
- Tactical threat assessment
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class VehicleDetectionResponseParser:
    """Parse structured vehicle intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract vehicle intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed vehicle intelligence data
        """
        return {
            "summary": self._parse_summary(text),
            "vehicles": self._parse_vehicles(text),
            "license_plates": self._parse_license_plates(text),
            "military_markings": self._parse_military_markings(text),
            "tactical_assessment": self._parse_tactical_assessment(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract vehicle summary."""
        match = re.search(
            r"RESUMEN\s*VEHICULAR:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_vehicles(self, text: str) -> list[dict[str, Any]]:
        """Extract individual vehicle entries."""
        vehicles: list[dict[str, Any]] = []

        # Find all vehicle blocks
        pattern = re.compile(
            r"\*\*Vehículo\s*(\d+):\*\*\s*(.*?)(?=\*\*Vehículo\s*\d+|###|MATRÍCULAS|$)",
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(text):
            vehicle_num = int(match.group(1))
            block = match.group(2)

            vehicle: dict[str, Any] = {
                "id": vehicle_num,
                "category": self._extract_field(block, "Categoría"),
                "type": self._extract_field(block, "Tipo"),
                "make_model": self._extract_field(block, "Marca/Modelo"),
                "color": self._extract_field(block, "Color"),
                "condition": self._extract_field(block, "Estado"),
                "position": self._extract_field(block, "Posición"),
                "license_plate": self._extract_field(block, "Matrícula"),
                "military_markings": self._extract_field(block, "Marcas militares"),
                "threat_level": self._extract_field(block, "Nivel de amenaza"),
            }
            vehicles.append(vehicle)

        return vehicles

    def _extract_field(self, block: str, field_name: str) -> str | None:
        """Extract a named field from a vehicle block."""
        pattern = rf"-\s*{field_name}:\s*\[?([^\]\n]+)\]?"
        match = re.search(pattern, block, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value.lower() in ["n/a", "no visible", "no aplica", "-"]:
                return None
            return value
        return None

    def _parse_license_plates(self, text: str) -> list[dict[str, Any]]:
        """Extract license plate readings."""
        plates: list[dict[str, Any]] = []

        section_match = re.search(
            r"MATRÍCULAS\s*DETECTADAS:\s*(.*?)(?=###|MARCAS\s*MILITARES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return plates

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        for item in items:
            plate_entry: dict[str, Any] = {
                "reading": item.strip(),
                "confidence": "medium",
            }
            # Try to extract confidence from the text
            conf_match = re.search(r"confianza[:\s]*(alta|media|baja)", item, re.IGNORECASE)
            if conf_match:
                plate_entry["confidence"] = conf_match.group(1).lower()
            plates.append(plate_entry)

        return plates[:20]  # Cap at 20 plates

    def _parse_military_markings(self, text: str) -> list[str]:
        """Extract military markings and identifiers."""
        section_match = re.search(
            r"MARCAS\s*MILITARES:\s*(.*?)(?=###|ANÁLISIS\s*TÁCTICO|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguna|ninguno|no\s+se\s+detectan|no\s+aplica", section_text, re.IGNORECASE
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]

    def _parse_tactical_assessment(self, text: str) -> dict[str, Any]:
        """Extract tactical threat assessment."""
        assessment: dict[str, Any] = {
            "threat_level": None,
            "movement_patterns": None,
            "anomalies": None,
        }

        # Threat level
        threat_match = re.search(
            r"Nivel\s*de\s*amenaza\s*vehicular:\*\*\s*\[?(NINGUNO|BAJO|MEDIO|ALTO|CRÍTICO)\]?",
            text,
            re.IGNORECASE,
        )
        if threat_match:
            assessment["threat_level"] = threat_match.group(1).strip().upper()

        # Movement patterns
        movement_match = re.search(
            r"Patrones\s*de\s*movimiento:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if movement_match:
            assessment["movement_patterns"] = movement_match.group(1).strip()

        # Anomalies
        anomaly_match = re.search(
            r"Anomalías:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if anomaly_match:
            value = anomaly_match.group(1).strip()
            if value.lower() not in ["ninguna", "ninguno", "no", "-"]:
                assessment["anomalies"] = value

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
