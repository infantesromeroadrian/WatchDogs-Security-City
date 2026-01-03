"""
Report Generation
Single Responsibility: Format analysis results into human-readable reports
Max: 200 lines
"""

import logging
from typing import Dict, Any

from ...config import METRICS_ENABLED
from ...utils.metrics_utils import get_agent_metrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates human-readable text reports from agent results"""

    @staticmethod
    def format_text_report(
        vision: Dict[str, Any],
        ocr: Dict[str, Any],
        detection: Dict[str, Any],
        geolocation: Dict[str, Any] = None,
    ) -> str:
        """
        Format combined results into readable text report.

        Args:
            vision: Vision agent result
            ocr: OCR agent result
            detection: Detection agent result
            geolocation: Geolocation agent result (optional)

        Returns:
            Formatted text report string
        """
        report_lines = [
            "=" * 80,
            "REPORTE DE ANÁLISIS DE IMAGEN - SISTEMA DE AGENTES OSINT",
            "=" * 80,
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📸 1. ANÁLISIS VISUAL GENERAL",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]

        # Vision section
        report_lines.extend(ReportGenerator._format_vision_section(vision))

        # OCR section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "📝 2. EXTRACCIÓN DE TEXTO (OCR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_ocr_section(ocr))

        # Detection section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🎯 3. DETECCIÓN DE OBJETOS Y PERSONAS",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_detection_section(detection))

        # Geolocation section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🌍 4. ANÁLISIS DE GEOLOCALIZACIÓN",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_geolocation_section(geolocation))

        # Metrics section
        if METRICS_ENABLED:
            report_lines.extend(ReportGenerator._format_metrics_section())

        report_lines.extend(["", "=" * 80, "FIN DEL REPORTE", "=" * 80])

        return "\n".join(report_lines)

    @staticmethod
    def _format_vision_section(vision: Dict[str, Any]) -> list[str]:
        """Format vision analysis section"""
        if vision.get("status") == "success":
            return [vision.get("analysis", "No analysis available")]
        else:
            return [f"⚠️ Error: {vision.get('error', 'Vision analysis failed')}"]

    @staticmethod
    def _format_ocr_section(ocr: Dict[str, Any]) -> list[str]:
        """Format OCR extraction section"""
        if ocr.get("status") == "success":
            return [ocr.get("analysis", "No text detected")]
        else:
            return [f"⚠️ Error: {ocr.get('error', 'OCR extraction failed')}"]

    @staticmethod
    def _format_detection_section(detection: Dict[str, Any]) -> list[str]:
        """Format detection analysis section"""
        if detection.get("status") == "success":
            return [detection.get("analysis", "No detections available")]
        elif detection.get("status") == "skipped":
            return ["⏭️ Detection Agent fue omitido"]
        else:
            return [f"⚠️ Error: {detection.get('error', 'Detection analysis failed')}"]

    @staticmethod
    def _format_geolocation_section(geolocation: Dict[str, Any] = None) -> list[str]:
        """Format geolocation analysis section"""
        lines = []

        if geolocation and geolocation.get("status") == "success":
            lines.append(
                geolocation.get("analysis", "No geolocation analysis available")
            )

            # Add coordinates if available
            coords = geolocation.get("coordinates")
            if coords:
                lines.append(
                    f"\n📍 Coordenadas: {coords.get('lat')}, {coords.get('lon')}"
                )

            # Add map link if available
            map_url = geolocation.get("map_url")
            if map_url:
                lines.append(f"🗺️ Mapa interactivo generado: {map_url}")
        elif geolocation and geolocation.get("status") == "skipped":
            lines.append("⏭️ Geolocation Agent fue omitido")
        elif geolocation:
            lines.append(
                f"⚠️ Error: {geolocation.get('error', 'Geolocation analysis failed')}"
            )
        else:
            lines.append("⏭️ Geolocation Agent no ejecutado")

        return lines

    @staticmethod
    def _format_metrics_section() -> list[str]:
        """Format performance metrics section"""
        metrics = get_agent_metrics()
        lines = [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📊 MÉTRICAS DE RENDIMIENTO",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        for agent_name, stats in metrics.items():
            if stats["total_calls"] > 0:
                lines.append(
                    f"{agent_name.upper()}: "
                    f"Llamadas: {stats['total_calls']}, "
                    f"Éxito: {stats['success_count']}, "
                    f"Latencia promedio: {stats.get('avg_latency_ms', 0):.2f}ms"
                )
        return lines
