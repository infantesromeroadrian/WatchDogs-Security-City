"""
LangGraph Construction
Single Responsibility: Build and configure the LangGraph workflow
Max: 150 lines

CIA-Level OSINT Analysis Graph with 7 parallel agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging
from collections.abc import Sequence

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .agent_runners import AgentRunners
from .result_combiner import ResultCombiner
from .state import AnalysisState

logger = logging.getLogger(__name__)


def route_to_enabled_agents(state: AnalysisState) -> Sequence[str]:
    """Route only to agents configured in agents_to_run."""
    return state["agents_to_run"]


class GraphBuilder:
    """Constructs LangGraph workflow with parallel agent execution."""

    @staticmethod
    def build_analysis_graph(
        agent_runners: AgentRunners,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> CompiledStateGraph:
        """
        Build the LangGraph workflow with native parallel execution.

        Creates a graph where enabled agents run in parallel, then converge
        to combine results into a comprehensive intelligence report.

        Graph structure:
                           ┌─────────────┐
                           │    START    │
                           └──────┬──────┘
                                  │
                                  ▼
                     route_to_enabled_agents(state)
                                  │
                                  ▼
                    [enabled agent nodes in parallel]
                                  │
                                  ▼
                           ┌─────────────┐
                           │   combine   │
                           └──────┬──────┘
                                  │
                                  ▼
                               ┌─────┐
                               │ END │
                               └─────┘

        Args:
            agent_runners: Instance of AgentRunners with initialized agents

        Returns:
            Compiled StateGraph ready for execution
        """
        logger.info("🔧 Building LangGraph workflow with conditional parallel routing...")

        # Create graph with AnalysisState schema
        workflow = StateGraph(AnalysisState)

        # Add agent nodes (separate nodes enable native parallelism)
        # Original 4 agents
        workflow.add_node("vision", agent_runners.run_vision_agent)
        workflow.add_node("ocr", agent_runners.run_ocr_agent)
        workflow.add_node("detection", agent_runners.run_detection_agent)
        workflow.add_node("geolocation", agent_runners.run_geolocation_agent)
        # CIA-level agents
        workflow.add_node("face_analysis", agent_runners.run_face_analysis_agent)
        workflow.add_node("forensic_analysis", agent_runners.run_forensic_analysis_agent)
        workflow.add_node("context_intel", agent_runners.run_context_intel_agent)

        # Add result combiner node
        workflow.add_node("combine", ResultCombiner.combine_results)

        # Define edges with conditional native parallelism
        workflow.add_conditional_edges(START, route_to_enabled_agents)

        # All agents converge to combine node
        workflow.add_edge("vision", "combine")
        workflow.add_edge("ocr", "combine")
        workflow.add_edge("detection", "combine")
        workflow.add_edge("geolocation", "combine")
        workflow.add_edge("face_analysis", "combine")
        workflow.add_edge("forensic_analysis", "combine")
        workflow.add_edge("context_intel", "combine")

        # Combine to END
        workflow.add_edge("combine", END)

        if checkpointer:
            logger.info(
                "✅ LangGraph workflow built with checkpointer + conditional parallel agents"
            )
        else:
            logger.info(
                "✅ LangGraph workflow built with conditional parallel agents (no checkpointer)"
            )

        return workflow.compile(checkpointer=checkpointer)
