"""
System routes: health, metrics, video upload, transcoding, video serving
"""

import logging
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ..config import (
    MAPBOX_ACCESS_TOKEN,
    METRICS_ENABLED,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    TEMP_VIDEO_PATH,
    VIDEO_RETENTION_HOURS,
)
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
    """Health check endpoint with dependency verification."""
    # L-5: Verify critical dependencies beyond a simple "ok"
    checks = {
        "llm_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY != "lm-studio"),
        "llm_model": OPENAI_MODEL,
        "temp_dir_writable": TEMP_VIDEO_PATH.is_dir(),
        "map_configured": bool(MAPBOX_ACCESS_TOKEN),
    }
    all_ok = checks["llm_configured"] and checks["temp_dir_writable"]
    return jsonify(
        {
            "status": "healthy" if all_ok else "degraded",
            "service": "video-analysis-agents",
            "checks": checks,
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


# =============================================================================
# Video transcoding & serving
# =============================================================================


@system_bp.route("/transcode-video", methods=["POST"])
@auth_required
def transcode_video():
    """
    Upload a video and transcode to H.264 if the codec is browser-incompatible.

    Called by the frontend when the ``<video>`` element fires a decode/source
    error (MediaError code 3 or 4).

    Expected: multipart/form-data with 'video' field.

    Returns:
        JSON with ``video_url``, ``transcoded`` bool, and ``original_codec``.
    """
    try:
        if "video" not in request.files:
            return jsonify({"success": False, "error": "No video file provided"}), 400

        file = request.files["video"]

        # Save the original file (runs full validation: extension, magic bytes, size)
        save_result = video_service.save_video(file)
        if not save_result["success"]:
            return jsonify(save_result), 400

        saved_path = str(save_result["path"])

        # Detect the video codec via ffprobe (for logging/response)
        codec = video_service.detect_video_codec(saved_path)
        logger.info("Codec detected for transcode request: %s", codec)

        # ALWAYS transcode — the frontend only calls this endpoint when the
        # browser already FAILED to play the video.  Even "h264" can fail if
        # the profile is High 10-bit or 4:4:4, so re-encoding to H.264 High
        # 8-bit yuv420p guarantees browser compatibility.
        transcode_result = video_service.transcode_to_h264(saved_path)
        if not transcode_result["success"]:
            return jsonify(transcode_result), 500

        # Cleanup old videos (including originals from previous uploads)
        deleted = video_service.cleanup_old_videos(VIDEO_RETENTION_HOURS)
        if deleted > 0:
            logger.info("Cleanup removed %s old video(s)", deleted)

        return jsonify(
            {
                "success": True,
                "transcoded": True,
                "original_codec": codec or "unknown",
                "video_url": f"/api/video/{transcode_result['filename']}",
            }
        ), 200

    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Transcode endpoint error: %s", e)
        return jsonify({"success": False, "error": "Transcoding failed"}), 500


@system_bp.route("/video/<filename>", methods=["GET"])
def serve_video(filename: str):
    """
    Serve a video file from temporary storage.

    This endpoint does NOT require ``@auth_required`` because the browser's
    ``<video src="...">`` element cannot send Bearer tokens.  The timestamped
    filename provides weak authorization (unguessable + 1-hour retention).

    Security:
    - ``secure_filename`` strips path traversal characters.
    - Resolved path is validated against ``TEMP_VIDEO_PATH``.
    """
    safe_name = secure_filename(filename)
    if not safe_name:
        return jsonify({"error": "Invalid filename"}), 400

    filepath = TEMP_VIDEO_PATH / safe_name

    # Double-check: resolved path must be under TEMP_VIDEO_PATH
    try:
        filepath.resolve().relative_to(TEMP_VIDEO_PATH.resolve())
    except ValueError:
        logger.warning("Path traversal attempt blocked: %s", filename)
        return jsonify({"error": "Invalid path"}), 403

    if not filepath.exists() or not filepath.is_file():
        return jsonify({"error": "Video not found"}), 404

    return send_file(filepath, mimetype="video/mp4")
