"""
EXIF data parsing and extraction
"""

import logging
from typing import Dict, Any, Optional

try:
    import piexif

    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExifParser:
    """Parse EXIF data from images"""

    @staticmethod
    def parse_exif(exif_data: Dict) -> Dict[str, Any]:
        """Parse raw EXIF data"""
        parsed = {}

        # Common EXIF tags
        tags = {
            271: "Make",
            272: "Model",
            274: "Orientation",
            282: "XResolution",
            283: "YResolution",
            296: "ResolutionUnit",
            305: "Software",
            306: "DateTime",
            36867: "DateTimeOriginal",
            36868: "DateTimeDigitized",
        }

        for tag_id, name in tags.items():
            if tag_id in exif_data:
                parsed[name] = str(exif_data[tag_id])

        return parsed

    @staticmethod
    def extract_camera_info(exif_0th: Dict) -> Dict[str, str]:
        """Extract camera information from EXIF"""
        if not PIEXIF_AVAILABLE:
            return {}

        camera = {}

        if piexif.ImageIFD.Make in exif_0th:
            camera["make"] = exif_0th[piexif.ImageIFD.Make].decode(
                "utf-8", errors="ignore"
            )

        if piexif.ImageIFD.Model in exif_0th:
            camera["model"] = exif_0th[piexif.ImageIFD.Model].decode(
                "utf-8", errors="ignore"
            )

        if piexif.ImageIFD.Software in exif_0th:
            camera["software"] = exif_0th[piexif.ImageIFD.Software].decode(
                "utf-8", errors="ignore"
            )

        return camera

    @staticmethod
    def extract_gps_info(gps_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from EXIF"""
        if not PIEXIF_AVAILABLE:
            return None

        try:
            gps_info = {}

            # Latitude
            if (
                piexif.GPSIFD.GPSLatitude in gps_data
                and piexif.GPSIFD.GPSLatitudeRef in gps_data
            ):
                lat = ExifParser._convert_to_degrees(
                    gps_data[piexif.GPSIFD.GPSLatitude]
                )
                lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode("utf-8")

                if lat_ref == "S":
                    lat = -lat

                gps_info["latitude"] = lat

            # Longitude
            if (
                piexif.GPSIFD.GPSLongitude in gps_data
                and piexif.GPSIFD.GPSLongitudeRef in gps_data
            ):
                lon = ExifParser._convert_to_degrees(
                    gps_data[piexif.GPSIFD.GPSLongitude]
                )
                lon_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode("utf-8")

                if lon_ref == "W":
                    lon = -lon

                gps_info["longitude"] = lon

            # Altitude
            if piexif.GPSIFD.GPSAltitude in gps_data:
                altitude = gps_data[piexif.GPSIFD.GPSAltitude]
                gps_info["altitude"] = float(altitude[0]) / float(altitude[1])

            # Timestamp
            if piexif.GPSIFD.GPSDateStamp in gps_data:
                gps_info["date"] = gps_data[piexif.GPSIFD.GPSDateStamp].decode("utf-8")

            if gps_info:
                logger.info(
                    f"📍 GPS data found: {gps_info.get('latitude', 'N/A')}, {gps_info.get('longitude', 'N/A')}"
                )

            return gps_info if gps_info else None

        except Exception as e:
            logger.debug(f"GPS extraction failed: {e}")
            return None

    @staticmethod
    def _convert_to_degrees(value: tuple) -> float:
        """Convert GPS coordinates to degrees"""
        d = float(value[0][0]) / float(value[0][1])
        m = float(value[1][0]) / float(value[1][1])
        s = float(value[2][0]) / float(value[2][1])

        return d + (m / 60.0) + (s / 3600.0)

    @staticmethod
    def extract_datetime_info(exif_data: Dict) -> Dict[str, str]:
        """Extract datetime information"""
        if not PIEXIF_AVAILABLE:
            return {}

        datetime_info = {}

        if piexif.ExifIFD.DateTimeOriginal in exif_data:
            datetime_info["original"] = exif_data[
                piexif.ExifIFD.DateTimeOriginal
            ].decode("utf-8")

        if piexif.ExifIFD.DateTimeDigitized in exif_data:
            datetime_info["digitized"] = exif_data[
                piexif.ExifIFD.DateTimeDigitized
            ].decode("utf-8")

        return datetime_info
