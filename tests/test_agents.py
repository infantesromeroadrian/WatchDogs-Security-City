"""
Unit tests for agent functionality.

M-11: Fixed — mocks now patch CACHE_ENABLED=False to skip cache validation
on test-grade base64 strings, and circuit breaker is disabled.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch


# ---------------------------------------------------------------------------
# Shared test base64 — long enough to pass get_image_hash validation (>=50 chars)
# ---------------------------------------------------------------------------
_FAKE_B64 = "data:image/png;base64," + "A" * 100


class TestVisionAgent:
    """Test suite for Vision Agent."""

    def test_agent_initialization(self):
        """Test that Vision Agent initializes correctly."""
        with patch("src.backend.llm.provider.ChatOpenAI"):
            from src.backend.agents.vision_agent import VisionAgent

            agent = VisionAgent()
            assert agent is not None
            assert hasattr(agent, "llm")
            assert hasattr(agent, "analyze")

    @patch("src.backend.agents.vision_agent.CACHE_ENABLED", False)
    @patch("src.backend.agents.vision_agent.CIRCUIT_BREAKER_ENABLED", False)
    @patch("src.backend.llm.provider.ChatOpenAI")
    def test_analyze_success(self, mock_openai):
        """Test successful analysis."""
        mock_response = Mock()
        mock_response.content = "Test analysis result"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        from src.backend.agents.vision_agent import VisionAgent

        agent = VisionAgent()
        result = agent.analyze(_FAKE_B64, "test context")

        assert result["agent"] == "vision"
        assert result["status"] == "success"
        assert "analysis" in result

    @patch("src.backend.agents.vision_agent.CACHE_ENABLED", False)
    @patch("src.backend.agents.vision_agent.CIRCUIT_BREAKER_ENABLED", False)
    @patch("src.backend.llm.provider.ChatOpenAI")
    def test_analyze_error_handling(self, mock_openai):
        """Test error handling when LLM returns an error."""
        mock_llm_instance = Mock()
        # Use ValueError — a realistic error the agent's analyze() actually catches
        mock_llm_instance.invoke.side_effect = ValueError("Invalid image data")
        mock_openai.return_value = mock_llm_instance

        from src.backend.agents.vision_agent import VisionAgent

        agent = VisionAgent()
        result = agent.analyze(_FAKE_B64)

        assert result["agent"] == "vision"
        assert result["status"] == "error"
        assert "error" in result


class TestOCRAgent:
    """Test suite for OCR Agent."""

    def test_agent_initialization(self):
        """Test that OCR Agent initializes correctly."""
        with patch("src.backend.llm.provider.ChatOpenAI"):
            from src.backend.agents.ocr_agent import OCRAgent

            agent = OCRAgent()
            assert agent is not None
            assert hasattr(agent, "llm")
            assert hasattr(agent, "analyze")

    @patch("src.backend.agents.ocr_agent.CACHE_ENABLED", False)
    @patch("src.backend.agents.ocr_agent.CIRCUIT_BREAKER_ENABLED", False)
    @patch("src.backend.llm.provider.ChatOpenAI")
    def test_analyze_with_text(self, mock_openai):
        """Test OCR analysis when text is found."""
        mock_response = Mock()
        mock_response.content = '{"has_text": true, "extracted_text": ["ABC123"], "summary": "plate"}'
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        from src.backend.agents.ocr_agent import OCRAgent

        agent = OCRAgent()
        result = agent.analyze(_FAKE_B64)

        assert result["agent"] == "ocr"
        assert result["status"] == "success"
        assert result["has_text"] is True

    @patch("src.backend.agents.ocr_agent.CACHE_ENABLED", False)
    @patch("src.backend.agents.ocr_agent.CIRCUIT_BREAKER_ENABLED", False)
    @patch("src.backend.llm.provider.ChatOpenAI")
    def test_analyze_no_text(self, mock_openai):
        """Test OCR analysis when no text is detected."""
        mock_response = Mock()
        mock_response.content = '{"has_text": false, "extracted_text": []}'
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        from src.backend.agents.ocr_agent import OCRAgent

        agent = OCRAgent()
        result = agent.analyze(_FAKE_B64)

        assert result["agent"] == "ocr"
        assert result["status"] == "success"
        assert result["has_text"] is False


class TestDetectionAgent:
    """Test suite for Detection Agent."""

    def test_agent_initialization(self):
        """Test that Detection Agent initializes correctly."""
        with patch("src.backend.llm.provider.ChatOpenAI"):
            from src.backend.agents.detection_agent import DetectionAgent

            agent = DetectionAgent()
            assert agent is not None
            assert hasattr(agent, "llm")
            assert hasattr(agent, "analyze")

    @patch("src.backend.agents.detection_agent.CACHE_ENABLED", False)
    @patch("src.backend.agents.detection_agent.CIRCUIT_BREAKER_ENABLED", False)
    @patch("src.backend.llm.provider.ChatOpenAI")
    def test_analyze_success(self, mock_openai):
        """Test successful detection analysis."""
        mock_response = Mock()
        mock_response.content = '{"objects": [{"label": "persona", "count": 2}], "total_people": 2, "total_vehicles": 1}'
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        from src.backend.agents.detection_agent import DetectionAgent

        agent = DetectionAgent()
        result = agent.analyze(_FAKE_B64)

        assert result["agent"] == "detection"
        assert result["status"] == "success"
        assert "analysis" in result
        assert result["total_people"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
