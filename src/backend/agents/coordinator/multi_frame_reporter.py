"""
Multi-Frame Report Generation
Single Responsibility: Generate summary reports for multi-frame analysis
Max: 150 lines
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MultiFrameReporter:
    """Generates human-readable summaries for multi-frame analysis"""

    @staticmethod
    def generate_summary(individual_results: list, combined_geolocation: dict[str, Any]) -> str:
        """
        Generate human-readable summary of multi-frame analysis.

        Args:
            individual_results: List of frame analysis results
            combined_geolocation: Combined geolocation data

        Returns:
            Formatted summary string
        """
        summary_lines = [
            "=" * 80,
            "RESUMEN DE ANÁLISIS MULTI-FRAME",
            "=" * 80,
            "",
            f"📊 Total de frames analizados: {len(individual_results)}",
            "",
        ]

        # Geolocation summary
        summary_lines.extend(MultiFrameReporter._format_geolocation_summary(combined_geolocation))

        # Frame by frame summary
        summary_lines.extend(
            [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "📸 RESUMEN POR FRAME",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        summary_lines.extend(MultiFrameReporter._format_frame_summaries(individual_results))

        summary_lines.extend(["=" * 80, "FIN DEL RESUMEN", "=" * 80])

        return "\n".join(summary_lines)

    @staticmethod
    def _format_geolocation_summary(combined_geolocation: dict[str, Any]) -> list[str]:
        """Format combined geolocation summary section"""
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🌍 GEOLOCALIZACIÓN COMBINADA",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]

        total_clues = combined_geolocation.get("total_clues_found", 0)
        lines.append(f"Pistas totales encontradas: {total_clues}")

        if combined_geolocation.get("most_likely_location"):
            location = combined_geolocation["most_likely_location"]
            lines.append(
                f"Ubicación más probable: {location.get('country', 'N/A')}, "
                f"{location.get('city', 'N/A')}"
            )
        else:
            lines.append("⚠️ No se pudo determinar ubicación específica")

        lines.append(f"Nivel de confianza: {combined_geolocation.get('confidence', 'UNKNOWN')}")
        lines.append("")

        # Key clues
        if combined_geolocation.get("combined_clues"):
            lines.extend(["Pistas clave acumuladas:", ""])
            for clue in combined_geolocation["combined_clues"][:10]:  # Top 10
                lines.append(f"  • {clue}")
            lines.append("")

        return lines

    @staticmethod
    def _format_frame_summaries(individual_results: list) -> list[str]:
        """Format frame-by-frame summary section"""
        lines = []

        for result_data in individual_results:
            idx = result_data["frame_index"]
            desc = result_data["description"]
            result = result_data["result"]

            json_result = result.get("json", {})
            agents = json_result.get("agents", {})

            lines.append(f"Frame {idx}: {desc}")

            # Status per agent
            if agents.get("vision"):
                lines.append(f"  ✓ Vision: {agents['vision'].get('status', 'unknown')}")
            if agents.get("ocr"):
                has_text = agents["ocr"].get("has_text", False)
                lines.append(f"  ✓ OCR: {'Texto encontrado' if has_text else 'Sin texto'}")
            if agents.get("detection"):
                lines.append(f"  ✓ Detection: {agents['detection'].get('status', 'unknown')}")

            lines.append("")

        return lines
