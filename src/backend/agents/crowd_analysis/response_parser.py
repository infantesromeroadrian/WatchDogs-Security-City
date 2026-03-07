"""
Crowd Analysis Response Parser

Parses structured crowd intelligence from LLM responses including:
- Density estimation with zone breakdown
- Demographic profiling
- Movement patterns
- Behavioral assessment
- Security concerns
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CrowdAnalysisResponseParser:
    """Parse structured crowd intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract crowd intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed crowd intelligence data
        """
        return {
            "summary": self._parse_summary(text),
            "density_estimate": self._parse_density_estimate(text),
            "demographics": self._parse_demographics(text),
            "movement_patterns": self._parse_movement_patterns(text),
            "behavioral_assessment": self._parse_behavioral_assessment(text),
            "security_concerns": self._parse_security_concerns(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract crowd analysis summary."""
        match = re.search(
            r"RESUMEN\s*DE\s*MULTITUD:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_density_estimate(self, text: str) -> dict[str, Any]:
        """Extract density estimation data."""
        density: dict[str, Any] = {
            "total_count": None,
            "density_level": None,
            "zones": {},
        }

        # Total count
        total_match = re.search(
            r"Total\s*estimado:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if total_match:
            value = total_match.group(1).strip()
            # Try to extract a number
            num_match = re.search(r"(\d+)", value)
            if num_match:
                density["total_count"] = int(num_match.group(1))
            else:
                density["total_count"] = value

        # Density level
        level_match = re.search(
            r"Nivel\s*de\s*densidad:\*\*\s*\[?(DISPERSA|MODERADA|DENSA|CRÍTICA)\]?",
            text,
            re.IGNORECASE,
        )
        if level_match:
            density["density_level"] = level_match.group(1).strip().upper()

        # Zones
        zone_section = re.search(
            r"Zonas:\*?\*?\s*(.*?)(?=###|PERFIL|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if zone_section:
            zone_text = zone_section.group(1)
            zone_patterns = [
                ("primer_plano", r"Primer\s*plano:\s*\[?([^\]\n]+)\]?"),
                ("zona_media", r"Zona\s*media:\s*\[?([^\]\n]+)\]?"),
                ("fondo", r"Fondo:\s*\[?([^\]\n]+)\]?"),
            ]
            for zone_key, pattern in zone_patterns:
                zone_match = re.search(pattern, zone_text, re.IGNORECASE)
                if zone_match:
                    density["zones"][zone_key] = zone_match.group(1).strip()

        return density

    def _parse_demographics(self, text: str) -> dict[str, Any]:
        """Extract demographic profile data."""
        demographics: dict[str, Any] = {
            "age_ranges": None,
            "gender_distribution": None,
            "predominant_attire": None,
            "uniforms": None,
        }

        section_match = re.search(
            r"PERFIL\s*DEMOGRÁFICO:\s*(.*?)(?=###|PATRONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return demographics

        section_text = section_match.group(1)

        # Age ranges
        age_match = re.search(
            r"Rangos\s*de\s*edad:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if age_match:
            demographics["age_ranges"] = age_match.group(1).strip()

        # Gender distribution
        gender_match = re.search(
            r"Distribución\s*de\s*género:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if gender_match:
            demographics["gender_distribution"] = gender_match.group(1).strip()

        # Predominant attire
        attire_match = re.search(
            r"Vestimenta\s*predominante:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if attire_match:
            demographics["predominant_attire"] = attire_match.group(1).strip()

        # Uniforms
        uniform_match = re.search(
            r"Uniformes:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if uniform_match:
            value = uniform_match.group(1).strip()
            if value.lower() not in ["ninguno", "no identificados", "no", "-"]:
                demographics["uniforms"] = value

        return demographics

    def _parse_movement_patterns(self, text: str) -> dict[str, Any]:
        """Extract movement pattern data."""
        movement: dict[str, Any] = {
            "predominant_direction": None,
            "speed": None,
            "bottlenecks": None,
            "general_pattern": None,
        }

        section_match = re.search(
            r"PATRONES\s*DE\s*MOVIMIENTO:\s*(.*?)(?=###|EVALUACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return movement

        section_text = section_match.group(1)

        # Direction
        dir_match = re.search(
            r"Dirección\s*predominante:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if dir_match:
            movement["predominant_direction"] = dir_match.group(1).strip()

        # Speed
        speed_match = re.search(
            r"Velocidad:\s*\[?(Lenta|Normal|Rápida|[^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if speed_match:
            movement["speed"] = speed_match.group(1).strip()

        # Bottlenecks
        bottle_match = re.search(
            r"Cuellos\s*de\s*botella:\s*\[?([^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if bottle_match:
            value = bottle_match.group(1).strip()
            if value.lower() not in ["ninguno", "no identificados", "no", "-"]:
                movement["bottlenecks"] = value

        # General pattern
        pattern_match = re.search(
            r"Patrón\s*general:\s*\[?(Convergencia|Dispersión|Estático|Flujo|[^\]\n]+)\]?",
            section_text,
            re.IGNORECASE,
        )
        if pattern_match:
            movement["general_pattern"] = pattern_match.group(1).strip()

        return movement

    def _parse_behavioral_assessment(self, text: str) -> dict[str, Any]:
        """Extract behavioral assessment data."""
        assessment: dict[str, Any] = {
            "general_mood": None,
            "anomalous_behaviors": None,
            "group_formations": None,
        }

        # General mood
        mood_match = re.search(
            r"Estado\s*de\s*ánimo\s*general:\*\*\s*\[?(Calmado|Alerta|Tenso|Agitado|Pánico|[^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if mood_match:
            assessment["general_mood"] = mood_match.group(1).strip()

        # Anomalous behaviors
        anomaly_match = re.search(
            r"Comportamientos\s*anómalos:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if anomaly_match:
            value = anomaly_match.group(1).strip()
            if value.lower() not in [
                "ninguno detectado",
                "ninguno",
                "no",
                "-",
                "no se detectan",
            ]:
                assessment["anomalous_behaviors"] = value

        # Group formations
        group_match = re.search(
            r"Formaciones\s*de\s*grupo:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if group_match:
            value = group_match.group(1).strip()
            if value.lower() not in ["ninguna", "ninguno", "no", "-"]:
                assessment["group_formations"] = value

        return assessment

    def _parse_security_concerns(self, text: str) -> list[str]:
        """Extract security concerns."""
        section_match = re.search(
            r"PREOCUPACIONES\s*DE\s*SEGURIDAD:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguna|ninguno|no\s+se\s+detectan|no\s+aplica|no\s+se\s+identifican",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:15]

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
