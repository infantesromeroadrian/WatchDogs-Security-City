"""
System routes: health, metrics, video upload
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from ..config import VIDEO_RETENTION_HOURS, METRICS_ENABLED
from ..services.video_service import VideoService
from ..utils.metrics_utils import get_agent_metrics
from ..utils.cache_utils import get_cache_stats

logger = logging.getLogger(__name__)

# Blueprint
system_bp = Blueprint("system", __name__)

# Services
video_service = VideoService()


@system_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "video-analysis-agents",
            "timestamp": datetime.now().isoformat(),
        }
    )


@system_bp.route("/upload-video", methods=["POST"])
def upload_video():
    """
    Upload video file for analysis.

    Expected: multipart/form-data with 'video' field
    Returns: JSON with upload status and file info
    """
    try:
        # Check if file is present
        if "video" not in request.files:
            return jsonify({"success": False, "error": "No video file provided"}), 400

        file = request.files["video"]

        # Save video
        result = video_service.save_video(file)

        if not result["success"]:
            return jsonify(result), 400

        logger.info(f"✅ Video uploaded: {result['filename']}")

        # Cleanup old videos
        deleted = video_service.cleanup_old_videos(VIDEO_RETENTION_HOURS)
        if deleted > 0:
            result["cleanup"] = f"{deleted} old videos removed"

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """Get agent metrics and cache statistics."""
    try:
        if not METRICS_ENABLED:
            return jsonify({"success": False, "error": "Metrics are disabled"}), 503

        metrics = get_agent_metrics()
        cache_stats = get_cache_stats()

        return jsonify(
            {
                "success": True,
                "metrics": metrics,
                "cache": cache_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ), 200

    except Exception as e:
        logger.error(f"❌ Error getting metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
