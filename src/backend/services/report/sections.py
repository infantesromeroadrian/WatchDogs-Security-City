"""
PDF report section builders for CIA-Level OSINT Intelligence Reports.

Supports 7 agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging
from datetime import UTC, datetime
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# COLOR PALETTE FOR SECTIONS
# =============================================================================

COLORS = {
    "header_bg": colors.HexColor("#1a1a2e"),
    "section_bg": colors.HexColor("#f0f0f0"),
    "alert_bg": colors.HexColor("#ffe6e6"),
    "alert_text": colors.HexColor("#cc0000"),
    "success_bg": colors.HexColor("#e6ffe6"),
    "success_text": colors.HexColor("#006600"),
    "warning_bg": colors.HexColor("#fff3e6"),
    "warning_text": colors.HexColor("#cc6600"),
    "forensic_bg": colors.HexColor("#e6e6ff"),
    "forensic_text": colors.HexColor("#000066"),
    "face_bg": colors.HexColor("#ffe6f0"),
    "face_text": colors.HexColor("#660033"),
    "context_bg": colors.HexColor("#e6fff0"),
    "context_text": colors.HexColor("#006633"),
}


class ReportSectionBuilder:
    """Builds individual sections of PDF reports"""

    def __init__(self, styles):
        """
        Initialize section builder.

        Args:
            styles: ReportLab StyleSheet
        """
        self.styles = styles

    def create_header(self, evidence_id: str | None) -> list:
        """Create report header section"""
        elements = []

        # Title
        title = Paragraph("🎯 WatchDogs OSINT - Intelligence Report", self.styles["CustomTitle"])
        elements.append(title)

        # Metadata table
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

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

    def create_executive_summary(self, results: dict[str, Any]) -> list:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))

        # Extract key findings
        summary_text = self._extract_summary(results)

        para = Paragraph(summary_text, self.styles["BodyText"])
        elements.append(para)
        elements.append(Spacer(1, 0.2 * inch))

        return elements

    def create_technical_analysis(self, results: dict[str, Any]) -> list:
        """Create technical analysis section"""
        elements = []

        elements.append(Paragraph("Technical Analysis", self.styles["SectionHeader"]))

        # Vision Analysis
        if "vision" in results:
            elements.append(Paragraph("<b>Visual Analysis:</b>", self.styles["Heading3"]))
            vision_text = results["vision"].get("analysis", "No data")
            elements.append(Paragraph(vision_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # OCR Analysis
        if "ocr" in results:
            elements.append(Paragraph("<b>Text Recognition (OCR):</b>", self.styles["Heading3"]))
            ocr_text = results["ocr"].get("analysis", "No text detected")
            elements.append(Paragraph(ocr_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Detection Analysis
        if "detection" in results:
            elements.append(Paragraph("<b>Object Detection:</b>", self.styles["Heading3"]))
            detection_text = results["detection"].get("analysis", "No objects detected")
            elements.append(Paragraph(detection_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_geolocation_section(self, results: dict[str, Any]) -> list:
        """Create geolocation intelligence section"""
        elements = []

        elements.append(Paragraph("Geolocation Intelligence", self.styles["SectionHeader"]))

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
                elements.append(Paragraph("<b>Geographic Clues:</b>", self.styles["Heading4"]))
                for i, clue in enumerate(clues, 1):
                    elements.append(Paragraph(f"{i}. {clue}", self.styles["BodyText"]))
                elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_metadata_section(self, metadata: dict[str, Any]) -> list:
        """Create technical metadata section"""
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
        if metadata.get("gps"):
            elements.append(Paragraph("<b>GPS Coordinates:</b>", self.styles["Heading4"]))
            gps = metadata["gps"]
            gps_text = f"Latitude: {gps.get('latitude', 'N/A')}<br/>"
            gps_text += f"Longitude: {gps.get('longitude', 'N/A')}<br/>"
            if "altitude" in gps:
                gps_text += f"Altitude: {gps['altitude']} m"

            elements.append(Paragraph(gps_text, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_forensic_section(self, forensics: dict[str, Any], evidence_id: str | None) -> list:
        """Create forensic evidence section"""
        elements = []

        elements.append(Paragraph("Forensic Evidence", self.styles["SectionHeader"]))

        data = [
            ["SHA-256 Hash:", forensics.get("sha256", "N/A")],
            ["MD5 Hash:", forensics.get("md5", "N/A")],
            ["File Size:", f"{forensics.get('size_bytes', 0)} bytes"],
            ["Timestamp:", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")],
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
        custody_note = (
            "<b>Chain of Custody:</b> This evidence has been processed by WatchDogs OSINT system. "
        )
        custody_note += "The SHA-256 hash can be used to verify integrity of the original data."
        elements.append(Paragraph(custody_note, self.styles["BodyText"]))

        return elements

    # =========================================================================
    # CIA-LEVEL SECTIONS: Face Analysis, Forensic Analysis, Context Intel
    # =========================================================================

    def create_face_analysis_section(self, results: dict[str, Any]) -> list:
        """Create face/person analysis section for CIA-level reports."""
        elements = []

        face_data = results.get("face_analysis", {})
        if not face_data or face_data.get("status") == "skipped":
            return elements

        elements.append(Paragraph("Person Identification Analysis", self.styles["SectionHeader"]))

        # Detection summary
        detection = face_data.get("detection_summary", {})
        total = detection.get("total_persons", face_data.get("person_count", 0))
        faces_visible = detection.get("faces_visible", 0)
        quality = detection.get("identification_quality", "unknown")

        summary_data = [
            ["Persons Detected:", str(total)],
            ["Faces Visible:", str(faces_visible)],
            ["ID Quality:", quality.upper()],
        ]

        table = Table(summary_data, colWidths=[2 * inch, 3.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), COLORS["face_bg"]),
                    ("TEXTCOLOR", (0, 0), (0, -1), COLORS["face_text"]),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.15 * inch))

        # Per-person details
        persons = face_data.get("persons", [])
        for person in persons[:5]:  # Limit to first 5 persons
            person_id = person.get("person_id", "?")
            elements.append(Paragraph(f"<b>Person #{person_id}</b>", self.styles["Heading4"]))

            details = []

            # Demographics
            demo = person.get("demographics", {})
            if demo:
                age = demo.get("age_range", "N/A")
                gender = demo.get("gender", "N/A")
                details.append(f"Demographics: {age}, {gender}")

            # Distinctive marks
            marks = person.get("distinctive_marks", {})
            if marks:
                mark_items = []
                if marks.get("scars"):
                    mark_items.append(f"Scars: {', '.join(marks['scars'])}")
                if marks.get("tattoos"):
                    mark_items.append(f"Tattoos: {', '.join(marks['tattoos'])}")
                if marks.get("piercings"):
                    mark_items.append(f"Piercings: {', '.join(marks['piercings'])}")
                if mark_items:
                    details.append("Marks: " + "; ".join(mark_items))

            # Clothing
            clothing = person.get("clothing", {})
            if clothing:
                upper = clothing.get("upper", "")
                lower = clothing.get("lower", "")
                if upper or lower:
                    details.append(f"Clothing: {upper}, {lower}".strip(", "))

            # Accessories
            accessories = person.get("accessories", [])
            if accessories:
                details.append(f"Accessories: {', '.join(accessories[:5])}")

            for detail in details:
                elements.append(Paragraph(f"• {detail}", self.styles["BodyText"]))

            elements.append(Spacer(1, 0.1 * inch))

        # Most distinctive features
        distinctive = face_data.get("most_distinctive_features", [])
        if distinctive:
            elements.append(Paragraph("<b>Most Distinctive Features:</b>", self.styles["Heading4"]))
            for i, feature in enumerate(distinctive[:5], 1):
                elements.append(Paragraph(f"{i}. {feature}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_forensic_analysis_section(self, results: dict[str, Any]) -> list:
        """Create image forensic analysis section for CIA-level reports."""
        elements = []

        forensic_data = results.get("forensic_analysis", {})
        if not forensic_data or forensic_data.get("status") == "skipped":
            return elements

        elements.append(Paragraph("Image Forensic Analysis", self.styles["SectionHeader"]))

        # Verdict summary
        verdict = forensic_data.get("verdict", {})
        classification = verdict.get("classification", "indeterminada")
        confidence = verdict.get("confidence", "media")
        integrity_score = forensic_data.get("integrity_score")

        # Determine colors based on verdict
        if classification.lower() in ["auténtica", "probablemente auténtica", "authentic"]:
            bg_color = COLORS["success_bg"]
            txt_color = COLORS["success_text"]
            verdict_icon = "✓"
        elif classification.lower() in [
            "manipulada",
            "probablemente manipulada",
            "generada por ia",
        ]:
            bg_color = COLORS["alert_bg"]
            txt_color = COLORS["alert_text"]
            verdict_icon = "⚠"
        else:
            bg_color = COLORS["warning_bg"]
            txt_color = COLORS["warning_text"]
            verdict_icon = "?"

        verdict_data = [
            ["Verdict:", f"{verdict_icon} {classification.upper()}"],
            ["Confidence:", confidence.upper()],
        ]
        if integrity_score is not None:
            verdict_data.append(["Integrity Score:", f"{integrity_score}/100"])

        table = Table(verdict_data, colWidths=[2 * inch, 3.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), bg_color),
                    ("TEXTCOLOR", (0, 0), (0, -1), txt_color),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.15 * inch))

        # Justification
        justification = verdict.get("justification")
        if justification:
            elements.append(Paragraph(f"<i>{justification}</i>", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Anomalies detected
        anomalies = forensic_data.get("anomalies", {})
        anomaly_items = []

        for _category, items in anomalies.items():
            if isinstance(items, list) and items:
                anomaly_items.extend(items)
            elif isinstance(items, dict):
                # Handle manipulation_specific nested dict
                for sub_key, sub_val in items.items():
                    if isinstance(sub_val, dict) and sub_val.get("detected"):
                        details = sub_val.get("details", sub_key)
                        anomaly_items.append(f"{sub_key}: {details}")

        if anomaly_items:
            elements.append(Paragraph("<b>Anomalies Detected:</b>", self.styles["Heading4"]))
            for anomaly in anomaly_items[:8]:
                elements.append(Paragraph(f"• {anomaly}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Suspicious regions
        suspicious = forensic_data.get("suspicious_regions", [])
        if suspicious:
            elements.append(Paragraph("<b>Suspicious Regions:</b>", self.styles["Heading4"]))
            for region in suspicious[:5]:
                if isinstance(region, dict):
                    loc = region.get("location", "unknown")
                    desc = region.get("description", "")
                    elements.append(Paragraph(f"• {loc}: {desc}", self.styles["BodyText"]))
                else:
                    elements.append(Paragraph(f"• {region}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Manipulation hypothesis
        hypothesis = forensic_data.get("manipulation_hypothesis")
        if hypothesis:
            elements.append(Paragraph("<b>Manipulation Hypothesis:</b>", self.styles["Heading4"]))
            elements.append(Paragraph(hypothesis, self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Recommendations
        recommendations = forensic_data.get("recommendations", [])
        if recommendations:
            elements.append(
                Paragraph("<b>Verification Recommendations:</b>", self.styles["Heading4"])
            )
            for i, rec in enumerate(recommendations[:5], 1):
                elements.append(Paragraph(f"{i}. {rec}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_context_intel_section(self, results: dict[str, Any]) -> list:
        """Create context intelligence section for CIA-level reports."""
        elements = []

        context_data = results.get("context_intel", {})
        if not context_data or context_data.get("status") == "skipped":
            return elements

        elements.append(Paragraph("Contextual Intelligence Analysis", self.styles["SectionHeader"]))

        # Executive summary
        exec_summary = context_data.get("executive_summary")
        if exec_summary:
            elements.append(Paragraph(f"<i>{exec_summary}</i>", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.15 * inch))

        # Temporal analysis
        temporal = context_data.get("temporal_analysis", {})
        if temporal:
            elements.append(Paragraph("<b>Temporal Analysis:</b>", self.styles["Heading4"]))

            temporal_items = []
            time_of_day = temporal.get("time_of_day", {})
            if time_of_day.get("value"):
                conf = time_of_day.get("confidence", "")
                temporal_items.append(f"Time of Day: {time_of_day['value']} (confidence: {conf})")

            day_type = temporal.get("day_type", {})
            if day_type.get("value"):
                temporal_items.append(f"Day Type: {day_type['value']}")

            season = temporal.get("season", {})
            if season.get("value"):
                temporal_items.append(f"Season: {season['value']}")

            era = temporal.get("era", {})
            if era.get("value"):
                temporal_items.append(f"Era/Decade: {era['value']}")

            specific_date = temporal.get("specific_date", {})
            if specific_date.get("value"):
                temporal_items.append(f"Specific Date: {specific_date['value']}")

            for item in temporal_items:
                elements.append(Paragraph(f"• {item}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Sociocultural analysis
        sociocultural = context_data.get("sociocultural_analysis", {})
        if sociocultural:
            elements.append(Paragraph("<b>Sociocultural Context:</b>", self.styles["Heading4"]))

            socio_level = sociocultural.get("socioeconomic_level")
            if socio_level:
                elements.append(
                    Paragraph(f"• Socioeconomic Level: {socio_level}", self.styles["BodyText"])
                )

            cultural = sociocultural.get("cultural_context")
            if cultural:
                elements.append(
                    Paragraph(f"• Cultural Context: {cultural}", self.styles["BodyText"])
                )

            political = sociocultural.get("political_situation")
            if political:
                elements.append(
                    Paragraph(f"• Political Situation: {political}", self.styles["BodyText"])
                )

            # Indicators
            indicators = sociocultural.get("socioeconomic_indicators", [])
            if indicators:
                elements.append(
                    Paragraph(f"• Indicators: {', '.join(indicators[:5])}", self.styles["BodyText"])
                )

            elements.append(Spacer(1, 0.1 * inch))

        # Event classification
        event = context_data.get("event_classification", {})
        if event and event.get("event_type"):
            elements.append(Paragraph("<b>Event Classification:</b>", self.styles["Heading4"]))

            event_type = event.get("event_type", "N/A")
            subtype = event.get("event_subtype", "")
            purpose = event.get("primary_purpose", "")

            elements.append(Paragraph(f"• Type: {event_type}", self.styles["BodyText"]))
            if subtype:
                elements.append(Paragraph(f"• Subtype: {subtype}", self.styles["BodyText"]))
            if purpose:
                elements.append(Paragraph(f"• Primary Purpose: {purpose}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        # Key inferences with confidence
        inferences = context_data.get("key_inferences", [])
        if inferences:
            elements.append(
                Paragraph("<b>Key Intelligence Inferences:</b>", self.styles["Heading4"])
            )

            # Build table for inferences with confidence
            inference_data = [["#", "Inference", "Confidence"]]
            for inf in inferences[:7]:
                order = inf.get("order", "")
                text = inf.get("inference", "")[:80]  # Truncate long text
                conf = inf.get("confidence_percent", "?")
                inference_data.append([str(order), text, f"{conf}%"])

            if len(inference_data) > 1:
                table = Table(inference_data, colWidths=[0.4 * inch, 4 * inch, 1 * inch])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), COLORS["context_bg"]),
                            ("TEXTCOLOR", (0, 0), (-1, 0), COLORS["context_text"]),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                            ("ALIGN", (0, 0), (0, -1), "CENTER"),
                            ("ALIGN", (2, 0), (2, -1), "CENTER"),
                        ]
                    )
                )
                elements.append(table)
                elements.append(Spacer(1, 0.1 * inch))

        # Anomalies
        anomalies = context_data.get("anomalies", [])
        if anomalies:
            elements.append(
                Paragraph("<b>Anomalies/Unusual Elements:</b>", self.styles["Heading4"])
            )
            for anomaly in anomalies[:5]:
                elements.append(Paragraph(f"• {anomaly}", self.styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def create_footer(self) -> list:
        """Create report footer section"""
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
        <br/><br/>
        <b>FACE ANALYSIS DISCLAIMER:</b> Person identification data is provided for intelligence purposes
        only. This system does not perform biometric identification and should not be used as sole
        evidence for identification. All findings require human verification.
        <br/><br/>
        <b>FORENSIC ANALYSIS DISCLAIMER:</b> Image authenticity assessments are probabilistic
        and should be verified by certified forensic analysts. The absence of detected manipulation
        does not guarantee authenticity.
        """

        elements.append(Paragraph(disclaimer_text, self.styles["BodyText"]))

        # Footer text
        footer_text = f"Generated by WatchDogs OSINT Platform v2.0 (CIA-Level) | {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        footer = Paragraph(footer_text, self.styles["Normal"])
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(footer)

        return elements

    def _extract_summary(self, results: dict[str, Any]) -> str:
        """Extract executive summary from all 7 agents."""
        summary_parts = []

        # Vision summary
        if "vision" in results:
            vision = results["vision"].get("analysis", "")
            if vision:
                summary_parts.append(f"<b>Visual Analysis:</b> {vision[:150]}...")

        # OCR summary
        if "ocr" in results:
            ocr = results["ocr"].get("analysis", "")
            if ocr and ocr != "No text detected":
                summary_parts.append(f"<b>Text Detected:</b> {ocr[:100]}...")

        # Geolocation summary
        geo_data = results.get("combined_geolocation") or results.get("geolocation", {})
        if geo_data:
            location = geo_data.get("location", {})
            city = location.get("city", "Unknown")
            country = location.get("country", "Unknown")
            if city != "Unknown" or country != "Unknown":
                summary_parts.append(f"<b>Probable Location:</b> {city}, {country}")

        # Face Analysis summary (CIA-level)
        face_data = results.get("face_analysis", {})
        if face_data and face_data.get("status") == "success":
            person_count = face_data.get("person_count", 0)
            if person_count > 0:
                summary_parts.append(f"<b>Persons Detected:</b> {person_count}")

        # Forensic Analysis summary (CIA-level)
        forensic_data = results.get("forensic_analysis", {})
        if forensic_data and forensic_data.get("status") == "success":
            verdict = forensic_data.get("verdict", {})
            classification = verdict.get("classification", "")
            integrity = forensic_data.get("integrity_score")
            if classification:
                verdict_text = f"<b>Image Authenticity:</b> {classification.upper()}"
                if integrity is not None:
                    verdict_text += f" (Integrity: {integrity}/100)"
                summary_parts.append(verdict_text)

        # Context Intel summary (CIA-level)
        context_data = results.get("context_intel", {})
        if context_data and context_data.get("status") == "success":
            exec_summary = context_data.get("executive_summary")
            if exec_summary:
                summary_parts.append(f"<b>Context:</b> {exec_summary[:150]}...")

        return (
            "<br/>".join(summary_parts)
            if summary_parts
            else "Analysis complete. See detailed sections below."
        )
