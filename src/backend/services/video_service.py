"""
Video processing service for handling video uploads and frame extraction.
"""

import logging
import os
import time
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..config import ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_MB, TEMP_VIDEO_PATH

MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

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
                if video_file.is_file():
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
