"""
Flask backend for Video Analysis Agent System.
Main API server with endpoints for video upload and frame analysis.
"""

import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import (
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    MAX_CONTENT_LENGTH,
    VIDEO_RETENTION_HOURS,
    ALLOWED_ORIGINS,
    RATE_LIMIT_PER_MINUTE,
    METRICS_ENABLED,
    MAX_BASE64_SIZE_BYTES,
    MAX_BASE64_SIZE_MB,
)
from .services.video_service import VideoService
from .services.image_service import ImageService
from .agents.coordinator import CoordinatorAgent
from .utils.metrics_utils import get_agent_metrics
from .utils.cache_utils import get_cache_stats

# Configure logging (following rule 19)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH  # Limit upload file size

# Configure CORS with restrictions (security baseline rule 01)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"],
        }
    },
)

# Configure rate limiting (security rule 21)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{RATE_LIMIT_PER_MINUTE} per minute"],
    storage_uri="memory://",  # In-memory for simplicity (use Redis for production)
)

# Initialize services and agents
video_service = VideoService()
image_service = ImageService()
coordinator = CoordinatorAgent()


def validate_base64_size(base64_string: str) -> tuple[bool, str | None]:
    """
    Validate base64 string size to prevent DoS attacks.

    Args:
        base64_string: Base64 encoded string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(base64_string) > MAX_BASE64_SIZE_BYTES:
        size_mb = len(base64_string) / (1024 * 1024)
        return (
            False,
            f"Frame too large ({size_mb:.1f}MB). Max allowed: {MAX_BASE64_SIZE_MB}MB",
        )
    return True, None


logger.info("🚀 Flask app initialized")


@app.route("/")
def index():
    """Serve main frontend page."""
    return send_from_directory("../frontend", "index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "video-analysis-agents",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/upload-video", methods=["POST"])
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


@app.route("/api/analyze-frame", methods=["POST"])
@limiter.limit("10 per minute")  # Stricter limit for expensive operations
def analyze_frame():
    """
    Analyze video frame with multi-agent system.

    Expected JSON:
    {
        "frame": "base64_encoded_image",
        "roi": {"x": 0, "y": 0, "width": 100, "height": 100},  // optional
        "context": "optional context string"
    }

    Returns: JSON with analysis results (both structured JSON and readable text)
    """
    try:
        data = request.get_json()

        if not data or "frame" not in data:
            return jsonify({"success": False, "error": "No frame data provided"}), 400

        frame_base64 = data["frame"]
        roi_coords = data.get("roi")
        context = data.get("context", "")

        # Validate base64 size (DoS prevention)
        is_valid, error_msg = validate_base64_size(frame_base64)
        if not is_valid:
            logger.warning(f"⚠️ Base64 validation failed: {error_msg}")
            return jsonify(
                {"success": False, "error": error_msg}
            ), 413  # Payload Too Large

        # Log ROI info (DEBUG level to avoid noise in production)
        logger.debug("=" * 80)
        logger.debug(f"ROI COORDS RECEIVED: {roi_coords}")
        logger.debug(f"ROI TYPE: {type(roi_coords)}")
        if roi_coords:
            logger.debug(
                f"ROI x={roi_coords.get('x')}, y={roi_coords.get('y')}, w={roi_coords.get('width')}, h={roi_coords.get('height')}"
            )
        else:
            logger.debug("NO ROI - Analyzing FULL frame")
        logger.debug("=" * 80)

        if context:
            logger.info(f"ℹ️ Context provided: {len(context)} chars")

        # Prepare image (decode and crop ROI if provided)
        image, prepared_base64 = image_service.prepare_for_analysis(
            frame_base64, roi_coords
        )

        # Execute multi-agent analysis
        results = coordinator.analyze_frame(prepared_base64, context)

        # Add timestamp
        if "json" in results:
            results["json"]["timestamp"] = datetime.now().isoformat()

        logger.info("✅ Frame analysis complete")

        return jsonify({"success": True, "results": results}), 200

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat-query", methods=["POST"])
@limiter.limit("10 per minute")
def chat_query():
    """
    Chat endpoint for conversational analysis of image(s).

    Expected JSON (single-frame):
    {
        "frame": "base64_encoded_image",
        "context": "conversation context"
    }

    OR (multi-frame):
    {
        "frames": [{"frame": "base64...", "description": "Frame 1"}, ...],
        "message": "user question",
        "context": "conversation context"
    }

    Returns: JSON with conversational response
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # MULTI-FRAME MODE
        if "frames" in data and isinstance(data["frames"], list):
            frames = data["frames"]
            message = data.get("message", "")
            context = data.get("context", "")

            logger.info(f"💬 Processing MULTI-FRAME chat query ({len(frames)} frames)")

            from .agents.vision_agent import VisionAgent

            vision_agent = VisionAgent()

            # Build comprehensive prompt
            full_context = f"{context}\n\nPregunta del usuario: {message}\n\n"
            full_context += f"A continuación recibirás {len(frames)} imágenes. Analízalas TODAS y responde la pregunta.\n"

            # Analyze each frame and collect responses
            frame_analyses = []
            for idx, frame_data in enumerate(frames, 1):
                frame_base64 = frame_data.get("frame", "")
                frame_desc = frame_data.get("description", f"Frame {idx}")

                # Analyze this frame
                frame_context = f"{full_context}\n\nEstás analizando: {frame_desc} ({idx}/{len(frames)})"
                result = vision_agent.analyze(frame_base64, frame_context)
                analysis = result.get("analysis", "Sin análisis")

                frame_analyses.append(f"**{frame_desc}**: {analysis}")
                logger.debug(f"   ✓ Frame {idx} analyzed")

            # Combine all analyses
            combined_response = "\n\n".join(frame_analyses)

            logger.info("✅ Multi-frame chat query complete")
            return jsonify({"success": True, "response": combined_response}), 200

        # SINGLE-FRAME MODE (original logic)
        elif "frame" in data:
            frame_base64 = data["frame"]
            context = data.get("context", "")

            logger.info(f"💬 Processing SINGLE-FRAME chat query")

            from .agents.vision_agent import VisionAgent

            vision_agent = VisionAgent()
            result = vision_agent.analyze(frame_base64, context)
            response_text = result.get("analysis", "No response generated")

            logger.info("✅ Single-frame chat query complete")
            return jsonify({"success": True, "response": response_text}), 200

        else:
            return jsonify(
                {"success": False, "error": "Invalid payload: need 'frame' or 'frames'"}
            ), 400

    except ValueError as e:
        logger.error(f"❌ Chat validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze-batch", methods=["POST"])
@limiter.limit("5 per minute")  # More restrictive for batch operations
def analyze_batch():
    """
    Analyze multiple frames for enhanced OSINT with accumulated context.

    Expected JSON:
    {
        "frames": [
            {"frame": "base64_1", "description": "Front view"},
            {"frame": "base64_2", "description": "Street sign"},
            ...
        ],
        "enable_context_accumulation": true
    }

    Returns: JSON with individual results and combined geolocation
    """
    try:
        data = request.get_json()

        if not data or "frames" not in data:
            return jsonify({"success": False, "error": "No frames provided"}), 400

        frames = data["frames"]
        enable_context = data.get("enable_context_accumulation", True)

        # Validate frames count
        if not frames or len(frames) > 10:
            return jsonify(
                {"success": False, "error": "Provide between 1 and 10 frames"}
            ), 400

        # Validate each frame has base64 data
        for idx, frame in enumerate(frames):
            if "frame" not in frame:
                return jsonify(
                    {"success": False, "error": f"Frame {idx + 1} missing base64 data"}
                ), 400

            # Validate base64 size
            is_valid, error_msg = validate_base64_size(frame["frame"])
            if not is_valid:
                return jsonify(
                    {"success": False, "error": f"Frame {idx + 1}: {error_msg}"}
                ), 413

        logger.info(
            f"🔍 Processing batch of {len(frames)} frames (context_accumulation={enable_context})"
        )

        # Analyze with accumulated context
        results = coordinator.analyze_multi_frame(frames, enable_context)

        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        results["frames_analyzed"] = len(frames)

        logger.info(f"✅ Batch analysis complete ({len(frames)} frames)")

        return jsonify({"success": True, "results": results}), 200

    except ValueError as e:
        logger.error(f"❌ Batch validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"❌ Batch analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics", methods=["GET"])
@limiter.limit("10 per minute")
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


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


def run_server():
    """Run Flask development server."""
    logger.info(f"🌐 Starting server on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"🔧 Debug mode: {FLASK_DEBUG}")

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


if __name__ == "__main__":
    run_server()
