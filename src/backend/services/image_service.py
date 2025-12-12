"""
Image processing service for frame extraction and ROI cropping.
"""
import base64
import logging
from io import BytesIO
from typing import Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ImageService:
    """Service for processing video frames and extracting regions of interest."""
    
    @staticmethod
    def decode_base64_image(base64_string: str) -> Image.Image:
        """
        Decode base64 string to PIL Image.
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If decoding fails
        """
        try:
            # Remove data URI prefix if present
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]
            
            image_data = base64.b64decode(base64_string)
            image = Image.open(BytesIO(image_data))
            logger.info(f"ℹ️ Image decoded successfully: {image.size}")
            return image
        except Exception as e:
            logger.error(f"❌ Failed to decode base64 image: {e}")
            raise ValueError(f"Invalid base64 image data: {e}")
    
    @staticmethod
    def crop_roi(
        image: Image.Image, 
        x: int, 
        y: int, 
        width: int, 
        height: int
    ) -> Image.Image:
        """
        Crop region of interest from image.
        
        Args:
            image: PIL Image object
            x: Top-left x coordinate
            y: Top-left y coordinate
            width: ROI width
            height: ROI height
            
        Returns:
            Cropped PIL Image
        """
        try:
            # Validate coordinates
            img_width, img_height = image.size
            x = max(0, min(x, img_width))
            y = max(0, min(y, img_height))
            right = min(x + width, img_width)
            bottom = min(y + height, img_height)
            
            cropped = image.crop((x, y, right, bottom))
            logger.info(f"ℹ️ ROI cropped: {cropped.size}")
            return cropped
        except Exception as e:
            logger.error(f"❌ Failed to crop ROI: {e}")
            raise ValueError(f"Failed to crop image: {e}")
    
    @staticmethod
    def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Base64 encoded image string
        """
        try:
            buffer = BytesIO()
            image.save(buffer, format=format)
            buffer.seek(0)
            base64_string = base64.b64encode(buffer.read()).decode("utf-8")
            return f"data:image/{format.lower()};base64,{base64_string}"
        except Exception as e:
            logger.error(f"❌ Failed to encode image to base64: {e}")
            raise ValueError(f"Failed to encode image: {e}")
    
    @staticmethod
    def prepare_for_analysis(
        base64_frame: str,
        roi_coords: dict | None = None
    ) -> Tuple[Image.Image, str]:
        """
        Prepare frame for agent analysis by decoding and optionally cropping ROI.
        
        Args:
            base64_frame: Base64 encoded frame
            roi_coords: Optional dict with keys: x, y, width, height
            
        Returns:
            Tuple of (PIL Image, base64 string for OpenAI)
        """
        # Decode frame
        image = ImageService.decode_base64_image(base64_frame)
        
        # Crop ROI if coordinates provided
        logger.info("=" * 80)
        logger.info(f"PREPARE_FOR_ANALYSIS: roi_coords = {roi_coords}")
        
        if roi_coords:
            x = roi_coords.get("x", 0)
            y = roi_coords.get("y", 0)
            width = roi_coords.get("width", image.width)
            height = roi_coords.get("height", image.height)
            
            logger.info(f"IMAGE SIZE BEFORE CROP: {image.size}")
            logger.info(f"CROPPING TO: x={x}, y={y}, w={width}, h={height}")
            
            image = ImageService.crop_roi(image, x, y, width, height)
            
            logger.info(f"IMAGE SIZE AFTER CROP: {image.size}")
            logger.info(f"ROI EXTRACTED SUCCESSFULLY")
        else:
            logger.info("NO ROI PROVIDED - Using full frame")
        
        logger.info("=" * 80)
        
        # Convert to base64 for OpenAI
        base64_for_api = ImageService.image_to_base64(image, format="PNG")
        
        return image, base64_for_api

