"""
Configuration module for the Video Analysis Agent System.
Loads environment variables and provides centralized configuration.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_VIDEO_PATH = BASE_DIR / "data" / "temp"

# Ensure temp directory exists
TEMP_VIDEO_PATH.mkdir(parents=True, exist_ok=True)

# LLM Configuration — supports OpenAI API and compatible servers (LM Studio, Ollama, vLLM)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL"
)  # None → default OpenAI, or e.g. "http://host.docker.internal:1234/v1"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
# M-2: Default to False — debug mode must be explicitly opted-in, never on by accident
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Video Configuration
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
VIDEO_RETENTION_HOURS = int(os.getenv("VIDEO_RETENTION_HOURS", "1"))
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# Flask Upload Configuration
MAX_CONTENT_LENGTH = MAX_VIDEO_SIZE_BYTES  # Use same limit as video size

# Security Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",")
RATE_LIMIT_PER_MINUTE = int(
    os.getenv("RATE_LIMIT_PER_MINUTE", "30")
)  # 30 requests per minute per IP

# Authentication — set AUTH_ENABLED=True to enforce Bearer token auth on all endpoints
# When False (default for local dev), endpoints are open. Enable for any exposed deployment.
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "False").lower() == "true"

# Base64 Image Size Limits (for DoS prevention)
# M-3: Aligned with frontend 20MB image upload limit (video-player.js loadImage)
MAX_BASE64_SIZE_MB = int(os.getenv("MAX_BASE64_SIZE_MB", "20"))  # 20MB default
MAX_BASE64_SIZE_BYTES = MAX_BASE64_SIZE_MB * 1024 * 1024

# Agent Configuration
# Note: GPT-5.1 Vision with complex prompts (geolocation, forensic) can take 30-45s
# Default increased to 60s for reliability; configurable via env var
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))  # Timeout per agent
AGENT_RETRY_MAX_ATTEMPTS = int(os.getenv("AGENT_RETRY_MAX_ATTEMPTS", "3"))  # Max retry attempts
AGENT_RETRY_MIN_WAIT = float(os.getenv("AGENT_RETRY_MIN_WAIT", "2.0"))  # Min wait between retries
AGENT_RETRY_MAX_WAIT = float(os.getenv("AGENT_RETRY_MAX_WAIT", "10.0"))  # Max wait between retries

# Caching Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour default

# Circuit Breaker Configuration
CIRCUIT_BREAKER_ENABLED = os.getenv("CIRCUIT_BREAKER_ENABLED", "True").lower() == "true"
CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = float(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60.0"))

# Metrics Configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "True").lower() == "true"

# =============================================================================
# PRIVACY & GDPR CONFIGURATION
# =============================================================================
# These settings control sensitive analysis features that may have privacy implications

# Face Analysis Agent - Analyzes persons, demographics, distinctive marks
# GDPR Art. 9: Biometric data is a "special category" requiring explicit consent
FACE_ANALYSIS_ENABLED = os.getenv("FACE_ANALYSIS_ENABLED", "True").lower() == "true"

# Forensic Analysis Agent - Analyzes image authenticity
# Generally less privacy-sensitive, but may reveal manipulation of personal images
FORENSIC_ANALYSIS_ENABLED = os.getenv("FORENSIC_ANALYSIS_ENABLED", "True").lower() == "true"

# Context Intel Agent - Infers temporal, cultural, socioeconomic context
# May infer sensitive information about individuals or groups
CONTEXT_INTEL_ENABLED = os.getenv("CONTEXT_INTEL_ENABLED", "True").lower() == "true"

# Data Retention Policy
# GDPR Art. 5(1)(e): Data should not be kept longer than necessary
# TODO: Implement GDPR enforcement (consent, anonymization, data retention)
# These controls should be enforced in face_agent.py and analysis_routes.py

# Privacy Mode - Disables ALL sensitive analysis (face, forensic, context)
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "False").lower() == "true"

# =============================================================================
# MILITARY INTELLIGENCE AGENTS (Block 1)
# =============================================================================
# These agents provide military-grade analysis capabilities

VEHICLE_DETECTION_ENABLED = os.getenv("VEHICLE_DETECTION_ENABLED", "True").lower() == "true"
WEAPON_DETECTION_ENABLED = os.getenv("WEAPON_DETECTION_ENABLED", "True").lower() == "true"
CROWD_ANALYSIS_ENABLED = os.getenv("CROWD_ANALYSIS_ENABLED", "True").lower() == "true"
SHADOW_ANALYSIS_ENABLED = os.getenv("SHADOW_ANALYSIS_ENABLED", "True").lower() == "true"
INFRASTRUCTURE_ANALYSIS_ENABLED = (
    os.getenv("INFRASTRUCTURE_ANALYSIS_ENABLED", "True").lower() == "true"
)

# =============================================================================
# MILITARY INTELLIGENCE AGENTS (Block 2)
# =============================================================================
# Temporal change detection and night/low-light analysis

TEMPORAL_COMPARISON_ENABLED = os.getenv("TEMPORAL_COMPARISON_ENABLED", "True").lower() == "true"
NIGHT_VISION_ENABLED = os.getenv("NIGHT_VISION_ENABLED", "True").lower() == "true"

# =============================================================================
# MILITARY INTELLIGENCE AGENTS (Block 3)
# =============================================================================
# NATO symbology classification and multi-monitor command center layouts

NATO_SYMBOLOGY_ENABLED = os.getenv("NATO_SYMBOLOGY_ENABLED", "True").lower() == "true"
MULTI_MONITOR_ENABLED = os.getenv("MULTI_MONITOR_ENABLED", "True").lower() == "true"

# Mapbox Configuration (optional — map features degrade gracefully)
MAPBOX_ACCESS_TOKEN = os.getenv("MAP_BOX_ACCESS_TOKEN")

# Logging Configuration (following rule 19)
LOG_LEVEL = logging.INFO if FLASK_ENV == "production" else logging.DEBUG
# Format includes filename:lineno for traceability
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

logger = logging.getLogger(__name__)
logger.info("ℹ️ Configuration loaded successfully")
logger.info("ℹ️ Temp video path: %s", TEMP_VIDEO_PATH)
logger.info("ℹ️ OpenAI model: %s", OPENAI_MODEL)
if AUTH_ENABLED:
    logger.info("🔐 AUTH_ENABLED=True — API endpoints require Bearer token")
else:
    logger.warning("⚠️ AUTH_ENABLED=False — API endpoints are OPEN (local dev mode)")
if not MAPBOX_ACCESS_TOKEN:
    logger.warning("⚠️ MAP_BOX_ACCESS_TOKEN not found — interactive map features disabled")

# Log privacy settings at startup
if PRIVACY_MODE:
    logger.warning("⚠️ PRIVACY_MODE enabled - Face, Forensic, and Context Intel agents DISABLED")
else:
    privacy_status = []
    if not FACE_ANALYSIS_ENABLED:
        privacy_status.append("Face Analysis: DISABLED")
    if not FORENSIC_ANALYSIS_ENABLED:
        privacy_status.append("Forensic Analysis: DISABLED")
    if not CONTEXT_INTEL_ENABLED:
        privacy_status.append("Context Intel: DISABLED")
    if privacy_status:
        logger.info("ℹ️ Privacy settings: %s", ", ".join(privacy_status))
