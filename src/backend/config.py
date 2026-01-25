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

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found in environment variables")

OPENAI_MODEL = "gpt-5.1"  # GPT-5.1 multimodal with advanced vision and reasoning capabilities
OPENAI_MAX_TOKENS = 3000
OPENAI_TEMPERATURE = 0.3

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
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

# Base64 Image Size Limits (for DoS prevention)
MAX_BASE64_SIZE_MB = int(os.getenv("MAX_BASE64_SIZE_MB", "10"))  # 10MB default
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
ANALYSIS_DATA_RETENTION_HOURS = int(os.getenv("ANALYSIS_DATA_RETENTION_HOURS", "24"))
PURGE_BIOMETRIC_DATA_IMMEDIATELY = (
    os.getenv("PURGE_BIOMETRIC_DATA_IMMEDIATELY", "False").lower() == "true"
)

# Consent Requirements
# If True, requires explicit consent flag in API requests for face analysis
REQUIRE_EXPLICIT_CONSENT_FOR_FACE_ANALYSIS = (
    os.getenv("REQUIRE_EXPLICIT_CONSENT_FOR_FACE_ANALYSIS", "False").lower() == "true"
)

# Anonymization
# If True, face analysis will blur/redact identifying features in reports
ANONYMIZE_FACE_ANALYSIS_OUTPUT = (
    os.getenv("ANONYMIZE_FACE_ANALYSIS_OUTPUT", "False").lower() == "true"
)

# Privacy Mode - Disables ALL sensitive analysis (face, forensic, context)
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "False").lower() == "true"

# Logging Configuration (following rule 19)
LOG_LEVEL = logging.INFO if FLASK_ENV == "production" else logging.DEBUG
# Format includes filename:lineno for traceability
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

logger = logging.getLogger(__name__)
logger.info("ℹ️ Configuration loaded successfully")
logger.info(f"ℹ️ Temp video path: {TEMP_VIDEO_PATH}")
logger.info(f"ℹ️ OpenAI model: {OPENAI_MODEL}")

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
        logger.info(f"ℹ️ Privacy settings: {', '.join(privacy_status)}")
