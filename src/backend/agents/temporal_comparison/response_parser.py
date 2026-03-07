"""
Temporal Comparison Response Parser

Parses structured temporal change intelligence from LLM responses including:
- Structural changes (construction, demolition, temporary structures)
- Activity detection (level, type, patterns)
- Strategic posture (buildup, withdrawal, fortification, normal, crisis)
- Environmental changes (vegetation, terrain, climate)
- Estimated chronology of detected changes
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class TemporalComparisonResponseParser:
    """Parse structured temporal change intelligence from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract temporal change intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed temporal comparison data
        """
        return {
            "summary": self._parse_summary(text),
            "structural_changes": self._parse_structural_changes(text),
            "activity_detection": self._parse_activity_detection(text),
            "strategic_posture": self._parse_strategic_posture(text),
            "environmental_changes": self._parse_environmental_changes(text),
            "chronology": self._parse_chronology(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract temporal analysis summary."""
        match = re.search(
            r"RESUMEN\s*TEMPORAL:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_structural_changes(self, text: str) -> dict[str, Any]:
        """Extract structural change data."""
        changes: dict[str, Any] = {
            "active_construction": None,
            "recent_damage": None,
            "temporary_structures": [],
            "estimated_age": None,
        }

        section_match = re.search(
            r"CAMBIOS\s*ESTRUCTURALES:\s*(.*?)(?=###|ACTIVIDAD|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return changes

        section = section_match.group(1)

        # Active construction
        constr_match = re.search(
            r"Construcción\s*activa:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if constr_match:
            changes["active_construction"] = constr_match.group(1).strip()

        # Recent damage/demolition
        damage_match = re.search(
            r"Demolición/daño\s*reciente:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if damage_match:
            changes["recent_damage"] = damage_match.group(1).strip()

        # Temporary structures
        temp_match = re.search(
            r"Estructuras\s*temporales:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if temp_match:
            value = temp_match.group(1).strip()
            if value.lower() not in ["ninguna", "no", "-", "no detectadas"]:
                changes["temporary_structures"] = [s.strip() for s in value.split(",") if s.strip()]

        # Estimated age
        age_match = re.search(
            r"Antigüedad\s*estimada:\*\*\s*\[?(Horas|Días|Semanas|Meses|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if age_match:
            changes["estimated_age"] = age_match.group(1).strip()

        return changes

    def _parse_activity_detection(self, text: str) -> dict[str, Any]:
        """Extract activity detection data."""
        activity: dict[str, Any] = {
            "activity_level": None,
            "predominant_type": None,
            "unusual_patterns": None,
        }

        section_match = re.search(
            r"ACTIVIDAD\s*DETECTADA:\s*(.*?)(?=###|POSTURA|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return activity

        section = section_match.group(1)

        # Activity level
        level_match = re.search(
            r"Nivel\s*de\s*actividad:\*\*\s*\[?(Alto|Medio|Bajo|Abandonado|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if level_match:
            activity["activity_level"] = level_match.group(1).strip()

        # Predominant type
        type_match = re.search(
            r"Tipo\s*predominante:\*\*\s*\[?(Militar|Civil|Comercial|Industrial|Mixto|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if type_match:
            activity["predominant_type"] = type_match.group(1).strip()

        # Unusual patterns
        pattern_match = re.search(
            r"Patrones\s*inusuales:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if pattern_match:
            value = pattern_match.group(1).strip()
            if value.lower() not in ["ninguno", "no", "-", "no detectados"]:
                activity["unusual_patterns"] = value

        return activity

    def _parse_strategic_posture(self, text: str) -> dict[str, Any]:
        """Extract strategic posture assessment."""
        posture: dict[str, Any] = {
            "classification": None,
            "confidence": None,
            "evidence": None,
        }

        section_match = re.search(
            r"POSTURA\s*ESTRATÉGICA:\s*(.*?)(?=###|CAMBIOS\s*AMBIENTALES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return posture

        section = section_match.group(1)

        # Classification
        class_match = re.search(
            r"Clasificación:\*\*\s*\[?"
            r"(BUILDUP|WITHDRAWAL|FORTIFICATION|NORMAL|CRISIS|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if class_match:
            posture["classification"] = class_match.group(1).strip().upper()

        # Confidence
        conf_match = re.search(
            r"Confianza:\*\*\s*\[?(Alta|Media|Baja|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if conf_match:
            posture["confidence"] = conf_match.group(1).strip()

        # Evidence
        evid_match = re.search(
            r"Evidencia:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if evid_match:
            posture["evidence"] = evid_match.group(1).strip()

        return posture

    def _parse_environmental_changes(self, text: str) -> dict[str, Any]:
        """Extract environmental change data."""
        env: dict[str, Any] = {
            "vegetation": None,
            "terrain": None,
            "climate_indicators": None,
        }

        section_match = re.search(
            r"CAMBIOS\s*AMBIENTALES:\s*(.*?)(?=###|CRONOLOGÍA|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return env

        section = section_match.group(1)

        # Vegetation
        veg_match = re.search(
            r"Vegetación:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if veg_match:
            env["vegetation"] = veg_match.group(1).strip()

        # Terrain
        terrain_match = re.search(
            r"Terreno:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if terrain_match:
            env["terrain"] = terrain_match.group(1).strip()

        # Climate
        climate_match = re.search(
            r"Clima:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if climate_match:
            env["climate_indicators"] = climate_match.group(1).strip()

        return env

    def _parse_chronology(self, text: str) -> list[dict[str, str]]:
        """Extract estimated event chronology."""
        section_match = re.search(
            r"CRONOLOGÍA\s*ESTIMADA:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        chronology = []
        for item in items[:10]:
            item = item.strip()
            if not item:
                continue
            # Try to split "event - temporality"
            parts = item.split(" - ", 1)
            if len(parts) == 2:
                chronology.append(
                    {
                        "event": parts[0].strip(),
                        "timeframe": parts[1].strip(),
                    }
                )
            else:
                chronology.append({"event": item, "timeframe": "Unknown"})

        return chronology

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
