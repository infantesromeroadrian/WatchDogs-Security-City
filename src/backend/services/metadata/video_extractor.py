"""
Video metadata extraction
"""

import logging
import hashlib
from datetime import datetime
from typing import Dict, Any

try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

logger = logging.getLogger(__name__)


class VideoMetadataExtractor:
    """Extract metadata from video files"""

    @staticmethod
    def extract_video_metadata(video_path: str) -> Dict[str, Any]:
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

        if not FFMPEG_AVAILABLE:
            metadata["error"] = "ffmpeg-python not available"
            return metadata

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
