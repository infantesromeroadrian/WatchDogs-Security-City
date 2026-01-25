"""
LangGraph Construction
Single Responsibility: Build and configure the LangGraph workflow
Max: 150 lines

CIA-Level OSINT Analysis Graph with 7 parallel agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .agent_runners import AgentRunners
from .result_combiner import ResultCombiner
from .state import AnalysisState

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Constructs LangGraph workflow with parallel agent execution."""

    @staticmethod
    def build_analysis_graph(agent_runners: AgentRunners) -> CompiledStateGraph:
        """
        Build the LangGraph workflow with native parallel execution.

        Creates a graph where all 6 agents run in parallel, then converge
        to combine results into a comprehensive intelligence report.

        Graph structure:
                           ┌─────────────┐
                           │    START    │
                           └──────┬──────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │           │         │         │           │
            ▼           ▼         ▼         ▼           ▼
        ┌───────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌───────────────┐
        │vision │ │   ocr   │ │detection│ │geolocation│ │ face_analysis │
        └───┬───┘ └────┬────┘ └────┬────┘ └─────┬─────┘ └───────┬───────┘
            │          │           │            │               │
            └──────────┴─────┬─────┴────────────┴───────────────┘
                             │                                  │
                             ▼                                  ▼
                        ┌─────────────────────────────────────────┐
                        │               combine                   │
                        └───────────────────┬─────────────────────┘
                                            │
                                            ▼
                                       ┌─────────┐
                                       │   END   │
                                       └─────────┘

        Plus forensic_analysis agent running in parallel.

        Args:
            agent_runners: Instance of AgentRunners with initialized agents

        Returns:
            Compiled StateGraph ready for execution
        """
        logger.info("🔧 Building LangGraph workflow with 6 parallel agents...")

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

        # Define edges with NATIVE PARALLELISM
        # All SEVEN agents run in parallel from START
        workflow.add_edge(START, "vision")
        workflow.add_edge(START, "ocr")
        workflow.add_edge(START, "detection")
        workflow.add_edge(START, "geolocation")
        workflow.add_edge(START, "face_analysis")
        workflow.add_edge(START, "forensic_analysis")
        workflow.add_edge(START, "context_intel")

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

        logger.info("✅ LangGraph workflow built with 7 parallel agents (CIA-level OSINT)")

        return workflow.compile()
