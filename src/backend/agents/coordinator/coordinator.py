"""
Coordinator Agent - Main Orchestrator
Single Responsibility: Coordinate multi-agent analysis using LangGraph
Max: 150 lines (thin orchestrator - delegates to modules)

CIA-Level OSINT Analysis with 6 parallel agents:
- vision: General scene analysis
- ocr: Text extraction
- detection: Object/person detection
- geolocation: Location identification
- face_analysis: Person identification (NEW)
- forensic_analysis: Image authenticity verification (NEW)
"""

import logging
from collections.abc import Generator
from typing import Any

from ...utils.image_utils import verify_image_size
from .agent_runners import AgentRunners
from .graph_builder import GraphBuilder
from .multi_frame_handler import MultiFrameHandler
from .state import DEFAULT_AGENTS, AgentType, AnalysisState

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Coordinator that orchestrates all 6 analysis agents using LangGraph.

    This is a thin orchestrator - actual logic is delegated to specialized modules:
    - AgentRunners: Execute individual agents (6 agents)
    - GraphBuilder: Build LangGraph workflow with 6-way parallelism
    - MultiFrameHandler: Handle multi-frame analysis
    - ResultCombiner: Combine agent results (called by graph)
    - ReportGenerator: Generate text reports (called by combiner)
    """

    def __init__(self):
        """Initialize coordinator and all sub-agents."""
        # Initialize agent runners (contains all 6 agents)
        self.agent_runners = AgentRunners()

        # Build LangGraph workflow with native parallelism
        self.graph = GraphBuilder.build_analysis_graph(self.agent_runners)

        # Initialize multi-frame handler
        self.multi_frame_handler = MultiFrameHandler(self.analyze_frame)

        logger.info("🚀 CoordinatorAgent initialized with LangGraph (7 parallel CIA-level agents)")

    def analyze_frame(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[AgentType] | None = None,
    ) -> dict[str, Any]:
        """
        Execute full analysis workflow on image frame with 6 parallel agents.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis
            agents_to_run: List of agents to run (None = all 6 agents)
                Options: vision, ocr, detection, geolocation, face_analysis, forensic_analysis

        Returns:
            Dict with both JSON and text reports (CIA-level intelligence)
        """
        try:
            # Verify image size ONCE (before distributing to agents)
            verify_image_size(image_base64, "COORDINATOR")

            logger.info("🚀 Starting CIA-level coordinated frame analysis (6 agents)...")

            # Default to all 6 agents if not specified
            if agents_to_run is None:
                agents_to_run = DEFAULT_AGENTS.copy()

            # Initialize state with all 7 result slots
            initial_state: AnalysisState = {
                "image_base64": image_base64,
                "context": context,
                "agents_to_run": agents_to_run,
                # Original 4 agents
                "vision_result": None,
                "ocr_result": None,
                "detection_result": None,
                "geolocation_result": None,
                # CIA-level agents
                "face_analysis_result": None,
                "forensic_analysis_result": None,
                "context_intel_result": None,
                # Final output
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

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("❌ Coordinated analysis failed: %s", e)
            return {
                "json": {"status": "error", "error": str(e)},
                "text": f"Error en análisis: {e!s}",
            }

    def analyze_frame_stream(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[AgentType] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream analysis results as each agent completes.

        Yields per-agent update dicts as they finish:
            {"event": "agent_update", "agent": "vision", "result": {...}}
            {"event": "agent_update", "agent": "ocr", "result": {...}}
            ...
            {"event": "complete", "final_report": {"json": {...}, "text": "..."}}
        """
        try:
            verify_image_size(image_base64, "COORDINATOR")

            logger.info("Starting streaming CIA-level coordinated frame analysis...")

            if agents_to_run is None:
                agents_to_run = DEFAULT_AGENTS.copy()

            initial_state: AnalysisState = {
                "image_base64": image_base64,
                "context": context,
                "agents_to_run": agents_to_run,
                "vision_result": None,
                "ocr_result": None,
                "detection_result": None,
                "geolocation_result": None,
                "face_analysis_result": None,
                "forensic_analysis_result": None,
                "context_intel_result": None,
                "final_report": None,
            }

            for update in self.graph.stream(initial_state, stream_mode="updates"):
                for node_name, node_output in update.items():
                    if node_name == "combine":
                        final_report = node_output.get("final_report")
                        if final_report:
                            yield {"event": "complete", "final_report": final_report}
                    else:
                        result_key = f"{node_name}_result"
                        result_data = node_output.get(result_key)
                        yield {
                            "event": "agent_update",
                            "agent": node_name,
                            "result": result_data,
                        }

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Streaming analysis failed: %s", e)
            yield {
                "event": "error",
                "error": str(e),
            }

    def analyze_multi_frame(
        self, frames: list[dict[str, str]], enable_context_accumulation: bool = True
    ) -> dict[str, Any]:
        """
        Analyze multiple frames with accumulated context for enhanced OSINT.

        This method delegates to MultiFrameHandler for the actual orchestration.

        Args:
            frames: List of dicts with {"frame": base64_str, "description": str}
            enable_context_accumulation: If True, pass clues from previous frames

        Returns:
            Dict with:
                - individual_results: List of results per frame
                - combined_geolocation: Enhanced geolocation from all frames
                - summary: Overall analysis
        """
        return self.multi_frame_handler.analyze_multi_frame(frames, enable_context_accumulation)
