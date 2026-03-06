"""
Pydantic models for validating agent results.

Each *Result model corresponds to one of the 7 analysis agents.
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


class AgentResults(BaseModel):
    """Combined results from all 7 agents."""

    vision: VisionResult
    ocr: OCRResult
    detection: DetectionResult
    geolocation: GeolocationResult | None = None  # Optional for backwards compatibility
    face_analysis: FaceAnalysisResult | None = None
    forensic_analysis: ForensicAnalysisResult | None = None
    context_intel: ContextIntelResult | None = None

    model_config = ConfigDict(frozen=False)


class FinalReport(BaseModel):
    """Final report structure."""

    timestamp: str = Field(description="ISO timestamp")
    status: str = Field(description="Overall status")
    agents: AgentResults = Field(description="Results from all agents")

    model_config = ConfigDict(frozen=False)
