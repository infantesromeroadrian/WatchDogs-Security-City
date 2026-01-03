"""
Agent Execution Functions
Single Responsibility: Run individual agents and handle their errors
Max: 200 lines
"""

import logging
from typing import Dict, Any

from ..vision_agent import VisionAgent
from ..ocr_agent import OCRAgent
from ..detection_agent import DetectionAgent
from ..geolocation_agent import GeolocationAgent
from ...services.geolocation_service import GeolocationService
from .state import AnalysisState

logger = logging.getLogger(__name__)


class AgentRunners:
    """Encapsulates execution logic for all analysis agents"""

    def __init__(self):
        """Initialize all agents"""
        self.vision_agent = VisionAgent()
        self.ocr_agent = OCRAgent()
        self.detection_agent = DetectionAgent()
        self.geolocation_agent = GeolocationAgent()
        self.geolocation_service = GeolocationService()

    def run_vision_agent(self, state: AnalysisState) -> Dict[str, Any]:
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

    def run_ocr_agent(self, state: AnalysisState) -> Dict[str, Any]:
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

    def run_detection_agent(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Execute Detection Agent (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with detection_result key
        """
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

    def run_geolocation_agent(self, state: AnalysisState) -> Dict[str, Any]:
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
            result = self.geolocation_agent.analyze(
                state["image_base64"], state.get("context", "")
            )

            # Enrich with geocoding and map generation
            enriched_result = self.geolocation_service.enrich_geolocation_result(result)

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
