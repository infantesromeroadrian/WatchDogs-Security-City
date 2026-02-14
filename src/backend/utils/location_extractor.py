"""
Location extractor for free-form text (chat responses, reports).

Extracts explicit coordinates from LLM responses using regex patterns
proven in the GeolocationResponseParser.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Coordinate regex patterns — reused from geolocation/response_parser.py
_COORD_PATTERNS: list[re.Pattern[str]] = [
    # "Coordenadas estimadas: [40.4168, -3.7038]"
    re.compile(
        r"Coordenadas\s*(?:estimadas)?:\s*\[?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]?",
        re.IGNORECASE,
    ),
    # "latitud: 40.4168 ... longitud: -3.7038"
    re.compile(
        r"lat(?:itud)?[:\s]+(-?\d+\.?\d*).*?lon(?:gitud)?[:\s]+(-?\d+\.?\d*)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "(40.4168, -3.7038)"
    re.compile(r"\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)"),
    # "40.4168, -3.7038" (at least 4 decimal places)
    re.compile(r"(-?\d+\.\d{4,})\s*,\s*(-?\d+\.\d{4,})"),
    # "GPS: 40.4168, -3.7038"
    re.compile(
        r"GPS[:\s]+(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)",
        re.IGNORECASE,
    ),
    # "coordinates: 40.4168, -3.7038"
    re.compile(
        r"coordinates?[:\s]+(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)",
        re.IGNORECASE,
    ),
]

# Label extraction patterns — try to capture what location the coords refer to
_LABEL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:ubicad[oa]s?\s+en|localizada?\s+en|cerca\s+de|en\s+la\s+zona\s+de)\s+([^.,\n]{3,50})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:city|ciudad|lugar|location)[:\s]+([^.,\n]{3,50})",
        re.IGNORECASE,
    ),
]


class LocationExtractor:
    """Extract coordinates from free-form text responses."""

    def extract(self, text: str) -> list[dict[str, Any]]:
        """Extract all coordinate pairs from *text*.

        Returns a list of dicts, each containing:
            - lat (float)
            - lon (float)
            - label (str | None) — nearby text hint about the location
            - confidence_radius_meters (int) — default 5000

        Duplicates (same lat/lon rounded to 4 decimals) are deduplicated.
        """
        if not text:
            return []

        seen: set[tuple[float, float]] = set()
        locations: list[dict[str, Any]] = []

        for pattern in _COORD_PATTERNS:
            for match in pattern.finditer(text):
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                except (ValueError, IndexError):
                    continue

                # Validate ranges
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    continue

                # Deduplicate
                key = (round(lat, 4), round(lon, 4))
                if key in seen:
                    continue
                seen.add(key)

                label = self._find_label(text, match.start())

                locations.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "label": label,
                        "confidence_radius_meters": 5000,
                    }
                )

        if locations:
            logger.info("📍 Extracted %s location(s) from text", len(locations))

        return locations

    @staticmethod
    def _find_label(text: str, match_pos: int) -> str | None:
        """Try to find a descriptive label near the coordinate match."""
        # Look in the 200 chars surrounding the match
        start = max(0, match_pos - 200)
        end = min(len(text), match_pos + 200)
        context = text[start:end]

        for pattern in _LABEL_PATTERNS:
            m = pattern.search(context)
            if m:
                return m.group(1).strip()

        return None
