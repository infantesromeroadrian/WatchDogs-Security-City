"""
Video processing service for handling video uploads, frame extraction,
and automatic transcoding for browser-incompatible codecs (H.265/VP9 → H.264).
"""

import logging
import os
import subprocess
import time
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..config import ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_MB, TEMP_VIDEO_PATH

try:
    import ffmpeg

    FFMPEG_PROBE_AVAILABLE = True
except ImportError:
    FFMPEG_PROBE_AVAILABLE = False

MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

# Codecs that HTML5 <video> can natively decode in all major browsers
_BROWSER_COMPATIBLE_CODECS = frozenset({"h264", "vp8", "theora", "av1"})

# Max transcoding time (seconds) — 5 min covers ~100 MB with -preset fast
_TRANSCODE_TIMEOUT_SECONDS = 300

logger = logging.getLogger(__name__)


# M-4: Magic byte signatures for supported video containers
_VIDEO_MAGIC_BYTES: dict[bytes, str] = {
    b"\x00\x00\x00\x1cftyp": "mp4/mov",  # ISO Base Media (MP4, MOV, M4V)
    b"\x00\x00\x00\x18ftyp": "mp4/mov",
    b"\x00\x00\x00\x20ftyp": "mp4/mov",
    b"\x1a\x45\xdf\xa3": "mkv/webm",  # Matroska/WebM (EBML header)
    b"RIFF": "avi",  # AVI container (RIFF header — second check for AVI below)
}


class VideoService:
    """Service for handling video uploads and temporary storage."""

    @staticmethod
    def is_allowed_extension(filename: str) -> bool:
        """Check if file extension is allowed."""
        return Path(filename).suffix.lower() in ALLOWED_VIDEO_EXTENSIONS

    @staticmethod
    def _check_magic_bytes(file: FileStorage) -> bool:
        """
        M-4: Validate file content matches a known video container format.

        Reads the first 12 bytes and checks against known magic signatures.
        Resets the file pointer after reading.
        """
        header = file.read(12)
        file.seek(0)

        if len(header) < 4:
            return False

        # Check direct prefix matches
        for magic, _fmt in _VIDEO_MAGIC_BYTES.items():
            if header[: len(magic)] == magic:
                # AVI: RIFF header must also contain 'AVI ' at offset 8
                if magic == b"RIFF":
                    return len(header) >= 12 and header[8:12] == b"AVI "
                return True

        return False

    @staticmethod
    def validate_video(file: FileStorage) -> dict[str, str | bool | float]:
        """
        Validate uploaded video file.

        Args:
            file: Uploaded file object

        Returns:
            Dict with 'valid' bool and optional 'error' message
        """
        if not file:
            return {"valid": False, "error": "No file provided"}

        if not file.filename:
            return {"valid": False, "error": "No filename provided"}

        if not VideoService.is_allowed_extension(file.filename):
            return {
                "valid": False,
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
            }

        # M-4: Check magic bytes (content validation, not just extension)
        if not VideoService._check_magic_bytes(file):
            logger.warning("⚠️ File %s has valid extension but invalid magic bytes", file.filename)
            return {
                "valid": False,
                "error": "File content does not match a supported video format",
            }

        # Check file size (if available)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > MAX_VIDEO_SIZE_BYTES:
            return {
                "valid": False,
                "error": f"File too large. Max size: {MAX_VIDEO_SIZE_BYTES / (1024 * 1024):.0f}MB",
            }

        return {"valid": True}

    @staticmethod
    def save_video(file: FileStorage) -> dict[str, str | bool | float]:
        """
        Save uploaded video to temporary storage.

        Args:
            file: Uploaded file object

        Returns:
            Dict with 'success' bool, 'path' str, 'filename' str,
            'size_mb' float, and optional 'error' str
        """
        try:
            # Validate file
            validation = VideoService.validate_video(file)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            # Generate secure filename with timestamp
            # file.filename is guaranteed non-None — validate_video checks it
            original_filename = secure_filename(file.filename)  # type: ignore[arg-type]
            timestamp = int(time.time())
            filename = f"{timestamp}_{original_filename}"
            filepath = TEMP_VIDEO_PATH / filename

            # Save file
            file.save(str(filepath))
            logger.info("ℹ️ Video saved: %s", filepath)

            return {
                "success": True,
                "path": str(filepath),
                "filename": filename,
                "size_mb": filepath.stat().st_size / (1024 * 1024),
            }

        except PermissionError as e:
            logger.error("❌ Permission denied saving video: %s", e)
            return {"success": False, "error": f"Permission denied: {e}"}
        except (OSError, IOError) as e:
            logger.error("❌ Failed to save video: %s", e)
            return {"success": False, "error": f"Failed to save video: {e}"}

    @staticmethod
    def cleanup_old_videos(retention_hours: int = 1) -> int:
        """
        Remove videos older than retention period.

        Args:
            retention_hours: Number of hours to keep videos

        Returns:
            Number of files deleted
        """
        try:
            current_time = time.time()
            cutoff_time = current_time - (retention_hours * 3600)
            deleted_count = 0

            for video_file in TEMP_VIDEO_PATH.glob("*"):
                # Skip dotfiles like .gitkeep
                if video_file.is_file() and not video_file.name.startswith("."):
                    file_age = video_file.stat().st_mtime
                    if file_age < cutoff_time:
                        video_file.unlink()
                        deleted_count += 1
                        logger.info("ℹ️ Deleted old video: %s", video_file.name)

            if deleted_count > 0:
                logger.info("ℹ️ Cleanup complete: %s videos deleted", deleted_count)

            return deleted_count

        except PermissionError as e:
            logger.error("❌ Permission denied during cleanup: %s", e)
            return 0
        except (OSError, IOError) as e:
            logger.error("❌ Cleanup failed: %s", e)
            return 0

    # ====================================================================
    # Codec detection & transcoding (H.265/VP9 → H.264 for browsers)
    # ====================================================================

    @staticmethod
    def detect_video_codec(filepath: str) -> str | None:
        """
        Detect the primary video codec using ffprobe.

        Args:
            filepath: Path to the video file on disk

        Returns:
            Codec name (e.g. 'h264', 'hevc', 'vp9') or None on failure
        """
        if not FFMPEG_PROBE_AVAILABLE:
            logger.warning("ffmpeg-python not installed — cannot detect codec")
            return None

        try:
            probe = ffmpeg.probe(filepath)
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    codec = stream.get("codec_name")
                    logger.info("Detected video codec: %s", codec)
                    return codec
        except ffmpeg.Error as e:
            logger.error("ffprobe failed for %s: %s", filepath, e)

        return None

    @staticmethod
    def needs_transcoding(codec_name: str | None) -> bool:
        """
        Check whether the codec requires transcoding for browser playback.

        H.264, VP8, Theora and AV1 are universally supported.
        H.265 (hevc), VP9-in-MP4, and exotic codecs are not.

        Args:
            codec_name: Codec identifier from ffprobe

        Returns:
            True if the codec is NOT browser-compatible
        """
        if codec_name is None:
            return False
        return codec_name.lower() not in _BROWSER_COMPATIBLE_CODECS

    @staticmethod
    def transcode_to_h264(input_path: str) -> dict[str, str | bool]:
        """
        Transcode a video file to H.264/AAC in an MP4 container.

        Uses ``ffmpeg -c:v libx264 -preset fast -crf 23 -movflags faststart``
        for broad browser compatibility and fast web start.

        Args:
            input_path: Path to the source video

        Returns:
            Dict with 'success' bool, 'output_path', 'filename', or 'error'
        """
        input_p = Path(input_path)
        output_filename = f"{input_p.stem}_h264.mp4"
        output_path = TEMP_VIDEO_PATH / output_filename

        try:
            logger.info("Transcoding %s → H.264 …", input_p.name)

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(input_path),
                    "-c:v",
                    "libx264",
                    "-profile:v",
                    "high",
                    "-level",
                    "4.1",
                    "-pix_fmt",
                    "yuv420p",  # Force 8-bit 4:2:0 (universal browser support)
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-movflags",
                    "faststart",
                    "-y",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=_TRANSCODE_TIMEOUT_SECONDS,
            )

            if result.returncode != 0:
                # Log last 500 chars of stderr for diagnostics
                logger.error("ffmpeg exited %s: %s", result.returncode, result.stderr[-500:])
                return {"success": False, "error": "Transcoding failed"}

            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info("Transcoded successfully: %s (%.1f MB)", output_filename, size_mb)

            return {
                "success": True,
                "output_path": str(output_path),
                "filename": output_filename,
                "size_mb": str(round(size_mb, 2)),
            }

        except subprocess.TimeoutExpired:
            logger.error(
                "Transcoding timed out after %ss for %s",
                _TRANSCODE_TIMEOUT_SECONDS,
                input_p.name,
            )
            if output_path.exists():
                output_path.unlink()
            return {
                "success": False,
                "error": "Transcoding timed out (max 5 minutes)",
            }

        except FileNotFoundError:
            logger.error("ffmpeg binary not found in PATH")
            return {
                "success": False,
                "error": "ffmpeg not installed on server",
            }

        except OSError as e:
            logger.error("Transcoding OS error: %s", e)
            return {"success": False, "error": "Transcoding system error"}
