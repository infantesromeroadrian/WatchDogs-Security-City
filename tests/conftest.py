"""
Pytest configuration and fixtures for WatchDogs Security City tests.
"""

import base64
from pathlib import Path
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

# ============================================================================
# Sample Test Data
# ============================================================================

# Minimal 1x1 white PNG image (base64)
SAMPLE_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

SAMPLE_ANALYSIS_RESULT = {
    "agent": "vision",
    "status": "success",
    "analysis": "Test analysis result",
    "confidence": "high",
}


# ============================================================================
# Flask Application Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """
    Create and configure a Flask application for testing.

    Yields:
        Configured Flask application instance
    """
    # Import app here to avoid circular imports
    from src.backend.app import app as flask_app

    # Configure for testing
    flask_app.config.update(
        {
            "TESTING": True,
            "DEBUG": False,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        }
    )

    yield flask_app


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """
    Create a test client for the Flask application.

    Args:
        app: Flask application fixture

    Returns:
        Flask test client
    """
    return app.test_client()


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture
def sample_image_base64() -> str:
    """Provide a sample base64-encoded image for testing."""
    return SAMPLE_IMAGE_BASE64


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Provide sample image bytes for testing."""
    # Decode the base64 image
    base64_data = SAMPLE_IMAGE_BASE64.split(",")[1]
    return base64.b64decode(base64_data)


@pytest.fixture
def sample_analysis_result() -> dict:
    """Provide a sample analysis result for testing."""
    return SAMPLE_ANALYSIS_RESULT.copy()


@pytest.fixture
def mock_video_path(tmp_path: Path) -> Path:
    """
    Create a mock video file path for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to mock video file
    """
    video_file = tmp_path / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    return video_file


# ============================================================================
# Agent Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_vision_response():
    """Mock response from Vision Agent."""
    return {
        "agent": "vision",
        "status": "success",
        "analysis": "Urban street scene with vehicles and buildings",
        "confidence": "high",
    }


@pytest.fixture
def mock_ocr_response():
    """Mock response from OCR Agent."""
    return {
        "agent": "ocr",
        "status": "success",
        "analysis": "Detected text: STOP, Main Street, 123",
        "has_text": True,
        "confidence": "high",
    }


@pytest.fixture
def mock_detection_response():
    """Mock response from Detection Agent."""
    return {
        "agent": "detection",
        "status": "success",
        "analysis": "Detected: 2 vehicles, 1 traffic sign",
        "confidence": "high",
    }


@pytest.fixture
def mock_geolocation_response():
    """Mock response from Geolocation Agent."""
    return {
        "agent": "geolocation",
        "status": "success",
        "analysis": "Location analysis based on visual clues",
        "confidence": "medium",
        "location": {
            "country": "Spain",
            "city": "Madrid",
            "district": "Centro",
        },
        "coordinates": {"lat": 40.4168, "lon": -3.7038},
        "key_clues": ["Spanish traffic signs", "European architecture"],
    }


# ============================================================================
# Environment Setup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """
    Automatically setup test environment for all tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture
        tmp_path: Pytest temporary directory
    """
    # Set test environment variables
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("CACHE_ENABLED", "False")  # Disable cache in tests
    monkeypatch.setenv("METRICS_ENABLED", "False")  # Disable metrics in tests
    monkeypatch.setenv("CIRCUIT_BREAKER_ENABLED", "False")  # Disable circuit breaker

    # Set temp path for uploads
    test_temp_path = tmp_path / "temp"
    test_temp_path.mkdir(exist_ok=True)
    monkeypatch.setenv("TEMP_VIDEO_PATH", str(test_temp_path))
