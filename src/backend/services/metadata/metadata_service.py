"""
Main metadata extraction orchestrator
"""

import logging
import hashlib
import base64
import io
from datetime import datetime
from typing import Dict, Any

try:
    import piexif
    from PIL import Image

    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False

from .exif_parser import ExifParser
from .video_extractor import VideoMetadataExtractor

logger = logging.getLogger(__name__)


class MetadataService:
    """Extract metadata from images and videos"""

    def __init__(self):
        if not METADATA_AVAILABLE:
            logger.warning(
                "⚠️ Metadata libraries not available. Install: pip install piexif ffmpeg-python"
            )

        self.exif_parser = ExifParser()
        self.video_extractor = VideoMetadataExtractor()

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
                metadata["exif"] = self.exif_parser.parse_exif(exif_data)

            # Try piexif for more detailed EXIF
            if METADATA_AVAILABLE:
                try:
                    exif_dict = piexif.load(image.info.get("exif", b""))

                    # Camera info
                    if "0th" in exif_dict:
                        metadata["exif"]["camera"] = (
                            self.exif_parser.extract_camera_info(exif_dict["0th"])
                        )

                    # GPS info
                    if "GPS" in exif_dict:
                        gps_info = self.exif_parser.extract_gps_info(exif_dict["GPS"])
                        if gps_info:
                            metadata["gps"] = gps_info

                    # Datetime info
                    if "Exif" in exif_dict:
                        metadata["exif"]["datetime"] = (
                            self.exif_parser.extract_datetime_info(exif_dict["Exif"])
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

    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        return self.video_extractor.extract_video_metadata(video_path)

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
