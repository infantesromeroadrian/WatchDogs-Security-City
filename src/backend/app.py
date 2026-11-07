"""
Flask backend for Video Analysis Agent System.
Main API server with Blueprint-based routes.
"""

import logging
import os
import secrets

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image
from werkzeug.middleware.proxy_fix import ProxyFix

# Import blueprints
from .api import analysis_bp, auth_bp, map_bp, professional_bp, system_bp
from .api.middleware import init_auth
from .config import (
    ALLOWED_ORIGINS,
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    IS_PRODUCTION,
    MAX_CONTENT_LENGTH,
    MAX_IMAGE_PIXELS,
    RATE_LIMIT_PER_MINUTE,
    TRUST_PROXY,
)
from .services.janitor import ensure_started as start_janitor
from .utils import log_redaction

# Configure logging (following rule 19)
logger = logging.getLogger(__name__)

log_redaction.install()  # no image data / tokens / e-mails in logs
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS  # decompression-bomb guard (Pillow raises above 2x)

# Initialize Flask app
app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH  # Limit upload file size
if TRUST_PROXY:
    # Behind Render's TLS proxy: real client IP for rate limiting, correct scheme for cookies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]

# H-3: Secret key from env var — required for session integrity and CSRF protection.
# Falls back to a random secret (safe but sessions won't survive restarts).
_env_secret = os.getenv("FLASK_SECRET_KEY")
if _env_secret:
    app.secret_key = _env_secret
elif IS_PRODUCTION:
    raise RuntimeError("FLASK_SECRET_KEY is required in production")
else:
    app.secret_key = secrets.token_hex(32)
    logger.warning("⚠️ FLASK_SECRET_KEY not set — using random secret (sessions lost on restart)")

# CORS: the SPA is served by this same app, so cross-origin access is OFF unless explicit origins
# are configured (ALLOWED_ORIGINS). Credentials are never shared cross-origin.
if ALLOWED_ORIGINS:
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ALLOWED_ORIGINS,
                "methods": ["GET", "POST"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
        supports_credentials=False,
    )

# Deny-by-default authentication for every route (see api/middleware.py)
init_auth(app)
app.before_request(start_janitor)

# Configure rate limiting (security rule 21)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{RATE_LIMIT_PER_MINUTE} per minute"],
    storage_uri="memory://",  # In-memory for simplicity (use Redis for production)
)

# Register blueprints
app.register_blueprint(system_bp, url_prefix="/api")
app.register_blueprint(analysis_bp, url_prefix="/api")
app.register_blueprint(professional_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(map_bp, url_prefix="/api")

# Apply rate limiting to specific blueprints
limiter.limit("10 per minute")(analysis_bp)
limiter.limit("20 per minute")(professional_bp)
limiter.limit("5 per minute")(auth_bp)
limiter.limit("5 per minute")(map_bp)

logger.info("🚀 Flask app initialized with blueprints")


# ---------------------------------------------------------------------------
# H-2: Security headers — applied to EVERY response
# ---------------------------------------------------------------------------
@app.after_request
def set_security_headers(response):
    """Inject security headers into every HTTP response."""
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Stop MIME-type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Enable XSS filter in older browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Referrer policy — send origin only to same-origin, nothing cross-origin
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Content-Security-Policy — allow self + inline (needed for the SPA) + Mapbox tiles/API
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://api.mapbox.com; "
        "style-src 'self' 'unsafe-inline' https://api.mapbox.com; "
        "font-src 'self' https://fonts.mapbox.com; "
        "img-src 'self' data: blob: https://*.mapbox.com; "
        "connect-src 'self' https://api.mapbox.com https://*.tiles.mapbox.com https://events.mapbox.com; "
        "worker-src 'self' blob:; "
        "frame-ancestors 'none';"
    )
    # Analysis results can contain personal data: never let browsers or proxies cache API responses
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    # HSTS — only in production (avoids locking out local dev)
    if not FLASK_DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.route("/")
def index():
    """Serve main frontend page (requires a session; otherwise the guard redirects to /login)."""
    return send_from_directory("../frontend", "index.html")


@app.route("/login")
def login_page():
    """Public login page."""
    return send_from_directory("../frontend", "login.html")


@app.errorhandler(413)
def too_large(error):
    """Handle oversized request bodies."""
    return {"success": False, "error": "Request body too large"}, 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return {"success": False, "error": "Endpoint not found"}, 404


@app.errorhandler(Exception)
def unhandled_error(error):
    """Last resort: log the traceback server-side, return nothing internal to the client."""
    from werkzeug.exceptions import HTTPException

    if isinstance(error, HTTPException):
        return error
    logger.exception("Unhandled error")
    return {"success": False, "error": "Internal server error"}, 500


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error("Internal error: %s", error)
    return {"success": False, "error": "Internal server error"}, 500


def run_server():
    """Run Flask development server."""
    logger.info("🌐 Starting server on %s:%s", FLASK_HOST, FLASK_PORT)
    logger.info("🔧 Debug mode: %s", FLASK_DEBUG)

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


if __name__ == "__main__":
    run_server()
