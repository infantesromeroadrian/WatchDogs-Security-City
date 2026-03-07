"""
LangGraph agents package for video frame analysis.

Military-Grade OSINT Analysis Agents (16 total):

Original CIA-Level (7):
- VisionAgent: General scene analysis
- OCRAgent: Text extraction
- DetectionAgent: Object and person detection
- GeolocationAgent: Location identification with forensic-level detail
- FaceAnalysisAgent: Person identification with comprehensive descriptors
- ForensicAnalysisAgent: Image authenticity and manipulation detection
- ContextIntelAgent: Temporal and cultural inference

Military Intelligence Block 1 (5):
- VehicleDetectionAgent: Vehicle classification and ALPR
- WeaponDetectionAgent: Weapon/threat identification
- CrowdAnalysisAgent: Crowd density and behavioral analysis
- ShadowAnalysisAgent: Sun position and temporal estimation
- InfrastructureAnalysisAgent: Strategic infrastructure classification

Military Intelligence Block 2 (2):
- TemporalComparisonAgent: Temporal change detection and strategic posture
- NightVisionAgent: Night/low-light scene analysis

Military Intelligence Block 3 (2):
- NATOSymbologyAgent: NATO APP-6D entity classification and SIDC codes
- MultiMonitorAgent: Multi-monitor command center layout optimization
"""

# Original agents
from .context_intel import ContextIntelAgent
from .detection_agent import DetectionAgent
from .face_analysis import FaceAnalysisAgent
from .forensic_analysis import ForensicAnalysisAgent
from .geolocation_agent import GeolocationAgent
from .ocr_agent import OCRAgent
from .vision_agent import VisionAgent

# Military Intelligence Block 1
from .crowd_analysis import CrowdAnalysisAgent
from .infrastructure_analysis import InfrastructureAnalysisAgent
from .shadow_analysis import ShadowAnalysisAgent
from .vehicle_detection import VehicleDetectionAgent
from .weapon_detection import WeaponDetectionAgent

# Military Intelligence Block 2
from .night_vision import NightVisionAgent
from .temporal_comparison import TemporalComparisonAgent

# Military Intelligence Block 3
from .multi_monitor import MultiMonitorAgent
from .nato_symbology import NATOSymbologyAgent

__all__ = [
    # Original
    "ContextIntelAgent",
    "DetectionAgent",
    "FaceAnalysisAgent",
    "ForensicAnalysisAgent",
    "GeolocationAgent",
    "OCRAgent",
    "VisionAgent",
    # Military Intelligence Block 1
    "CrowdAnalysisAgent",
    "InfrastructureAnalysisAgent",
    "ShadowAnalysisAgent",
    "VehicleDetectionAgent",
    "WeaponDetectionAgent",
    # Military Intelligence Block 2
    "NightVisionAgent",
    "TemporalComparisonAgent",
    # Military Intelligence Block 3
    "MultiMonitorAgent",
    "NATOSymbologyAgent",
]
