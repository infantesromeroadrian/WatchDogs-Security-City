"""
Pydantic models for validating agent results.

Each *Result model corresponds to one of the 16 analysis agents.
Fields use generic ``dict`` / ``list`` types because the LLM response
is parsed from free-text into dicts by each agent's response_parser —
typed sub-models were defined historically but never wired up and have
been removed to reduce dead code.
"""

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# BASIC AGENT RESULTS
# =============================================================================


class VisionResult(BaseModel):
    """Result from Vision Agent."""

    agent: str = Field(default="vision", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Analysis text output")
    confidence: str | None = Field(default=None, description="Confidence level")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class OCRResult(BaseModel):
    """Result from OCR Agent."""

    agent: str = Field(default="ocr", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="OCR text output")
    has_text: bool = Field(default=False, description="Whether text was detected")
    confidence: str | None = Field(default=None, description="Confidence level")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class DetectionResult(BaseModel):
    """Result from Detection Agent."""

    agent: str = Field(default="detection", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Detection text output")
    confidence: str | None = Field(default=None, description="Confidence level")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# GEOLOCATION RESULT
# =============================================================================


class GeolocationResult(BaseModel):
    """
    Result from Geolocation Agent.

    Includes hierarchical location, evidence chain, temporal analysis,
    and verification suggestions.
    """

    agent: str = Field(default="geolocation", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full geolocation analysis text")

    # Core location data
    location: dict = Field(
        default_factory=dict,
        description="Hierarchical location (country, region, city, district, street, number)",
    )
    coordinates: dict | None = Field(
        default=None,
        description="Coordinates with lat, lon, and confidence_radius_meters",
    )

    # Confidence levels
    confidence: str | None = Field(
        default=None,
        description="Overall confidence level (backward compatible)",
    )
    confidence_by_level: dict = Field(
        default_factory=dict,
        description="Confidence per location component (country, region, city, etc.)",
    )

    # Evidence and analysis
    evidence_chain: list = Field(
        default_factory=list,
        description="Ordered list of evidence items with confidence scores",
    )
    key_clues: list = Field(
        default_factory=list,
        description="Key visual clues (backward compatible)",
    )

    # Temporal analysis
    temporal_analysis: dict = Field(
        default_factory=dict,
        description="Time/season/date estimates from visual analysis",
    )

    # Limitations and verification
    limitations: list = Field(
        default_factory=list,
        description="Analysis limitations and caveats",
    )
    verification_suggestions: dict = Field(
        default_factory=dict,
        description="Suggestions for verifying the geolocation",
    )

    # Error handling
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# FACE ANALYSIS RESULT
# =============================================================================


class FaceAnalysisResult(BaseModel):
    """
    Result from Face Analysis Agent.

    Includes comprehensive person descriptors for all detected individuals.
    """

    agent: str = Field(default="face_analysis", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full face analysis text")

    # Detection overview
    detection_summary: dict = Field(
        default_factory=dict,
        description="Summary of detection (counts, quality)",
    )

    # Per-person data
    persons: list = Field(
        default_factory=list,
        description="List of person descriptors for each detected person",
    )
    person_count: int = Field(default=0, description="Number of persons detected")

    # Identification aids
    most_distinctive_features: list = Field(
        default_factory=list,
        description="Most distinctive features for identification",
    )

    # Metadata
    limitations: list = Field(
        default_factory=list,
        description="Analysis limitations",
    )

    # Error handling
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# FORENSIC ANALYSIS RESULT
# =============================================================================


class ForensicAnalysisResult(BaseModel):
    """
    Result from Forensic Analysis Agent.

    Includes comprehensive authenticity verification and manipulation detection.
    """

    agent: str = Field(default="forensic_analysis", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full forensic analysis text")

    # Core verdict
    verdict: dict = Field(
        default_factory=dict,
        description="Authenticity verdict with classification, confidence, justification",
    )
    integrity_score: int | None = Field(
        default=None,
        description="Integrity score 0-100 (100 = completely authentic)",
    )

    # Anomalies
    anomalies: dict = Field(
        default_factory=dict,
        description="Anomalies detected by category",
    )

    # Detection details
    suspicious_regions: list = Field(
        default_factory=list,
        description="List of suspicious regions in the image",
    )
    evidence_chain: list = Field(
        default_factory=list,
        description="Ordered chain of evidence",
    )
    manipulation_hypothesis: str | None = Field(
        default=None,
        description="Hypothesis about what was manipulated and how",
    )

    # Quality assessment
    image_quality: dict = Field(
        default_factory=dict,
        description="Image quality assessment for analysis",
    )

    # Recommendations
    recommendations: list = Field(
        default_factory=list,
        description="Recommendations for further verification",
    )

    # Error handling
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# CONTEXT INTELLIGENCE RESULT
# =============================================================================


class ContextIntelResult(BaseModel):
    """
    Result from Context Intelligence Agent.

    Includes comprehensive temporal, cultural, and contextual analysis.
    """

    agent: str = Field(default="context_intel", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full context intel analysis text")

    # Executive summary
    executive_summary: str | None = Field(
        default=None,
        description="2-3 sentence executive summary",
    )

    # Core analysis
    temporal_analysis: dict = Field(
        default_factory=dict,
        description="Temporal analysis (time, day, season, era, date)",
    )
    sociocultural_analysis: dict = Field(
        default_factory=dict,
        description="Sociocultural and socioeconomic analysis",
    )
    event_classification: dict = Field(
        default_factory=dict,
        description="Event type and classification",
    )
    environmental_conditions: dict = Field(
        default_factory=dict,
        description="Environmental and weather conditions",
    )

    # Insights
    anomalies: list = Field(
        default_factory=list,
        description="Detected anomalies and unusual elements",
    )
    key_inferences: list = Field(
        default_factory=list,
        description="Key inferences with confidence levels",
    )

    # Metadata
    limitations: list = Field(
        default_factory=list,
        description="Analysis limitations",
    )
    open_questions: list = Field(
        default_factory=list,
        description="Questions that couldn't be answered",
    )

    # Error handling
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# COMBINED RESULTS
# =============================================================================


# =============================================================================
# MILITARY INTELLIGENCE RESULTS (Block 1 - 5 new agents)
# =============================================================================


class VehicleDetectionResult(BaseModel):
    """
    Result from Vehicle Detection & ALPR Agent.

    Military-grade vehicle intelligence including license plate recognition.
    """

    agent: str = Field(default="vehicle_detection", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full vehicle detection analysis text")

    summary: str | None = Field(default=None, description="Vehicle inventory summary")
    vehicles: list = Field(default_factory=list, description="List of detected vehicles")
    vehicle_count: int = Field(default=0, description="Total vehicles detected")
    license_plates: list = Field(default_factory=list, description="License plate readings")
    military_markings: list = Field(default_factory=list, description="Military markings found")
    tactical_assessment: dict = Field(
        default_factory=dict,
        description="Tactical threat assessment from vehicles",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class WeaponDetectionResult(BaseModel):
    """
    Result from Weapon/Threat Detection Agent.

    Military-grade weapon and threat identification.
    """

    agent: str = Field(default="weapon_detection", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full weapon detection analysis text")

    summary: str | None = Field(default=None, description="Weapon/threat summary")
    weapons: list = Field(default_factory=list, description="List of detected weapons")
    weapon_count: int = Field(default=0, description="Total weapons detected")
    explosive_indicators: list = Field(
        default_factory=list, description="Explosive device indicators"
    )
    military_equipment: list = Field(
        default_factory=list, description="Military equipment detected"
    )
    threat_assessment: dict = Field(
        default_factory=dict,
        description="Overall threat assessment",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class CrowdAnalysisResult(BaseModel):
    """
    Result from Crowd Analysis Agent.

    Crowd density, demographics, movement, and behavioral analysis.
    """

    agent: str = Field(default="crowd_analysis", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full crowd analysis text")

    summary: str | None = Field(default=None, description="Crowd analysis summary")
    density_estimate: dict = Field(
        default_factory=dict,
        description="Crowd density estimation (count, level, zones)",
    )
    demographics: dict = Field(default_factory=dict, description="Demographic composition")
    movement_patterns: dict = Field(default_factory=dict, description="Movement flow and patterns")
    behavioral_assessment: dict = Field(
        default_factory=dict,
        description="Behavioral analysis (mood, anomalies, groups)",
    )
    security_concerns: list = Field(default_factory=list, description="Security risk factors")
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class ShadowAnalysisResult(BaseModel):
    """
    Result from Shadow/Sun Analysis Agent.

    Sun position, shadow geometry, and temporal estimation from lighting.
    """

    agent: str = Field(default="shadow_analysis", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full shadow analysis text")

    summary: str | None = Field(default=None, description="Shadow analysis summary")
    shadow_geometry: dict = Field(
        default_factory=dict,
        description="Shadow direction, length ratio, consistency",
    )
    sun_position: dict = Field(
        default_factory=dict,
        description="Estimated sun azimuth, elevation, hemisphere",
    )
    time_estimate: dict = Field(
        default_factory=dict,
        description="Time-of-day estimation from shadows",
    )
    season_inference: dict = Field(
        default_factory=dict,
        description="Season inference from sun angle",
    )
    lighting_analysis: dict = Field(
        default_factory=dict,
        description="Natural vs artificial lighting analysis",
    )
    forensic_indicators: list = Field(
        default_factory=list, description="Shadow inconsistencies (manipulation)"
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class InfrastructureAnalysisResult(BaseModel):
    """
    Result from Infrastructure Analysis Agent.

    Building, road, utility, and strategic infrastructure classification.
    """

    agent: str = Field(default="infrastructure_analysis", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full infrastructure analysis text")

    summary: str | None = Field(default=None, description="Infrastructure summary")
    buildings: list = Field(default_factory=list, description="Building inventory")
    roads: list = Field(default_factory=list, description="Road infrastructure")
    utilities: list = Field(default_factory=list, description="Utility infrastructure")
    bridges: list = Field(default_factory=list, description="Bridges and structures")
    signage: list = Field(default_factory=list, description="Signage analysis")
    strategic_assessment: dict = Field(
        default_factory=dict,
        description="Strategic infrastructure assessment",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# MILITARY INTELLIGENCE RESULTS (Block 2 - 2 new agents)
# =============================================================================


class TemporalComparisonResult(BaseModel):
    """
    Result from Temporal Comparison Agent.

    Military-grade temporal change detection and strategic posture analysis.
    """

    agent: str = Field(default="temporal_comparison", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full temporal comparison analysis text")

    summary: str | None = Field(default=None, description="Temporal comparison summary")
    structural_changes: dict = Field(
        default_factory=dict,
        description="Detected structural changes (new, removed, modified)",
    )
    activity_detection: dict = Field(
        default_factory=dict,
        description="Activity pattern changes (vehicle, personnel, equipment)",
    )
    strategic_posture: dict = Field(
        default_factory=dict,
        description="Strategic posture assessment (buildup, withdrawal, fortification)",
    )
    environmental_changes: dict = Field(
        default_factory=dict,
        description="Environmental/terrain temporal shifts",
    )
    chronology: list = Field(
        default_factory=list,
        description="Chronological sequence of detected changes",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class NightVisionResult(BaseModel):
    """
    Result from Night Vision Enhancement Agent.

    Military-grade night/low-light image analysis and interpretation.
    """

    agent: str = Field(default="night_vision", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full night vision analysis text")

    summary: str | None = Field(default=None, description="Night vision analysis summary")
    visibility_conditions: dict = Field(
        default_factory=dict,
        description="Visibility assessment (ambient light, distance, quality)",
    )
    light_sources: dict = Field(
        default_factory=dict,
        description="Light source identification and classification",
    )
    nocturnal_activity: dict = Field(
        default_factory=dict,
        description="Night activity pattern detection",
    )
    covert_indicators: dict = Field(
        default_factory=dict,
        description="Covert activity indicators and anomalies",
    )
    tactical_assessment: dict = Field(
        default_factory=dict,
        description="Tactical night assessment (cover, concealment, approach routes)",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# MILITARY INTELLIGENCE RESULTS (Block 3 - 2 new agents)
# =============================================================================


class NATOSymbologyResult(BaseModel):
    """
    Result from NATO APP-6 Symbology Agent.

    Military-grade entity classification using NATO APP-6D standard.
    """

    agent: str = Field(default="nato_symbology", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full NATO symbology analysis text")

    summary: str | None = Field(default=None, description="NATO symbology summary")
    identified_entities: list = Field(
        default_factory=list,
        description="Entities with SIDC codes and affiliations",
    )
    force_composition: dict = Field(
        default_factory=dict,
        description="Force composition (friendly, hostile, neutral, unknown counts)",
    )
    operational_environment: dict = Field(
        default_factory=dict,
        description="Operational environment (domain, weather, terrain)",
    )
    tactical_graphics: list = Field(
        default_factory=list,
        description="Recommended tactical graphic overlays",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


class MultiMonitorResult(BaseModel):
    """
    Result from Multi-Monitor Layout Agent.

    Command center multi-monitor display optimization.
    """

    agent: str = Field(default="multi_monitor", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Full multi-monitor layout analysis text")

    summary: str | None = Field(default=None, description="Multi-monitor layout summary")
    scene_complexity: dict = Field(
        default_factory=dict,
        description="Scene complexity assessment (level, density, priority agents)",
    )
    layout_recommendation: dict = Field(
        default_factory=dict,
        description="Layout recommendation (monitor count, arrangement, type)",
    )
    information_density: dict = Field(
        default_factory=dict,
        description="Information density (critical data, zoom areas, declutter)",
    )
    alert_priorities: list = Field(
        default_factory=list,
        description="Alert priorities with recommended actions",
    )
    limitations: list = Field(default_factory=list, description="Analysis limitations")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(frozen=False)


# =============================================================================
# COMBINED RESULTS
# =============================================================================


class AgentResults(BaseModel):
    """Combined results from all 16 agents (7 original + 5 military B1 + 2 military B2 + 2 military B3)."""

    # Original agents
    vision: VisionResult
    ocr: OCRResult
    detection: DetectionResult
    geolocation: GeolocationResult | None = None
    face_analysis: FaceAnalysisResult | None = None
    forensic_analysis: ForensicAnalysisResult | None = None
    context_intel: ContextIntelResult | None = None
    # Military intelligence agents (Block 1)
    vehicle_detection: VehicleDetectionResult | None = None
    weapon_detection: WeaponDetectionResult | None = None
    crowd_analysis: CrowdAnalysisResult | None = None
    shadow_analysis: ShadowAnalysisResult | None = None
    infrastructure_analysis: InfrastructureAnalysisResult | None = None
    # Military intelligence agents (Block 2)
    temporal_comparison: TemporalComparisonResult | None = None
    night_vision: NightVisionResult | None = None
    # Military intelligence agents (Block 3)
    nato_symbology: NATOSymbologyResult | None = None
    multi_monitor: MultiMonitorResult | None = None

    model_config = ConfigDict(frozen=False)


class FinalReport(BaseModel):
    """Final report structure."""

    timestamp: str = Field(description="ISO timestamp")
    status: str = Field(description="Overall status")
    agents: AgentResults = Field(description="Results from all agents")

    model_config = ConfigDict(frozen=False)
