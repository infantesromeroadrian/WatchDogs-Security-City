"""
Pydantic models for validating agent results.

Enhanced with CIA-level OSINT models for:
- Hierarchical location intelligence
- Evidence chains with confidence scores
- Temporal analysis
- Detailed geolocation with confidence radius
"""

from pydantic import BaseModel, Field

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

    class Config:
        """Pydantic config."""

        frozen = False  # Allow updates for error handling


class OCRResult(BaseModel):
    """Result from OCR Agent."""

    agent: str = Field(default="ocr", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="OCR text output")
    has_text: bool = Field(default=False, description="Whether text was detected")
    confidence: str | None = Field(default=None, description="Confidence level")
    error: str | None = Field(default=None, description="Error message if failed")

    class Config:
        """Pydantic config."""

        frozen = False


class DetectionResult(BaseModel):
    """Result from Detection Agent."""

    agent: str = Field(default="detection", description="Agent identifier")
    status: str = Field(description="Status: success, error, timeout")
    analysis: str = Field(description="Detection text output")
    confidence: str | None = Field(default=None, description="Confidence level")
    error: str | None = Field(default=None, description="Error message if failed")

    class Config:
        """Pydantic config."""

        frozen = False


# =============================================================================
# CIA-LEVEL GEOLOCATION MODELS
# =============================================================================


class LocationHierarchy(BaseModel):
    """Hierarchical location from country to street number."""

    country: str | None = Field(default=None, description="Country name")
    region: str | None = Field(default=None, description="Region/State/Province")
    city: str | None = Field(default=None, description="City name")
    district: str | None = Field(default=None, description="District/Neighborhood")
    street: str | None = Field(default=None, description="Street name")
    number: str | None = Field(default=None, description="Building/house number")

    def get_precision_level(self) -> str:
        """Return the most precise level identified."""
        if self.number:
            return "building"
        if self.street:
            return "street"
        if self.district:
            return "district"
        if self.city:
            return "city"
        if self.region:
            return "region"
        if self.country:
            return "country"
        return "unknown"


class Coordinates(BaseModel):
    """GPS coordinates with confidence radius."""

    lat: float = Field(description="Latitude in decimal degrees")
    lon: float = Field(description="Longitude in decimal degrees")
    confidence_radius_meters: int = Field(
        default=10000,
        description="Estimated accuracy radius in meters",
    )

    def to_google_maps_url(self) -> str:
        """Generate Google Maps URL for these coordinates."""
        return f"https://www.google.com/maps?q={self.lat},{self.lon}"

    def to_osm_url(self) -> str:
        """Generate OpenStreetMap URL."""
        return f"https://www.openstreetmap.org/?mlat={self.lat}&mlon={self.lon}&zoom=15"


class ConfidenceLevel(BaseModel):
    """Confidence assessment for a location component."""

    level: str = Field(description="Confidence: muy alto, alto, medio, bajo, muy bajo")
    justification: str = Field(default="", description="Why this confidence level")


class EvidenceItem(BaseModel):
    """Single piece of evidence in the chain."""

    evidence: str = Field(description="Description of the visual evidence")
    confidence_percent: int | None = Field(
        default=None,
        description="Confidence in this evidence (0-100)",
    )
    supports: str = Field(
        default="general",
        description="What conclusion this evidence supports",
    )
    order: int | None = Field(default=None, description="Order of importance")


class TemporalAnalysis(BaseModel):
    """Temporal estimates from visual analysis."""

    estimated_time: str | None = Field(
        default=None,
        description="Estimated time of day (e.g., '14:30 aproximado')",
    )
    season: str | None = Field(
        default=None,
        description="Estimated season (primavera, verano, otoño, invierno)",
    )
    estimated_date: str | None = Field(
        default=None,
        description="Estimated date or date range if identifiable",
    )


class VerificationSuggestions(BaseModel):
    """Suggestions for verifying the geolocation."""

    search_terms: list[str] = Field(
        default_factory=list,
        description="Recommended search terms for Google Maps/Street View",
    )
    alternative_coordinates: list[str] = Field(
        default_factory=list,
        description="Alternative coordinate pairs to check",
    )
    additional_sources: list[str] = Field(
        default_factory=list,
        description="Additional databases or sources to consult",
    )


class GeolocationResult(BaseModel):
    """
    Enhanced result from Geolocation Agent with CIA-level detail.

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

    class Config:
        """Pydantic config."""

        frozen = False

    def get_best_estimate_text(self) -> str:
        """Return a human-readable best estimate of location."""
        loc = self.location
        parts = []

        if loc.get("street"):
            street_part = loc["street"]
            if loc.get("number"):
                street_part = f"{loc['number']} {street_part}"
            parts.append(street_part)

        if loc.get("district"):
            parts.append(loc["district"])

        if loc.get("city"):
            parts.append(loc["city"])

        if loc.get("region"):
            parts.append(loc["region"])

        if loc.get("country"):
            parts.append(loc["country"])

        return ", ".join(parts) if parts else "Ubicación no determinada"


# =============================================================================
# CIA-LEVEL FACE ANALYSIS MODELS
# =============================================================================


class PersonDemographics(BaseModel):
    """Demographic estimates for a detected person."""

    age_range: str | None = Field(default=None, description="Estimated age range")
    age_confidence: str | None = Field(default=None, description="Confidence in age estimate")
    gender: str | None = Field(default=None, description="Apparent gender")
    gender_confidence: str | None = Field(default=None, description="Confidence in gender")
    ethnicity_description: str | None = Field(
        default=None, description="General ethnicity description"
    )


class FacialFeatures(BaseModel):
    """Detailed facial feature descriptors."""

    face_shape: str | None = Field(default=None, description="Overall face shape")
    forehead: str | None = Field(default=None, description="Forehead description")
    eyebrows: str | None = Field(default=None, description="Eyebrow description")
    eyes: str | None = Field(default=None, description="Eye description")
    nose: str | None = Field(default=None, description="Nose description")
    mouth: str | None = Field(default=None, description="Mouth description")
    ears: str | None = Field(default=None, description="Ear description if visible")
    hair: str | None = Field(default=None, description="Hair description")
    facial_hair: str | None = Field(default=None, description="Facial hair if present")


class DistinctiveMarks(BaseModel):
    """Distinctive identifying marks."""

    scars: list[str] = Field(default_factory=list, description="Visible scars")
    moles: list[str] = Field(default_factory=list, description="Notable moles/birthmarks")
    tattoos: list[str] = Field(default_factory=list, description="Visible tattoos")
    piercings: list[str] = Field(default_factory=list, description="Visible piercings")
    other: list[str] = Field(default_factory=list, description="Other distinctive marks")


class BodyDescription(BaseModel):
    """Body characteristics."""

    height: str | None = Field(default=None, description="Apparent height")
    build: str | None = Field(default=None, description="Body build/complexion")
    posture: str | None = Field(default=None, description="Posture description")


class ClothingDescription(BaseModel):
    """Clothing and attire description."""

    upper: str | None = Field(default=None, description="Upper body clothing")
    lower: str | None = Field(default=None, description="Lower body clothing")
    footwear: str | None = Field(default=None, description="Footwear if visible")


class PersonContext(BaseModel):
    """Contextual information about person's behavior."""

    activity: str | None = Field(default=None, description="Apparent activity")
    expression: str | None = Field(default=None, description="Facial expression/emotional state")
    distinctive_elements: str | None = Field(default=None, description="Other distinctive elements")


class PersonDescriptor(BaseModel):
    """Complete descriptor for a single detected person."""

    person_id: int = Field(description="Person identifier in this image")
    position: str | None = Field(default=None, description="Position in image")
    demographics: dict = Field(default_factory=dict, description="Demographic estimates")
    face: dict = Field(default_factory=dict, description="Facial features")
    distinctive_marks: dict = Field(default_factory=dict, description="Distinctive marks")
    body: dict = Field(default_factory=dict, description="Body description")
    clothing: dict = Field(default_factory=dict, description="Clothing description")
    accessories: list[str] = Field(default_factory=list, description="Accessories list")
    context: dict = Field(default_factory=dict, description="Behavioral context")
    confidence: dict = Field(default_factory=dict, description="Confidence level and justification")


class DetectionSummary(BaseModel):
    """Summary of person detection in image."""

    total_persons: int = Field(default=0, description="Total persons detected")
    faces_visible: int = Field(default=0, description="Faces clearly visible")
    partial_visibility: int = Field(default=0, description="Persons partially visible")
    identification_quality: str = Field(
        default="unknown", description="Overall quality for identification"
    )


class FaceAnalysisResult(BaseModel):
    """
    Enhanced result from Face Analysis Agent with CIA-level detail.

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
        description="List of PersonDescriptor for each detected person",
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

    class Config:
        """Pydantic config."""

        frozen = False


# =============================================================================
# CIA-LEVEL FORENSIC ANALYSIS MODELS
# =============================================================================


class AuthenticityVerdict(BaseModel):
    """Authenticity verdict for image forensic analysis."""

    classification: str = Field(
        default="indeterminada",
        description="Classification: auténtica, probablemente auténtica, indeterminada, "
        "probablemente manipulada, manipulada, generada por ia",
    )
    confidence: str = Field(
        default="media",
        description="Confidence: muy alta, alta, media, baja, muy baja",
    )
    justification: str | None = Field(
        default=None,
        description="Brief justification for the verdict",
    )


class ManipulationDetection(BaseModel):
    """Detection result for a specific manipulation type."""

    detected: bool = Field(default=False, description="Whether manipulation was detected")
    details: str | None = Field(default=None, description="Details if detected")


class ManipulationSpecific(BaseModel):
    """Specific manipulation types detection."""

    copy_paste: dict = Field(
        default_factory=lambda: {"detected": False, "details": None},
        description="Copy-paste/cloning detection",
    )
    splicing: dict = Field(
        default_factory=lambda: {"detected": False, "details": None},
        description="Splicing/composition detection",
    )
    retouching: dict = Field(
        default_factory=lambda: {"detected": False, "details": None},
        description="Retouching/healing detection",
    )
    ai_generated: dict = Field(
        default_factory=lambda: {"detected": False, "details": None},
        description="AI-generated content detection",
    )


class ForensicAnomalies(BaseModel):
    """Anomalies detected in forensic analysis."""

    compression_artifacts: list[str] = Field(
        default_factory=list,
        description="Compression and artifact anomalies",
    )
    lighting_shadows: list[str] = Field(
        default_factory=list,
        description="Lighting and shadow inconsistencies",
    )
    perspective_geometry: list[str] = Field(
        default_factory=list,
        description="Perspective and geometry issues",
    )
    color_tonality: list[str] = Field(
        default_factory=list,
        description="Color and tonality anomalies",
    )
    manipulation_specific: dict = Field(
        default_factory=dict,
        description="Specific manipulation type detections",
    )
    semantic_content: list[str] = Field(
        default_factory=list,
        description="Semantic/content inconsistencies",
    )


class ForensicEvidence(BaseModel):
    """Single piece of forensic evidence."""

    order: int = Field(description="Order of importance")
    evidence: str = Field(description="Description of the evidence")
    weight: str = Field(description="Weight: alto, medio, bajo")
    indicates: str = Field(description="What this evidence indicates")


class ImageQualityAssessment(BaseModel):
    """Image quality assessment for forensic analysis."""

    resolution: str | None = Field(
        default=None,
        description="Resolution quality: suficiente, limitada, insuficiente",
    )
    compression: str | None = Field(
        default=None,
        description="Compression level: baja, media, alta, muy alta",
    )
    limiting_factors: list[str] = Field(
        default_factory=list,
        description="Factors limiting the analysis",
    )


class ForensicAnalysisResult(BaseModel):
    """
    Enhanced result from Forensic Analysis Agent with CIA-level detail.

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

    class Config:
        """Pydantic config."""

        frozen = False

    def is_likely_manipulated(self) -> bool:
        """Check if the image is likely manipulated based on verdict."""
        classification = self.verdict.get("classification", "").lower()
        return classification in ["manipulada", "probablemente manipulada", "generada por ia"]

    def is_likely_authentic(self) -> bool:
        """Check if the image is likely authentic based on verdict."""
        classification = self.verdict.get("classification", "").lower()
        return classification in ["auténtica", "probablemente auténtica"]

    def get_manipulation_types_detected(self) -> list[str]:
        """Return list of manipulation types detected."""
        types = []
        manipulation = self.anomalies.get("manipulation_specific", {})
        if manipulation.get("copy_paste", {}).get("detected"):
            types.append("copy_paste")
        if manipulation.get("splicing", {}).get("detected"):
            types.append("splicing")
        if manipulation.get("retouching", {}).get("detected"):
            types.append("retouching")
        if manipulation.get("ai_generated", {}).get("detected"):
            types.append("ai_generated")
        return types


# =============================================================================
# CIA-LEVEL CONTEXT INTELLIGENCE MODELS
# =============================================================================


class TemporalItem(BaseModel):
    """Single temporal analysis item with value, confidence, and evidence."""

    value: str | None = Field(default=None, description="Inferred value")
    confidence: str | None = Field(default=None, description="Confidence: alta, media, baja")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")


class TemporalAnalysis(BaseModel):
    """Complete temporal analysis."""

    time_of_day: dict = Field(
        default_factory=dict,
        description="Time of day analysis with value, confidence, evidence",
    )
    day_type: dict = Field(
        default_factory=dict,
        description="Day type (workday/weekend) analysis",
    )
    season: dict = Field(
        default_factory=dict,
        description="Season analysis",
    )
    era: dict = Field(
        default_factory=dict,
        description="Era/decade analysis",
    )
    specific_date: dict = Field(
        default_factory=dict,
        description="Specific date if determinable",
    )


class SocioculturalAnalysis(BaseModel):
    """Sociocultural analysis results."""

    socioeconomic_level: str | None = Field(
        default=None,
        description="Socioeconomic level: alto, medio-alto, medio, medio-bajo, bajo, mixto",
    )
    socioeconomic_indicators: list[str] = Field(
        default_factory=list,
        description="Indicators of socioeconomic level",
    )
    cultural_context: str | None = Field(
        default=None,
        description="Cultural context description",
    )
    cultural_indicators: list[str] = Field(
        default_factory=list,
        description="Cultural markers observed",
    )
    political_situation: str | None = Field(
        default=None,
        description="Political/social situation",
    )
    political_indicators: list[str] = Field(
        default_factory=list,
        description="Political indicators if any",
    )


class EventClassification(BaseModel):
    """Event/activity classification."""

    event_type: str | None = Field(default=None, description="Primary event type")
    event_subtype: str | None = Field(default=None, description="Event subtype if applicable")
    primary_purpose: str | None = Field(default=None, description="Primary purpose of presence")
    social_dynamics: str | None = Field(default=None, description="Social dynamics observed")


class EnvironmentalConditions(BaseModel):
    """Environmental and weather conditions."""

    weather: str | None = Field(default=None, description="Weather conditions")
    temperature: str | None = Field(default=None, description="Apparent temperature")
    special_conditions: str | None = Field(default=None, description="Special conditions if any")


class KeyInference(BaseModel):
    """Key inference with confidence level."""

    order: int = Field(description="Order of importance")
    inference: str = Field(description="The inference made")
    confidence_percent: int = Field(description="Confidence level 0-100")


class ContextIntelResult(BaseModel):
    """
    Enhanced result from Context Intelligence Agent with CIA-level detail.

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

    class Config:
        """Pydantic config."""

        frozen = False

    def get_estimated_time_range(self) -> str | None:
        """Get the estimated time of day if available."""
        time_data = self.temporal_analysis.get("time_of_day", {})
        return time_data.get("value")

    def get_estimated_era(self) -> str | None:
        """Get the estimated era/decade if available."""
        era_data = self.temporal_analysis.get("era", {})
        return era_data.get("value")

    def get_highest_confidence_inference(self) -> dict | None:
        """Get the inference with highest confidence."""
        if not self.key_inferences:
            return None
        sorted_inferences = sorted(
            self.key_inferences,
            key=lambda x: x.get("confidence_percent", 0),
            reverse=True,
        )
        return sorted_inferences[0] if sorted_inferences else None


# =============================================================================
# COMBINED RESULTS
# =============================================================================


class AgentResults(BaseModel):
    """Combined results from all 7 agents."""

    vision: VisionResult
    ocr: OCRResult
    detection: DetectionResult
    geolocation: GeolocationResult | None = None  # Optional for backwards compatibility
    face_analysis: FaceAnalysisResult | None = None  # CIA-level person identification
    forensic_analysis: ForensicAnalysisResult | None = None  # CIA-level image forensics
    context_intel: ContextIntelResult | None = None  # CIA-level contextual intelligence

    class Config:
        """Pydantic config."""

        frozen = False


class FinalReport(BaseModel):
    """Final report structure."""

    timestamp: str = Field(description="ISO timestamp")
    status: str = Field(description="Overall status")
    agents: AgentResults = Field(description="Results from all agents")

    class Config:
        """Pydantic config."""

        frozen = False
