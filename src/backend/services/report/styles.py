"""
ReportLab styles configuration for PDF reports
"""

import logging

try:
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_report_styles():
    """
    Get configured styles for PDF reports.

    Returns:
        StyleSheet with custom styles or None if reportlab unavailable
    """
    if not REPORT_AVAILABLE:
        return None

    styles = getSampleStyleSheet()

    # Custom title style
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
    )

    # Custom section header style
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#00d2ff"),
            spaceAfter=12,
            spaceBefore=12,
        )
    )

    return styles
