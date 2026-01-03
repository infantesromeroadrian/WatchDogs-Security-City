"""
LangGraph Construction
Single Responsibility: Build and configure the LangGraph workflow
Max: 150 lines
"""

import logging
from langgraph.graph import StateGraph, START, END

from .state import AnalysisState
from .agent_runners import AgentRunners
from .result_combiner import ResultCombiner

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Constructs LangGraph workflow with parallel agent execution"""

    @staticmethod
    def build_analysis_graph(agent_runners: AgentRunners) -> StateGraph:
        """
        Build the LangGraph workflow with native parallel execution.

        Creates a graph where all 4 agents (vision, ocr, detection, geolocation)
        run in parallel, then converge to combine results.

        Args:
            agent_runners: Instance of AgentRunners with initialized agents

        Returns:
            Compiled StateGraph ready for execution
        """
        logger.info("🔧 Building LangGraph workflow...")

        # Create graph with AnalysisState schema
        workflow = StateGraph(AnalysisState)

        # Add agent nodes (separate nodes enable native parallelism)
        workflow.add_node("vision", agent_runners.run_vision_agent)
        workflow.add_node("ocr", agent_runners.run_ocr_agent)
        workflow.add_node("detection", agent_runners.run_detection_agent)
        workflow.add_node("geolocation", agent_runners.run_geolocation_agent)

        # Add result combiner node
        workflow.add_node("combine", ResultCombiner.combine_results)

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

        logger.info("✅ LangGraph workflow built with 4 parallel agents")

        return workflow.compile()
