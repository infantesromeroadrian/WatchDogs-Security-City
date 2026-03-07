"""
Agent Execution Functions
Single Responsibility: Run individual agents and handle their errors

Military-Grade OSINT Analysis with 16 parallel agents:
- vision, ocr, detection, geolocation (original)
- face_analysis, forensic_analysis, context_intel (CIA-level)
- vehicle_detection, weapon_detection, crowd_analysis,
  shadow_analysis, infrastructure_analysis (military intel B1)
- temporal_comparison, night_vision (military intel B2)
- nato_symbology, multi_monitor (military intel B3)
"""

import logging
from typing import Any

from ...services.geolocation_service import GeolocationService
from ...utils.timeout_utils import TimeoutError as AgentTimeoutError
from ..context_intel import ContextIntelAgent
from ..crowd_analysis import CrowdAnalysisAgent
from ..detection_agent import DetectionAgent
from ..face_analysis import FaceAnalysisAgent
from ..forensic_analysis import ForensicAnalysisAgent
from ..geolocation_agent import GeolocationAgent
from ..infrastructure_analysis import InfrastructureAnalysisAgent
from ..multi_monitor import MultiMonitorAgent
from ..nato_symbology import NATOSymbologyAgent
from ..night_vision import NightVisionAgent
from ..ocr_agent import OCRAgent
from ..shadow_analysis import ShadowAnalysisAgent
from ..temporal_comparison import TemporalComparisonAgent
from ..vehicle_detection import VehicleDetectionAgent
from ..vision_agent import VisionAgent
from ..weapon_detection import WeaponDetectionAgent
from .state import AnalysisState

logger = logging.getLogger(__name__)


class AgentRunners:
    """Encapsulates execution logic for all 16 analysis agents."""

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
        # Military Intelligence Block 1
        self.vehicle_detection_agent = VehicleDetectionAgent()
        self.weapon_detection_agent = WeaponDetectionAgent()
        self.crowd_analysis_agent = CrowdAnalysisAgent()
        self.shadow_analysis_agent = ShadowAnalysisAgent()
        self.infrastructure_analysis_agent = InfrastructureAnalysisAgent()
        # Military Intelligence Block 2
        self.temporal_comparison_agent = TemporalComparisonAgent()
        self.night_vision_agent = NightVisionAgent()
        # Military Intelligence Block 3
        self.nato_symbology_agent = NATOSymbologyAgent()
        self.multi_monitor_agent = MultiMonitorAgent()

    def run_vision_agent(self, state: AnalysisState) -> dict[str, Any]:
        """
        Execute Vision Agent (separate node for native parallelism).

        Args:
            state: Current analysis state

        Returns:
            Dict with vision_result key
        """
        try:
            logger.info("🔍 Running Vision Agent (native parallel)...")
            result = self.vision_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"vision_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Vision agent timeout: %s", e)
            return {
                "vision_result": {
                    "agent": "vision",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Vision analysis timed out - partial results unavailable",
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Vision agent error: %s", e)
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
        try:
            logger.info("📝 Running OCR Agent (native parallel)...")
            result = self.ocr_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"ocr_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ OCR agent timeout: %s", e)
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
            logger.error("❌ OCR agent error: %s", e)
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
        try:
            logger.info("🎯 Running Detection Agent (native parallel)...")
            result = self.detection_agent.analyze(state["image_base64"], state.get("context", ""))
            return {"detection_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Detection agent timeout: %s", e)
            return {
                "detection_result": {
                    "agent": "detection",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Detection analysis timed out",
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Detection agent error: %s", e)
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
        try:
            logger.info("🌍 Running Geolocation Agent (native parallel)...")
            result = self.geolocation_agent.analyze(state["image_base64"], state.get("context", ""))

            # Enrich with geocoding and map generation
            enriched_result = self.geolocation_service.enrich_geolocation_result(result)

            return {"geolocation_result": enriched_result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Geolocation agent timeout: %s", e)
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
            logger.error("❌ Geolocation agent error: %s", e)
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
        try:
            logger.info("👤 Running Face Analysis Agent (native parallel)...")
            result = self.face_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"face_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Face analysis agent timeout: %s", e)
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
            logger.error("❌ Face analysis agent error: %s", e)
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
        try:
            logger.info("🔬 Running Forensic Analysis Agent (native parallel)...")
            result = self.forensic_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"forensic_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Forensic analysis agent timeout: %s", e)
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
            logger.error("❌ Forensic analysis agent error: %s", e)
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
        try:
            logger.info("🧠 Running Context Intel Agent (native parallel)...")
            result = self.context_intel_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"context_intel_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Context intel agent timeout: %s", e)
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
            logger.error("❌ Context intel agent error: %s", e)
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

    # =========================================================================
    # MILITARY INTELLIGENCE BLOCK 1 — 5 new agents
    # =========================================================================

    def run_vehicle_detection_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Vehicle Detection & ALPR Agent (native parallel)."""
        try:
            logger.info("🚗 Running Vehicle Detection Agent (native parallel)...")
            result = self.vehicle_detection_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"vehicle_detection_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Vehicle detection agent timeout: %s", e)
            return {
                "vehicle_detection_result": {
                    "agent": "vehicle_detection",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Vehicle detection timed out",
                    "summary": None,
                    "vehicles": [],
                    "vehicle_count": 0,
                    "license_plates": [],
                    "military_markings": [],
                    "tactical_assessment": {},
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Vehicle detection agent error: %s", e)
            return {
                "vehicle_detection_result": {
                    "agent": "vehicle_detection",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Vehicle detection failed",
                    "summary": None,
                    "vehicles": [],
                    "vehicle_count": 0,
                    "license_plates": [],
                    "military_markings": [],
                    "tactical_assessment": {},
                    "limitations": [str(e)],
                }
            }

    def run_weapon_detection_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Weapon/Threat Detection Agent (native parallel)."""
        try:
            logger.info("🔫 Running Weapon Detection Agent (native parallel)...")
            result = self.weapon_detection_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"weapon_detection_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Weapon detection agent timeout: %s", e)
            return {
                "weapon_detection_result": {
                    "agent": "weapon_detection",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Weapon detection timed out",
                    "summary": None,
                    "weapons": [],
                    "weapon_count": 0,
                    "explosive_indicators": [],
                    "military_equipment": [],
                    "threat_assessment": {},
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Weapon detection agent error: %s", e)
            return {
                "weapon_detection_result": {
                    "agent": "weapon_detection",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Weapon detection failed",
                    "summary": None,
                    "weapons": [],
                    "weapon_count": 0,
                    "explosive_indicators": [],
                    "military_equipment": [],
                    "threat_assessment": {},
                    "limitations": [str(e)],
                }
            }

    def run_crowd_analysis_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Crowd Analysis Agent (native parallel)."""
        try:
            logger.info("👥 Running Crowd Analysis Agent (native parallel)...")
            result = self.crowd_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"crowd_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Crowd analysis agent timeout: %s", e)
            return {
                "crowd_analysis_result": {
                    "agent": "crowd_analysis",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Crowd analysis timed out",
                    "summary": None,
                    "density_estimate": {},
                    "demographics": {},
                    "movement_patterns": {},
                    "behavioral_assessment": {},
                    "security_concerns": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Crowd analysis agent error: %s", e)
            return {
                "crowd_analysis_result": {
                    "agent": "crowd_analysis",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Crowd analysis failed",
                    "summary": None,
                    "density_estimate": {},
                    "demographics": {},
                    "movement_patterns": {},
                    "behavioral_assessment": {},
                    "security_concerns": [],
                    "limitations": [str(e)],
                }
            }

    def run_shadow_analysis_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Shadow/Sun Analysis Agent (native parallel)."""
        try:
            logger.info("☀️ Running Shadow Analysis Agent (native parallel)...")
            result = self.shadow_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"shadow_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Shadow analysis agent timeout: %s", e)
            return {
                "shadow_analysis_result": {
                    "agent": "shadow_analysis",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Shadow analysis timed out",
                    "summary": None,
                    "shadow_geometry": {},
                    "sun_position": {},
                    "time_estimate": {},
                    "season_inference": {},
                    "lighting_analysis": {},
                    "forensic_indicators": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Shadow analysis agent error: %s", e)
            return {
                "shadow_analysis_result": {
                    "agent": "shadow_analysis",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Shadow analysis failed",
                    "summary": None,
                    "shadow_geometry": {},
                    "sun_position": {},
                    "time_estimate": {},
                    "season_inference": {},
                    "lighting_analysis": {},
                    "forensic_indicators": [],
                    "limitations": [str(e)],
                }
            }

    def run_infrastructure_analysis_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Infrastructure Analysis Agent (native parallel)."""
        try:
            logger.info("🏗️ Running Infrastructure Analysis Agent (native parallel)...")
            result = self.infrastructure_analysis_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"infrastructure_analysis_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Infrastructure analysis agent timeout: %s", e)
            return {
                "infrastructure_analysis_result": {
                    "agent": "infrastructure_analysis",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Infrastructure analysis timed out",
                    "summary": None,
                    "buildings": [],
                    "roads": [],
                    "utilities": [],
                    "bridges": [],
                    "signage": [],
                    "strategic_assessment": {},
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Infrastructure analysis agent error: %s", e)
            return {
                "infrastructure_analysis_result": {
                    "agent": "infrastructure_analysis",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Infrastructure analysis failed",
                    "summary": None,
                    "buildings": [],
                    "roads": [],
                    "utilities": [],
                    "bridges": [],
                    "signage": [],
                    "strategic_assessment": {},
                    "limitations": [str(e)],
                }
            }

    # =========================================================================
    # MILITARY INTELLIGENCE BLOCK 2 — 2 new agents
    # =========================================================================

    def run_temporal_comparison_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Temporal Comparison Agent (native parallel)."""
        try:
            logger.info("🕐 Running Temporal Comparison Agent (native parallel)...")
            result = self.temporal_comparison_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"temporal_comparison_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Temporal comparison agent timeout: %s", e)
            return {
                "temporal_comparison_result": {
                    "agent": "temporal_comparison",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Temporal comparison timed out",
                    "summary": None,
                    "structural_changes": {},
                    "activity_detection": {},
                    "strategic_posture": {},
                    "environmental_changes": {},
                    "chronology": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Temporal comparison agent error: %s", e)
            return {
                "temporal_comparison_result": {
                    "agent": "temporal_comparison",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Temporal comparison failed",
                    "summary": None,
                    "structural_changes": {},
                    "activity_detection": {},
                    "strategic_posture": {},
                    "environmental_changes": {},
                    "chronology": [],
                    "limitations": [str(e)],
                }
            }

    def run_night_vision_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Night Vision Enhancement Agent (native parallel)."""
        try:
            logger.info("🌙 Running Night Vision Agent (native parallel)...")
            result = self.night_vision_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"night_vision_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Night vision agent timeout: %s", e)
            return {
                "night_vision_result": {
                    "agent": "night_vision",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Night vision analysis timed out",
                    "summary": None,
                    "visibility_conditions": {},
                    "light_sources": {},
                    "nocturnal_activity": {},
                    "covert_indicators": {},
                    "tactical_assessment": {},
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Night vision agent error: %s", e)
            return {
                "night_vision_result": {
                    "agent": "night_vision",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Night vision analysis failed",
                    "summary": None,
                    "visibility_conditions": {},
                    "light_sources": {},
                    "nocturnal_activity": {},
                    "covert_indicators": {},
                    "tactical_assessment": {},
                    "limitations": [str(e)],
                }
            }

    # =========================================================================
    # MILITARY INTELLIGENCE BLOCK 3 — 2 new agents
    # =========================================================================

    def run_nato_symbology_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute NATO APP-6 Symbology Agent (native parallel)."""
        try:
            logger.info("⚔️ Running NATO Symbology Agent (native parallel)...")
            result = self.nato_symbology_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"nato_symbology_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ NATO symbology agent timeout: %s", e)
            return {
                "nato_symbology_result": {
                    "agent": "nato_symbology",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "NATO symbology analysis timed out",
                    "summary": None,
                    "identified_entities": [],
                    "force_composition": {},
                    "operational_environment": {},
                    "tactical_graphics": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ NATO symbology agent error: %s", e)
            return {
                "nato_symbology_result": {
                    "agent": "nato_symbology",
                    "status": "error",
                    "error": str(e),
                    "analysis": "NATO symbology analysis failed",
                    "summary": None,
                    "identified_entities": [],
                    "force_composition": {},
                    "operational_environment": {},
                    "tactical_graphics": [],
                    "limitations": [str(e)],
                }
            }

    def run_multi_monitor_agent(self, state: AnalysisState) -> dict[str, Any]:
        """Execute Multi-Monitor Layout Agent (native parallel)."""
        try:
            logger.info("🖥️ Running Multi-Monitor Layout Agent (native parallel)...")
            result = self.multi_monitor_agent.analyze(
                state["image_base64"], state.get("context", "")
            )
            return {"multi_monitor_result": result}
        except AgentTimeoutError as e:
            logger.warning("⏱️ Multi-monitor agent timeout: %s", e)
            return {
                "multi_monitor_result": {
                    "agent": "multi_monitor",
                    "status": "timeout",
                    "error": str(e),
                    "analysis": "Multi-monitor layout analysis timed out",
                    "summary": None,
                    "scene_complexity": {},
                    "layout_recommendation": {},
                    "information_density": {},
                    "alert_priorities": [],
                    "limitations": ["Analysis timed out"],
                }
            }
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("❌ Multi-monitor agent error: %s", e)
            return {
                "multi_monitor_result": {
                    "agent": "multi_monitor",
                    "status": "error",
                    "error": str(e),
                    "analysis": "Multi-monitor layout analysis failed",
                    "summary": None,
                    "scene_complexity": {},
                    "layout_recommendation": {},
                    "information_density": {},
                    "alert_priorities": [],
                    "limitations": [str(e)],
                }
            }
