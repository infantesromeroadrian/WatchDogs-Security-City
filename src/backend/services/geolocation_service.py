"""
Geolocation service for generating maps and geocoding.
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)


class GeolocationService:
    """Service for geocoding and map generation."""

    def __init__(self):
        """Initialize geolocation service."""
        # Initialize geocoder with custom user agent
        self.geolocator = Nominatim(user_agent="watchdogs-osint-v1.0")
        logger.info("ℹ️ GeolocationService initialized")

    @staticmethod
    def generate_map(
        latitude: float,
        longitude: float,
        zoom_start: int = 15,
        marker_popup: str = "Location",
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate interactive HTML map with marker.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            zoom_start: Initial zoom level (default 15)
            marker_popup: Text to show in marker popup
            output_path: Optional custom output path

        Returns:
            Path to generated HTML file
        """
        try:
            # Create map centered on coordinates
            m = folium.Map(
                location=[latitude, longitude],
                zoom_start=zoom_start,
                tiles="OpenStreetMap",
            )

            # Add marker
            folium.Marker(
                location=[latitude, longitude],
                popup=marker_popup,
                tooltip="Click for details",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)

            # Add circle to show approximate area
            folium.Circle(
                location=[latitude, longitude],
                radius=100,  # meters
                color="blue",
                fill=True,
                fillOpacity=0.2,
                popup=f"Approximate area (~100m radius)",
            ).add_to(m)

            # Generate output path
            if not output_path:
                maps_dir = Path("data/maps")
                maps_dir.mkdir(parents=True, exist_ok=True)
                output_path = maps_dir / f"map_{latitude}_{longitude}.html"

            # Save map
            m.save(str(output_path))
            logger.info(f"✅ Map generated: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"❌ Map generation failed: {e}")
            raise ValueError(f"Failed to generate map: {e}")

    def geocode_address(
        self, address: str, timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates using Nominatim.

        Args:
            address: Address string to geocode
            timeout: Request timeout in seconds

        Returns:
            Dict with location data or None if not found
        """
        try:
            logger.info(f"🔍 Geocoding address: {address}")

            location = self.geolocator.geocode(address, timeout=timeout)

            if location:
                result = {
                    "address": location.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "raw": location.raw,
                }
                logger.info(f"✅ Geocoded: {location.address}")
                return result
            else:
                logger.warning(f"⚠️ No results for: {address}")
                return None

        except GeocoderTimedOut:
            logger.error(f"⏱️ Geocoding timeout for: {address}")
            return None
        except GeocoderServiceError as e:
            logger.error(f"❌ Geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Geocoding failed: {e}")
            return None

    def reverse_geocode(
        self, latitude: float, longitude: float, timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
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
            logger.info(f"🔍 Reverse geocoding: {latitude}, {longitude}")

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
                logger.info(f"✅ Reverse geocoded: {location.address}")
                return result
            else:
                logger.warning(f"⚠️ No results for coordinates: {latitude}, {longitude}")
                return None

        except GeocoderTimedOut:
            logger.error(f"⏱️ Reverse geocoding timeout")
            return None
        except GeocoderServiceError as e:
            logger.error(f"❌ Reverse geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Reverse geocoding failed: {e}")
            return None

    @staticmethod
    def validate_coordinates(
        latitude: float, longitude: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate coordinate ranges.

        Args:
            latitude: Latitude to validate
            longitude: Longitude to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            return False, "Coordinates must be numeric"

        if not -90 <= latitude <= 90:
            return False, f"Latitude must be between -90 and 90, got {latitude}"

        if not -180 <= longitude <= 180:
            return False, f"Longitude must be between -180 and 180, got {longitude}"

        return True, None

    def enrich_geolocation_result(
        self, geolocation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                # Validate coordinates
                is_valid, error = self.validate_coordinates(lat, lon)

                if is_valid:
                    # Generate map
                    try:
                        popup_text = f"{location_info.get('city', 'Unknown')}, {location_info.get('country', 'Unknown')}"
                        map_path = self.generate_map(
                            latitude=lat, longitude=lon, marker_popup=popup_text
                        )
                        enriched["map_path"] = map_path
                        enriched["map_url"] = f"/maps/{os.path.basename(map_path)}"
                    except Exception as e:
                        logger.warning(f"⚠️ Map generation failed: {e}")

                    # Reverse geocode for detailed address
                    reverse_result = self.reverse_geocode(lat, lon)
                    if reverse_result:
                        enriched["geocoded_address"] = reverse_result["address"]
                        enriched["geocoding_raw"] = reverse_result["raw"]
                else:
                    logger.warning(f"⚠️ Invalid coordinates: {error}")

        # Try forward geocoding if location info available but no coords
        elif location_info and not coords:
            # Build address string from available parts
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

                    # Generate map with geocoded coordinates
                    try:
                        map_path = self.generate_map(
                            latitude=geocode_result["latitude"],
                            longitude=geocode_result["longitude"],
                            marker_popup=geocode_result["address"],
                        )
                        enriched["map_path"] = map_path
                        enriched["map_url"] = f"/maps/{os.path.basename(map_path)}"
                    except Exception as e:
                        logger.warning(f"⚠️ Map generation failed: {e}")

        return enriched
