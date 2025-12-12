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
from ..models.agent_results import VisionResult, OCRResult, DetectionResult, FinalReport, AgentResults
from ..config import METRICS_ENABLED
from ..utils.metrics_utils import get_agent_metrics

logger = logging.getLogger(__name__)


class AnalysisState(TypedDict):
    """State structure for the analysis graph."""
    image_base64: str
    context: str
    agents_to_run: list[Literal["vision", "ocr", "detection"]]  # Conditional execution
    vision_result: Dict[str, Any] | None
    ocr_result: Dict[str, Any] | None
    detection_result: Dict[str, Any] | None
    final_report: Dict[str, Any] | None


class CoordinatorAgent:
    """Coordinator that orchestrates all analysis agents using LangGraph."""
    
    def __init__(self):
        """Initialize coordinator and all sub-agents."""
        self.vision_agent = VisionAgent()
        self.ocr_agent = OCRAgent()
        self.detection_agent = DetectionAgent()
        
        # Build LangGraph workflow with native parallelism
        self.graph = self._build_graph()
        logger.info("ℹ️ CoordinatorAgent initialized with LangGraph native parallelism")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with native parallel execution."""
        
        def run_vision_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute Vision Agent (separate node for native parallelism)."""
            if "vision" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
                logger.info("⏭️ Skipping Vision Agent (not in agents_to_run)")
                return {"vision_result": None}
            
            try:
                logger.info("🔍 Running Vision Agent (native parallel)...")
                result = self.vision_agent.analyze(
                    state["image_base64"],
                    state.get("context", "")
                )
                return {"vision_result": result}
            except Exception as e:
                logger.error(f"❌ Vision agent error: {e}")
                return {
                    "vision_result": {
                        "agent": "vision",
                        "status": "error",
                        "error": str(e),
                        "analysis": "Vision analysis failed"
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
                    state["image_base64"],
                    state.get("context", "")
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
                        "has_text": False
                    }
                }
        
        def run_detection_agent(state: AnalysisState) -> Dict[str, Any]:
            """Execute Detection Agent (separate node for native parallelism)."""
            if "detection" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
                logger.info("⏭️ Skipping Detection Agent (not in agents_to_run)")
                return {"detection_result": None}
            
            try:
                logger.info("🎯 Running Detection Agent (native parallel)...")
                result = self.detection_agent.analyze(
                    state["image_base64"],
                    state.get("context", "")
                )
                return {"detection_result": result}
            except Exception as e:
                logger.error(f"❌ Detection agent error: {e}")
                return {
                    "detection_result": {
                        "agent": "detection",
                        "status": "error",
                        "error": str(e),
                        "analysis": "Detection analysis failed"
                    }
                }
        
        def combine_results(state: AnalysisState) -> Dict[str, Any]:
            """Combine all agent results into final report with validation."""
            logger.info("📊 Combining agent results...")
            
            vision = state.get("vision_result") or {}
            ocr = state.get("ocr_result") or {}
            detection = state.get("detection_result") or {}
            
            # Validate results with Pydantic
            try:
                vision_result = VisionResult(**vision) if vision else None
                ocr_result = OCRResult(**ocr) if ocr else None
                detection_result = DetectionResult(**detection) if detection else None
                
                # Build validated report
                if vision_result and ocr_result and detection_result:
                    agents = AgentResults(
                        vision=vision_result,
                        ocr=ocr_result,
                        detection=detection_result
                    )
                else:
                    # Handle partial results
                    agents = AgentResults(
                        vision=vision_result or VisionResult(
                            agent="vision",
                            status="skipped",
                            analysis="Agent was skipped"
                        ),
                        ocr=ocr_result or OCRResult(
                            agent="ocr",
                            status="skipped",
                            analysis="Agent was skipped",
                            has_text=False
                        ),
                        detection=detection_result or DetectionResult(
                            agent="detection",
                            status="skipped",
                            analysis="Agent was skipped"
                        )
                    )
                
                # Build final report
                from datetime import datetime
                final_report = FinalReport(
                    timestamp=datetime.utcnow().isoformat(),
                    status="success",
                    agents=agents
                )
                
                json_report = final_report.model_dump()
                
            except Exception as validation_error:
                logger.warning(f"⚠️ Result validation failed: {validation_error}, using raw results")
                # Fallback to raw dict structure
                json_report = {
                    "timestamp": "",
                    "status": "success",
                    "agents": {
                        "vision": {
                            "status": vision.get("status", "unknown"),
                            "confidence": vision.get("confidence", "unknown"),
                            "analysis": vision.get("analysis", "")
                        },
                        "ocr": {
                            "status": ocr.get("status", "unknown"),
                            "has_text": ocr.get("has_text", False),
                            "confidence": ocr.get("confidence", "unknown"),
                            "analysis": ocr.get("analysis", "")
                        },
                        "detection": {
                            "status": detection.get("status", "unknown"),
                            "confidence": detection.get("confidence", "unknown"),
                            "analysis": detection.get("analysis", "")
                        }
                    }
                }
            
            # Build human-readable text report
            text_report = self._format_text_report(vision, ocr, detection)
            
            logger.info("✅ Analysis complete - Report generated")
            return {
                "final_report": {
                    "json": json_report,
                    "text": text_report
                }
            }
        
        # Create graph
        workflow = StateGraph(AnalysisState)
        
        # Add nodes (separate nodes for each agent - enables native parallelism)
        workflow.add_node("vision", run_vision_agent)
        workflow.add_node("ocr", run_ocr_agent)
        workflow.add_node("detection", run_detection_agent)
        workflow.add_node("combine", combine_results)
        
        # Define edges with NATIVE PARALLELISM
        # All three agents run in parallel from START
        workflow.add_edge(START, "vision")
        workflow.add_edge(START, "ocr")
        workflow.add_edge(START, "detection")
        
        # All agents converge to combine node
        workflow.add_edge("vision", "combine")
        workflow.add_edge("ocr", "combine")
        workflow.add_edge("detection", "combine")
        
        # Combine to END
        workflow.add_edge("combine", END)
        
        return workflow.compile()
    
    def _format_text_report(
        self,
        vision: Dict[str, Any],
        ocr: Dict[str, Any],
        detection: Dict[str, Any]
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
            ""
        ]
        
        if vision.get("status") == "success":
            report_lines.append(vision.get("analysis", "No analysis available"))
        else:
            report_lines.append(f"⚠️ Error: {vision.get('error', 'Vision analysis failed')}")
        
        report_lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📝 2. EXTRACCIÓN DE TEXTO (OCR)",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])
        
        if ocr.get("status") == "success":
            report_lines.append(ocr.get("analysis", "No text detected"))
        else:
            report_lines.append(f"⚠️ Error: {ocr.get('error', 'OCR extraction failed')}")
        
        report_lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🎯 3. DETECCIÓN DE OBJETOS Y PERSONAS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])
        
        if detection.get("status") == "success":
            report_lines.append(detection.get("analysis", "No detections available"))
        elif detection.get("status") == "skipped":
            report_lines.append("⏭️ Detection Agent fue omitido")
        else:
            report_lines.append(f"⚠️ Error: {detection.get('error', 'Detection analysis failed')}")
        
        # Add metrics if enabled
        if METRICS_ENABLED:
            metrics = get_agent_metrics()
            report_lines.extend([
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "📊 MÉTRICAS DE RENDIMIENTO",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ""
            ])
            for agent_name, stats in metrics.items():
                if stats["total_calls"] > 0:
                    report_lines.append(
                        f"{agent_name.upper()}: "
                        f"Llamadas: {stats['total_calls']}, "
                        f"Éxito: {stats['success_count']}, "
                        f"Latencia promedio: {stats.get('avg_latency_ms', 0):.2f}ms"
                    )
        
        report_lines.extend([
            "",
            "=" * 80,
            "FIN DEL REPORTE",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def analyze_frame(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[Literal["vision", "ocr", "detection"]] | None = None
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
            logger.info("🚀 Starting coordinated frame analysis...")
            
            # Default to all agents if not specified
            if agents_to_run is None:
                agents_to_run = ["vision", "ocr", "detection"]
            
            # Initialize state
            initial_state: AnalysisState = {
                "image_base64": image_base64,
                "context": context,
                "agents_to_run": agents_to_run,
                "vision_result": None,
                "ocr_result": None,
                "detection_result": None,
                "final_report": None
            }
            
            # Execute graph (LangGraph handles parallelism natively)
            final_state = self.graph.invoke(initial_state)
            
            # Return final report
            return final_state.get("final_report", {
                "json": {"status": "error", "message": "No report generated"},
                "text": "Error: Analysis workflow failed"
            })
            
        except Exception as e:
            logger.error(f"❌ Coordinated analysis failed: {e}")
            return {
                "json": {
                    "status": "error",
                    "error": str(e)
                },
                "text": f"Error en análisis: {str(e)}"
            }

