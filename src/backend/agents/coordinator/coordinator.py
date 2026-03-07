"""
Coordinator Agent - Main Orchestrator
Single Responsibility: Coordinate multi-agent analysis using LangGraph
Max: 150 lines (thin orchestrator - delegates to modules)

Military-Grade OSINT Analysis with 12 parallel agents:

Original CIA-Level (7):
- vision, ocr, detection, geolocation
- face_analysis, forensic_analysis, context_intel

Military Intelligence Block 1 (5):
- vehicle_detection, weapon_detection, crowd_analysis
- shadow_analysis, infrastructure_analysis
"""

import logging
import uuid
from collections.abc import Generator
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

from ...utils.image_utils import verify_image_size
from .agent_runners import AgentRunners
from .chat_graph import ChatGraphBuilder
from .graph_builder import GraphBuilder
from .multi_frame_handler import MultiFrameHandler
from .state import DEFAULT_AGENTS, AgentType, AnalysisState

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Coordinator that orchestrates all 12 analysis agents using LangGraph.

    This is a thin orchestrator - actual logic is delegated to specialized modules:
    - AgentRunners: Execute individual agents (12 agents)
    - GraphBuilder: Build LangGraph workflow with 12-way parallelism
    - MultiFrameHandler: Handle multi-frame analysis
    - ResultCombiner: Combine agent results (called by graph)
    - ReportGenerator: Generate text reports (called by combiner)
    """

    def __init__(self):
        """Initialize coordinator and all sub-agents."""
        # Initialize agent runners (contains all 12 agents)
        self.agent_runners = AgentRunners()

        # LangGraph checkpointer for state persistence across invocations
        self.checkpointer = InMemorySaver()

        # Build LangGraph workflow with checkpointer for thread-level state persistence
        self.graph = GraphBuilder.build_analysis_graph(
            self.agent_runners,
            checkpointer=self.checkpointer,
        )

        # Build chat graph with same checkpointer for shared thread state
        self.chat_graph = ChatGraphBuilder(checkpointer=self.checkpointer)

        # Initialize multi-frame handler
        self.multi_frame_handler = MultiFrameHandler(self.analyze_frame)

        logger.info(
            "CoordinatorAgent initialized with LangGraph checkpointer (7 agents + chat graph)"
        )

    def analyze_frame(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[AgentType] | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute full analysis workflow on image frame with 7 parallel agents.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis
            agents_to_run: List of agents to run (None = all enabled agents)
            thread_id: Session thread ID for LangGraph state persistence.
                If None, generates a unique ID (stateless single-shot analysis).

        Returns:
            Dict with both JSON and text reports (CIA-level intelligence)
        """
        try:
            # Verify image size ONCE (before distributing to agents)
            verify_image_size(image_base64, "COORDINATOR")

            # Generate thread_id if not provided (single-shot analysis)
            if thread_id is None:
                thread_id = str(uuid.uuid4())

            # Default to all enabled agents if not specified
            if agents_to_run is None:
                agents_to_run = DEFAULT_AGENTS.copy()

            logger.info(
                "Starting coordinated frame analysis (%s agents, thread=%s)",
                len(agents_to_run),
                thread_id[:8],
            )

            # Initialize state with all 12 result slots
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
                # Military Intelligence Block 1
                "vehicle_detection_result": None,
                "weapon_detection_result": None,
                "crowd_analysis_result": None,
                "shadow_analysis_result": None,
                "infrastructure_analysis_result": None,
                # Final output
                "final_report": None,
            }

            # LangGraph config with thread_id for checkpointer state persistence
            config: RunnableConfig = {
                "configurable": {"thread_id": thread_id},
            }

            # Execute graph (LangGraph handles parallelism natively)
            final_state = self.graph.invoke(initial_state, config=config)

            # Return final report
            return final_state.get(
                "final_report",
                {
                    "json": {"status": "error", "message": "No report generated"},
                    "text": "Error: Analysis workflow failed",
                },
            )

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Coordinated analysis failed: %s", e)
            return {
                "json": {"status": "error", "error": str(e)},
                "text": f"Error en análisis: {e!s}",
            }

    def analyze_frame_stream(
        self,
        image_base64: str,
        context: str = "",
        agents_to_run: list[AgentType] | None = None,
        thread_id: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream analysis results as each agent completes.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis
            agents_to_run: List of agents to run (None = all enabled agents)
            thread_id: Session thread ID for LangGraph state persistence.
                If None, generates a unique ID (stateless single-shot analysis).

        Yields per-agent update dicts as they finish:
            {"event": "agent_update", "agent": "vision", "result": {...}}
            {"event": "agent_update", "agent": "ocr", "result": {...}}
            ...
            {"event": "complete", "final_report": {"json": {...}, "text": "..."}}
        """
        try:
            verify_image_size(image_base64, "COORDINATOR")

            if thread_id is None:
                thread_id = str(uuid.uuid4())

            if agents_to_run is None:
                agents_to_run = DEFAULT_AGENTS.copy()

            logger.info(
                "Starting streaming frame analysis (%s agents, thread=%s)",
                len(agents_to_run),
                thread_id[:8],
            )

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
                # Military Intelligence Block 1
                "vehicle_detection_result": None,
                "weapon_detection_result": None,
                "crowd_analysis_result": None,
                "shadow_analysis_result": None,
                "infrastructure_analysis_result": None,
                # Final output
                "final_report": None,
            }

            # LangGraph config with thread_id for checkpointer state persistence
            config: RunnableConfig = {
                "configurable": {"thread_id": thread_id},
            }

            for update in self.graph.stream(initial_state, config=config, stream_mode="updates"):
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

    def chat(
        self,
        user_message: str,
        image_base64: str = "",
        analysis_summary: str = "",
        thread_id: str = "",
    ) -> str:
        """
        Conversational chat with LangGraph message history.

        Uses the chat graph with MessagesState for proper multi-turn
        HumanMessage/AIMessage alternation. The checkpointer maintains
        conversation history per thread_id.

        Args:
            user_message: The user's question.
            image_base64: Base64 image (only needed on first call per session).
            analysis_summary: Previous analysis results (only on first call).
            thread_id: Session thread ID for conversation persistence.

        Returns:
            The assistant's response text.
        """
        try:
            return self.chat_graph.chat(
                user_message=user_message,
                image_base64=image_base64,
                analysis_summary=analysis_summary,
                thread_id=thread_id,
            )
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Chat graph error: %s", e)
            return f"Error en el chat: {e!s}"
