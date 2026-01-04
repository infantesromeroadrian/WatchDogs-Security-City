"""
Flask backend for Video Analysis Agent System.
Main API server with Blueprint-based routes.
"""

import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import (
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    MAX_CONTENT_LENGTH,
    ALLOWED_ORIGINS,
    RATE_LIMIT_PER_MINUTE,
)

# Import blueprints
from .api import analysis_bp, professional_bp, auth_bp, system_bp

# Configure logging (following rule 19)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH  # Limit upload file size

# Configure CORS with restrictions (security baseline rule 01)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"],
        }
    },
)

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

# Apply rate limiting to specific blueprints
limiter.limit("10 per minute")(analysis_bp)
limiter.limit("20 per minute")(professional_bp)
limiter.limit("5 per minute")(auth_bp)

logger.info("🚀 Flask app initialized with blueprints")


@app.route("/")
def index():
    """Serve main frontend page."""
    return send_from_directory("../frontend", "index.html")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return {"success": False, "error": "Endpoint not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return {"success": False, "error": "Internal server error"}, 500


def run_server():
    """Run Flask development server."""
    logger.info(f"🌐 Starting server on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"🔧 Debug mode: {FLASK_DEBUG}")

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


if __name__ == "__main__":
    run_server()
