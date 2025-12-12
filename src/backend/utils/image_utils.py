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
            image_base64.split(',')[1] if ',' in image_base64 else image_base64
        )
        img = Image.open(io.BytesIO(img_data))
        width, height = img.size
        
        # Log verification info
        logger.debug("=" * 80)
        logger.debug(f"🖼️ {agent_name} - Image Size Verification:")
        logger.debug(f"   📏 Dimensions: {width}x{height} pixels")
        
        if width < 640 or height < 360:
            logger.debug("   ✂️ STATUS: THIS IS A CROPPED ROI (smaller than full frame)")
        else:
            logger.debug("   📸 STATUS: THIS IS LIKELY THE FULL FRAME")
        logger.debug("=" * 80)
        
        return (width, height)
        
    except Exception as e:
        logger.warning(f"⚠️ {agent_name}: Could not decode image for size check: {e}")
        return None

