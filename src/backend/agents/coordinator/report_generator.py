"""
Report Generation
Single Responsibility: Format analysis results into human-readable reports

Military-Grade OSINT Intelligence Brief with 14 agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
- vehicle_detection, weapon_detection, crowd_analysis,
  shadow_analysis, infrastructure_analysis (military intel B1)
- temporal_comparison, night_vision (military intel B2)
"""

import logging
from typing import Any

from ...config import METRICS_ENABLED
from ...utils.metrics_utils import get_agent_metrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates human-readable intelligence briefs from 14 agent results."""

    @staticmethod
    def format_text_report(
        vision: dict[str, Any],
        ocr: dict[str, Any],
        detection: dict[str, Any],
        geolocation: dict[str, Any] | None = None,
        face_analysis: dict[str, Any] | None = None,
        forensic_analysis: dict[str, Any] | None = None,
        context_intel: dict[str, Any] | None = None,
        vehicle_detection: dict[str, Any] | None = None,
        weapon_detection: dict[str, Any] | None = None,
        crowd_analysis: dict[str, Any] | None = None,
        shadow_analysis: dict[str, Any] | None = None,
        infrastructure_analysis: dict[str, Any] | None = None,
        temporal_comparison: dict[str, Any] | None = None,
        night_vision: dict[str, Any] | None = None,
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
            "INTELLIGENCE BRIEF - SISTEMA OSINT MILITARY-GRADE (14 AGENTES)",
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

        # =====================================================================
        # MILITARY INTELLIGENCE BLOCK 1 (5 new agents)
        # =====================================================================

        # Vehicle Detection section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🚗 8. DETECCIÓN VEHICULAR & ALPR (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_vehicle_section(vehicle_detection))

        # Weapon Detection section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🔫 9. DETECCIÓN DE ARMAS Y AMENAZAS (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_weapon_section(weapon_detection))

        # Crowd Analysis section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "👥 10. ANÁLISIS DE MULTITUDES (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_crowd_section(crowd_analysis))

        # Shadow Analysis section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "☀️ 11. ANÁLISIS SOLAR Y DE SOMBRAS (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_shadow_section(shadow_analysis))

        # Infrastructure Analysis section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🏗️ 12. ANÁLISIS DE INFRAESTRUCTURA (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_infrastructure_section(infrastructure_analysis))

        # =====================================================================
        # MILITARY INTELLIGENCE BLOCK 2 (2 new agents)
        # =====================================================================

        # Temporal Comparison section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🕐 13. COMPARACIÓN TEMPORAL (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(
            ReportGenerator._format_temporal_comparison_section(temporal_comparison)
        )

        # Night Vision section
        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🌙 14. VISIÓN NOCTURNA (MILITAR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )
        report_lines.extend(ReportGenerator._format_night_vision_section(night_vision))

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

            # Map is rendered client-side via Mapbox GL JS
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

    # =========================================================================
    # MILITARY INTELLIGENCE BLOCK 1 — Report formatters
    # =========================================================================

    @staticmethod
    def _format_vehicle_section(vehicle: dict[str, Any] | None = None) -> list[str]:
        """Format vehicle detection / ALPR section."""
        lines: list[str] = []
        if vehicle and vehicle.get("status") == "success":
            summary = vehicle.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            vehicle_count = vehicle.get("vehicle_count", 0)
            lines.append(f"🚗 Vehículos detectados: {vehicle_count}")

            plates = vehicle.get("license_plates", [])
            if plates:
                lines.append("")
                lines.append("🔢 Matrículas identificadas:")
                for plate in plates[:10]:
                    reading = plate.get("reading", "N/A") if isinstance(plate, dict) else plate
                    lines.append(f"   - {reading}")

            markings = vehicle.get("military_markings", [])
            if markings:
                lines.append("")
                lines.append("⚔️ Marcas militares:")
                for m in markings[:5]:
                    lines.append(f"   - {m}")

            assessment = vehicle.get("tactical_assessment", {})
            if assessment.get("threat_level"):
                lines.append("")
                lines.append(f"🎯 Amenaza vehicular: {assessment['threat_level']}")

            lines.append("")
            lines.append(vehicle.get("analysis", "No vehicle analysis available"))

        elif vehicle and vehicle.get("status") == "skipped":
            lines.append("⏭️ Vehicle Detection Agent fue omitido")
        elif vehicle:
            lines.append(f"⚠️ Error: {vehicle.get('error', 'Vehicle detection failed')}")
        else:
            lines.append("⏭️ Vehicle Detection Agent no ejecutado")
        return lines

    @staticmethod
    def _format_weapon_section(weapon: dict[str, Any] | None = None) -> list[str]:
        """Format weapon/threat detection section."""
        lines: list[str] = []
        if weapon and weapon.get("status") == "success":
            summary = weapon.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            weapon_count = weapon.get("weapon_count", 0)
            lines.append(f"🔫 Armas detectadas: {weapon_count}")

            assessment = weapon.get("threat_assessment", {})
            threat_level = assessment.get("threat_level")
            if threat_level:
                lines.append(f"🚨 NIVEL DE AMENAZA: {threat_level}")

            equipment = weapon.get("military_equipment", [])
            if equipment:
                lines.append("")
                lines.append("⚔️ Equipamiento militar:")
                for eq in equipment[:5]:
                    lines.append(f"   - {eq}")

            explosive = weapon.get("explosive_indicators", [])
            if explosive:
                lines.append("")
                lines.append("💣 Indicadores explosivos:")
                for ind in explosive[:5]:
                    lines.append(f"   - {ind}")

            lines.append("")
            lines.append(weapon.get("analysis", "No weapon analysis available"))

        elif weapon and weapon.get("status") == "skipped":
            lines.append("⏭️ Weapon Detection Agent fue omitido")
        elif weapon:
            lines.append(f"⚠️ Error: {weapon.get('error', 'Weapon detection failed')}")
        else:
            lines.append("⏭️ Weapon Detection Agent no ejecutado")
        return lines

    @staticmethod
    def _format_crowd_section(crowd: dict[str, Any] | None = None) -> list[str]:
        """Format crowd analysis section."""
        lines: list[str] = []
        if crowd and crowd.get("status") == "success":
            summary = crowd.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            density = crowd.get("density_estimate", {})
            if density:
                total = density.get("total_count", "N/A")
                level = density.get("density_level", "N/A")
                lines.append(f"👥 Estimación: {total} personas — Densidad: {level}")

            behavior = crowd.get("behavioral_assessment", {})
            if behavior.get("general_mood"):
                lines.append(f"🧠 Estado general: {behavior['general_mood']}")

            concerns = crowd.get("security_concerns", [])
            if concerns:
                lines.append("")
                lines.append("🚨 Preocupaciones de seguridad:")
                for c in concerns[:5]:
                    lines.append(f"   - {c}")

            lines.append("")
            lines.append(crowd.get("analysis", "No crowd analysis available"))

        elif crowd and crowd.get("status") == "skipped":
            lines.append("⏭️ Crowd Analysis Agent fue omitido")
        elif crowd:
            lines.append(f"⚠️ Error: {crowd.get('error', 'Crowd analysis failed')}")
        else:
            lines.append("⏭️ Crowd Analysis Agent no ejecutado")
        return lines

    @staticmethod
    def _format_shadow_section(shadow: dict[str, Any] | None = None) -> list[str]:
        """Format shadow/sun analysis section."""
        lines: list[str] = []
        if shadow and shadow.get("status") == "success":
            summary = shadow.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            time_est = shadow.get("time_estimate", {})
            if time_est.get("time_range"):
                lines.append(
                    f"⏰ Hora estimada: {time_est['time_range']} "
                    f"(Confianza: {time_est.get('confidence', 'N/A')})"
                )

            sun_pos = shadow.get("sun_position", {})
            if sun_pos.get("azimuth_estimate"):
                lines.append(f"☀️ Azimut solar: {sun_pos['azimuth_estimate']}")
            if sun_pos.get("hemisphere"):
                lines.append(f"🌍 Hemisferio: {sun_pos['hemisphere']}")

            season = shadow.get("season_inference", {})
            if season.get("estimated_season"):
                lines.append(
                    f"📅 Estación: {season['estimated_season']} "
                    f"(Confianza: {season.get('confidence', 'N/A')})"
                )

            forensic = shadow.get("forensic_indicators", [])
            if forensic:
                lines.append("")
                lines.append("🔬 Indicadores forenses (inconsistencias de sombras):")
                for f_item in forensic[:5]:
                    lines.append(f"   - {f_item}")

            lines.append("")
            lines.append(shadow.get("analysis", "No shadow analysis available"))

        elif shadow and shadow.get("status") == "skipped":
            lines.append("⏭️ Shadow Analysis Agent fue omitido")
        elif shadow:
            lines.append(f"⚠️ Error: {shadow.get('error', 'Shadow analysis failed')}")
        else:
            lines.append("⏭️ Shadow Analysis Agent no ejecutado")
        return lines

    @staticmethod
    def _format_infrastructure_section(infra: dict[str, Any] | None = None) -> list[str]:
        """Format infrastructure analysis section."""
        lines: list[str] = []
        if infra and infra.get("status") == "success":
            summary = infra.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            buildings = infra.get("buildings", [])
            if buildings:
                lines.append(f"🏢 Edificios clasificados: {len(buildings)}")

            roads = infra.get("roads", [])
            if roads:
                lines.append(f"🛣️ Infraestructura vial: {len(roads)} elementos")

            bridges = infra.get("bridges", [])
            if bridges:
                lines.append(f"🌉 Puentes/estructuras: {len(bridges)}")

            assessment = infra.get("strategic_assessment", {})
            if assessment.get("military_significance"):
                lines.append("")
                lines.append(f"⚔️ Significado militar: {assessment['military_significance']}")

            vulnerabilities = assessment.get("vulnerability_points", [])
            if vulnerabilities:
                lines.append("")
                lines.append("🎯 Puntos vulnerables:")
                for v in (
                    vulnerabilities[:5] if isinstance(vulnerabilities, list) else [vulnerabilities]
                ):
                    lines.append(f"   - {v}")

            lines.append("")
            lines.append(infra.get("analysis", "No infrastructure analysis available"))

        elif infra and infra.get("status") == "skipped":
            lines.append("⏭️ Infrastructure Analysis Agent fue omitido")
        elif infra:
            lines.append(f"⚠️ Error: {infra.get('error', 'Infrastructure analysis failed')}")
        else:
            lines.append("⏭️ Infrastructure Analysis Agent no ejecutado")
        return lines

    # =========================================================================
    # MILITARY INTELLIGENCE BLOCK 2 — Report formatters
    # =========================================================================

    @staticmethod
    def _format_temporal_comparison_section(
        temporal: dict[str, Any] | None = None,
    ) -> list[str]:
        """Format temporal comparison / change detection section."""
        lines: list[str] = []
        if temporal and temporal.get("status") == "success":
            summary = temporal.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            posture = temporal.get("strategic_posture", {})
            if posture.get("posture_type"):
                lines.append(f"⚔️ Postura estratégica: {posture['posture_type']}")
            if posture.get("confidence"):
                lines.append(f"   Confianza: {posture['confidence']}")

            structural = temporal.get("structural_changes", {})
            if structural:
                new_items = structural.get("new_constructions", [])
                removed = structural.get("removed_structures", [])
                modified = structural.get("modifications", [])
                if new_items:
                    lines.append("")
                    lines.append(f"🆕 Nuevas construcciones: {len(new_items)}")
                if removed:
                    lines.append(f"🗑️ Estructuras eliminadas: {len(removed)}")
                if modified:
                    lines.append(f"🔄 Modificaciones: {len(modified)}")

            activity = temporal.get("activity_detection", {})
            if activity:
                lines.append("")
                lines.append("📊 Cambios de actividad detectados:")
                for key, val in list(activity.items())[:5]:
                    lines.append(f"   - {key}: {val}")

            chronology = temporal.get("chronology", [])
            if chronology:
                lines.append("")
                lines.append("📅 Cronología de cambios:")
                for i, event in enumerate(chronology[:5], 1):
                    if isinstance(event, dict):
                        lines.append(
                            f"   {i}. {event.get('description', 'N/A')} "
                            f"({event.get('timeframe', 'N/A')})"
                        )
                    else:
                        lines.append(f"   {i}. {event}")

            lines.append("")
            lines.append(temporal.get("analysis", "No temporal comparison available"))

        elif temporal and temporal.get("status") == "skipped":
            lines.append("⏭️ Temporal Comparison Agent fue omitido")
        elif temporal:
            lines.append(f"⚠️ Error: {temporal.get('error', 'Temporal comparison failed')}")
        else:
            lines.append("⏭️ Temporal Comparison Agent no ejecutado")
        return lines

    @staticmethod
    def _format_night_vision_section(
        night: dict[str, Any] | None = None,
    ) -> list[str]:
        """Format night vision / low-light analysis section."""
        lines: list[str] = []
        if night and night.get("status") == "success":
            summary = night.get("summary")
            if summary:
                lines.append(f"📋 Resumen: {summary}")
                lines.append("")

            visibility = night.get("visibility_conditions", {})
            if visibility:
                if visibility.get("ambient_light"):
                    lines.append(f"💡 Luz ambiental: {visibility['ambient_light']}")
                if visibility.get("visibility_range"):
                    lines.append(f"👁️ Rango de visibilidad: {visibility['visibility_range']}")
                if visibility.get("quality"):
                    lines.append(f"📊 Calidad de imagen: {visibility['quality']}")

            light_sources = night.get("light_sources", {})
            if light_sources:
                sources = light_sources.get("identified_sources", [])
                if sources:
                    lines.append("")
                    lines.append("🔦 Fuentes de luz identificadas:")
                    for src in sources[:5]:
                        if isinstance(src, dict):
                            lines.append(
                                f"   - {src.get('type', 'N/A')}: {src.get('description', 'N/A')}"
                            )
                        else:
                            lines.append(f"   - {src}")

            nocturnal = night.get("nocturnal_activity", {})
            if nocturnal:
                lines.append("")
                lines.append("🌙 Actividad nocturna:")
                for key, val in list(nocturnal.items())[:5]:
                    lines.append(f"   - {key}: {val}")

            covert = night.get("covert_indicators", {})
            if covert:
                indicators = covert.get("indicators", [])
                if indicators:
                    lines.append("")
                    lines.append("🕵️ Indicadores de actividad encubierta:")
                    for ind in indicators[:5]:
                        lines.append(f"   - {ind}")

            assessment = night.get("tactical_assessment", {})
            if assessment.get("risk_level"):
                lines.append("")
                lines.append(f"🎯 Nivel de riesgo nocturno: {assessment['risk_level']}")

            lines.append("")
            lines.append(night.get("analysis", "No night vision analysis available"))

        elif night and night.get("status") == "skipped":
            lines.append("⏭️ Night Vision Agent fue omitido")
        elif night:
            lines.append(f"⚠️ Error: {night.get('error', 'Night vision failed')}")
        else:
            lines.append("⏭️ Night Vision Agent no ejecutado")
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
