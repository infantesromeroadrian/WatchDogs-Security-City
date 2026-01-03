"""
Coordinator Agent - Main Orchestrator
Single Responsibility: Coordinate multi-agent analysis using LangGraph
Max: 150 lines (thin orchestrator - delegates to modules)
"""

import logging
from typing import Dict, Any, Literal

from ...utils.image_utils import verify_image_size
from .state import AnalysisState
from .agent_runners import AgentRunners
from .graph_builder import GraphBuilder
from .multi_frame_handler import MultiFrameHandler

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Coordinator that orchestrates all analysis agents using LangGraph.

    This is a thin orchestrator - actual logic is delegated to specialized modules:
    - AgentRunners: Execute individual agents
    - GraphBuilder: Build LangGraph workflow
    - MultiFrameHandler: Handle multi-frame analysis
    - ResultCombiner: Combine agent results (called by graph)
    - ReportGenerator: Generate text reports (called by combiner)
    """

    def __init__(self):
        """Initialize coordinator and all sub-agents."""
        # Initialize agent runners (contains all 4 agents)
        self.agent_runners = AgentRunners()

        # Build LangGraph workflow with native parallelism
        self.graph = GraphBuilder.build_analysis_graph(self.agent_runners)

        # Initialize multi-frame handler
        self.multi_frame_handler = MultiFrameHandler(self.analyze_frame)

        logger.info(
            "ℹ️ CoordinatorAgent initialized with LangGraph native parallelism (4 agents)"
        )

    def analyze_frame(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[Literal["vision", "ocr", "detection", "geolocation"]]
        | None = None,
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
        return self.multi_frame_handler.analyze_multi_frame(
            frames, enable_context_accumulation
        )
