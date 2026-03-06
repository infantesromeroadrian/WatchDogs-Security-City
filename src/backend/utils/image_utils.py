"""
Image utility functions for agent verification and logging.
"""

import base64
import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def verify_image_size(image_base64: str, agent_name: str = "Agent") -> tuple[int, int] | None:
    """
    Verify and log image dimensions for debugging.

    Args:
        image_base64: Base64 encoded image with data URI
        agent_name: Name of the agent calling this (for logging)

    Returns:
        Tuple of (width, height) if successful, None otherwise
    """
    try:
        # Decode base64
        img_data = base64.b64decode(
            image_base64.split(",")[1] if "," in image_base64 else image_base64
        )
        img = Image.open(io.BytesIO(img_data))
        width, height = img.size

        # Log verification info
        logger.debug(
            "🖼️ %s — image %sx%s pixels",
            agent_name,
            width,
            height,
        )

        return (width, height)

    except (ValueError, TypeError, RuntimeError) as e:
        logger.warning("⚠️ %s: Could not decode image for size check: %s", agent_name, e)
        return None
