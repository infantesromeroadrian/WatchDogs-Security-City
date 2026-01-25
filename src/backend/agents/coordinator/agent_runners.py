"""
Agent Execution Functions
Single Responsibility: Run individual agents and handle their errors
Max: 350 lines

CIA-Level OSINT Analysis with 7 parallel agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
"""

import logging
from typing import Any

from ...services.geolocation_service import GeolocationService
from ...utils.timeout_utils import TimeoutError as AgentTimeoutError
from ..context_intel import ContextIntelAgent
from ..detection_agent import DetectionAgent
from ..face_analysis import FaceAnalysisAgent
from ..forensic_analysis import ForensicAnalysisAgent
from ..geolocation_agent import GeolocationAgent
from ..ocr_agent import OCRAgent
from ..vision_agent import VisionAgent
from .state import AnalysisState

logger = logging.getLogger(__name__)


class AgentRunners:
    """Encapsulates execution logic for all 7 analysis agents."""

    def __init__(self):
        """Initialize all agents."""
        # Original 4 agents
        self.vision_agent = VisionAgent()
        self.ocr_agent = OCRAgent()
        self.detection_agent = DetectionAgent()
        self.geolocation_agent = GeolocationAgent()
        self.geolocation_service = GeolocationService()
        # CIA-level agents
        self.face_analysis_agent = FaceAnalysisAgent()
        self.forensic_analysis_agent = ForensicAnalysisAgent()
        self.context_intel_agent = ContextIntelAgent()

    def run_vision_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Vision Agent (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with vision_result key
        """
        if "vision" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
            logger.info("⏭️ Skipping Vision Agent (not in agents_to_run)")
            return {"vision_result": None}

        try:
            logger.info("🔍 Running Vision Agent (native parallel)...")
            result = self.vision_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"vision_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Vision agent timeout: {e}")
            return {
                "vision_result": {
                    "agent": "vision",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Vision analysis timed out - partial results unavailable",
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"❌ Vision agent error: {e}")
            return {
                "vision_result": {
                    "agent": "vision",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Vision analysis failed",
                }
            }

    def run_ocr_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute OCR Agent (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with ocr_result key
        """
        if "ocr" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
            logger.info("⏭️ Skipping OCR Agent (not in agents_to_run)")
            return {"ocr_result": None}

        try:
            logger.info("📝 Running OCR Agent (native parallel)...")
            result = self.ocr_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"ocr_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ OCR agent timeout: {e}")
            return {
                "ocr_result": {
                    "agent": "ocr",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "OCR extraction timed out",
                    "has_text": False,
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
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

    def run_detection_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Detection Agent (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with detection_result key
        """
        if "detection" not in state.get("agents_to_run", ["vision", "ocr", "detection"]):
            logger.info("⏭️ Skipping Detection Agent (not in agents_to_run)")
            return {"detection_result": None}

        try:
            logger.info("🎯 Running Detection Agent (native parallel)...")
            result = self.detection_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"detection_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Detection agent timeout: {e}")
            return {
                "detection_result": {
                    "agent": "detection",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Detection analysis timed out",
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"❌ Detection agent error: {e}")
            return {
                "detection_result": {
                    "agent": "detection",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Detection analysis failed",
                }
            }

    def run_geolocation_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Geolocation Agent with enrichment (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with geolocation_result key (enriched with geocoding/maps)
        """
        if "geolocation" not in state.get(
            "agents_to_run", ["vision", "ocr", "detection", "geolocation"]
        ):
            logger.info("⏭️ Skipping Geolocation Agent (not in agents_to_run)")
            return {"geolocation_result": None}

        try:
            logger.info("🌍 Running Geolocation Agent (native parallel)...")
            result = self.geolocation_agent.analyze(state["image_base64"], state.get("context", ""))

            # Enrich with geocoding and map generation
            enriched_result = self.geolocation_service.enrich_geolocation_result(result)

            return {"geolocation_result": enriched_result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Geolocation agent timeout: {e}")
            return {
                "geolocation_result": {
                    "agent": "geolocation",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Geolocation analysis timed out - location inference unavailable",
                    "location": {},
                    "coordinates": None,
                    "confidence": "unknown",
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
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

    def run_face_analysis_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Face Analysis Agent (separate node for native parallelism).

        CIA-level person identification including:
        - Facial features and demographics
        - Distinctive marks (scars, tattoos, piercings)
        - Clothing and accessories
        - Behavioral context

        Args:
            state: Current analysis state

        Returns:
            Dict with face_analysis_result key
        """
        if "face_analysis" not in state.get("agents_to_run", []):
            logger.info("⏭️ Skipping Face Analysis Agent (not in agents_to_run)")
            return {"face_analysis_result": None}

        try:
            logger.info("👤 Running Face Analysis Agent (native parallel)...")
            result = self.face_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"face_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Face analysis agent timeout: {e}")
            return {
                "face_analysis_result": {
                    "agent": "face_analysis",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Face analysis timed out",
                    "detection_summary": {
                        "total_persons": 0,
                        "faces_visible": 0,
                        "partial_visibility": 0,
                        "identification_quality": "unknown",
                    },
                    "persons": [],
                    "person_count": 0,
                    "most_distinctive_features": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"❌ Face analysis agent error: {e}")
            return {
                "face_analysis_result": {
                    "agent": "face_analysis",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Face analysis failed",
                    "detection_summary": {
                        "total_persons": 0,
                        "faces_visible": 0,
                        "partial_visibility": 0,
                        "identification_quality": "unknown",
                    },
                    "persons": [],
                    "person_count": 0,
                    "most_distinctive_features": [],
                    "limitations": [str(e)],
                }
            }

    def run_forensic_analysis_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Forensic Analysis Agent (separate node for native parallelism).

        CIA-level image authenticity verification including:
        - Manipulation detection (copy-paste, splicing, AI-generated)
        - Compression artifact analysis
        - Lighting/shadow consistency
        - Perspective/geometry verification

        Args:
            state: Current analysis state

        Returns:
            Dict with forensic_analysis_result key
        """
        if "forensic_analysis" not in state.get("agents_to_run", []):
            logger.info("⏭️ Skipping Forensic Analysis Agent (not in agents_to_run)")
            return {"forensic_analysis_result": None}

        try:
            logger.info("🔬 Running Forensic Analysis Agent (native parallel)...")
            result = self.forensic_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"forensic_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Forensic analysis agent timeout: {e}")
            return {
                "forensic_analysis_result": {
                    "agent": "forensic_analysis",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Forensic analysis timed out",
                    "verdict": {
                        "classification": "indeterminada",
                        "confidence": "muy baja",
                        "justification": "Analysis timed out",
                    },
                    "integrity_score": None,
                    "anomalies": {},
                    "suspicious_regions": [],
                    "evidence_chain": [],
                    "manipulation_hypothesis": None,
                    "image_quality": {"limiting_factors": ["timeout"]},
                    "recommendations": [],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"❌ Forensic analysis agent error: {e}")
            return {
                "forensic_analysis_result": {
                    "agent": "forensic_analysis",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Forensic analysis failed",
                    "verdict": {
                        "classification": "indeterminada",
                        "confidence": "muy baja",
                        "justification": f"Error: {e}",
                    },
                    "integrity_score": None,
                    "anomalies": {},
                    "suspicious_regions": [],
                    "evidence_chain": [],
                    "manipulation_hypothesis": None,
                    "image_quality": {"limiting_factors": [str(e)]},
                    "recommendations": [],
                }
            }

    def run_context_intel_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Context Intelligence Agent (separate node for native parallelism).

        CIA-level temporal and cultural inference including:
        - Time of day, day of week, season, era estimation
        - Cultural and socioeconomic indicators
        - Event classification
        - Environmental conditions
        - Anomaly detection

        Args:
            state: Current analysis state

        Returns:
            Dict with context_intel_result key
        """
        if "context_intel" not in state.get("agents_to_run", []):
            logger.info("⏭️ Skipping Context Intel Agent (not in agents_to_run)")
            return {"context_intel_result": None}

        try:
            logger.info("🧠 Running Context Intel Agent (native parallel)...")
            result = self.context_intel_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"context_intel_result": result}
        except AgentTimeoutError as e:
            logger.warning(f"⏱️ Context intel agent timeout: {e}")
            return {
                "context_intel_result": {
                    "agent": "context_intel",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Context intel analysis timed out",
                    "executive_summary": None,
                    "temporal_analysis": {},
                    "sociocultural_analysis": {},
                    "event_classification": {},
                    "environmental_conditions": {},
                    "anomalies": [],
                    "key_inferences": [],
                    "limitations": ["Analysis timed out"],
                    "open_questions": [],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error(f"❌ Context intel agent error: {e}")
            return {
                "context_intel_result": {
                    "agent": "context_intel",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Context intel analysis failed",
                    "executive_summary": None,
                    "temporal_analysis": {},
                    "sociocultural_analysis": {},
                    "event_classification": {},
                    "environmental_conditions": {},
                    "anomalies": [],
                    "key_inferences": [],
                    "limitations": [str(e)],
                    "open_questions": [],
                }
            }
