"""
Pytest configuration and fixtures for WatchDogs tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.models import Base
from src.database.connection import get_db
from src.api.main import app


# ==========================================
# Database Fixtures
# ==========================================

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override the get_db dependency for tests."""
    def _override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ==========================================
# API Client Fixtures
# ==========================================

@pytest.fixture(scope="function")
def client(override_get_db):
    """Create a test client for API testing."""
    with TestClient(app) as test_client:
        yield test_client


# ==========================================
# Mock Data Fixtures
# ==========================================

@pytest.fixture
def mock_video_data():
    """Mock video data for testing."""
    return {
        "source_path": "/test/video.mp4",
        "source_type": "file",
        "filename": "test_video.mp4",
        "duration_seconds": 60.0,
        "fps": 30,
        "resolution": "1920x1080",
    }


@pytest.fixture
def mock_face_encoding():
    """Mock face encoding (128D vector)."""
    import numpy as np
    return np.random.rand(128).tolist()


@pytest.fixture
def mock_frame_data():
    """Mock frame data for testing."""
    return {
        "frame_number": 100,
        "timestamp_ms": 3333,
        "storage_path": "test/frame_100.jpg",
        "has_faces": True,
    }


# ==========================================
# Test Utilities
# ==========================================

@pytest.fixture
def create_test_video(test_db, mock_video_data):
    """Create a test video in the database."""
    from src.database import crud, schemas
    
    video_create = schemas.VideoCreate(**mock_video_data)
    video = crud.create_video(test_db, video_create)
    return video

