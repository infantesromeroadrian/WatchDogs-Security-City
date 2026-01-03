"""
Coordinator Agent using LangGraph with native parallelism.
Refactored to use LangGraph's native parallel execution instead of threading.
"""

import logging
from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, START, END

from .vision_agent import VisionAgent
from .ocr_agent import OCRAgent
from .detection_agent import DetectionAgent
from .geolocation_agent import GeolocationAgent
from ..models.agent_results import (
    VisionResult,
    OCRResult,
    DetectionResult,
    GeolocationResult,
    FinalReport,
    AgentResults,
)
from ..config import METRICS_ENABLED
from ..utils.metrics_utils import get_agent_metrics
from ..utils.image_utils import verify_image_size
from ..services.geolocation_service import GeolocationService

logger = logging.getLogger(__name__)


class AnalysisState(TypedDict):
    """State structure for the analysis graph."""

    image_base64: str
    context: str
    agents_to_run: list[
        Literal["vision", "ocr", "detection", "geolocation"]
    ]  # Conditional execution
    vision_result: Dict[str, Any] | None
    ocr_result: Dict[str, Any] | None
    detection_result: Dict[str, Any] | None
    geolocation_result: Dict[str, Any] | None
    final_report: Dict[str, Any] | None


class CoordinatorAgent:
    """Coordinator that orchestrates all analysis agents using LangGraph."""

    def __init__(self):
        """Initialize coordinator and all sub-agents."""
        self.vision_agent = VisionAgent()
        self.ocr_agent = OCRAgent()
        self.detection_agent = DetectionAgent()
        self.geolocation_agent = GeolocationAgent()
        self.geolocation_service = GeolocationService()

        # Build LangGraph workflow with native parallelism
        self.graph = self._build_graph()
        logger.info(
            "ℹ️ CoordinatorAgent initialized with LangGraph native parallelism (4 agents)"
        )

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with native parallel execution."""

        def run_vision_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute Vision Agent (separate node for native parallelism)."""
            if "vision" not in state.get(
                "agents_to_run", ["vision", "ocr", "detection"]
            ):
                logger.info("⏭️ Skipping Vision Agent (not in agents_to_run)")
                return {"vision_result": None}

            try:
                logger.info("🔍 Running Vision Agent (native parallel)...")
                result = self.vision_agent.analyze(
                    state["image_base64"], state.get("context", "")
                )
                return {"vision_result": result}
            except Exception as e:
                logger.error(f"❌ Vision agent error: {e}")
                return {
                    "vision_result": {
                        "agent": "vision",
                        "status": "error",
                        "error": str(e),
                        "analysis": "Vision analysis failed",
                    }
                }

        def run_ocr_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute OCR Agent (separate node for native parallelism)."""
            if "ocr" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
                logger.info("⏭️ Skipping OCR Agent (not in agents_to_run)")
                return {"ocr_result": None}

            try:
                logger.info("📝 Running OCR Agent (native parallel)...")
                result = self.ocr_agent.analyze(
                    state["image_base64"], state.get("context", "")
                )
                return {"ocr_result": result}
            except Exception as e:
                logger.error(f"❌ OCR agent error: {e}")
                return {
                    "ocr_result": {
                        "agent": "ocr",
                        "status": "error",
                        "error": str(e),
                        "analysis": "OCR extraction failed",
                        "has_text": False,
                    }
                }

        def run_detection_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute Detection Agent (separate node for native parallelism)."""
            if "detection" not in state.get(
                "agents_to_run", ["vision", "ocr", "detection"]
            ):
                logger.info("⏭️ Skipping Detection Agent (not in agents_to_run)")
                return {"detection_result": None}

            try:
                logger.info("🎯 Running Detection Agent (native parallel)...")
                result = self.detection_agent.analyze(
                    state["image_base64"], state.get("context", "")
                )
                return {"detection_result": result}
            except Exception as e:
                logger.error(f"❌ Detection agent error: {e}")
                return {
                    "detection_result": {
                        "agent": "detection",
                        "status": "error",
                        "error": str(e),
                        "analysis": "Detection analysis failed",
                    }
                }

        def run_geolocation_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute Geolocation Agent (separate node for native parallelism)."""
            if "geolocation" not in state.get(
                "agents_to_run", ["vision", "ocr", "detection", "geolocation"]
            ):
                logger.info("⏭️ Skipping Geolocation Agent (not in agents_to_run)")
                return {"geolocation_result": None}

            try:
                logger.info("🌍 Running Geolocation Agent (native parallel)...")
                result = self.geolocation_agent.analyze(
                    state["image_base64"], state.get("context", "")
                )

                # Enrich with geocoding and map generation
                enriched_result = self.geolocation_service.enrich_geolocation_result(
                    result
                )

                return {"geolocation_result": enriched_result}
            except Exception as e:
                logger.error(f"❌ Geolocation agent error: {e}")
                return {
                    "geolocation_result": {
                        "agent": "geolocation",
                        "status": "error",
                        "error": str(e),
                        "analysis": "Geolocation analysis failed",
                        "location": {},
                    }
                }

        def combine_results(state: AnalysisState) -> Dict[str, Any]:
            """Combine all agent results into final report with validation."""
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
                    # Handle partial results
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
                from datetime import datetime

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
                json_report = {
                    "timestamp": "",
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
                    },
                }

            # Build human-readable text report
            text_report = self._format_text_report(vision, ocr, detection, geolocation)

            logger.info("✅ Analysis complete - Report generated")
            return {"final_report": {"json": json_report, "text": text_report}}

        # Create graph
        workflow = StateGraph(AnalysisState)

        # Add nodes (separate nodes for each agent - enables native parallelism)
        workflow.add_node("vision", run_vision_agent)
        workflow.add_node("ocr", run_ocr_agent)
        workflow.add_node("detection", run_detection_agent)
        workflow.add_node("geolocation", run_geolocation_agent)
        workflow.add_node("combine", combine_results)

        # Define edges with NATIVE PARALLELISM
        # All FOUR agents run in parallel from START
        workflow.add_edge(START, "vision")
        workflow.add_edge(START, "ocr")
        workflow.add_edge(START, "detection")
        workflow.add_edge(START, "geolocation")

        # All agents converge to combine node
        workflow.add_edge("vision", "combine")
        workflow.add_edge("ocr", "combine")
        workflow.add_edge("detection", "combine")
        workflow.add_edge("geolocation", "combine")

        # Combine to END
        workflow.add_edge("combine", END)

        return workflow.compile()

    def _format_text_report(
        self,
        vision: Dict[str, Any],
        ocr: Dict[str, Any],
        detection: Dict[str, Any],
        geolocation: Dict[str, Any] = None,
    ) -> str:
        """Format combined results into readable text report."""

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

        if vision.get("status") == "success":
            report_lines.append(vision.get("analysis", "No analysis available"))
        else:
            report_lines.append(
                f"⚠️ Error: {vision.get('error', 'Vision analysis failed')}"
            )

        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "📝 2. EXTRACCIÓN DE TEXTO (OCR)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        if ocr.get("status") == "success":
            report_lines.append(ocr.get("analysis", "No text detected"))
        else:
            report_lines.append(f"⚠️ Error: {ocr.get('error', 'OCR extraction failed')}")

        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🎯 3. DETECCIÓN DE OBJETOS Y PERSONAS",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        if detection.get("status") == "success":
            report_lines.append(detection.get("analysis", "No detections available"))
        elif detection.get("status") == "skipped":
            report_lines.append("⏭️ Detection Agent fue omitido")
        else:
            report_lines.append(
                f"⚠️ Error: {detection.get('error', 'Detection analysis failed')}"
            )

        report_lines.extend(
            [
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🌍 4. ANÁLISIS DE GEOLOCALIZACIÓN",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        if geolocation and geolocation.get("status") == "success":
            report_lines.append(
                geolocation.get("analysis", "No geolocation analysis available")
            )

            # Add coordinates if available
            coords = geolocation.get("coordinates")
            if coords:
                report_lines.append(
                    f"\n📍 Coordenadas: {coords.get('lat')}, {coords.get('lon')}"
                )

            # Add map link if available
            map_url = geolocation.get("map_url")
            if map_url:
                report_lines.append(f"🗺️ Mapa interactivo generado: {map_url}")
        elif geolocation and geolocation.get("status") == "skipped":
            report_lines.append("⏭️ Geolocation Agent fue omitido")
        elif geolocation:
            report_lines.append(
                f"⚠️ Error: {geolocation.get('error', 'Geolocation analysis failed')}"
            )
        else:
            report_lines.append("⏭️ Geolocation Agent no ejecutado")

        # Add metrics if enabled
        if METRICS_ENABLED:
            metrics = get_agent_metrics()
            report_lines.extend(
                [
                    "",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    "📊 MÉTRICAS DE RENDIMIENTO",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    "",
                ]
            )
            for agent_name, stats in metrics.items():
                if stats["total_calls"] > 0:
                    report_lines.append(
                        f"{agent_name.upper()}: "
                        f"Llamadas: {stats['total_calls']}, "
                        f"Éxito: {stats['success_count']}, "
                        f"Latencia promedio: {stats.get('avg_latency_ms', 0):.2f}ms"
                    )

        report_lines.extend(["", "=" * 80, "FIN DEL REPORTE", "=" * 80])

        return "\n".join(report_lines)

    def analyze_frame(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[Literal["vision", "ocr", "detection"]] | None = None,
    ) -> Dict[str, Any]:
        """
        Execute full analysis workflow on image frame.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis
            agents_to_run: List of agents to run (None = all agents)

        Returns:
            Dict with both JSON and text reports
        """
        try:
            # Verify image size ONCE (before distributing to agents)
            verify_image_size(image_base64, "COORDINATOR")

            logger.info("🚀 Starting coordinated frame analysis...")

            # Default to all agents if not specified
            if agents_to_run is None:
                agents_to_run = ["vision", "ocr", "detection", "geolocation"]

            # Initialize state
            initial_state: AnalysisState = {
                "image_base64": image_base64,
                "context": context,
                "agents_to_run": agents_to_run,
                "vision_result": None,
                "ocr_result": None,
                "detection_result": None,
                "geolocation_result": None,
                "final_report": None,
            }

            # Execute graph (LangGraph handles parallelism natively)
            final_state = self.graph.invoke(initial_state)

            # Return final report
            return final_state.get(
                "final_report",
                {
                    "json": {"status": "error", "message": "No report generated"},
                    "text": "Error: Analysis workflow failed",
                },
            )

        except Exception as e:
            logger.error(f"❌ Coordinated analysis failed: {e}")
            return {
                "json": {"status": "error", "error": str(e)},
                "text": f"Error en análisis: {str(e)}",
            }

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
                f"🔍 Starting multi-frame analysis ({len(frames)} frames, context={'ON' if enable_context_accumulation else 'OFF'})"
            )

            individual_results = []
            accumulated_geolocation_clues = []
            accumulated_ocr_texts = []
            accumulated_detections = []

            for idx, frame_data in enumerate(frames):
                frame_base64 = frame_data.get("frame", "")
                description = frame_data.get("description", f"Frame {idx + 1}")

                # Build context from accumulated clues
                context = f"Imagen {idx + 1}/{len(frames)}: {description}"

                if enable_context_accumulation and idx > 0:
                    context += "\n\n🔍 PISTAS ACUMULADAS DE IMÁGENES ANTERIORES:\n"

                    if accumulated_geolocation_clues:
                        context += "\n📍 Geolocalización:\n"
                        context += "\n".join(
                            accumulated_geolocation_clues[-10:]
                        )  # Last 10 clues

                    if accumulated_ocr_texts:
                        context += "\n\n📝 Textos encontrados:\n"
                        context += "\n".join(accumulated_ocr_texts[-5:])

                    if accumulated_detections:
                        context += "\n\n🎯 Objetos detectados:\n"
                        context += "\n".join(accumulated_detections[-5:])

                logger.info(
                    f"  🖼️ Analyzing frame {idx + 1}/{len(frames)}: {description}"
                )

                # Analyze frame
                result = self.analyze_frame(frame_base64, context)

                # Extract clues for next iterations
                if enable_context_accumulation:
                    json_result = result.get("json", {})
                    agents = json_result.get("agents", {})

                    # Extract geolocation clues
                    geo = agents.get("geolocation", {})
                    if geo.get("key_clues"):
                        accumulated_geolocation_clues.extend(geo["key_clues"])

                    # Extract OCR texts
                    ocr = agents.get("ocr", {})
                    if ocr.get("status") == "success" and ocr.get("has_text"):
                        analysis = ocr.get("analysis", "")
                        if analysis and len(analysis) > 10:
                            accumulated_ocr_texts.append(
                                f"Frame {idx + 1}: {analysis[:200]}"
                            )

                    # Extract key detections
                    detection = agents.get("detection", {})
                    if detection.get("status") == "success":
                        analysis = detection.get("analysis", "")
                        if analysis and len(analysis) > 10:
                            accumulated_detections.append(
                                f"Frame {idx + 1}: {analysis[:150]}"
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

    def _combine_geolocation_results(self, individual_results: list) -> Dict[str, Any]:
        """
        Combine geolocation results from multiple frames.

        Accumulates clues and attempts to determine most likely location.
        """
        all_clues = []
        all_locations = []
        confidence_scores = []

        for result_data in individual_results:
            result = result_data.get("result", {})
            json_result = result.get("json", {})
            agents = json_result.get("agents", {})
            geo = agents.get("geolocation", {})

            if geo.get("key_clues"):
                all_clues.extend(geo["key_clues"])

            if geo.get("location"):
                all_locations.append(geo["location"])

            if geo.get("confidence"):
                confidence_scores.append(geo["confidence"])

        # Determine most common/likely location
        if all_locations:
            # Simple: take location with highest confidence
            best_location = all_locations[0]  # For now, just first

            return {
                "combined_clues": all_clues,
                "most_likely_location": best_location,
                "all_detected_locations": all_locations,
                "total_clues_found": len(all_clues),
                "confidence": "MEDIUM" if len(all_clues) > 5 else "LOW",
            }
        else:
            return {
                "combined_clues": all_clues,
                "most_likely_location": None,
                "total_clues_found": len(all_clues),
                "confidence": "VERY LOW",
                "note": "No se pudo determinar ubicación con certeza",
            }

    def _generate_multi_frame_summary(
        self, individual_results: list, combined_geolocation: Dict[str, Any]
    ) -> str:
        """Generate human-readable summary of multi-frame analysis."""

        summary_lines = [
            "=" * 80,
            "RESUMEN DE ANÁLISIS MULTI-FRAME",
            "=" * 80,
            "",
            f"📊 Total de frames analizados: {len(individual_results)}",
            "",
        ]

        # Geolocation summary
        summary_lines.extend(
            [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "🌍 GEOLOCALIZACIÓN COMBINADA",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        total_clues = combined_geolocation.get("total_clues_found", 0)
        summary_lines.append(f"Pistas totales encontradas: {total_clues}")

        if combined_geolocation.get("most_likely_location"):
            location = combined_geolocation["most_likely_location"]
            summary_lines.append(
                f"Ubicación más probable: {location.get('country', 'N/A')}, {location.get('city', 'N/A')}"
            )
        else:
            summary_lines.append("⚠️ No se pudo determinar ubicación específica")

        summary_lines.append(
            f"Nivel de confianza: {combined_geolocation.get('confidence', 'UNKNOWN')}"
        )
        summary_lines.append("")

        # Key clues
        if combined_geolocation.get("combined_clues"):
            summary_lines.extend(["Pistas clave acumuladas:", ""])
            for clue in combined_geolocation["combined_clues"][:10]:  # Top 10
                summary_lines.append(f"  • {clue}")
            summary_lines.append("")

        # Frame by frame summary
        summary_lines.extend(
            [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "📸 RESUMEN POR FRAME",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
            ]
        )

        for result_data in individual_results:
            idx = result_data["frame_index"]
            desc = result_data["description"]
            result = result_data["result"]

            json_result = result.get("json", {})
            agents = json_result.get("agents", {})

            summary_lines.append(f"Frame {idx}: {desc}")

            # Status per agent
            if agents.get("vision"):
                summary_lines.append(
                    f"  ✓ Vision: {agents['vision'].get('status', 'unknown')}"
                )
            if agents.get("ocr"):
                has_text = agents["ocr"].get("has_text", False)
                summary_lines.append(
                    f"  ✓ OCR: {'Texto encontrado' if has_text else 'Sin texto'}"
                )
            if agents.get("detection"):
                summary_lines.append(
                    f"  ✓ Detection: {agents['detection'].get('status', 'unknown')}"
                )

            summary_lines.append("")

        summary_lines.extend(["=" * 80, "FIN DEL RESUMEN", "=" * 80])

        return "\n".join(summary_lines)
