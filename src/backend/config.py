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

# LLM Configuration — OpenAI-compatible endpoints (OpenAI, Groq, Ollama, LM Studio, vLLM).
# LLM_PROVIDER picks default endpoint + model (see llm/provider.py); the OPENAI_* variables
# below override each piece individually. Default: Groq (the deployed provider).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or None  # None → provider's default model
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
# Hard HTTP timeout per LLM request (closes the socket; a thread timeout cannot)
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
# Max simultaneous LLM requests per process (rate-limit and CPU protection)
LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "16"))

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
# Render sets RENDER=true; treat it as production even if FLASK_ENV is missing.
IS_PRODUCTION = FLASK_ENV == "production" or bool(os.getenv("RENDER"))
# M-2: Default to False — debug mode must be explicitly opted-in, never on by accident
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Video Configuration
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "50"))
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
# Uploaded videos are deleted by a background janitor after this many minutes
VIDEO_RETENTION_MINUTES = int(os.getenv("VIDEO_RETENTION_MINUTES", "15"))
VIDEO_RETENTION_HOURS = VIDEO_RETENTION_MINUTES / 60  # legacy name, kept for callers
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# Flask Upload Configuration
MAX_CONTENT_LENGTH = MAX_VIDEO_SIZE_BYTES  # Use same limit as video size

# Security Configuration
# CORS: the SPA is same-origin, so by default NO cross-origin access is allowed.
# Set ALLOWED_ORIGINS=https://a.example,https://b.example only if a separate frontend needs it.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if "*" in ALLOWED_ORIGINS:
    raise RuntimeError("ALLOWED_ORIGINS must list explicit origins; '*' is not allowed")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))  # per IP

# Authentication is ON by default for every /api route and the SPA (deny-by-default guard in
# app.py). Credentials come from ADMIN_USERNAME / ADMIN_PASSWORD (env); sessions are signed with
# FLASK_SECRET_KEY. It can be disabled for local development only; never in production.
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() != "false"
AUTH_COOKIE_NAME = "wd_session"
SESSION_HOURS = float(os.getenv("SESSION_HOURS", "8"))
# Behind Render's TLS-terminating proxy: trust X-Forwarded-Proto/For (set TRUST_PROXY=1)
TRUST_PROXY = os.getenv("TRUST_PROXY", "1" if os.getenv("RENDER") else "0") == "1"
if not AUTH_ENABLED and IS_PRODUCTION:
    raise RuntimeError("AUTH_ENABLED=false is not allowed in production")

# LLM budget: hard daily caps on provider calls (a full analysis = 16 calls per frame).
# The counter is persisted in SQLite so worker recycling does not reset it.
LLM_DAILY_CALL_LIMIT = int(os.getenv("LLM_DAILY_CALL_LIMIT", "480"))  # ~30 full analyses/day
LLM_DAILY_CALL_LIMIT_PER_USER = int(os.getenv("LLM_DAILY_CALL_LIMIT_PER_USER", "320"))
LLM_BUDGET_DB = os.getenv("LLM_BUDGET_DB", str(BASE_DIR / "data" / "llm_budget.sqlite3"))

# Request body cap for JSON endpoints (frames are base64; videos use MAX_VIDEO_SIZE_MB)
MAX_JSON_BODY_MB = int(os.getenv("MAX_JSON_BODY_MB", "30"))
MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", str(40_000_000)))  # decompression-bomb guard

# Base64 Image Size Limits (for DoS prevention)
# M-3: Aligned with frontend 20MB image upload limit (video-player.js loadImage)
MAX_BASE64_SIZE_MB = int(os.getenv("MAX_BASE64_SIZE_MB", "12"))  # per image
MAX_BASE64_SIZE_BYTES = MAX_BASE64_SIZE_MB * 1024 * 1024

# Agent Configuration
# Note: vision LLMs with complex prompts (geolocation, forensic) can take 30-45s
# Default increased to 60s for reliability; configurable via env var
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))  # Timeout per agent
AGENT_RETRY_MAX_ATTEMPTS = int(os.getenv("AGENT_RETRY_MAX_ATTEMPTS", "3"))  # Max retry attempts
AGENT_RETRY_MIN_WAIT = float(os.getenv("AGENT_RETRY_MIN_WAIT", "2.0"))  # Min wait between retries
AGENT_RETRY_MAX_WAIT = float(os.getenv("AGENT_RETRY_MAX_WAIT", "10.0"))  # Max wait between retries

# Caching Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 min: results of an image are not kept longer than needed

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
logger.info("ℹ️ LLM provider: %s (model override: %s)", LLM_PROVIDER, OPENAI_MODEL)
if AUTH_ENABLED:
    logger.info("🔐 Authentication required on all /api routes and the SPA")
else:
    logger.warning("⚠️ AUTH_ENABLED=false — API is OPEN (local development only)")
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
