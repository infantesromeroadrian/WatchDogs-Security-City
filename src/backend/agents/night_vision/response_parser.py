"""
Night Vision Enhancement Response Parser

Parses structured night vision intelligence from LLM responses including:
- Visibility conditions (illumination level, range, quality)
- Light source inventory (type, intensity, anomalies)
- Nocturnal activity (personnel, vehicles, operations)
- Covert activity indicators (concealment, thermal signatures)
- Tactical assessment (vulnerabilities, surveillance coverage, risk)
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class NightVisionResponseParser:
    """Parse structured night vision intelligence from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract night vision intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed night vision data
        """
        return {
            "summary": self._parse_summary(text),
            "visibility_conditions": self._parse_visibility(text),
            "light_sources": self._parse_light_sources(text),
            "nocturnal_activity": self._parse_nocturnal_activity(text),
            "covert_indicators": self._parse_covert_indicators(text),
            "tactical_assessment": self._parse_tactical_assessment(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract night vision analysis summary."""
        match = re.search(
            r"RESUMEN\s*NOCTURNO:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_visibility(self, text: str) -> dict[str, Any]:
        """Extract visibility conditions data."""
        visibility: dict[str, Any] = {
            "illumination_level": None,
            "observation_range": None,
            "image_quality": None,
        }

        section_match = re.search(
            r"CONDICIONES\s*DE\s*VISIBILIDAD:\s*(.*?)(?=###|FUENTES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return visibility

        section = section_match.group(1)

        # Illumination level
        illum_match = re.search(
            r"Nivel\s*de\s*iluminación:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if illum_match:
            visibility["illumination_level"] = illum_match.group(1).strip()

        # Observation range
        range_match = re.search(
            r"Rango\s*de\s*observación:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if range_match:
            visibility["observation_range"] = range_match.group(1).strip()

        # Image quality
        quality_match = re.search(
            r"Calidad\s*de\s*imagen:\*\*\s*\[?(Buena|Aceptable|Degradada|Muy\s*pobre|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if quality_match:
            visibility["image_quality"] = quality_match.group(1).strip()

        return visibility

    def _parse_light_sources(self, text: str) -> dict[str, Any]:
        """Extract light source inventory."""
        sources: dict[str, Any] = {
            "total_count": None,
            "dominant_type": None,
            "anomalous_sources": None,
        }

        section_match = re.search(
            r"FUENTES\s*DE\s*LUZ:\s*(.*?)(?=###|ACTIVIDAD|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return sources

        section = section_match.group(1)

        # Total count
        count_match = re.search(
            r"Cantidad\s*total:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if count_match:
            value = count_match.group(1).strip()
            try:
                sources["total_count"] = int(value)
            except ValueError:
                sources["total_count"] = value

        # Dominant type
        type_match = re.search(
            r"Tipo\s*dominante:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if type_match:
            sources["dominant_type"] = type_match.group(1).strip()

        # Anomalous sources
        anom_match = re.search(
            r"Fuentes\s*anómalas:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if anom_match:
            value = anom_match.group(1).strip()
            if value.lower() not in ["ninguna", "no", "-", "no detectadas"]:
                sources["anomalous_sources"] = value

        return sources

    def _parse_nocturnal_activity(self, text: str) -> dict[str, Any]:
        """Extract nocturnal activity data."""
        activity: dict[str, Any] = {
            "activity_level": None,
            "personnel_detected": None,
            "active_vehicles": None,
            "operations": None,
        }

        section_match = re.search(
            r"ACTIVIDAD\s*NOCTURNA:\s*(.*?)(?=###|INDICADORES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return activity

        section = section_match.group(1)

        # Activity level
        level_match = re.search(
            r"Nivel\s*de\s*actividad:\*\*\s*\[?(Alto|Medio|Bajo|Nulo|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if level_match:
            activity["activity_level"] = level_match.group(1).strip()

        # Personnel
        pers_match = re.search(
            r"Personal\s*detectado:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if pers_match:
            activity["personnel_detected"] = pers_match.group(1).strip()

        # Vehicles
        veh_match = re.search(
            r"Vehículos\s*activos:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if veh_match:
            activity["active_vehicles"] = veh_match.group(1).strip()

        # Operations
        ops_match = re.search(
            r"Operaciones:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if ops_match:
            activity["operations"] = ops_match.group(1).strip()

        return activity

    def _parse_covert_indicators(self, text: str) -> dict[str, Any]:
        """Extract covert activity indicators."""
        covert: dict[str, Any] = {
            "concealment_detected": None,
            "thermal_signatures": None,
            "suspicion_level": None,
        }

        section_match = re.search(
            r"INDICADORES\s*ENCUBIERTOS:\s*(.*?)(?=###|EVALUACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return covert

        section = section_match.group(1)

        # Concealment
        conceal_match = re.search(
            r"Ocultación\s*detectada:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if conceal_match:
            covert["concealment_detected"] = conceal_match.group(1).strip()

        # Thermal
        thermal_match = re.search(
            r"Firmas\s*térmicas:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if thermal_match:
            covert["thermal_signatures"] = thermal_match.group(1).strip()

        # Suspicion level
        susp_match = re.search(
            r"Nivel\s*de\s*sospecha:\*\*\s*\[?(Alto|Medio|Bajo|Nulo|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if susp_match:
            covert["suspicion_level"] = susp_match.group(1).strip()

        return covert

    def _parse_tactical_assessment(self, text: str) -> dict[str, Any]:
        """Extract tactical night assessment."""
        tactical: dict[str, Any] = {
            "vulnerabilities": None,
            "surveillance_coverage": None,
            "night_risk_level": None,
        }

        section_match = re.search(
            r"EVALUACIÓN\s*TÁCTICA:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return tactical

        section = section_match.group(1)

        # Vulnerabilities
        vuln_match = re.search(
            r"Vulnerabilidades:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if vuln_match:
            tactical["vulnerabilities"] = vuln_match.group(1).strip()

        # Surveillance coverage
        surv_match = re.search(
            r"Cobertura\s*de\s*vigilancia:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if surv_match:
            tactical["surveillance_coverage"] = surv_match.group(1).strip()

        # Night risk level
        risk_match = re.search(
            r"Nivel\s*de\s*riesgo\s*nocturno:\*\*\s*\[?"
            r"(CRITICAL|HIGH|MEDIUM|LOW|MINIMAL|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if risk_match:
            tactical["night_risk_level"] = risk_match.group(1).strip().upper()

        return tactical

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
