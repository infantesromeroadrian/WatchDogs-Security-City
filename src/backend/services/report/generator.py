"""
Main PDF report generator orchestrator
"""

import io
import logging
from typing import Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate

    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

from .sections import ReportSectionBuilder
from .styles import get_report_styles

logger = logging.getLogger(__name__)


class ReportService:
    """Generate professional PDF reports"""

    def __init__(self):
        if not REPORT_AVAILABLE:
            logger.warning(
                "⚠️ Report libraries not available. Install: pip install reportlab matplotlib"
            )
            self.styles = None
            self.section_builder = None
        else:
            self.styles = get_report_styles()
            self.section_builder = ReportSectionBuilder(self.styles)

    def generate_analysis_report(
        self,
        analysis_results: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        evidence_id: str | None = None,
    ) -> bytes:
        """
        Generate comprehensive PDF report.

        Args:
            analysis_results: Results from multi-agent analysis
            metadata: Optional metadata from metadata_service
            evidence_id: Optional evidence ID for forensics

        Returns:
            PDF bytes

        Raises:
            RuntimeError: If report libraries not available
        """
        if not REPORT_AVAILABLE:
            raise RuntimeError("Report libraries not available")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build all sections
        elements = []
        elements.extend(self.section_builder.create_header(evidence_id))
        elements.extend(self.section_builder.create_executive_summary(analysis_results))
        elements.extend(self.section_builder.create_technical_analysis(analysis_results))

        # Original sections
        if "geolocation" in analysis_results or "combined_geolocation" in analysis_results:
            elements.extend(self.section_builder.create_geolocation_section(analysis_results))

        # =================================================================
        # CIA-Level Agent Sections
        # =================================================================

        # Face Analysis Section (Person Identification)
        if "face_analysis" in analysis_results:
            elements.extend(self.section_builder.create_face_analysis_section(analysis_results))

        # Forensic Analysis Section (Image Authenticity)
        if "forensic_analysis" in analysis_results:
            elements.extend(self.section_builder.create_forensic_analysis_section(analysis_results))

        # Context Intelligence Section (Temporal/Cultural Analysis)
        if "context_intel" in analysis_results:
            elements.extend(self.section_builder.create_context_intel_section(analysis_results))

        # =================================================================
        # Metadata and Forensic Evidence (file hashes, etc.)
        # =================================================================
        if metadata:
            elements.extend(self.section_builder.create_metadata_section(metadata))

        if metadata and "forensics" in metadata:
            elements.extend(
                self.section_builder.create_forensic_section(metadata["forensics"], evidence_id)
            )

        elements.extend(self.section_builder.create_footer())

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info("📄 PDF report generated: %s bytes", len(pdf_bytes))

        return pdf_bytes


# Global instance
report_service = ReportService()
