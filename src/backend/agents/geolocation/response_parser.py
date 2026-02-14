"""
Geolocation Response Parser - CIA-Level OSINT Analysis
Single Responsibility: Parse structured data from LLM geolocation responses

Enhanced to extract:
- Hierarchical location (country → region → city → district → street → number)
- Confidence levels per component
- Evidence chain with individual confidence scores
- Temporal analysis (time, season, date estimates)
- Confidence radius for coordinates
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class GeolocationResponseParser:
    """Parse structured location data from CIA-level geolocation LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract comprehensive location intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed location data including evidence chain
        """
        return {
            "location": self._parse_location(text),
            "coordinates": self._parse_coordinates(text),
            "confidence": self._parse_overall_confidence(text),
            "confidence_by_level": self._parse_confidence_by_level(text),
            "evidence_chain": self._parse_evidence_chain(text),
            "temporal_analysis": self._parse_temporal_analysis(text),
            "key_clues": self._parse_clues(text),  # Backward compatibility
            "limitations": self._parse_limitations(text),
            "verification_suggestions": self._parse_verification(text),
        }

    # =========================================================================
    # LOCATION PARSING
    # =========================================================================

    def _parse_location(self, text: str) -> dict[str, str | None]:
        """
        Extract hierarchical location components.

        Returns dict with all levels, None for undetermined.
        """
        location: dict[str, str | None] = {
            "country": self._extract_field(text, r"País:\s*(.+?)(?:\n|$)"),
            "region": self._extract_field(text, r"Región/Estado/Provincia:\s*(.+?)(?:\n|$)"),
            "city": self._extract_field(text, r"Ciudad:\s*(.+?)(?:\n|$)"),
            "district": self._extract_field(text, r"Distrito/Barrio:\s*(.+?)(?:\n|$)"),
            "street": self._extract_field(text, r"Calle:\s*(.+?)(?:\n|$)"),
            "number": self._extract_field(text, r"Número/Dirección:\s*(.+?)(?:\n|$)"),
        }

        # Filter out "No determinado" values but keep structure
        for key, value in location.items():
            if value and "no determinad" in value.lower():
                location[key] = None

        return location

    def _extract_field(self, text: str, pattern: str) -> str | None:
        """Generic field extractor with cleanup."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Remove markdown formatting
            value = re.sub(r"\*+", "", value)
            # Remove trailing punctuation
            value = value.rstrip(".,;:")
            return value if value else None
        return None

    # =========================================================================
    # COORDINATES PARSING
    # =========================================================================

    def _parse_coordinates(self, text: str) -> dict[str, Any] | None:
        """
        Extract coordinates with confidence radius.

        Returns:
            Dict with lat, lon, and confidence_radius_meters
        """
        # Multiple patterns for coordinate extraction
        coords_patterns = [
            # Standard format: Coordenadas estimadas: [40.4168, -3.7038]
            r"Coordenadas\s*(?:estimadas)?:\s*\[?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]?",
            # Lat/lon format
            r"lat(?:itud)?[:\s]+(-?\d+\.?\d*).*?lon(?:gitud)?[:\s]+(-?\d+\.?\d*)",
            # Parentheses format: (40.4168, -3.7038)
            r"\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)",
            # Plain decimal format
            r"(-?\d+\.\d{4,})\s*,\s*(-?\d+\.\d{4,})",
        ]

        coords = None
        for pattern in coords_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))

                    # Validate coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        coords = {"lat": lat, "lon": lon}
                        break
                    logger.warning("Coordinates out of range: %s, %s", lat, lon)
                except (ValueError, IndexError) as e:
                    logger.warning("Failed to parse coordinates: %s", e)
                    continue

        if not coords:
            return None

        # Extract confidence radius
        radius_match = re.search(
            r"Radio\s*(?:de)?\s*(?:confianza)?:\s*(\d+)\s*(?:metros?|m|km)?",
            text,
            re.IGNORECASE,
        )
        if radius_match:
            radius = int(radius_match.group(1))
            # Convert km to meters if needed
            if "km" in text[radius_match.start() : radius_match.end()].lower():
                radius *= 1000
            coords["confidence_radius_meters"] = radius
        else:
            # Estimate radius based on location precision
            coords["confidence_radius_meters"] = self._estimate_radius(text)

        return coords

    def _estimate_radius(self, text: str) -> int:
        """Estimate confidence radius based on location detail level."""
        location = self._parse_location(text)

        if location.get("number"):
            return 50  # Building level
        if location.get("street"):
            return 200  # Street level
        if location.get("district"):
            return 1000  # Neighborhood level
        if location.get("city"):
            return 5000  # City level
        if location.get("region"):
            return 50000  # Region level
        if location.get("country"):
            return 500000  # Country level

        return 1000000  # Unknown

    # =========================================================================
    # CONFIDENCE PARSING
    # =========================================================================

    def _parse_overall_confidence(self, text: str) -> str:
        """Extract overall confidence level (backward compatible)."""
        # Try new format first (per-component)
        patterns = [
            r"País:.*?(Muy Alto|Alto|Medio|Bajo|Muy Bajo)",
            r"NIVEL DE CONFIANZA.*?:\s*(Muy Alto|Alto|Medio|Bajo|Muy Bajo)",
            r"Confianza.*?:\s*(Muy Alto|Alto|Medio|Bajo|Muy Bajo)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).lower()

        return "unknown"

    def _parse_confidence_by_level(self, text: str) -> dict[str, dict[str, str]]:
        """
        Extract confidence levels for each location component.

        Returns:
            Dict mapping component to {level, justification}
        """
        confidence: dict[str, dict[str, str]] = {}

        # Patterns for each component
        components = [
            ("country", r"País:\s*\[(Muy Alto|Alto|Medio|Bajo|Muy Bajo)\]\s*-?\s*(.*)"),
            ("region", r"Región:\s*\[(Muy Alto|Alto|Medio|Bajo|Muy Bajo)\]\s*-?\s*(.*)"),
            ("city", r"Ciudad:\s*\[(Muy Alto|Alto|Medio|Bajo|Muy Bajo)\]\s*-?\s*(.*)"),
            (
                "exact_location",
                r"Ubicación exacta:\s*\[(Muy Alto|Alto|Medio|Bajo|Muy Bajo)\]\s*-?\s*(.*)",
            ),
        ]

        for component, pattern in components:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                confidence[component] = {
                    "level": match.group(1).lower(),
                    "justification": match.group(2).strip() if match.group(2) else "",
                }

        return confidence

    # =========================================================================
    # EVIDENCE CHAIN PARSING
    # =========================================================================

    def _parse_evidence_chain(self, text: str) -> list[dict[str, Any]]:
        """
        Extract the evidence chain with confidence scores.

        Returns:
            List of evidence items with confidence and what they support
        """
        evidence_chain: list[dict[str, Any]] = []

        # Find evidence section
        evidence_section = re.search(
            r"CADENA DE EVIDENCIAS.*?:(.*?)(?:###|ANÁLISIS TEMPORAL|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if not evidence_section:
            # Fallback to old format (PISTAS CLAVE)
            return self._parse_clues_as_evidence(text)

        evidence_text = evidence_section.group(1)

        # Pattern: 1. [Evidence] - Confianza: X% - Soporta: [conclusion]
        pattern = (
            r"\d+\.\s*\[?([^\]]+)\]?\s*-\s*Confianza:\s*(\d+)%?\s*-\s*Soporta:\s*(.+?)(?:\n|$)"
        )
        matches = re.findall(pattern, evidence_text, re.IGNORECASE)

        for match in matches:
            evidence_chain.append(
                {
                    "evidence": match[0].strip(),
                    "confidence_percent": int(match[1]),
                    "supports": match[2].strip(),
                }
            )

        # If no structured matches, try simpler pattern
        if not evidence_chain:
            simple_pattern = r"\d+\.\s*(.+?)(?:\n|$)"
            simple_matches = re.findall(simple_pattern, evidence_text)
            for idx, match in enumerate(simple_matches[:10]):  # Max 10
                evidence_chain.append(
                    {
                        "evidence": match.strip(),
                        "confidence_percent": None,
                        "supports": "general",
                        "order": idx + 1,
                    }
                )

        return evidence_chain

    def _parse_clues_as_evidence(self, text: str) -> list[dict[str, Any]]:
        """Convert old-style clues to evidence format."""
        clues = self._parse_clues(text)
        return [
            {"evidence": clue, "confidence_percent": None, "supports": "general"} for clue in clues
        ]

    def _parse_clues(self, text: str) -> list[str]:
        """
        Extract key clues list (backward compatible).

        Returns:
            List of clue strings
        """
        # Try new format first
        evidence_section = re.search(
            r"CADENA DE EVIDENCIAS.*?:(.*?)(?:###|ANÁLISIS|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if evidence_section:
            clues_text = evidence_section.group(1)
        else:
            # Fallback to old format
            clues_section = re.search(
                r"PISTAS CLAVE.*?:(.*?)(?:\*\*|###|$)",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if not clues_section:
                return []
            clues_text = clues_section.group(1)

        # Extract bullet points or numbered items
        clues = re.findall(r"[-•\d.]+\s*\[?([^\]\n]+)\]?", clues_text)

        # Clean and deduplicate
        cleaned = []
        seen = set()
        for clue in clues:
            clean_clue = clue.strip().rstrip(".,;:-")
            if clean_clue and clean_clue.lower() not in seen:
                cleaned.append(clean_clue)
                seen.add(clean_clue.lower())

        return cleaned[:10]  # Max 10 clues

    # =========================================================================
    # TEMPORAL ANALYSIS PARSING
    # =========================================================================

    def _parse_temporal_analysis(self, text: str) -> dict[str, str | None]:
        """
        Extract temporal analysis (time, season, date).

        Returns:
            Dict with estimated_time, season, estimated_date
        """
        temporal: dict[str, str | None] = {
            "estimated_time": None,
            "season": None,
            "estimated_date": None,
        }

        # Time extraction
        time_match = re.search(r"Hora\s*(?:estimada)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if time_match:
            value = time_match.group(1).strip()
            if "no determinable" not in value.lower():
                temporal["estimated_time"] = value

        # Season extraction
        season_match = re.search(r"Época\s*(?:del año)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if season_match:
            value = season_match.group(1).strip()
            if "no determinable" not in value.lower():
                temporal["season"] = value

        # Date extraction
        date_match = re.search(r"Fecha\s*(?:aproximada)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if date_match:
            value = date_match.group(1).strip()
            if "no determinable" not in value.lower():
                temporal["estimated_date"] = value

        return temporal

    # =========================================================================
    # LIMITATIONS AND VERIFICATION PARSING
    # =========================================================================

    def _parse_limitations(self, text: str) -> list[str]:
        """Extract analysis limitations and caveats."""
        limitations_section = re.search(
            r"LIMITACIONES.*?:(.*?)(?:###|$)", text, re.IGNORECASE | re.DOTALL
        )

        if not limitations_section:
            return []

        limitations_text = limitations_section.group(1)
        limitations = re.findall(r"[-•]\s*(.+?)(?:\n|$)", limitations_text)

        return [lim.strip() for lim in limitations if lim.strip()][:5]

    def _parse_verification(self, text: str) -> dict[str, list[str]]:
        """Extract verification suggestions."""
        verification: dict[str, list[str]] = {
            "search_terms": [],
            "alternative_coordinates": [],
            "additional_sources": [],
        }

        # Search terms
        search_match = re.search(
            r"Búsquedas\s*(?:recomendadas)?:\s*(.+?)(?:\n-|\n\n|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if search_match:
            terms = re.findall(r"\[([^\]]+)\]", search_match.group(1))
            if not terms:
                terms = [search_match.group(1).strip()]
            verification["search_terms"] = [t.strip() for t in terms if t.strip()]

        # Alternative coordinates
        alt_coords_match = re.search(
            r"Coordenadas\s*(?:para)?\s*(?:verificar)?:\s*(.+?)(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if alt_coords_match:
            coords = re.findall(r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)", alt_coords_match.group(1))
            verification["alternative_coordinates"] = [f"{lat}, {lon}" for lat, lon in coords]

        # Additional sources
        sources_match = re.search(
            r"Fuentes\s*(?:adicionales)?:\s*(.+?)(?:\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if sources_match:
            sources = re.findall(r"[-•]\s*(.+?)(?:\n|$)", sources_match.group(1))
            verification["additional_sources"] = [s.strip() for s in sources if s.strip()]

        return verification
