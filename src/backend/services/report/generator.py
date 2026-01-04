"""
Main PDF report generator orchestrator
"""

import logging
import io
from typing import Dict, Any, Optional

try:
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import letter
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

from .styles import get_report_styles
from .sections import ReportSectionBuilder

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
        analysis_results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        evidence_id: Optional[str] = None,
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
        elements.extend(
            self.section_builder.create_technical_analysis(analysis_results)
        )

        # Optional sections
        if (
            "geolocation" in analysis_results
            or "combined_geolocation" in analysis_results
        ):
            elements.extend(
                self.section_builder.create_geolocation_section(analysis_results)
            )

        if metadata:
            elements.extend(self.section_builder.create_metadata_section(metadata))

        if metadata and "forensics" in metadata:
            elements.extend(
                self.section_builder.create_forensic_section(
                    metadata["forensics"], evidence_id
                )
            )

        elements.extend(self.section_builder.create_footer())

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"📄 PDF report generated: {len(pdf_bytes)} bytes")

        return pdf_bytes


# Global instance
report_service = ReportService()
