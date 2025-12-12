"""
Unit tests for agent functionality.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from src.backend.agents.vision_agent import VisionAgent
from src.backend.agents.ocr_agent import OCRAgent
from src.backend.agents.detection_agent import DetectionAgent


class TestVisionAgent:
    """Test suite for Vision Agent."""
    
    def test_agent_initialization(self):
        """Test that Vision Agent initializes correctly."""
        with patch('src.backend.agents.vision_agent.ChatOpenAI'):
            agent = VisionAgent()
            assert agent is not None
            assert hasattr(agent, 'llm')
            assert hasattr(agent, 'analyze')
    
    @patch('src.backend.agents.vision_agent.ChatOpenAI')
    def test_analyze_success(self, mock_openai):
        """Test successful analysis."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Test analysis result"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance
        
        agent = VisionAgent()
        result = agent.analyze("data:image/png;base64,test", "test context")
        
        assert result["agent"] == "vision"
        assert result["status"] == "success"
        assert "analysis" in result
        assert result["confidence"] == "high"
    
    @patch('src.backend.agents.vision_agent.ChatOpenAI')
    def test_analyze_error_handling(self, mock_openai):
        """Test error handling in analysis."""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception("API Error")
        mock_openai.return_value = mock_llm_instance
        
        agent = VisionAgent()
        result = agent.analyze("data:image/png;base64,test")
        
        assert result["agent"] == "vision"
        assert result["status"] == "error"
        assert "error" in result


class TestOCRAgent:
    """Test suite for OCR Agent."""
    
    def test_agent_initialization(self):
        """Test that OCR Agent initializes correctly."""
        with patch('src.backend.agents.ocr_agent.ChatOpenAI'):
            agent = OCRAgent()
            assert agent is not None
            assert hasattr(agent, 'llm')
            assert hasattr(agent, 'analyze')
    
    @patch('src.backend.agents.ocr_agent.ChatOpenAI')
    def test_analyze_with_text(self, mock_openai):
        """Test OCR analysis when text is found."""
        mock_response = Mock()
        mock_response.content = "Detected text: ABC123"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance
        
        agent = OCRAgent()
        result = agent.analyze("data:image/png;base64,test")
        
        assert result["agent"] == "ocr"
        assert result["status"] == "success"
        assert result["has_text"] is True
    
    @patch('src.backend.agents.ocr_agent.ChatOpenAI')
    def test_analyze_no_text(self, mock_openai):
        """Test OCR analysis when no text is detected."""
        mock_response = Mock()
        mock_response.content = "No se detectó texto en la imagen"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance
        
        agent = OCRAgent()
        result = agent.analyze("data:image/png;base64,test")
        
        assert result["agent"] == "ocr"
        assert result["status"] == "success"
        assert result["has_text"] is False


class TestDetectionAgent:
    """Test suite for Detection Agent."""
    
    def test_agent_initialization(self):
        """Test that Detection Agent initializes correctly."""
        with patch('src.backend.agents.detection_agent.ChatOpenAI'):
            agent = DetectionAgent()
            assert agent is not None
            assert hasattr(agent, 'llm')
            assert hasattr(agent, 'analyze')
    
    @patch('src.backend.agents.detection_agent.ChatOpenAI')
    def test_analyze_success(self, mock_openai):
        """Test successful detection analysis."""
        mock_response = Mock()
        mock_response.content = "Detected: 2 persons, 1 vehicle"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance
        
        agent = DetectionAgent()
        result = agent.analyze("data:image/png;base64,test")
        
        assert result["agent"] == "detection"
        assert result["status"] == "success"
        assert "analysis" in result
        assert result["confidence"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

