"""
Professional PDF Report Generation Service
Creates forensic-grade reports without external APIs
"""

import logging
import io
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image as RLImage,
        PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReportService:
    """Generate professional PDF reports"""

    def __init__(self):
        if not REPORT_AVAILABLE:
            logger.warning(
                "⚠️ Report libraries not available. Install: pip install reportlab matplotlib"
            )

        self.styles = getSampleStyleSheet() if REPORT_AVAILABLE else None

        if REPORT_AVAILABLE:
            # Custom styles
            self.styles.add(
                ParagraphStyle(
                    name="CustomTitle",
                    parent=self.styles["Heading1"],
                    fontSize=24,
                    textColor=colors.HexColor("#1a1a2e"),
                    spaceAfter=30,
                    alignment=TA_CENTER,
                )
            )

            self.styles.add(
                ParagraphStyle(
                    name="SectionHeader",
                    parent=self.styles["Heading2"],
                    fontSize=14,
                    textColor=colors.HexColor("#00d2ff"),
                    spaceAfter=12,
                    spaceBefore=12,
                )
            )

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

        # Container for elements
        elements = []

        # Header
        elements.extend(self._create_header(evidence_id))

        # Executive Summary
        elements.extend(self._create_executive_summary(analysis_results))

        # Technical Analysis
        elements.extend(self._create_technical_analysis(analysis_results))

        # Geolocation Section
        if (
            "geolocation" in analysis_results
            or "combined_geolocation" in analysis_results
        ):
            elements.extend(self._create_geolocation_section(analysis_results))

        # Metadata Section
        if metadata:
            elements.extend(self._create_metadata_section(metadata))

        # Forensic Evidence
        if metadata and "forensics" in metadata:
            elements.extend(
                self._create_forensic_section(metadata["forensics"], evidence_id)
            )

        # Footer
        elements.extend(self._create_footer())

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"📄 PDF report generated: {len(pdf_bytes)} bytes")

        return pdf_bytes

    def _create_header(self, evidence_id: Optional[str]) -> List:
        """Create report header"""
        elements = []

        # Title
        title = Paragraph(
            "🎯 WatchDogs OSINT - Intelligence Report", self.styles["CustomTitle"]
        )
        elements.append(title)

        # Metadata table
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        data = [
            ["Report Generated:", timestamp],
            ["System:", "WatchDogs Multi-Agent Analysis Platform"],
        ]

        if evidence_id:
            data.append(["Evidence ID:", evidence_id])

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_executive_summary(self, results: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))

        # Extract key findings
        summary_text = self._extract_summary(results)

        para = Paragraph(summary_text, self.styles["BodyText"])
        elements.append(para)
        elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _create_technical_analysis(self, results: Dict[str, Any]) -> List:
        """Create technical analysis section"""
        elements = []

        elements.append(Paragraph("Technical Analysis", self.styles["SectionHeader"]))

        # Vision Analysis
        if "vision" in results:
            elements.append(
                Paragraph("<b>Visual Analysis:</b>", self.styles["Heading3"])
            )
            vision_text = results["vision"].get("analysis", "No data")
            elements.append(Paragraph(vision_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # OCR Analysis
        if "ocr" in results:
            elements.append(
                Paragraph("<b>Text Recognition (OCR):</b>", self.styles["Heading3"])
            )
            ocr_text = results["ocr"].get("analysis", "No text detected")
            elements.append(Paragraph(ocr_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Detection Analysis
        if "detection" in results:
            elements.append(
                Paragraph("<b>Object Detection:</b>", self.styles["Heading3"])
            )
            detection_text = results["detection"].get("analysis", "No objects detected")
            elements.append(Paragraph(detection_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_geolocation_section(self, results: Dict[str, Any]) -> List:
        """Create geolocation section"""
        elements = []

        elements.append(
            Paragraph("Geolocation Intelligence", self.styles["SectionHeader"])
        )

        geo_data = results.get("combined_geolocation") or results.get("geolocation", {})

        if geo_data:
            # Location summary
            location = geo_data.get("location", {})
            city = location.get("city", "Unknown")
            country = location.get("country", "Unknown")
            confidence = geo_data.get("confidence", "UNKNOWN")

            summary = f"<b>Probable Location:</b> {city}, {country}<br/>"
            summary += f"<b>Confidence Level:</b> {confidence}<br/>"

            elements.append(Paragraph(summary, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

            # Clues
            clues = geo_data.get("clues", [])
            if clues:
                elements.append(
                    Paragraph("<b>Geographic Clues:</b>", self.styles["Heading4"])
                )
                for i, clue in enumerate(clues, 1):
                    elements.append(Paragraph(f"{i}. {clue}", self.styles["BodyText"]))
                elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_metadata_section(self, metadata: Dict[str, Any]) -> List:
        """Create metadata section"""
        elements = []

        elements.append(Paragraph("Technical Metadata", self.styles["SectionHeader"]))

        # Technical specs
        if "technical" in metadata:
            tech = metadata["technical"]
            data = [
                ["Format:", tech.get("format", "N/A")],
                ["Dimensions:", tech.get("size", "N/A")],
                ["Color Mode:", tech.get("mode", "N/A")],
                [
                    "File Size:",
                    f"{metadata.get('forensics', {}).get('size_bytes', 0)} bytes",
                ],
            ]

            table = Table(data, colWidths=[1.5 * inch, 4 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )

            elements.append(table)
            elements.append(Spacer(1, 0.2 * inch))

        # GPS data
        if "gps" in metadata and metadata["gps"]:
            elements.append(
                Paragraph("<b>GPS Coordinates:</b>", self.styles["Heading4"])
            )
            gps = metadata["gps"]
            gps_text = f"Latitude: {gps.get('latitude', 'N/A')}<br/>"
            gps_text += f"Longitude: {gps.get('longitude', 'N/A')}<br/>"
            if "altitude" in gps:
                gps_text += f"Altitude: {gps['altitude']} m"

            elements.append(Paragraph(gps_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_forensic_section(
        self, forensics: Dict[str, Any], evidence_id: Optional[str]
    ) -> List:
        """Create forensic evidence section"""
        elements = []

        elements.append(Paragraph("Forensic Evidence", self.styles["SectionHeader"]))

        data = [
            ["SHA-256 Hash:", forensics.get("sha256", "N/A")],
            ["MD5 Hash:", forensics.get("md5", "N/A")],
            ["File Size:", f"{forensics.get('size_bytes', 0)} bytes"],
            ["Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")],
        ]

        if evidence_id:
            data.insert(0, ["Evidence ID:", evidence_id])

        table = Table(data, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ffe6e6")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#cc0000")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("FONTNAME", (1, 0), (1, -1), "Courier"),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        # Chain of custody note
        custody_note = "<b>Chain of Custody:</b> This evidence has been processed by WatchDogs OSINT system. "
        custody_note += (
            "The SHA-256 hash can be used to verify integrity of the original data."
        )
        elements.append(Paragraph(custody_note, self.styles["BodyText"]))

        return elements

    def _create_footer(self) -> List:
        """Create report footer"""
        elements = []

        elements.append(Spacer(1, 0.5 * inch))
        elements.append(PageBreak())

        # Disclaimer
        disclaimer_title = Paragraph("Legal Disclaimer", self.styles["Heading3"])
        elements.append(disclaimer_title)

        disclaimer_text = """
        This report is generated by an AI-powered OSINT analysis system. The findings are based on 
        automated analysis and should be verified by human analysts. This report is intended for 
        lawful intelligence purposes only. Unauthorized use, distribution, or reproduction is prohibited.
        The system does not guarantee 100% accuracy and results should be cross-referenced with 
        additional sources.
        """

        elements.append(Paragraph(disclaimer_text, self.styles["BodyText"]))

        # Footer text
        footer_text = f"Generated by WatchDogs OSINT Platform v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        footer = Paragraph(footer_text, self.styles["Normal"])
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(footer)

        return elements

    def _extract_summary(self, results: Dict[str, Any]) -> str:
        """Extract executive summary from results"""
        summary_parts = []

        # Vision summary
        if "vision" in results:
            vision = results["vision"].get("analysis", "")
            if vision:
                summary_parts.append(f"Visual Analysis: {vision[:200]}...")

        # OCR summary
        if "ocr" in results:
            ocr = results["ocr"].get("analysis", "")
            if ocr and ocr != "No text detected":
                summary_parts.append(f"Text Detected: {ocr[:150]}...")

        # Geolocation summary
        geo_data = results.get("combined_geolocation") or results.get("geolocation", {})
        if geo_data:
            location = geo_data.get("location", {})
            city = location.get("city", "Unknown")
            country = location.get("country", "Unknown")
            if city != "Unknown" or country != "Unknown":
                summary_parts.append(f"Probable Location: {city}, {country}")

        return (
            " ".join(summary_parts)
            if summary_parts
            else "Analysis complete. See detailed sections below."
        )


# Global instance
report_service = ReportService()
