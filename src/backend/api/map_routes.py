"""
Map routes: Mapbox token endpoint.
"""

import logging

from flask import Blueprint, jsonify

from ..config import MAPBOX_ACCESS_TOKEN

logger = logging.getLogger(__name__)

# Blueprint
map_bp = Blueprint("map", __name__)


@map_bp.route("/mapbox-token", methods=["GET"])
def get_mapbox_token():
    """Serve Mapbox access token to the frontend.

    Rate-limited to 5/min at the blueprint level (configured in app.py).
    """
    if not MAPBOX_ACCESS_TOKEN:
        return jsonify({"success": False, "error": "Map service not configured"}), 503

    return jsonify({"success": True, "token": MAPBOX_ACCESS_TOKEN}), 200
