"""Multi-frame orchestration with sequential and Send-based parallel modes."""

import logging
import operator
from collections.abc import Callable
from typing import Annotated, Any, NotRequired, TypedDict, cast

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .geolocation_combiner import GeolocationCombiner
from .multi_frame_reporter import MultiFrameReporter

logger = logging.getLogger(__name__)


class FrameWorkerState(TypedDict):
    """State for a single frame worker spawned by Send API."""

    frame_base64: str
    context: str
    frame_index: int
    description: str


class MultiFrameGraphState(TypedDict):
    """State for parallel multi-frame graph execution."""

    frames: list[dict[str, str]]
    individual_results: Annotated[list[dict[str, Any]], operator.add]
    combined_geolocation: NotRequired[dict[str, Any]]
    summary: NotRequired[str]


class MultiFrameHandler:
    """Handle multi-frame analysis with optional context accumulation."""

    def __init__(
        self,
        single_frame_analyzer: Callable[[str, str], dict[str, Any]],
    ) -> None:
        """Initialize handler and compile parallel graph.

        Args:
            single_frame_analyzer: Callable for single-frame analysis.
        """
        self.single_frame_analyzer = single_frame_analyzer
        analyzer = self.single_frame_analyzer

        def analyze_frame_worker(state: FrameWorkerState) -> dict[str, list[dict[str, Any]]]:
            """Analyze one frame in an isolated Send worker."""
            result = analyzer(state["frame_base64"], state["context"])
            return {
                "individual_results": [
                    {
                        "frame_index": state["frame_index"] + 1,
                        "description": state["description"],
                        "result": result,
                    }
                ]
            }

        def synthesize_results(
            state: MultiFrameGraphState,
        ) -> dict[str, Any]:
            """Combine worker outputs into final multi-frame artifacts."""
            sorted_results = sorted(
                state["individual_results"],
                key=lambda result_data: int(result_data["frame_index"]),
            )
            combined_geolocation = GeolocationCombiner.combine_results(sorted_results)
            summary = MultiFrameReporter.generate_summary(sorted_results, combined_geolocation)
            return {
                "combined_geolocation": combined_geolocation,
                "summary": summary,
            }

        def dispatch_frames(state: MultiFrameGraphState) -> list[Send]:
            """Generate one Send instruction per independent frame."""
            frames = state["frames"]
            return [
                Send(
                    "analyze_frame_worker",
                    {
                        "frame_base64": frame_data.get("frame", ""),
                        "context": frame_data.get("description", f"Frame {idx + 1}"),
                        "frame_index": idx,
                        "description": frame_data.get("description", f"Frame {idx + 1}"),
                    },
                )
                for idx, frame_data in enumerate(frames)
            ]

        workflow = StateGraph(MultiFrameGraphState)
        workflow.add_node("analyze_frame_worker", analyze_frame_worker)
        workflow.add_node("synthesize", synthesize_results)
        workflow.add_conditional_edges(START, dispatch_frames, ["analyze_frame_worker"])
        workflow.add_edge("analyze_frame_worker", "synthesize")
        workflow.add_edge("synthesize", END)
        self.parallel_graph: Any = workflow.compile()

    def analyze_multi_frame(
        self,
        frames: list[dict[str, str]],
        enable_context_accumulation: bool = True,
    ) -> dict[str, Any]:
        """Route analysis to sequential or parallel mode.

        Args:
            frames: Frames with `frame` and optional `description`.
            enable_context_accumulation: Use sequential clue accumulation mode.

        Returns:
            Unified payload for frontend rendering.
        """
        logger.info(
            "Starting multi-frame analysis (%s frames, context=%s)",
            len(frames),
            "ON" if enable_context_accumulation else "OFF",
        )
        if enable_context_accumulation:
            return self._analyze_sequential(frames, enable_context_accumulation)
        return self._analyze_parallel(frames, enable_context_accumulation)

    def _analyze_sequential(
        self,
        frames: list[dict[str, str]],
        enable_context_accumulation: bool,
    ) -> dict[str, Any]:
        """Analyze frames sequentially with clue accumulation between steps."""
        individual_results: list[dict[str, Any]] = []
        accumulated_geolocation_clues: list[str] = []
        accumulated_ocr_texts: list[str] = []
        accumulated_detections: list[str] = []

        try:
            for idx, frame_data in enumerate(frames):
                frame_base64 = frame_data.get("frame", "")
                description = frame_data.get("description", f"Frame {idx + 1}")
                context = self._build_frame_context(
                    idx=idx,
                    total_frames=len(frames),
                    description=description,
                    enable_context=enable_context_accumulation,
                    geo_clues=accumulated_geolocation_clues,
                    ocr_texts=accumulated_ocr_texts,
                    detections=accumulated_detections,
                )
                logger.info("Analyzing frame %s/%s: %s", idx + 1, len(frames), description)
                result = self.single_frame_analyzer(frame_base64, context)
                self._extract_clues_from_result(
                    result=result,
                    idx=idx,
                    geo_clues=accumulated_geolocation_clues,
                    ocr_texts=accumulated_ocr_texts,
                    detections=accumulated_detections,
                )
                individual_results.append(
                    {
                        "frame_index": idx + 1,
                        "description": description,
                        "result": result,
                    }
                )
            combined_geolocation = self._combine_geolocation_results(individual_results)
            summary = self._generate_multi_frame_summary(individual_results, combined_geolocation)
            logger.info("Sequential multi-frame analysis complete (%s frames)", len(frames))
            return self._build_response(
                summary=summary,
                individual_results=individual_results,
                combined_geolocation=combined_geolocation,
                total_frames=len(frames),
                context_accumulation_enabled=enable_context_accumulation,
            )
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            logger.error("Sequential multi-frame analysis failed: %s", exc)
            return self._build_error_response(exc, individual_results, len(frames))

    def _analyze_parallel(
        self,
        frames: list[dict[str, str]],
        enable_context_accumulation: bool,
    ) -> dict[str, Any]:
        """Analyze frames in parallel using LangGraph Send workers."""
        try:
            graph_input: MultiFrameGraphState = {
                "frames": frames,
                "individual_results": [],
            }
            graph = cast(Any, self.parallel_graph)
            final_state = cast(dict[str, Any], graph.invoke(graph_input))
            individual_results = sorted(
                final_state.get("individual_results", []),
                key=lambda result_data: int(result_data["frame_index"]),
            )
            combined_geolocation = final_state.get("combined_geolocation", {})
            summary = final_state.get("summary", "")
            logger.info("Parallel multi-frame analysis complete (%s frames)", len(frames))
            return self._build_response(
                summary=summary,
                individual_results=individual_results,
                combined_geolocation=combined_geolocation,
                total_frames=len(frames),
                context_accumulation_enabled=enable_context_accumulation,
            )
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            logger.error("Parallel multi-frame analysis failed: %s", exc)
            return self._build_error_response(exc, [], len(frames))

    @staticmethod
    def _build_response(
        summary: str,
        individual_results: list[dict[str, Any]],
        combined_geolocation: dict[str, Any],
        total_frames: int,
        context_accumulation_enabled: bool,
    ) -> dict[str, Any]:
        """Build frontend-compatible response payload.

        Args:
            summary: Human-readable report.
            individual_results: Per-frame analysis results.
            combined_geolocation: Combined geolocation artifact.
            total_frames: Number of analyzed frames.
            context_accumulation_enabled: Execution mode marker.

        Returns:
            Response with `text` and structured `json` keys.
        """
        return {
            "text": summary,
            "json": {
                "individual_results": individual_results,
                "combined_geolocation": combined_geolocation,
                "total_frames": total_frames,
                "context_accumulation_enabled": context_accumulation_enabled,
            },
        }

    @staticmethod
    def _build_error_response(
        error: Exception,
        individual_results: list[dict[str, Any]],
        total_frames: int,
    ) -> dict[str, Any]:
        """Build error payload with partial results when available."""
        error_text = f"⚠️ Error en análisis multi-frame: {error!s}"
        return {
            "text": error_text,
            "json": {
                "error": str(error),
                "individual_results": individual_results,
                "combined_geolocation": {},
                "total_frames": total_frames,
                "context_accumulation_enabled": False,
            },
        }

    @staticmethod
    def _build_frame_context(
        idx: int,
        total_frames: int,
        description: str,
        enable_context: bool,
        geo_clues: list[str],
        ocr_texts: list[str],
        detections: list[str],
    ) -> str:
        """Build contextual prompt from previous frame clues.

        Args:
            idx: Current frame index (zero-based).
            total_frames: Number of frames.
            description: Current frame description.
            enable_context: Whether to include accumulated clues.
            geo_clues: Accumulated geolocation clues.
            ocr_texts: Accumulated OCR findings.
            detections: Accumulated detection findings.

        Returns:
            Context string for frame analysis.
        """
        context = f"Imagen {idx + 1}/{total_frames}: {description}"
        if enable_context and idx > 0:
            context += "\n\n🔍 PISTAS ACUMULADAS DE IMÁGENES ANTERIORES:\n"
            if geo_clues:
                context += "\n📍 Geolocalización:\n"
                context += "\n".join(geo_clues[-10:])
            if ocr_texts:
                context += "\n\n📝 Textos encontrados:\n"
                context += "\n".join(ocr_texts[-5:])
            if detections:
                context += "\n\n🎯 Objetos detectados:\n"
                context += "\n".join(detections[-5:])
        return context

    @staticmethod
    def _extract_clues_from_result(
        result: dict[str, Any],
        idx: int,
        geo_clues: list[str],
        ocr_texts: list[str],
        detections: list[str],
    ) -> None:
        """Extract clues from frame result for context accumulation.

        Args:
            result: Raw analyzer output.
            idx: Current frame index (zero-based).
            geo_clues: Mutable geolocation clue list.
            ocr_texts: Mutable OCR clue list.
            detections: Mutable detection clue list.
        """
        json_result = result.get("json", {})
        agents = json_result.get("agents", {})

        geolocation = agents.get("geolocation", {})
        if geolocation.get("key_clues"):
            geo_clues.extend(geolocation["key_clues"])

        ocr = agents.get("ocr", {})
        if ocr.get("status") == "success" and ocr.get("has_text"):
            analysis = ocr.get("analysis", "")
            if analysis and len(analysis) > 10:
                ocr_texts.append(f"Frame {idx + 1}: {analysis[:200]}")

        detection = agents.get("detection", {})
        if detection.get("status") == "success":
            analysis = detection.get("analysis", "")
            if analysis and len(analysis) > 10:
                detections.append(f"Frame {idx + 1}: {analysis[:150]}")

    @staticmethod
    def _combine_geolocation_results(individual_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Combine geolocation results from multiple frames.

        Args:
            individual_results: Per-frame analysis outputs.

        Returns:
            Combined geolocation payload.
        """
        return cast(dict[str, Any], GeolocationCombiner.combine_results(individual_results))

    @staticmethod
    def _generate_multi_frame_summary(
        individual_results: list[dict[str, Any]],
        combined_geolocation: dict[str, Any],
    ) -> str:
        """Generate multi-frame summary for operators.

        Args:
            individual_results: Per-frame analysis outputs.
            combined_geolocation: Combined geolocation payload.

        Returns:
            Human-readable report.
        """
        return cast(
            str,
            MultiFrameReporter.generate_summary(individual_results, combined_geolocation),
        )
