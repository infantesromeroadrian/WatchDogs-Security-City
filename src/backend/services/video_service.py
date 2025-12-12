"""
Video upload and management service.
"""
import logging
import os
import time
from pathlib import Path
from typing import Dict
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ..config import TEMP_VIDEO_PATH, ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_BYTES

logger = logging.getLogger(__name__)


class VideoService:
    """Service for handling video uploads and temporary storage."""
    
    @staticmethod
    def is_allowed_extension(filename: str) -> bool:
        """Check if file extension is allowed."""
        return Path(filename).suffix.lower() in ALLOWED_VIDEO_EXTENSIONS
    
    @staticmethod
    def validate_video(file: FileStorage) -> Dict[str, str | bool]:
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
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
            }
        
        # Check file size (if available)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_VIDEO_SIZE_BYTES:
            return {
                "valid": False,
                "error": f"File too large. Max size: {MAX_VIDEO_SIZE_BYTES / (1024*1024):.0f}MB"
            }
        
        return {"valid": True}
    
    @staticmethod
    def save_video(file: FileStorage) -> Dict[str, str]:
        """
        Save uploaded video to temporary storage.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dict with 'success' bool, 'path' str, and optional 'error' str
        """
        try:
            # Validate file
            validation = VideoService.validate_video(file)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}
            
            # Generate secure filename with timestamp
            original_filename = secure_filename(file.filename)
            timestamp = int(time.time())
            filename = f"{timestamp}_{original_filename}"
            filepath = TEMP_VIDEO_PATH / filename
            
            # Save file
            file.save(str(filepath))
            logger.info(f"ℹ️ Video saved: {filepath}")
            
            return {
                "success": True,
                "path": str(filepath),
                "filename": filename,
                "size_mb": filepath.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to save video: {e}")
            return {"success": False, "error": str(e)}
    
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
                        logger.info(f"ℹ️ Deleted old video: {video_file.name}")
            
            if deleted_count > 0:
                logger.info(f"ℹ️ Cleanup complete: {deleted_count} videos deleted")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return 0

