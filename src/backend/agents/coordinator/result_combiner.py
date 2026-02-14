"""
Result Combination Logic
Single Responsibility: Combine and validate agent results
Max: 300 lines

CIA-Level OSINT Analysis with 7 agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from ...models.agent_results import (
    AgentResults,
    ContextIntelResult,
    DetectionResult,
    FaceAnalysisResult,
    FinalReport,
    ForensicAnalysisResult,
    GeolocationResult,
    OCRResult,
    VisionResult,
)
from .state import AnalysisState

logger = logging.getLogger(__name__)


class ResultCombiner:
    """Combines and validates results from all 7 agents."""

    @staticmethod
    def combine_results(state: AnalysisState) -> dict[str, Any]:
        """
        Combine all 7 agent results into final report with validation.

        Args:
            state: Analysis state with all agent results

        Returns:
            Dict with final_report key containing JSON and text reports
        """
        logger.info("📊 Combining 7 agent results...")

        # Extract all results
        vision = state.get("vision_result") or {}
        ocr = state.get("ocr_result") or {}
        detection = state.get("detection_result") or {}
        geolocation = state.get("geolocation_result") or {}
        face_analysis = state.get("face_analysis_result") or {}
        forensic_analysis = state.get("forensic_analysis_result") or {}
        context_intel = state.get("context_intel_result") or {}

        # Validate results with Pydantic
        try:
            vision_result = VisionResult(**vision) if vision else None
            ocr_result = OCRResult(**ocr) if ocr else None
            detection_result = DetectionResult(**detection) if detection else None
            geolocation_result = GeolocationResult(**geolocation) if geolocation else None
            face_analysis_result = FaceAnalysisResult(**face_analysis) if face_analysis else None
            forensic_result = (
                ForensicAnalysisResult(**forensic_analysis) if forensic_analysis else None
            )
            context_intel_result = ContextIntelResult(**context_intel) if context_intel else None

            # Build validated report
            if vision_result and ocr_result and detection_result:
                agents = AgentResults(
                    vision=vision_result,
                    ocr=ocr_result,
                    detection=detection_result,
                    geolocation=geolocation_result,
                    face_analysis=face_analysis_result,
                    forensic_analysis=forensic_result,
                    context_intel=context_intel_result,
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
                    geolocation=geolocation_result,
                    face_analysis=face_analysis_result,
                    forensic_analysis=forensic_result,
                    context_intel=context_intel_result,
                )

            # Build final report
            final_report = FinalReport(
                timestamp=datetime.now(UTC).isoformat(),
                status="success",
                agents=agents,
            )

            json_report = final_report.model_dump()

        except (ValueError, TypeError, KeyError) as validation_error:
            logger.warning("⚠️ Result validation failed: %s, using raw results", validation_error)
            # Fallback to raw dict structure
            json_report = ResultCombiner._build_fallback_report(
                vision, ocr, detection, geolocation, face_analysis, forensic_analysis, context_intel
            )

        # Build human-readable text report
        from .report_generator import ReportGenerator

        text_report = ReportGenerator.format_text_report(
            vision, ocr, detection, geolocation, face_analysis, forensic_analysis, context_intel
        )

        logger.info("✅ Analysis complete - CIA-level report generated with 7 agents")
        return {"final_report": {"json": json_report, "text": text_report}}

    @staticmethod
    def _build_fallback_report(
        vision: dict[str, Any],
        ocr: dict[str, Any],
        detection: dict[str, Any],
        geolocation: dict[str, Any],
        face_analysis: dict[str, Any],
        forensic_analysis: dict[str, Any],
        context_intel: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build fallback report when Pydantic validation fails.

        Args:
            vision: Raw vision result
            ocr: Raw OCR result
            detection: Raw detection result
            geolocation: Raw geolocation result
            face_analysis: Raw face analysis result
            forensic_analysis: Raw forensic analysis result
            context_intel: Raw context intel result

        Returns:
            Dict with basic report structure
        """
        return {
            "timestamp": datetime.now(UTC).isoformat(),
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
                    "status": geolocation.get("status", "unknown") if geolocation else "skipped",
                    "analysis": geolocation.get("analysis", "") if geolocation else "",
                    "location": geolocation.get("location", {}) if geolocation else {},
                },
                "face_analysis": {
                    "status": face_analysis.get("status", "unknown")
                    if face_analysis
                    else "skipped",
                    "person_count": face_analysis.get("person_count", 0) if face_analysis else 0,
                    "analysis": face_analysis.get("analysis", "") if face_analysis else "",
                },
                "forensic_analysis": {
                    "status": forensic_analysis.get("status", "unknown")
                    if forensic_analysis
                    else "skipped",
                    "verdict": forensic_analysis.get("verdict", {}) if forensic_analysis else {},
                    "integrity_score": forensic_analysis.get("integrity_score")
                    if forensic_analysis
                    else None,
                    "analysis": forensic_analysis.get("analysis", "") if forensic_analysis else "",
                },
                "context_intel": {
                    "status": context_intel.get("status", "unknown")
                    if context_intel
                    else "skipped",
                    "executive_summary": context_intel.get("executive_summary")
                    if context_intel
                    else None,
                    "temporal_analysis": context_intel.get("temporal_analysis", {})
                    if context_intel
                    else {},
                    "analysis": context_intel.get("analysis", "") if context_intel else "",
                },
            },
        }
