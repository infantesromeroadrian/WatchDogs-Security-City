"""
Professional OSINT routes: metadata, PDF reports, evidence packages
"""

import logging
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from ..services.metadata import metadata_service
from ..services.report import report_service

logger = logging.getLogger(__name__)

# Blueprint
professional_bp = Blueprint("professional", __name__)


def validate_base64_size(
    base64_string: str, max_mb: int = 10
) -> tuple[bool, str | None]:
    """Validate base64 size"""
    max_bytes = max_mb * 1024 * 1024
    if len(base64_string) > max_bytes:
        size_mb = len(base64_string) / (1024 * 1024)
        return False, f"Frame too large ({size_mb:.1f}MB). Max allowed: {max_mb}MB"
    return True, None


@professional_bp.route("/extract-metadata", methods=["POST"])
def extract_metadata():
    """
    Extract comprehensive metadata from image.

    Expected JSON:
    {
        "frame": "base64_encoded_image"
    }

    Returns: Metadata including EXIF, GPS, forensics
    """
    try:
        data = request.get_json()

        if not data or "frame" not in data:
            return jsonify({"success": False, "error": "No frame provided"}), 400

        frame_base64 = data["frame"]

        # Validate size
        is_valid, error_msg = validate_base64_size(frame_base64)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400

        logger.info("📊 Extracting metadata...")

        # Extract metadata
        metadata = metadata_service.extract_image_metadata(frame_base64)

        logger.info("✅ Metadata extraction complete")

        return jsonify({"success": True, "metadata": metadata}), 200

    except Exception as e:
        logger.error(f"❌ Metadata extraction error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@professional_bp.route("/generate-pdf-report", methods=["POST"])
def generate_pdf_report():
    """
    Generate professional PDF report.

    Expected JSON:
    {
        "analysis_results": {...},
        "metadata": {...} (optional),
        "evidence_id": "..." (optional)
    }

    Returns: PDF file
    """
    try:
        data = request.get_json()

        if not data or "analysis_results" not in data:
            return jsonify(
                {"success": False, "error": "No analysis results provided"}
            ), 400

        analysis_results = data["analysis_results"]
        metadata = data.get("metadata")
        evidence_id = data.get("evidence_id")

        logger.info("📄 Generating PDF report...")

        # Generate PDF
        pdf_bytes = report_service.generate_analysis_report(
            analysis_results=analysis_results,
            metadata=metadata,
            evidence_id=evidence_id,
        )

        # Create file-like object
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"watchdogs_report_{timestamp}.pdf"

        logger.info(f"✅ PDF report generated: {filename}")

        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        logger.error(f"❌ PDF generation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@professional_bp.route("/generate-evidence-package", methods=["POST"])
def generate_evidence_package():
    """
    Generate forensic evidence package with chain of custody.

    Expected JSON:
    {
        "frame": "base64_encoded_image",
        "analysis_results": {...}
    }

    Returns: Complete evidence package
    """
    try:
        data = request.get_json()

        if not data or "frame" not in data or "analysis_results" not in data:
            return jsonify(
                {"success": False, "error": "Missing frame or analysis results"}
            ), 400

        frame_base64 = data["frame"]
        analysis_results = data["analysis_results"]

        # Validate size
        is_valid, error_msg = validate_base64_size(frame_base64)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400

        logger.info("📦 Generating evidence package...")

        # Generate evidence package
        package = metadata_service.generate_evidence_package(
            frame_base64=frame_base64, analysis_results=analysis_results
        )

        logger.info(f"✅ Evidence package generated: {package['evidence_id']}")

        return jsonify({"success": True, "evidence_package": package}), 200

    except Exception as e:
        logger.error(f"❌ Evidence package error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
