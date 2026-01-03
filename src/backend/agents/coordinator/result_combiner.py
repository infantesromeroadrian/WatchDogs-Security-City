"""
Result Combination Logic
Single Responsibility: Combine and validate agent results
Max: 200 lines
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ...models.agent_results import (
    VisionResult,
    OCRResult,
    DetectionResult,
    GeolocationResult,
    FinalReport,
    AgentResults,
)
from .state import AnalysisState

logger = logging.getLogger(__name__)


class ResultCombiner:
    """Combines and validates results from multiple agents"""

    @staticmethod
    def combine_results(state: AnalysisState) -> Dict[str, Any]:
        """
        Combine all agent results into final report with validation.

        Args:
            state: Analysis state with all agent results

        Returns:
            Dict with final_report key containing JSON and text reports
        """
        logger.info("📊 Combining agent results...")

        vision = state.get("vision_result") or {}
        ocr = state.get("ocr_result") or {}
        detection = state.get("detection_result") or {}
        geolocation = state.get("geolocation_result") or {}

        # Validate results with Pydantic
        try:
            vision_result = VisionResult(**vision) if vision else None
            ocr_result = OCRResult(**ocr) if ocr else None
            detection_result = DetectionResult(**detection) if detection else None
            geolocation_result = (
                GeolocationResult(**geolocation) if geolocation else None
            )

            # Build validated report
            if vision_result and ocr_result and detection_result:
                agents = AgentResults(
                    vision=vision_result,
                    ocr=ocr_result,
                    detection=detection_result,
                    geolocation=geolocation_result,  # Can be None
                )
            else:
                # Handle partial results with defaults
                agents = AgentResults(
                    vision=vision_result
                    or VisionResult(
                        agent="vision",
                        status="skipped",
                        analysis="Agent was skipped",
                    ),
                    ocr=ocr_result
                    or OCRResult(
                        agent="ocr",
                        status="skipped",
                        analysis="Agent was skipped",
                        has_text=False,
                    ),
                    detection=detection_result
                    or DetectionResult(
                        agent="detection",
                        status="skipped",
                        analysis="Agent was skipped",
                    ),
                    geolocation=geolocation_result,  # Can be None
                )

            # Build final report
            final_report = FinalReport(
                timestamp=datetime.utcnow().isoformat(),
                status="success",
                agents=agents,
            )

            json_report = final_report.model_dump()

        except Exception as validation_error:
            logger.warning(
                f"⚠️ Result validation failed: {validation_error}, using raw results"
            )
            # Fallback to raw dict structure
            json_report = ResultCombiner._build_fallback_report(
                vision, ocr, detection, geolocation
            )

        # Build human-readable text report
        from .report_generator import ReportGenerator

        text_report = ReportGenerator.format_text_report(
            vision, ocr, detection, geolocation
        )

        logger.info("✅ Analysis complete - Report generated")
        return {"final_report": {"json": json_report, "text": text_report}}

    @staticmethod
    def _build_fallback_report(
        vision: Dict[str, Any],
        ocr: Dict[str, Any],
        detection: Dict[str, Any],
        geolocation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build fallback report when Pydantic validation fails.

        Args:
            vision: Raw vision result
            ocr: Raw OCR result
            detection: Raw detection result
            geolocation: Raw geolocation result

        Returns:
            Dict with basic report structure
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "agents": {
                "vision": {
                    "status": vision.get("status", "unknown"),
                    "confidence": vision.get("confidence", "unknown"),
                    "analysis": vision.get("analysis", ""),
                },
                "ocr": {
                    "status": ocr.get("status", "unknown"),
                    "has_text": ocr.get("has_text", False),
                    "confidence": ocr.get("confidence", "unknown"),
                    "analysis": ocr.get("analysis", ""),
                },
                "detection": {
                    "status": detection.get("status", "unknown"),
                    "confidence": detection.get("confidence", "unknown"),
                    "analysis": detection.get("analysis", ""),
                },
                "geolocation": {
                    "status": geolocation.get("status", "unknown")
                    if geolocation
                    else "skipped",
                    "analysis": geolocation.get("analysis", "") if geolocation else "",
                },
            },
        }
