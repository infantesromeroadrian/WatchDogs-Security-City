"""
Report Generation
Single Responsibility: Format analysis results into human-readable reports
Max: 350 lines

CIA-Level OSINT Intelligence Brief with 7 agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging
from typing import Any

from ...config import METRICS_ENABLED
from ...utils.metrics_utils import get_agent_metrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates human-readable intelligence briefs from 7 agent results."""

    @staticmethod
    def format_text_report(
        vision: dict[str, Any],
        ocr: dict[str, Any],
        detection: dict[str, Any],
        geolocation: dict[str, Any] | None = None,
        face_analysis: dict[str, Any] | None = None,
        forensic_analysis: dict[str, Any] | None = None,
        context_intel: dict[str, Any] | None = None,
    ) -> str:
        """
        Format combined results into CIA-level intelligence brief.

        Args:
            vision: Vision agent result
            ocr: OCR agent result
            detection: Detection agent result
            geolocation: Geolocation agent result (optional)
            face_analysis: Face analysis agent result (optional)
            forensic_analysis: Forensic analysis agent result (optional)
            context_intel: Context intel agent result (optional)

        Returns:
            Formatted intelligence brief string
        """
        report_lines = [
            "=" * 80,
            "INTELLIGENCE BRIEF - SISTEMA OSINT CIA-LEVEL (7 AGENTES)",
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

        # Face Analysis section (NEW)
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "👤 5. IDENTIFICACIÓN DE PERSONAS (CIA-LEVEL)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_face_analysis_section(face_analysis))

        # Forensic Analysis section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🔬 6. ANÁLISIS FORENSE DE IMAGEN",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_forensic_section(forensic_analysis))

        # Context Intelligence section (NEW)
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🧠 7. INTELIGENCIA CONTEXTUAL (TEMPORAL/CULTURAL)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_context_intel_section(context_intel))

        # Metrics section
        if METRICS_ENABLED:
            report_lines.extend(ReportGenerator._format_metrics_section())

        report_lines.extend(["", "=" * 80, "FIN DEL INTELLIGENCE BRIEF", "=" * 80])

        return "\n".join(report_lines)

    @staticmethod
    def _format_vision_section(vision: dict[str, Any]) -> list[str]:
        """Format vision analysis section"""
        if vision.get("status") == "success":
            return [vision.get("analysis", "No analysis available")]
        return [f"⚠️ Error: {vision.get('error', 'Vision analysis failed')}"]

    @staticmethod
    def _format_ocr_section(ocr: dict[str, Any]) -> list[str]:
        """Format OCR extraction section"""
        if ocr.get("status") == "success":
            return [ocr.get("analysis", "No text detected")]
        return [f"⚠️ Error: {ocr.get('error', 'OCR extraction failed')}"]

    @staticmethod
    def _format_detection_section(detection: dict[str, Any]) -> list[str]:
        """Format detection analysis section"""
        if detection.get("status") == "success":
            return [detection.get("analysis", "No detections available")]
        if detection.get("status") == "skipped":
            return ["⏭️ Detection Agent fue omitido"]
        return [f"⚠️ Error: {detection.get('error', 'Detection analysis failed')}"]

    @staticmethod
    def _format_geolocation_section(geolocation: dict[str, Any] | None = None) -> list[str]:
        """Format geolocation analysis section."""
        lines: list[str] = []

        if geolocation and geolocation.get("status") == "success":
            lines.append(geolocation.get("analysis", "No geolocation analysis available"))

            # Add coordinates if available
            coords = geolocation.get("coordinates")
            if coords:
                lines.append(f"\n📍 Coordenadas: {coords.get('lat')}, {coords.get('lon')}")

            # Add map link if available
            map_url = geolocation.get("map_url")
            if map_url:
                lines.append(f"🗺️ Mapa interactivo generado: {map_url}")
        elif geolocation and geolocation.get("status") == "skipped":
            lines.append("⏭️ Geolocation Agent fue omitido")
        elif geolocation:
            lines.append(f"⚠️ Error: {geolocation.get('error', 'Geolocation analysis failed')}")
        else:
            lines.append("⏭️ Geolocation Agent no ejecutado")

        return lines

    @staticmethod
    def _format_face_analysis_section(face_analysis: dict[str, Any] | None = None) -> list[str]:
        """Format face analysis / person identification section."""
        lines: list[str] = []

        if face_analysis and face_analysis.get("status") == "success":
            lines.append(face_analysis.get("analysis", "No person analysis available"))

            # Add detection summary
            summary = face_analysis.get("detection_summary", {})
            if summary:
                lines.append("")
                lines.append(f"📊 Resumen: {summary.get('total_persons', 0)} personas detectadas")
                lines.append(f"   - Rostros visibles: {summary.get('faces_visible', 0)}")
                lines.append(f"   - Parcialmente visibles: {summary.get('partial_visibility', 0)}")
                lines.append(
                    f"   - Calidad identificación: {summary.get('identification_quality', 'N/A')}"
                )

            # Add most distinctive features
            features = face_analysis.get("most_distinctive_features", [])
            if features:
                lines.append("")
                lines.append("🔍 Características más distintivas:")
                for i, feature in enumerate(features[:5], 1):
                    lines.append(f"   {i}. {feature}")

        elif face_analysis and face_analysis.get("status") == "skipped":
            lines.append("⏭️ Face Analysis Agent fue omitido")
        elif face_analysis:
            lines.append(f"⚠️ Error: {face_analysis.get('error', 'Face analysis failed')}")
        else:
            lines.append("⏭️ Face Analysis Agent no ejecutado")

        return lines

    @staticmethod
    def _format_forensic_section(forensic: dict[str, Any] | None = None) -> list[str]:
        """Format forensic analysis / image authenticity section."""
        lines: list[str] = []

        if forensic and forensic.get("status") == "success":
            # Verdict summary
            verdict = forensic.get("verdict", {})
            classification = verdict.get("classification", "indeterminada").upper()
            confidence = verdict.get("confidence", "N/A")
            integrity = forensic.get("integrity_score")

            lines.append(f"🎯 VEREDICTO: {classification}")
            lines.append(f"   Confianza: {confidence}")
            if integrity is not None:
                lines.append(f"   Puntuación de integridad: {integrity}/100")

            justification = verdict.get("justification")
            if justification:
                lines.append(f"   Justificación: {justification}")

            lines.append("")
            lines.append(forensic.get("analysis", "No forensic analysis available"))

            # Manipulation hypothesis
            hypothesis = forensic.get("manipulation_hypothesis")
            if hypothesis:
                lines.append("")
                lines.append(f"🚨 Hipótesis de manipulación: {hypothesis}")

            # Suspicious regions
            regions = forensic.get("suspicious_regions", [])
            if regions:
                lines.append("")
                lines.append("📍 Regiones sospechosas:")
                for region in regions[:5]:
                    lines.append(f"   - {region}")

            # Recommendations
            recs = forensic.get("recommendations", [])
            if recs:
                lines.append("")
                lines.append("💡 Recomendaciones:")
                for rec in recs[:3]:
                    lines.append(f"   - {rec}")

        elif forensic and forensic.get("status") == "skipped":
            lines.append("⏭️ Forensic Analysis Agent fue omitido")
        elif forensic:
            lines.append(f"⚠️ Error: {forensic.get('error', 'Forensic analysis failed')}")
        else:
            lines.append("⏭️ Forensic Analysis Agent no ejecutado")

        return lines

    @staticmethod
    def _format_context_intel_section(context_intel: dict[str, Any] | None = None) -> list[str]:
        """Format context intelligence / temporal-cultural inference section."""
        lines: list[str] = []

        if context_intel and context_intel.get("status") == "success":
            # Executive summary
            summary = context_intel.get("executive_summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            # Temporal analysis
            temporal = context_intel.get("temporal_analysis", {})
            if temporal:
                lines.append("⏰ Análisis Temporal:")
                time_data = temporal.get("time_of_day", {})
                if time_data.get("value"):
                    lines.append(
                        f"   - Hora: {time_data['value']} "
                        f"(Confianza: {time_data.get('confidence', 'N/A')})"
                    )
                season_data = temporal.get("season", {})
                if season_data.get("value"):
                    lines.append(
                        f"   - Estación: {season_data['value']} "
                        f"(Confianza: {season_data.get('confidence', 'N/A')})"
                    )
                era_data = temporal.get("era", {})
                if era_data.get("value"):
                    lines.append(
                        f"   - Época: {era_data['value']} "
                        f"(Confianza: {era_data.get('confidence', 'N/A')})"
                    )

            # Sociocultural analysis
            socio = context_intel.get("sociocultural_analysis", {})
            if socio:
                lines.append("")
                lines.append("🌍 Análisis Sociocultural:")
                if socio.get("socioeconomic_level"):
                    lines.append(f"   - Nivel socioeconómico: {socio['socioeconomic_level']}")
                if socio.get("cultural_context"):
                    lines.append(f"   - Contexto cultural: {socio['cultural_context']}")

            # Event classification
            event = context_intel.get("event_classification", {})
            if event and event.get("event_type"):
                lines.append("")
                lines.append("📌 Clasificación de Evento:")
                lines.append(f"   - Tipo: {event['event_type']}")
                if event.get("primary_purpose"):
                    lines.append(f"   - Propósito: {event['primary_purpose']}")

            # Key inferences
            inferences = context_intel.get("key_inferences", [])
            if inferences:
                lines.append("")
                lines.append("💡 Inferencias Clave:")
                for inf in inferences[:3]:
                    lines.append(
                        f"   - {inf.get('inference', 'N/A')} "
                        f"(Confianza: {inf.get('confidence_percent', 0)}%)"
                    )

            # Full analysis
            lines.append("")
            lines.append(context_intel.get("analysis", "No context analysis available"))

        elif context_intel and context_intel.get("status") == "skipped":
            lines.append("⏭️ Context Intel Agent fue omitido")
        elif context_intel:
            lines.append(f"⚠️ Error: {context_intel.get('error', 'Context intel failed')}")
        else:
            lines.append("⏭️ Context Intel Agent no ejecutado")

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
