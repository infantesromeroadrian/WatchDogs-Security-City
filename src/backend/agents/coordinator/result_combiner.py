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
    CrowdAnalysisResult,
    DetectionResult,
    FaceAnalysisResult,
    FinalReport,
    ForensicAnalysisResult,
    GeolocationResult,
    InfrastructureAnalysisResult,
    OCRResult,
    ShadowAnalysisResult,
    VehicleDetectionResult,
    VisionResult,
    WeaponDetectionResult,
)
from .state import AnalysisState

logger = logging.getLogger(__name__)


class ResultCombiner:
    """Combines and validates results from all 12 agents."""

    @staticmethod
    def combine_results(state: AnalysisState) -> dict[str, Any]:
        """
        Combine all 12 agent results into final report with validation.

        Args:
            state: Analysis state with all agent results

        Returns:
            Dict with final_report key containing JSON and text reports
        """
        logger.info("📊 Combining 12 agent results...")

        # Extract all results — original 7
        vision = state.get("vision_result") or {}
        ocr = state.get("ocr_result") or {}
        detection = state.get("detection_result") or {}
        geolocation = state.get("geolocation_result") or {}
        face_analysis = state.get("face_analysis_result") or {}
        forensic_analysis = state.get("forensic_analysis_result") or {}
        context_intel = state.get("context_intel_result") or {}
        # Military Intelligence Block 1
        vehicle_detection = state.get("vehicle_detection_result") or {}
        weapon_detection = state.get("weapon_detection_result") or {}
        crowd_analysis = state.get("crowd_analysis_result") or {}
        shadow_analysis = state.get("shadow_analysis_result") or {}
        infrastructure_analysis = state.get("infrastructure_analysis_result") or {}

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
            # Military Intelligence Block 1
            vehicle_result = (
                VehicleDetectionResult(**vehicle_detection) if vehicle_detection else None
            )
            weapon_result = WeaponDetectionResult(**weapon_detection) if weapon_detection else None
            crowd_result = CrowdAnalysisResult(**crowd_analysis) if crowd_analysis else None
            shadow_result = ShadowAnalysisResult(**shadow_analysis) if shadow_analysis else None
            infra_result = (
                InfrastructureAnalysisResult(**infrastructure_analysis)
                if infrastructure_analysis
                else None
            )

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
                    vehicle_detection=vehicle_result,
                    weapon_detection=weapon_result,
                    crowd_analysis=crowd_result,
                    shadow_analysis=shadow_result,
                    infrastructure_analysis=infra_result,
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
                    vehicle_detection=vehicle_result,
                    weapon_detection=weapon_result,
                    crowd_analysis=crowd_result,
                    shadow_analysis=shadow_result,
                    infrastructure_analysis=infra_result,
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
                vision,
                ocr,
                detection,
                geolocation,
                face_analysis,
                forensic_analysis,
                context_intel,
                vehicle_detection,
                weapon_detection,
                crowd_analysis,
                shadow_analysis,
                infrastructure_analysis,
            )

        # Build human-readable text report
        from .report_generator import ReportGenerator

        text_report = ReportGenerator.format_text_report(
            vision,
            ocr,
            detection,
            geolocation,
            face_analysis,
            forensic_analysis,
            context_intel,
            vehicle_detection,
            weapon_detection,
            crowd_analysis,
            shadow_analysis,
            infrastructure_analysis,
        )

        logger.info("✅ Analysis complete - military-grade report generated with 12 agents")
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
        vehicle_detection: dict[str, Any] | None = None,
        weapon_detection: dict[str, Any] | None = None,
        crowd_analysis: dict[str, Any] | None = None,
        shadow_analysis: dict[str, Any] | None = None,
        infrastructure_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build fallback report when Pydantic validation fails."""
        report: dict[str, Any] = {
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
                # Military Intelligence Block 1
                "vehicle_detection": {
                    "status": vehicle_detection.get("status", "unknown")
                    if vehicle_detection
                    else "skipped",
                    "vehicle_count": vehicle_detection.get("vehicle_count", 0)
                    if vehicle_detection
                    else 0,
                    "analysis": vehicle_detection.get("analysis", "") if vehicle_detection else "",
                },
                "weapon_detection": {
                    "status": weapon_detection.get("status", "unknown")
                    if weapon_detection
                    else "skipped",
                    "weapon_count": weapon_detection.get("weapon_count", 0)
                    if weapon_detection
                    else 0,
                    "threat_assessment": weapon_detection.get("threat_assessment", {})
                    if weapon_detection
                    else {},
                    "analysis": weapon_detection.get("analysis", "") if weapon_detection else "",
                },
                "crowd_analysis": {
                    "status": crowd_analysis.get("status", "unknown")
                    if crowd_analysis
                    else "skipped",
                    "density_estimate": crowd_analysis.get("density_estimate", {})
                    if crowd_analysis
                    else {},
                    "analysis": crowd_analysis.get("analysis", "") if crowd_analysis else "",
                },
                "shadow_analysis": {
                    "status": shadow_analysis.get("status", "unknown")
                    if shadow_analysis
                    else "skipped",
                    "time_estimate": shadow_analysis.get("time_estimate", {})
                    if shadow_analysis
                    else {},
                    "analysis": shadow_analysis.get("analysis", "") if shadow_analysis else "",
                },
                "infrastructure_analysis": {
                    "status": infrastructure_analysis.get("status", "unknown")
                    if infrastructure_analysis
                    else "skipped",
                    "strategic_assessment": infrastructure_analysis.get("strategic_assessment", {})
                    if infrastructure_analysis
                    else {},
                    "analysis": infrastructure_analysis.get("analysis", "")
                    if infrastructure_analysis
                    else "",
                },
            },
        }
        return report
