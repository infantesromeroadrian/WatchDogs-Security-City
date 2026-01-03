"""
Multi-Frame Analysis Handler
Single Responsibility: Orchestrate multi-frame analysis with context accumulation
Max: 200 lines
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MultiFrameHandler:
    """Handles multi-frame analysis with accumulated context for enhanced OSINT"""

    def __init__(self, single_frame_analyzer):
        """
        Initialize with reference to single-frame analyzer.

        Args:
            single_frame_analyzer: Callable that analyzes single frame (analyze_frame method)
        """
        self.single_frame_analyzer = single_frame_analyzer

    def analyze_multi_frame(
        self, frames: list[Dict[str, str]], enable_context_accumulation: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze multiple frames with accumulated context for enhanced OSINT.

        Args:
            frames: List of dicts with {"frame": base64_str, "description": str}
            enable_context_accumulation: If True, pass clues from previous frames

        Returns:
            Dict with:
                - individual_results: List of results per frame
                - combined_geolocation: Enhanced geolocation from all frames
                - summary: Overall analysis
        """
        try:
            logger.info(
                f"🔍 Starting multi-frame analysis ({len(frames)} frames, "
                f"context={'ON' if enable_context_accumulation else 'OFF'})"
            )

            individual_results = []
            accumulated_geolocation_clues = []
            accumulated_ocr_texts = []
            accumulated_detections = []

            for idx, frame_data in enumerate(frames):
                frame_base64 = frame_data.get("frame", "")
                description = frame_data.get("description", f"Frame {idx + 1}")

                # Build context from accumulated clues
                context = self._build_frame_context(
                    idx,
                    len(frames),
                    description,
                    enable_context_accumulation,
                    accumulated_geolocation_clues,
                    accumulated_ocr_texts,
                    accumulated_detections,
                )

                logger.info(
                    f"  🖼️ Analyzing frame {idx + 1}/{len(frames)}: {description}"
                )

                # Analyze frame
                result = self.single_frame_analyzer(frame_base64, context)

                # Extract clues for next iterations
                if enable_context_accumulation:
                    self._extract_clues_from_result(
                        result,
                        idx,
                        accumulated_geolocation_clues,
                        accumulated_ocr_texts,
                        accumulated_detections,
                    )

                individual_results.append(
                    {
                        "frame_index": idx + 1,
                        "description": description,
                        "result": result,
                    }
                )

            # Combine geolocation from all frames
            logger.info("🌍 Combining geolocation clues from all frames...")
            combined_geolocation = self._combine_geolocation_results(individual_results)

            # Generate summary
            summary = self._generate_multi_frame_summary(
                individual_results, combined_geolocation
            )

            logger.info(
                f"✅ Multi-frame analysis complete ({len(frames)} frames processed)"
            )

            return {
                "individual_results": individual_results,
                "combined_geolocation": combined_geolocation,
                "summary": summary,
                "total_frames": len(frames),
                "context_accumulation_enabled": enable_context_accumulation,
            }

        except Exception as e:
            logger.error(f"❌ Multi-frame analysis failed: {e}")
            return {
                "error": str(e),
                "individual_results": individual_results if individual_results else [],
                "total_frames": len(frames),
            }

    @staticmethod
    def _build_frame_context(
        idx: int,
        total_frames: int,
        description: str,
        enable_context: bool,
        geo_clues: list,
        ocr_texts: list,
        detections: list,
    ) -> str:
        """Build context string for current frame from accumulated data"""
        context = f"Imagen {idx + 1}/{total_frames}: {description}"

        if enable_context and idx > 0:
            context += "\n\n🔍 PISTAS ACUMULADAS DE IMÁGENES ANTERIORES:\n"

            if geo_clues:
                context += "\n📍 Geolocalización:\n"
                context += "\n".join(geo_clues[-10:])  # Last 10 clues

            if ocr_texts:
                context += "\n\n📝 Textos encontrados:\n"
                context += "\n".join(ocr_texts[-5:])

            if detections:
                context += "\n\n🎯 Objetos detectados:\n"
                context += "\n".join(detections[-5:])

        return context

    @staticmethod
    def _extract_clues_from_result(
        result: Dict[str, Any],
        idx: int,
        geo_clues: list,
        ocr_texts: list,
        detections: list,
    ) -> None:
        """Extract clues from frame result for context accumulation"""
        json_result = result.get("json", {})
        agents = json_result.get("agents", {})

        # Extract geolocation clues
        geo = agents.get("geolocation", {})
        if geo.get("key_clues"):
            geo_clues.extend(geo["key_clues"])

        # Extract OCR texts
        ocr = agents.get("ocr", {})
        if ocr.get("status") == "success" and ocr.get("has_text"):
            analysis = ocr.get("analysis", "")
            if analysis and len(analysis) > 10:
                ocr_texts.append(f"Frame {idx + 1}: {analysis[:200]}")

        # Extract key detections
        detection = agents.get("detection", {})
        if detection.get("status") == "success":
            analysis = detection.get("analysis", "")
            if analysis and len(analysis) > 10:
                detections.append(f"Frame {idx + 1}: {analysis[:150]}")

    @staticmethod
    def _combine_geolocation_results(individual_results: list) -> Dict[str, Any]:
        """Combine geolocation results from multiple frames"""
        from .geolocation_combiner import GeolocationCombiner

        return GeolocationCombiner.combine_results(individual_results)

    @staticmethod
    def _generate_multi_frame_summary(
        individual_results: list, combined_geolocation: Dict[str, Any]
    ) -> str:
        """Generate human-readable summary of multi-frame analysis"""
        from .multi_frame_reporter import MultiFrameReporter

        return MultiFrameReporter.generate_summary(
            individual_results, combined_geolocation
        )
