"""
Video metadata extraction
"""

import hashlib
import logging
import os
from datetime import UTC, datetime
from typing import Any

try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

logger = logging.getLogger(__name__)


def _parse_frame_rate(rate_str: str) -> float:
    """Safely parse ffprobe frame rate string (e.g. '30/1') without eval().

    Args:
        rate_str: Frame rate string in 'numerator/denominator' format

    Returns:
        Parsed frame rate as float, or 0.0 on parse failure
    """
    try:
        if "/" in rate_str:
            num, den = rate_str.split("/", maxsplit=1)
            denominator = float(den)
            return float(num) / denominator if denominator != 0 else 0.0
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        logger.warning("Could not parse frame rate: %s", rate_str)
        return 0.0


class VideoMetadataExtractor:
    """Extract metadata from video files"""

    @staticmethod
    def extract_video_metadata(video_path: str) -> dict[str, Any]:
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
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if not FFMPEG_AVAILABLE:
            metadata["error"] = "ffmpeg-python not available"
            return metadata

        try:
            # Get file hash — incremental to avoid loading entire file into RAM
            sha256 = hashlib.sha256()
            file_size = os.path.getsize(video_path)
            with open(video_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            metadata["forensics"]["sha256"] = sha256.hexdigest()
            metadata["forensics"]["size_bytes"] = file_size

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
                                "fps": _parse_frame_rate(stream.get("r_frame_rate", "0/1")),
                                "pix_fmt": stream.get("pix_fmt", "unknown"),
                            }
                        )

                    metadata["streams"].append(stream_info)

            logger.info(
                "✅ Video metadata extracted: %s",
                metadata["format"].get("format_name", "unknown"),
            )

        except (OSError, IOError, KeyError, ValueError) as e:
            logger.error("❌ Video metadata extraction error: %s", e)
            metadata["error"] = str(e)

        return metadata
