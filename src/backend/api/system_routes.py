"""
System routes: health, metrics, video upload
"""

import logging
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from ..config import METRICS_ENABLED, VIDEO_RETENTION_HOURS
from ..services.video_service import VideoService
from ..utils.cache_utils import get_cache_stats
from ..utils.metrics_utils import get_agent_metrics
from .middleware import auth_required

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
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@system_bp.route("/upload-video", methods=["POST"])
@auth_required
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

        logger.info("✅ Video uploaded: %s", result["filename"])

        # Cleanup old videos
        deleted = video_service.cleanup_old_videos(VIDEO_RETENTION_HOURS)
        if deleted > 0:
            result["cleanup"] = f"{deleted} old videos removed"

        return jsonify(result), 200

    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Upload error: %s", e)
        # M-8: Don't expose internal exception details to client
        return jsonify({"success": False, "error": "Upload processing failed"}), 500


@system_bp.route("/metrics", methods=["GET"])
@auth_required
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
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ), 200

    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Error getting metrics: %s", e)
        return jsonify({"success": False, "error": "Failed to retrieve metrics"}), 500
