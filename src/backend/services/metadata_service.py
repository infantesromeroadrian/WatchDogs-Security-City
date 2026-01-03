"""
Metadata Extraction Service
Extracts EXIF, GPS, and video metadata without external APIs
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import base64
import io

try:
    import piexif
    from PIL import Image
    import ffmpeg

    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetadataService:
    """Extract metadata from images and videos"""

    def __init__(self):
        if not METADATA_AVAILABLE:
            logger.warning(
                "⚠️ Metadata libraries not available. Install: pip install piexif ffmpeg-python"
            )

    def extract_image_metadata(self, image_base64: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from base64 image.

        Args:
            image_base64: Base64 encoded image

        Returns:
            Dictionary with metadata including EXIF, GPS, hashes
        """
        metadata = {
            "exif": {},
            "gps": {},
            "technical": {},
            "forensics": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Decode base64
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]

            image_bytes = base64.b64decode(image_base64)

            # Calculate hashes for forensics
            metadata["forensics"]["sha256"] = hashlib.sha256(image_bytes).hexdigest()
            metadata["forensics"]["md5"] = hashlib.md5(image_bytes).hexdigest()
            metadata["forensics"]["size_bytes"] = len(image_bytes)

            # Open image
            image = Image.open(io.BytesIO(image_bytes))

            # Basic technical info
            metadata["technical"]["format"] = image.format
            metadata["technical"]["mode"] = image.mode
            metadata["technical"]["size"] = f"{image.size[0]}x{image.size[1]}"
            metadata["technical"]["width"] = image.size[0]
            metadata["technical"]["height"] = image.size[1]

            # Extract EXIF if available
            if hasattr(image, "_getexif") and image._getexif() is not None:
                exif_data = image._getexif()
                metadata["exif"] = self._parse_exif(exif_data)

            # Try piexif for more detailed EXIF
            try:
                exif_dict = piexif.load(image.info.get("exif", b""))

                # Camera info
                if "0th" in exif_dict:
                    metadata["exif"]["camera"] = self._extract_camera_info(
                        exif_dict["0th"]
                    )

                # GPS info
                if "GPS" in exif_dict:
                    gps_info = self._extract_gps_info(exif_dict["GPS"])
                    if gps_info:
                        metadata["gps"] = gps_info

                # Datetime info
                if "Exif" in exif_dict:
                    metadata["exif"]["datetime"] = self._extract_datetime_info(
                        exif_dict["Exif"]
                    )

            except Exception as e:
                logger.debug(f"Piexif extraction failed (normal for non-JPEG): {e}")

            logger.info(
                f"✅ Metadata extracted: {metadata['technical']['format']}, {metadata['technical']['size']}"
            )

        except Exception as e:
            logger.error(f"❌ Metadata extraction error: {e}")
            metadata["error"] = str(e)

        return metadata

    def _parse_exif(self, exif_data: Dict) -> Dict[str, Any]:
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

    def _extract_camera_info(self, exif_0th: Dict) -> Dict[str, str]:
        """Extract camera information from EXIF"""
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

    def _extract_gps_info(self, gps_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from EXIF"""
        try:
            gps_info = {}

            # Latitude
            if (
                piexif.GPSIFD.GPSLatitude in gps_data
                and piexif.GPSIFD.GPSLatitudeRef in gps_data
            ):
                lat = self._convert_to_degrees(gps_data[piexif.GPSIFD.GPSLatitude])
                lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode("utf-8")

                if lat_ref == "S":
                    lat = -lat

                gps_info["latitude"] = lat

            # Longitude
            if (
                piexif.GPSIFD.GPSLongitude in gps_data
                and piexif.GPSIFD.GPSLongitudeRef in gps_data
            ):
                lon = self._convert_to_degrees(gps_data[piexif.GPSIFD.GPSLongitude])
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

    def _convert_to_degrees(self, value: tuple) -> float:
        """Convert GPS coordinates to degrees"""
        d = float(value[0][0]) / float(value[0][1])
        m = float(value[1][0]) / float(value[1][1])
        s = float(value[2][0]) / float(value[2][1])

        return d + (m / 60.0) + (s / 3600.0)

    def _extract_datetime_info(self, exif_data: Dict) -> Dict[str, str]:
        """Extract datetime information"""
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

    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract metadata from video file using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        metadata = {
            "format": {},
            "streams": [],
            "technical": {},
            "forensics": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Get file hash
            with open(video_path, "rb") as f:
                video_bytes = f.read()
                metadata["forensics"]["sha256"] = hashlib.sha256(
                    video_bytes
                ).hexdigest()
                metadata["forensics"]["md5"] = hashlib.md5(video_bytes).hexdigest()
                metadata["forensics"]["size_bytes"] = len(video_bytes)

            # Use ffprobe to get metadata
            probe = ffmpeg.probe(video_path)

            # Format info
            if "format" in probe:
                fmt = probe["format"]
                metadata["format"] = {
                    "filename": fmt.get("filename", "unknown"),
                    "format_name": fmt.get("format_name", "unknown"),
                    "format_long_name": fmt.get("format_long_name", "unknown"),
                    "duration": float(fmt.get("duration", 0)),
                    "size": int(fmt.get("size", 0)),
                    "bit_rate": int(fmt.get("bit_rate", 0)),
                    "nb_streams": int(fmt.get("nb_streams", 0)),
                }

                # Extract creation time if available
                if "tags" in fmt and "creation_time" in fmt["tags"]:
                    metadata["format"]["creation_time"] = fmt["tags"]["creation_time"]

            # Stream info
            if "streams" in probe:
                for stream in probe["streams"]:
                    stream_info = {
                        "codec_type": stream.get("codec_type", "unknown"),
                        "codec_name": stream.get("codec_name", "unknown"),
                    }

                    if stream["codec_type"] == "video":
                        stream_info.update(
                            {
                                "width": stream.get("width", 0),
                                "height": stream.get("height", 0),
                                "fps": eval(stream.get("r_frame_rate", "0/1")),
                                "pix_fmt": stream.get("pix_fmt", "unknown"),
                            }
                        )

                    metadata["streams"].append(stream_info)

            logger.info(
                f"✅ Video metadata extracted: {metadata['format'].get('format_name', 'unknown')}"
            )

        except Exception as e:
            logger.error(f"❌ Video metadata extraction error: {e}")
            metadata["error"] = str(e)

        return metadata

    def generate_evidence_package(
        self, frame_base64: str, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate forensic evidence package with chain of custody.

        Args:
            frame_base64: Base64 encoded frame
            analysis_results: Analysis results from agents

        Returns:
            Evidence package with metadata, hashes, and chain of custody
        """
        timestamp = datetime.now().isoformat()

        # Extract metadata
        metadata = self.extract_image_metadata(frame_base64)

        # Generate evidence ID
        evidence_id = hashlib.sha256(
            f"{timestamp}{metadata['forensics']['sha256']}".encode()
        ).hexdigest()[:16]

        package = {
            "evidence_id": evidence_id,
            "timestamp": timestamp,
            "metadata": metadata,
            "analysis": analysis_results,
            "chain_of_custody": [
                {
                    "action": "captured",
                    "timestamp": timestamp,
                    "hash": metadata["forensics"]["sha256"],
                },
                {
                    "action": "analyzed",
                    "timestamp": timestamp,
                    "system": "WatchDogs-OSINT",
                },
            ],
            "integrity": {
                "sha256": metadata["forensics"]["sha256"],
                "verified": True,
                "verification_timestamp": timestamp,
            },
        }

        logger.info(f"📦 Evidence package generated: {evidence_id}")

        return package


# Global instance
metadata_service = MetadataService()
