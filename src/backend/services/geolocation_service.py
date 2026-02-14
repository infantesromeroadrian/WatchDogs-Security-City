"""
Geolocation service for geocoding and coordinate enrichment.

Maps are rendered client-side via Mapbox GL JS (see MapHandler in frontend).
This service handles server-side geocoding only (Nominatim / OpenStreetMap).
"""

import logging
from typing import Any

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


class GeolocationService:
    """Service for geocoding and map generation."""

    def __init__(self):
        """Initialize geolocation service."""
        # Initialize geocoder with custom user agent
        self.geolocator = Nominatim(user_agent="watchdogs-osint-v1.0")
        logger.info("ℹ️ GeolocationService initialized")

    def geocode_address(self, address: str, timeout: int = 10) -> dict[str, Any] | None:
        """
        Convert address to coordinates using Nominatim.

        Args:
            address: Address string to geocode
            timeout: Request timeout in seconds

        Returns:
            Dict with location data or None if not found
        """
        try:
            logger.info("🔍 Geocoding address: %s", address)

            location = self.geolocator.geocode(address, timeout=timeout)

            if location:
                result = {
                    "address": location.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "raw": location.raw,
                }
                logger.info("✅ Geocoded: %s", location.address)
                return result
            logger.warning("⚠️ No results for: %s", address)
            return None

        except GeocoderTimedOut:
            logger.error("⏱️ Geocoding timeout for: %s", address)
            return None
        except GeocoderServiceError as e:
            logger.error("❌ Geocoding service error: %s", e)
            return None
        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid geocoding parameters: %s", e)
            return None

    def reverse_geocode(
        self, latitude: float, longitude: float, timeout: int = 10
    ) -> dict[str, Any] | None:
        """
        Convert coordinates to address (reverse geocoding).

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            timeout: Request timeout in seconds

        Returns:
            Dict with address data or None if not found
        """
        try:
            logger.info("🔍 Reverse geocoding: %s, %s", latitude, longitude)

            location = self.geolocator.reverse(
                (latitude, longitude),
                timeout=timeout,
                language="es",  # Preferir respuestas en español
            )

            if location:
                result = {
                    "address": location.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "raw": location.raw,
                }
                logger.info("✅ Reverse geocoded: %s", location.address)
                return result
            logger.warning("⚠️ No results for coordinates: %s, %s", latitude, longitude)
            return None

        except GeocoderTimedOut:
            logger.error("⏱️ Reverse geocoding timeout")
            return None
        except GeocoderServiceError as e:
            logger.error("❌ Reverse geocoding service error: %s", e)
            return None
        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid coordinates for reverse geocoding: %s", e)
            return None

    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> tuple[bool, str | None]:
        """
        Validate coordinate ranges.

        Args:
            latitude: Latitude to validate
            longitude: Longitude to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False, "Coordinates must be numeric"

        if not -90 <= latitude <= 90:
            return False, f"Latitude must be between -90 and 90, got {latitude}"

        if not -180 <= longitude <= 180:
            return False, f"Longitude must be between -180 and 180, got {longitude}"

        return True, None

    def enrich_geolocation_result(self, geolocation_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich geolocation result with geocoding and map generation.

        Args:
            geolocation_data: Result from GeolocationAgent

        Returns:
            Enriched result with map path and geocoding data
        """
        enriched = geolocation_data.copy()

        # Extract coordinates if present
        coords = geolocation_data.get("coordinates")
        location_info = geolocation_data.get("location", {})

        # Try reverse geocoding if coordinates available
        if coords and isinstance(coords, dict):
            lat = coords.get("lat")
            lon = coords.get("lon")

            if lat is not None and lon is not None:
                is_valid, error = self.validate_coordinates(lat, lon)

                if is_valid:
                    # Reverse geocode for detailed address
                    reverse_result = self.reverse_geocode(lat, lon)
                    if reverse_result:
                        enriched["geocoded_address"] = reverse_result["address"]
                        enriched["geocoding_raw"] = reverse_result["raw"]
                else:
                    logger.warning("⚠️ Invalid coordinates: %s", error)

        # Try forward geocoding if location info available but no coords
        elif location_info and not coords:
            address_parts = []
            if location_info.get("street"):
                address_parts.append(location_info["street"])
            if location_info.get("city"):
                address_parts.append(location_info["city"])
            if location_info.get("country"):
                address_parts.append(location_info["country"])

            if address_parts:
                address = ", ".join(address_parts)
                geocode_result = self.geocode_address(address)

                if geocode_result:
                    enriched["coordinates"] = {
                        "lat": geocode_result["latitude"],
                        "lon": geocode_result["longitude"],
                    }
                    enriched["geocoded_address"] = geocode_result["address"]

        return enriched
