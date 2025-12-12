"""
Unit tests for service functionality.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from io import BytesIO
from PIL import Image
from src.backend.services.image_service import ImageService


class TestImageService:
    """Test suite for Image Service."""
    
    def create_test_image(self, width=100, height=100):
        """Helper to create test image."""
        img = Image.new('RGB', (width, height), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return img, buffer
    
    def test_decode_base64_image(self):
        """Test base64 image decoding."""
        # Create test image
        img, buffer = self.create_test_image()
        
        # Convert to base64
        import base64
        b64_data = base64.b64encode(buffer.read()).decode('utf-8')
        b64_string = f"data:image/png;base64,{b64_data}"
        
        # Test decoding
        decoded_img = ImageService.decode_base64_image(b64_string)
        assert decoded_img is not None
        assert decoded_img.size == (100, 100)
    
    def test_decode_base64_invalid(self):
        """Test handling of invalid base64 data."""
        with pytest.raises(ValueError):
            ImageService.decode_base64_image("invalid_base64")
    
    def test_crop_roi(self):
        """Test ROI cropping."""
        img, _ = self.create_test_image(200, 200)
        
        # Crop a 50x50 region
        cropped = ImageService.crop_roi(img, 10, 10, 50, 50)
        assert cropped.size == (50, 50)
    
    def test_crop_roi_bounds(self):
        """Test ROI cropping respects image bounds."""
        img, _ = self.create_test_image(100, 100)
        
        # Try to crop beyond bounds
        cropped = ImageService.crop_roi(img, 90, 90, 50, 50)
        # Should be clipped to image bounds
        assert cropped.width <= 100
        assert cropped.height <= 100
    
    def test_image_to_base64(self):
        """Test image to base64 conversion."""
        img, _ = self.create_test_image()
        
        b64_string = ImageService.image_to_base64(img, format='PNG')
        assert b64_string.startswith('data:image/png;base64,')
        assert len(b64_string) > 100  # Has actual data
    
    def test_prepare_for_analysis_full_frame(self):
        """Test frame preparation without ROI."""
        img, buffer = self.create_test_image()
        buffer.seek(0)
        
        import base64
        b64_data = base64.b64encode(buffer.read()).decode('utf-8')
        b64_string = f"data:image/png;base64,{b64_data}"
        
        prepared_img, prepared_b64 = ImageService.prepare_for_analysis(b64_string)
        
        assert prepared_img is not None
        assert prepared_img.size == (100, 100)
        assert prepared_b64.startswith('data:image/png;base64,')
    
    def test_prepare_for_analysis_with_roi(self):
        """Test frame preparation with ROI."""
        img, buffer = self.create_test_image(200, 200)
        buffer.seek(0)
        
        import base64
        b64_data = base64.b64encode(buffer.read()).decode('utf-8')
        b64_string = f"data:image/png;base64,{b64_data}"
        
        roi_coords = {"x": 50, "y": 50, "width": 100, "height": 100}
        prepared_img, prepared_b64 = ImageService.prepare_for_analysis(
            b64_string, 
            roi_coords
        )
        
        assert prepared_img is not None
        assert prepared_img.size == (100, 100)  # Cropped to ROI
        assert prepared_b64.startswith('data:image/png;base64,')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
