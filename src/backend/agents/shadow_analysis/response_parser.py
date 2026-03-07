"""
Shadow/Sun Analysis Response Parser

Parses structured shadow and sun intelligence from LLM responses including:
- Shadow geometry (direction, length ratio, consistency)
- Sun position (azimuth, elevation, hemisphere)
- Time estimation (range, confidence, evidence)
- Season inference
- Lighting analysis
- Forensic indicators
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ShadowAnalysisResponseParser:
    """Parse structured shadow and sun intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract shadow and sun intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed shadow analysis data
        """
        return {
            "summary": self._parse_summary(text),
            "shadow_geometry": self._parse_shadow_geometry(text),
            "sun_position": self._parse_sun_position(text),
            "time_estimate": self._parse_time_estimate(text),
            "season_inference": self._parse_season_inference(text),
            "lighting_analysis": self._parse_lighting_analysis(text),
            "forensic_indicators": self._parse_forensic_indicators(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract shadow analysis summary."""
        match = re.search(
            r"RESUMEN\s*SOLAR:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_shadow_geometry(self, text: str) -> dict[str, Any]:
        """Extract shadow geometry data."""
        geometry: dict[str, Any] = {
            "direction": None,
            "length_ratio": None,
            "consistency": None,
        }

        # Direction
        dir_match = re.search(
            r"Dirección:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if dir_match:
            geometry["direction"] = dir_match.group(1).strip()

        # Length ratio
        ratio_match = re.search(
            r"Proporción\s*longitud/altura:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if ratio_match:
            geometry["length_ratio"] = ratio_match.group(1).strip()

        # Consistency
        consist_match = re.search(
            r"Consistencia:\*\*\s*\[?(Consistente|Inconsistente|[^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if consist_match:
            geometry["consistency"] = consist_match.group(1).strip()

        return geometry

    def _parse_sun_position(self, text: str) -> dict[str, Any]:
        """Extract sun position data."""
        position: dict[str, Any] = {
            "azimuth_estimate": None,
            "elevation_estimate": None,
            "hemisphere": None,
        }

        # Azimuth
        azimuth_match = re.search(
            r"Azimut\s*estimado:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if azimuth_match:
            position["azimuth_estimate"] = azimuth_match.group(1).strip()

        # Elevation
        elevation_match = re.search(
            r"Elevación\s*estimada:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if elevation_match:
            position["elevation_estimate"] = elevation_match.group(1).strip()

        # Hemisphere
        hemi_match = re.search(
            r"Hemisferio:\*\*\s*\[?(Norte|Sur|Indeterminado|[^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if hemi_match:
            position["hemisphere"] = hemi_match.group(1).strip()

        return position

    def _parse_time_estimate(self, text: str) -> dict[str, Any]:
        """Extract time estimation data."""
        time_est: dict[str, Any] = {
            "time_range": None,
            "confidence": None,
            "evidence": None,
        }

        # Time range
        time_match = re.search(
            r"Rango\s*horario:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if time_match:
            time_est["time_range"] = time_match.group(1).strip()

        # Confidence (in time section)
        section_match = re.search(
            r"ESTIMACIÓN\s*TEMPORAL:\s*(.*?)(?=###|INFERENCIA|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if section_match:
            section = section_match.group(1)
            conf_match = re.search(
                r"Confianza:\*\*\s*\[?(Alta|Media|Baja|[^\]\n]+)\]?",
                section,
                re.IGNORECASE,
            )
            if conf_match:
                time_est["confidence"] = conf_match.group(1).strip()

            evid_match = re.search(
                r"Evidencia:\*\*\s*\[?([^\]\n]+)\]?",
                section,
                re.IGNORECASE,
            )
            if evid_match:
                time_est["evidence"] = evid_match.group(1).strip()

        return time_est

    def _parse_season_inference(self, text: str) -> dict[str, Any]:
        """Extract season inference data."""
        season: dict[str, Any] = {
            "estimated_season": None,
            "confidence": None,
            "evidence": None,
        }

        section_match = re.search(
            r"INFERENCIA\s*ESTACIONAL:\s*(.*?)(?=###|ANÁLISIS\s*DE\s*ILUMINACIÓN|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return season

        section = section_match.group(1)

        # Season
        season_match = re.search(
            r"Estación\s*estimada:\*\*\s*\[?(Primavera|Verano|Otoño|Invierno|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if season_match:
            season["estimated_season"] = season_match.group(1).strip()

        # Confidence
        conf_match = re.search(
            r"Confianza:\*\*\s*\[?(Alta|Media|Baja|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if conf_match:
            season["confidence"] = conf_match.group(1).strip()

        # Evidence
        evid_match = re.search(
            r"Evidencia:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if evid_match:
            season["evidence"] = evid_match.group(1).strip()

        return season

    def _parse_lighting_analysis(self, text: str) -> dict[str, Any]:
        """Extract lighting analysis data."""
        lighting: dict[str, Any] = {
            "primary_source": None,
            "artificial_sources": None,
            "consistency": None,
        }

        # Primary source
        source_match = re.search(
            r"Fuente\s*principal:\*\*\s*\[?(Natural|Artificial|Mixta|[^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if source_match:
            lighting["primary_source"] = source_match.group(1).strip()

        # Artificial sources
        art_match = re.search(
            r"Fuentes\s*artificiales:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if art_match:
            value = art_match.group(1).strip()
            if value.lower() not in ["ninguna", "no identificadas", "no", "-"]:
                lighting["artificial_sources"] = value

        # Consistency (in lighting section)
        section_match = re.search(
            r"ANÁLISIS\s*DE\s*ILUMINACIÓN:\s*(.*?)(?=###|INDICADORES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if section_match:
            section = section_match.group(1)
            consist_match = re.search(
                r"Consistencia:\*\*\s*\[?(Consistente|Inconsistente|[^\]\n]+)\]?",
                section,
                re.IGNORECASE,
            )
            if consist_match:
                lighting["consistency"] = consist_match.group(1).strip()

        return lighting

    def _parse_forensic_indicators(self, text: str) -> list[str]:
        """Extract forensic indicators of manipulation."""
        section_match = re.search(
            r"INDICADORES\s*FORENSES:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        if re.search(
            r"ninguno\s*detectado|ninguno|ninguna|no\s+se\s+detectan",
            section_text,
            re.IGNORECASE,
        ):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]

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
