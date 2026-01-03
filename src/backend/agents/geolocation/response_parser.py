"""
Geolocation Response Parser
Single Responsibility: Parse structured data from LLM geolocation responses
Max: 200 lines
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GeolocationResponseParser:
    """Parse structured location data from geolocation LLM responses"""

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract structured location data.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed location data
        """
        return {
            "location": self._parse_location(text),
            "confidence": self._parse_confidence(text),
            "coordinates": self._parse_coordinates(text),
            "key_clues": self._parse_clues(text),
        }

    def _parse_location(self, text: str) -> Dict[str, str]:
        """
        Extract location components (country, city, district, street).

        Args:
            text: Raw LLM response

        Returns:
            Dict with location components (only non-None values)
        """
        location = {}

        # Extract country
        country = self._extract_country(text)
        if country:
            location["country"] = country

        # Extract city
        city = self._extract_city(text)
        if city:
            location["city"] = city

        # Extract district
        district = self._extract_district(text)
        if district:
            location["district"] = district

        # Extract street
        street = self._extract_street(text)
        if street:
            location["street"] = street

        return location

    def _extract_country(self, text: str) -> Optional[str]:
        """Extract country name from response"""
        match = re.search(r"País:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_city(self, text: str) -> Optional[str]:
        """Extract city name from response"""
        match = re.search(r"Ciudad:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_district(self, text: str) -> Optional[str]:
        """Extract district/neighborhood from response"""
        match = re.search(r"Distrito/Barrio:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_street(self, text: str) -> Optional[str]:
        """Extract street/plaza name from response"""
        match = re.search(r"Calle/Plaza:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _parse_coordinates(self, text: str) -> Optional[Dict[str, float]]:
        """
        Extract and validate coordinates from response.

        Tries multiple regex patterns to catch various coordinate formats.

        Args:
            text: Raw LLM response

        Returns:
            Dict with lat/lon keys or None if not found/invalid
        """
        # Multiple patterns to handle different coordinate formats
        coords_patterns = [
            r"Coordenadas.*?:\s*\[?\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*\]?",
            r"lat[itude]*:\s*(-?\d+\.?\d*).*?lon[gitude]*:\s*(-?\d+\.?\d*)",
            r"(-?\d+\.\d+),\s*(-?\d+\.\d+)",
        ]

        for pattern in coords_patterns:
            coords_match = re.search(pattern, text, re.IGNORECASE)
            if coords_match:
                try:
                    lat = float(coords_match.group(1))
                    lon = float(coords_match.group(2))

                    # Validate coordinates are within valid range
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return {"lat": lat, "lon": lon}
                    else:
                        logger.warning(
                            f"Invalid coordinates range: lat={lat}, lon={lon}"
                        )
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse coordinates: {e}")
                    continue

        return None

    def _parse_confidence(self, text: str) -> str:
        """
        Extract confidence level from response.

        Args:
            text: Raw LLM response

        Returns:
            Confidence level string (lowercase) or "unknown"
        """
        match = re.search(
            r"NIVEL DE CONFIANZA.*?:\s*(Muy Alto|Alto|Medio|Bajo|Muy Bajo)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).lower() if match else "unknown"

    def _parse_clues(self, text: str) -> list[str]:
        """
        Extract key clues list from response.

        Args:
            text: Raw LLM response

        Returns:
            List of clue strings (max 5)
        """
        # Find the "PISTAS CLAVE" section
        clues_section = re.search(
            r"PISTAS CLAVE.*?:(.*?)(?:\*\*|$)", text, re.IGNORECASE | re.DOTALL
        )

        if not clues_section:
            return []

        clues_text = clues_section.group(1)

        # Extract bullet points or numbered items
        clues = re.findall(r"[-•\d.]+\s*(.+?)(?:\n|$)", clues_text)

        # Clean and limit to 5 clues
        return [c.strip() for c in clues if c.strip()][:5]
