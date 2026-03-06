"""
Image processing service for frame extraction and ROI cropping.
"""

import base64
import binascii
import logging
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from ..exceptions import ImageProcessingError

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
            logger.info("ℹ️ Image decoded successfully: %s", image.size)
            return image
        except binascii.Error as e:
            logger.error("❌ Invalid base64 encoding: %s", e)
            raise ValueError(f"Invalid base64 encoding: {e}") from e
        except UnidentifiedImageError as e:
            logger.error("❌ Unidentified image format: %s", e)
            raise ImageProcessingError(f"Cannot identify image format: {e}") from e
        except (OSError, IOError) as e:
            logger.error("❌ Failed to read image data: %s", e)
            raise ImageProcessingError(f"Failed to read image data: {e}") from e

    @staticmethod
    def crop_roi(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
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
            logger.info("ℹ️ ROI cropped: %s", cropped.size)
            return cropped
        except AttributeError as e:
            logger.error("❌ Invalid image object: %s", e)
            raise TypeError(f"Expected PIL Image object, got {type(image)}") from e
        except (TypeError, ValueError) as e:
            logger.error("❌ Invalid crop coordinates: %s", e)
            raise ValueError(f"Invalid crop coordinates: {e}") from e

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
        except (OSError, IOError) as e:
            logger.error("❌ Failed to save image: %s", e)
            raise ImageProcessingError(f"Failed to save image to buffer: {e}") from e
        except (KeyError, ValueError) as e:
            logger.error("❌ Invalid image format '%s': %s", format, e)
            raise ValueError(f"Invalid image format '{format}': {e}") from e

    @staticmethod
    def prepare_for_analysis(
        base64_frame: str, roi_coords: dict | None = None
    ) -> tuple[Image.Image, str]:
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
        if roi_coords:
            x = roi_coords.get("x", 0)
            y = roi_coords.get("y", 0)
            width = roi_coords.get("width", image.width)
            height = roi_coords.get("height", image.height)

            logger.info(
                "✂️ Cropping ROI: original %s → region x=%s y=%s w=%s h=%s",
                image.size,
                x,
                y,
                width,
                height,
            )

            image = ImageService.crop_roi(image, x, y, width, height)

            logger.info("✂️ Sending CROPPED image to agents: %s", image.size)
        else:
            logger.info("📸 No ROI selected — sending FULL frame %s to agents", image.size)

        # Convert to base64 for OpenAI
        base64_for_api = ImageService.image_to_base64(image, format="PNG")

        return image, base64_for_api
