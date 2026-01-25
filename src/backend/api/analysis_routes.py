"""
Analysis routes: frame analysis, chat, batch processing
"""

import logging
import re
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..agents.coordinator import CoordinatorAgent
from ..config import MAX_BASE64_SIZE_BYTES, MAX_BASE64_SIZE_MB
from ..services.image_service import ImageService

logger = logging.getLogger(__name__)

# Blueprint
analysis_bp = Blueprint("analysis", __name__)

# Services
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


def detect_specific_frame_request(message: str, total_frames: int) -> int | None:
    """
    Detect if user is asking about a specific frame.

    Args:
        message: User's message/question
        total_frames: Total number of frames available

    Returns:
        Frame index (1-based) if detected, None otherwise

    Examples:
        "Detalla el frame 1" -> 1
        "¿Qué ves en el segundo frame?" -> 2
        "Analiza la primera imagen" -> 1
        "Compara todos los frames" -> None (general question)
    """
    message_lower = message.lower()

    # Pattern 1: "frame N", "frame número N"
    patterns = [
        r"\bframe\s+(\d+)\b",
        r"\bframe\s+n[úu]mero\s+(\d+)\b",
        r"\bel\s+frame\s+(\d+)\b",
        r"\bla\s+imagen\s+(\d+)\b",
        r"\bfoto\s+(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            frame_num = int(match.group(1))
            if 1 <= frame_num <= total_frames:
                return frame_num

    # Pattern 2: Ordinal words (primer, segundo, tercer, etc.)
    ordinals = {
        r"\bprim(er|era?)\b": 1,
        r"\bsegund[ao]\b": 2,
        r"\btercer[ao]?\b": 3,
        r"\bcuart[ao]\b": 4,
        r"\bquint[ao]\b": 5,
        r"\bsext[ao]\b": 6,
        r"\bs[ée]ptim[ao]\b": 7,
        r"\boctav[ao]\b": 8,
        r"\bnoven[ao]\b": 9,
        r"\bd[ée]cim[ao]\b": 10,
    }

    for pattern, num in ordinals.items():
        if re.search(pattern, message_lower) and num <= total_frames:
            # Make sure it's about frame/image (not just "primero" in general context)
            if re.search(r"\b(frame|imagen|foto|fotograf[íi]a)\b", message_lower) or re.search(
                pattern + r"\s+(frame|imagen|foto)", message_lower
            ):
                return num

    # Pattern 3: "el último", "la última imagen"
    if re.search(r"\b[úu]ltim[ao]\b", message_lower) and re.search(
        r"\b(frame|imagen|foto)\b", message_lower
    ):
        return total_frames

    # No specific frame detected
    return None


@analysis_bp.route("/analyze-frame", methods=["POST"])
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
            return jsonify({"success": False, "error": error_msg}), 413  # Payload Too Large

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
        _image, prepared_base64 = image_service.prepare_for_analysis(frame_base64, roi_coords)

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

    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"❌ Analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@analysis_bp.route("/chat-query", methods=["POST"])
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

            from ..agents.vision_agent import VisionAgent

            vision_agent = VisionAgent()

            # 🎯 Smart frame detection: Check if user is asking about a specific frame
            specific_frame_idx = detect_specific_frame_request(message, len(frames))

            if specific_frame_idx is not None:
                # User asked about a specific frame - optimize by analyzing only that one
                logger.info(f"🎯 Detected specific frame request: Frame {specific_frame_idx}")
                target_frame = frames[specific_frame_idx - 1]  # Convert to 0-based index
                frame_base64 = target_frame.get("frame", "")
                frame_desc = target_frame.get("description", f"Frame {specific_frame_idx}")

                # Build context for single frame
                single_context = f"{context}\n\nPregunta del usuario: {message}\n\n"
                single_context += f"Estás analizando: {frame_desc}\n"
                single_context += "Responde SOLO sobre este frame específico.\n"

                result = vision_agent.analyze(frame_base64, single_context)
                response_text = result.get("analysis", "Sin análisis")

                logger.info(f"✅ Single-frame chat query complete (frame {specific_frame_idx})")
                return jsonify({"success": True, "response": response_text}), 200

            else:
                # General question - analyze all frames
                logger.info("🔍 General question detected - analyzing all frames")

                # Build comprehensive prompt
                full_context = f"{context}\n\nPregunta del usuario: {message}\n\n"
                full_context += f"A continuación recibirás {len(frames)} imágenes. Analízalas TODAS y responde la pregunta.\n"

                # Analyze each frame and collect responses
                frame_analyses = []
                for idx, frame_data in enumerate(frames, 1):
                    frame_base64 = frame_data.get("frame", "")
                    frame_desc = frame_data.get("description", f"Frame {idx}")

                    # Analyze this frame
                    frame_context = (
                        f"{full_context}\n\nEstás analizando: {frame_desc} ({idx}/{len(frames)})"
                    )
                    result = vision_agent.analyze(frame_base64, frame_context)
                    analysis = result.get("analysis", "Sin análisis")

                    frame_analyses.append(f"**{frame_desc}**: {analysis}")
                    logger.debug(f"   ✓ Frame {idx} analyzed")

                # Combine all analyses
                combined_response = "\n\n".join(frame_analyses)

                logger.info("✅ Multi-frame chat query complete")
                return jsonify({"success": True, "response": combined_response}), 200

        # SINGLE-FRAME MODE (original logic)
        if "frame" in data:
            frame_base64 = data["frame"]
            context = data.get("context", "")

            # DEBUG: Log what we received
            logger.debug(f"🔍 DEBUG chat-query received:")
            logger.debug(f"   - frame type: {type(frame_base64).__name__}")
            logger.debug(f"   - frame is None: {frame_base64 is None}")
            if isinstance(frame_base64, dict):
                logger.debug(
                    f"   - frame keys: {list(frame_base64.keys()) if frame_base64 else 'empty'}"
                )
                logger.debug(f"   - frame preview: {str(frame_base64)[:200]}")
            elif isinstance(frame_base64, str):
                logger.debug(f"   - frame length: {len(frame_base64)}")
                logger.debug(
                    f"   - frame starts with: {frame_base64[:50] if len(frame_base64) > 50 else frame_base64}"
                )

            # Validate frame is a string (defensive against malformed payloads)
            if not isinstance(frame_base64, str):
                logger.error(f"❌ Invalid frame type: {type(frame_base64).__name__} (expected str)")
                return jsonify(
                    {
                        "success": False,
                        "error": f"Invalid 'frame' type: expected base64 string, got {type(frame_base64).__name__}",
                    }
                ), 400

            if not frame_base64 or len(frame_base64) < 100:
                logger.error(
                    f"❌ Frame is empty or too short: {len(frame_base64) if frame_base64 else 0} chars"
                )
                return jsonify(
                    {
                        "success": False,
                        "error": "Frame data is empty or invalid. Please capture a frame first.",
                    }
                ), 400

            logger.info("💬 Processing SINGLE-FRAME chat query")

            from ..agents.vision_agent import VisionAgent

            vision_agent = VisionAgent()
            result = vision_agent.analyze(frame_base64, context)
            response_text = result.get("analysis", "No response generated")

            logger.info("✅ Single-frame chat query complete")
            return jsonify({"success": True, "response": response_text}), 200

        return jsonify(
            {"success": False, "error": "Invalid payload: need 'frame' or 'frames'"}
        ), 400

    except ValueError as e:
        logger.error(f"❌ Chat validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@analysis_bp.route("/analyze-batch", methods=["POST"])
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
            return jsonify({"success": False, "error": "Provide between 1 and 10 frames"}), 400

        # Validate each frame has base64 data
        for idx, frame in enumerate(frames):
            if "frame" not in frame:
                return jsonify(
                    {"success": False, "error": f"Frame {idx + 1} missing base64 data"}
                ), 400

            # Validate base64 size
            is_valid, error_msg = validate_base64_size(frame["frame"])
            if not is_valid:
                return jsonify({"success": False, "error": f"Frame {idx + 1}: {error_msg}"}), 413

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

    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"❌ Batch analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
