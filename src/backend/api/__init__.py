"""
API Blueprints module
"""

from .analysis_routes import analysis_bp
from .auth_routes import auth_bp
from .map_routes import map_bp
from .professional_routes import professional_bp
from .system_routes import system_bp

__all__ = ["analysis_bp", "auth_bp", "map_bp", "professional_bp", "system_bp"]
