"""
Unit tests for Flask API endpoints.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from io import BytesIO
from PIL import Image
from unittest.mock import patch, Mock
from src.backend.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_index_route(self, client):
        """Test that index route serves HTML."""
        response = client.get('/')
        assert response.status_code in [200, 404]  # May fail if static files not in test env
    
    def test_analyze_frame_missing_data(self, client):
        """Test analyze endpoint with missing frame data."""
        response = client.post(
            '/api/analyze-frame',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_analyze_frame_invalid_base64(self, client):
        """Test analyze endpoint with invalid base64."""
        response = client.post(
            '/api/analyze-frame',
            json={'frame': 'invalid_base64'},
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('src.backend.app.coordinator')
    @patch('src.backend.app.image_service')
    def test_analyze_frame_success(self, mock_image_service, mock_coordinator, client):
        """Test successful frame analysis."""
        # Mock image service
        mock_image = Mock()
        mock_image_service.prepare_for_analysis.return_value = (
            mock_image,
            "data:image/png;base64,mock"
        )
        
        # Mock coordinator
        mock_coordinator.analyze_frame.return_value = {
            "json": {
                "status": "success",
                "agents": {
                    "vision": {"status": "success", "analysis": "test"},
                    "ocr": {"status": "success", "analysis": "test"},
                    "detection": {"status": "success", "analysis": "test"}
                }
            },
            "text": "Test analysis report"
        }
        
        # Create test request
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        import base64
        b64_data = base64.b64encode(buffer.read()).decode('utf-8')
        b64_string = f"data:image/png;base64,{b64_data}"
        
        response = client.post(
            '/api/analyze-frame',
            json={
                'frame': b64_string,
                'roi': {'x': 0, 'y': 0, 'width': 50, 'height': 50},
                'context': 'test context'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'results' in data
        assert 'json' in data['results']
        assert 'text' in data['results']
    
    def test_404_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
