"""
Pydantic output schemas for the OSINT agents (structured model output).

Each schema mirrors the dict shape the legacy regex parsers produced, so the
combiner, report generator and frontend keep working unchanged. Scalars are
coerced leniently (a number where text is expected, a string where a list is
expected, ``null`` anywhere) because small vision models are loose with types;
what is enforced is the structure: object vs list, required core fields, and
integer counts.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _txt(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)):
        return str(v)
    if isinstance(v, list):
        return "; ".join(s for s in (_txt(x) for x in v) if s) or None
    return json.dumps(v, ensure_ascii=False)


def _int(v: Any) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(round(v))
    if isinstance(v, str):
        digits = "".join(c for c in v if c.isdigit() or c == "-")
        return int(digits) if digits not in ("", "-") else None
    return None


def _flt(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _flag(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "si", "sí", "yes", "detectado", "1")
    return bool(v)


def _strs(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (str, int, float, bool)):
        return [_txt(v) or ""] if v != "" else []
    if isinstance(v, dict):
        return [f"{k}: {_txt(x)}" for k, x in v.items() if _txt(x)]
    return [s for s in (_txt(x) for x in v) if s]


def _items(v: Any) -> list[Any]:
    if v is None:
        return []
    if isinstance(v, dict):
        return [v]
    return list(v) if isinstance(v, list) else [v]


Txt = Annotated[str | None, BeforeValidator(_txt)]
Int = Annotated[int | None, BeforeValidator(_int)]
Flt = Annotated[float | None, BeforeValidator(_flt)]
Flag = Annotated[bool, BeforeValidator(_flag)]
Strs = Annotated[list[str], BeforeValidator(_strs)]
Anys = Annotated[list[Any], BeforeValidator(_items)]


class _M(BaseModel):
    """Base: ignore unknown keys, drop nulls so defaults apply, accept a bare string."""

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _prepare(cls, v: Any) -> Any:
        if isinstance(v, str):
            first = next(iter(cls.model_fields))
            return {first: v}
        if isinstance(v, dict):
            return {k: x for k, x in v.items() if x is not None}
        return v


def _items_of(model: type[_M]) -> Any:
    return Annotated[list[model], BeforeValidator(_items)]  # type: ignore[valid-type]


# --------------------------------------------------------------------------- OCR
class OcrText(_M):
    text: Txt = None
    kind: Txt = Field(default=None, description="matrícula, cartel, rótulo, documento, otro")
    language: Txt = None
    confidence: Txt = None


class OcrSchema(_M):
    has_text: Flag = False
    extracted_text: Strs = Field(default_factory=list, description="cada texto legible, literal")
    texts: _items_of(OcrText) = Field(default_factory=list)  # type: ignore[valid-type]
    summary: Txt = None
    confidence: Txt = None


# ---------------------------------------------------------------------- detection
class DetectedObject(_M):
    label: Txt = None
    count: Int = None
    notes: Txt = None


class DetectionSchema(_M):
    objects: _items_of(DetectedObject) = Field(default_factory=list)  # type: ignore[valid-type]
    total_people: Int = None
    total_vehicles: Int = None
    summary: Txt = None
    confidence: Txt = None


# -------------------------------------------------------------------- geolocation
class GeoLocation(_M):
    country: Txt = None
    region: Txt = None
    city: Txt = None
    district: Txt = None
    street: Txt = None
    number: Txt = None


class GeoCoordinates(_M):
    lat: Flt = None
    lon: Flt = None
    confidence_radius_meters: Int = None


class GeoEvidence(_M):
    evidence: Txt = None
    confidence_percent: Int = None
    supports: Txt = None


class GeoTemporal(_M):
    estimated_time: Txt = None
    season: Txt = None
    estimated_date: Txt = None


class GeoVerification(_M):
    search_terms: Strs = Field(default_factory=list)
    alternative_coordinates: Strs = Field(default_factory=list)
    additional_sources: Strs = Field(default_factory=list)


class GeolocationSchema(_M):
    @model_validator(mode="after")
    def _drop_null_island(self) -> GeolocationSchema:
        """(0, 0) is a placeholder, not a prediction: report "no coordinates" instead."""
        c = self.coordinates
        if c is not None and (c.lat in (None, 0.0) and c.lon in (None, 0.0)):
            self.coordinates = None
        return self

    location: GeoLocation = Field(default_factory=GeoLocation)
    coordinates: GeoCoordinates | None = None
    confidence: Txt = "unknown"
    confidence_by_level: dict[str, Any] = Field(default_factory=dict)
    evidence_chain: _items_of(GeoEvidence) = Field(default_factory=list)  # type: ignore[valid-type]
    key_clues: Strs = Field(default_factory=list)
    temporal_analysis: GeoTemporal = Field(default_factory=GeoTemporal)
    limitations: Strs = Field(default_factory=list)
    verification_suggestions: GeoVerification = Field(default_factory=GeoVerification)


# --------------------------------------------------------------------------- face
class FaceDetectionSummary(_M):
    total_persons: Int = None
    faces_visible: Int = None
    partial_visibility: Int = None
    identification_quality: Txt = None


class FaceDemographics(_M):
    age_range: Txt = None
    age_confidence: Txt = None
    gender: Txt = None
    gender_confidence: Txt = None


class FaceFeatures(_M):
    face_shape: Txt = None
    forehead: Txt = None
    eyebrows: Txt = None
    eyes: Txt = None
    nose: Txt = None
    mouth: Txt = None
    ears: Txt = None
    hair: Txt = None
    facial_hair: Txt = None


class FaceMarks(_M):
    scars: Strs = Field(default_factory=list)
    moles: Strs = Field(default_factory=list)
    tattoos: Strs = Field(default_factory=list)
    piercings: Strs = Field(default_factory=list)
    other: Strs = Field(default_factory=list)


class FaceBody(_M):
    height: Txt = None
    build: Txt = None
    posture: Txt = None


class FaceClothing(_M):
    upper: Txt = None
    lower: Txt = None
    footwear: Txt = None


class FaceContext(_M):
    activity: Txt = None
    expression: Txt = None
    distinctive_elements: Txt = None


class FaceConfidence(_M):
    level: Txt = None
    justification: Txt = None


class FacePerson(_M):
    person_id: Int = None
    position: Txt = None
    demographics: FaceDemographics = Field(default_factory=FaceDemographics)
    face: FaceFeatures = Field(default_factory=FaceFeatures)
    distinctive_marks: FaceMarks = Field(default_factory=FaceMarks)
    body: FaceBody = Field(default_factory=FaceBody)
    clothing: FaceClothing = Field(default_factory=FaceClothing)
    accessories: Strs = Field(default_factory=list)
    context: FaceContext = Field(default_factory=FaceContext)
    confidence: FaceConfidence = Field(default_factory=FaceConfidence)


class FaceSchema(_M):
    detection_summary: FaceDetectionSummary = Field(default_factory=FaceDetectionSummary)
    persons: _items_of(FacePerson) = Field(default_factory=list)  # type: ignore[valid-type]
    person_count: Int = 0
    most_distinctive_features: Strs = Field(default_factory=list)
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------------ forensic
class ForensicVerdict(_M):
    classification: Txt = None
    confidence: Txt = None
    justification: Txt = None


class ForensicFlag(_M):
    detected: Flag = False
    details: Txt = None


class ForensicManipulation(_M):
    copy_paste: ForensicFlag = Field(default_factory=ForensicFlag)
    splicing: ForensicFlag = Field(default_factory=ForensicFlag)
    retouching: ForensicFlag = Field(default_factory=ForensicFlag)
    ai_generated: ForensicFlag = Field(default_factory=ForensicFlag)


class ForensicAnomalies(_M):
    compression_artifacts: Anys = Field(default_factory=list)
    lighting_shadows: Anys = Field(default_factory=list)
    perspective_geometry: Anys = Field(default_factory=list)
    color_tonality: Anys = Field(default_factory=list)
    manipulation_specific: ForensicManipulation = Field(default_factory=ForensicManipulation)
    semantic_content: Anys = Field(default_factory=list)


class ForensicEvidence(_M):
    order: Int = None
    evidence: Txt = None
    weight: Txt = None
    indicates: Txt = None


class ForensicQuality(_M):
    resolution: Txt = None
    compression: Txt = None
    limiting_factors: Strs = Field(default_factory=list)


class ForensicSchema(_M):
    verdict: ForensicVerdict = Field(default_factory=ForensicVerdict)
    integrity_score: Int = None
    anomalies: ForensicAnomalies = Field(default_factory=ForensicAnomalies)
    suspicious_regions: Anys = Field(default_factory=list)
    evidence_chain: _items_of(ForensicEvidence) = Field(default_factory=list)  # type: ignore[valid-type]
    manipulation_hypothesis: Txt = None
    image_quality: ForensicQuality = Field(default_factory=ForensicQuality)
    recommendations: Strs = Field(default_factory=list)


# ---------------------------------------------------------------------- context
class CtxEstimate(_M):
    value: Txt = None
    confidence: Txt = None
    evidence: Strs = Field(default_factory=list)


class CtxTemporal(_M):
    time_of_day: CtxEstimate = Field(default_factory=CtxEstimate)
    day_type: CtxEstimate = Field(default_factory=CtxEstimate)
    season: CtxEstimate = Field(default_factory=CtxEstimate)
    era: CtxEstimate = Field(default_factory=CtxEstimate)
    specific_date: CtxEstimate = Field(default_factory=CtxEstimate)


class CtxSocio(_M):
    socioeconomic_level: Txt = None
    socioeconomic_indicators: Strs = Field(default_factory=list)
    cultural_context: Txt = None
    cultural_indicators: Strs = Field(default_factory=list)
    political_situation: Txt = None
    political_indicators: Strs = Field(default_factory=list)


class CtxEvent(_M):
    event_type: Txt = None
    event_subtype: Txt = None
    primary_purpose: Txt = None
    social_dynamics: Txt = None


class CtxEnvironment(_M):
    weather: Txt = None
    temperature: Txt = None
    special_conditions: Txt = None


class ContextIntelSchema(_M):
    executive_summary: Txt = None
    temporal_analysis: CtxTemporal = Field(default_factory=CtxTemporal)
    sociocultural_analysis: CtxSocio = Field(default_factory=CtxSocio)
    event_classification: CtxEvent = Field(default_factory=CtxEvent)
    environmental_conditions: CtxEnvironment = Field(default_factory=CtxEnvironment)
    anomalies: Strs = Field(default_factory=list)
    key_inferences: Strs = Field(default_factory=list)
    limitations: Strs = Field(default_factory=list)
    open_questions: Strs = Field(default_factory=list)


# ---------------------------------------------------------------------- vehicles
class Vehicle(_M):
    id: Int = None
    category: Txt = None
    type: Txt = None
    make_model: Txt = None
    color: Txt = None
    condition: Txt = None
    position: Txt = None
    license_plate: Txt = None
    military_markings: Txt = None
    threat_level: Txt = None


class LicensePlate(_M):
    reading: Txt = None
    confidence: Txt = None


class VehicleTactical(_M):
    threat_level: Txt = None
    movement_patterns: Txt = None
    anomalies: Txt = None


class VehicleSchema(_M):
    summary: Txt = None
    vehicles: _items_of(Vehicle) = Field(default_factory=list)  # type: ignore[valid-type]
    vehicle_count: Int = 0
    license_plates: _items_of(LicensePlate) = Field(default_factory=list)  # type: ignore[valid-type]
    military_markings: Strs = Field(default_factory=list)
    tactical_assessment: VehicleTactical = Field(default_factory=VehicleTactical)
    limitations: Strs = Field(default_factory=list)


# ----------------------------------------------------------------------- weapons
class Weapon(_M):
    id: Int = None
    type: Txt = None
    subtype: Txt = None
    caliber: Txt = None
    make_model: Txt = None
    condition: Txt = None
    operational_status: Txt = None
    threat_level: Txt = None


class WeaponThreat(_M):
    threat_level: Txt = None
    immediate_threats: Txt = None
    escalation_risk: Txt = None


class WeaponSchema(_M):
    summary: Txt = None
    weapons: _items_of(Weapon) = Field(default_factory=list)  # type: ignore[valid-type]
    weapon_count: Int = 0
    explosive_indicators: Strs = Field(default_factory=list)
    military_equipment: Strs = Field(default_factory=list)
    threat_assessment: WeaponThreat = Field(default_factory=WeaponThreat)
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------------- crowd
class CrowdZones(_M):
    primer_plano: Txt = None
    zona_media: Txt = None
    fondo: Txt = None


class CrowdDensity(_M):
    total_count: Int = None
    density_level: Txt = None
    zones: CrowdZones = Field(default_factory=CrowdZones)


class CrowdDemographics(_M):
    age_ranges: Txt = None
    gender_distribution: Txt = None
    predominant_attire: Txt = None
    uniforms: Txt = None


class CrowdMovement(_M):
    predominant_direction: Txt = None
    speed: Txt = None
    bottlenecks: Txt = None
    general_pattern: Txt = None


class CrowdBehavior(_M):
    general_mood: Txt = None
    anomalous_behaviors: Txt = None
    group_formations: Txt = None


class CrowdSchema(_M):
    summary: Txt = None
    density_estimate: CrowdDensity = Field(default_factory=CrowdDensity)
    demographics: CrowdDemographics = Field(default_factory=CrowdDemographics)
    movement_patterns: CrowdMovement = Field(default_factory=CrowdMovement)
    behavioral_assessment: CrowdBehavior = Field(default_factory=CrowdBehavior)
    security_concerns: Strs = Field(default_factory=list)
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------------ shadow
class ShadowGeometry(_M):
    direction: Txt = None
    length_ratio: Txt = None
    consistency: Txt = None


class ShadowSun(_M):
    azimuth_estimate: Txt = None
    elevation_estimate: Txt = None
    hemisphere: Txt = None


class ShadowTime(_M):
    time_range: Txt = None
    confidence: Txt = None
    evidence: Txt = None


class ShadowSeason(_M):
    estimated_season: Txt = None
    confidence: Txt = None
    evidence: Txt = None


class ShadowLighting(_M):
    primary_source: Txt = None
    artificial_sources: Txt = None
    consistency: Txt = None


class ShadowSchema(_M):
    summary: Txt = None
    shadow_geometry: ShadowGeometry = Field(default_factory=ShadowGeometry)
    sun_position: ShadowSun = Field(default_factory=ShadowSun)
    time_estimate: ShadowTime = Field(default_factory=ShadowTime)
    season_inference: ShadowSeason = Field(default_factory=ShadowSeason)
    lighting_analysis: ShadowLighting = Field(default_factory=ShadowLighting)
    forensic_indicators: Strs = Field(default_factory=list)
    limitations: Strs = Field(default_factory=list)


# --------------------------------------------------------------- infrastructure
class Building(_M):
    id: Int = None
    type: Txt = None
    stories: Txt = None
    condition: Txt = None
    age: Txt = None
    strategic_value: Txt = None


class InfraStrategic(_M):
    critical_infrastructure: Txt = None
    vulnerability_points: Txt = None
    military_significance: Txt = None


class InfrastructureSchema(_M):
    summary: Txt = None
    buildings: _items_of(Building) = Field(default_factory=list)  # type: ignore[valid-type]
    roads: Anys = Field(default_factory=list)
    utilities: Anys = Field(default_factory=list)
    bridges: Strs = Field(default_factory=list)
    signage: Anys = Field(default_factory=list)
    strategic_assessment: InfraStrategic = Field(default_factory=InfraStrategic)
    limitations: Strs = Field(default_factory=list)


# --------------------------------------------------------------------- temporal
class TemporalStructural(_M):
    active_construction: Txt = None
    recent_damage: Txt = None
    temporary_structures: Strs = Field(default_factory=list)
    estimated_age: Txt = None


class TemporalActivity(_M):
    activity_level: Txt = None
    predominant_type: Txt = None
    unusual_patterns: Txt = None


class TemporalPosture(_M):
    classification: Txt = None
    confidence: Txt = None
    evidence: Txt = None


class TemporalEnvironment(_M):
    vegetation: Txt = None
    terrain: Txt = None
    climate_indicators: Txt = None


class TemporalEvent(_M):
    event: Txt = None
    timeframe: Txt = None


class TemporalSchema(_M):
    summary: Txt = None
    structural_changes: TemporalStructural = Field(default_factory=TemporalStructural)
    activity_detection: TemporalActivity = Field(default_factory=TemporalActivity)
    strategic_posture: TemporalPosture = Field(default_factory=TemporalPosture)
    environmental_changes: TemporalEnvironment = Field(default_factory=TemporalEnvironment)
    chronology: _items_of(TemporalEvent) = Field(default_factory=list)  # type: ignore[valid-type]
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------ night vision
class NightVisibility(_M):
    illumination_level: Txt = None
    observation_range: Txt = None
    image_quality: Txt = None


class NightLights(_M):
    total_count: Int = None
    dominant_type: Txt = None
    anomalous_sources: Txt = None


class NightActivity(_M):
    activity_level: Txt = None
    personnel_detected: Txt = None
    active_vehicles: Txt = None
    operations: Txt = None


class NightCovert(_M):
    concealment_detected: Txt = None
    thermal_signatures: Txt = None
    suspicion_level: Txt = None


class NightTactical(_M):
    vulnerabilities: Txt = None
    surveillance_coverage: Txt = None
    night_risk_level: Txt = None


class NightVisionSchema(_M):
    summary: Txt = None
    visibility_conditions: NightVisibility = Field(default_factory=NightVisibility)
    light_sources: NightLights = Field(default_factory=NightLights)
    nocturnal_activity: NightActivity = Field(default_factory=NightActivity)
    covert_indicators: NightCovert = Field(default_factory=NightCovert)
    tactical_assessment: NightTactical = Field(default_factory=NightTactical)
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------------- NATO
class NatoEntity(_M):
    description: Txt = None
    sidc: Txt = Field(default=None, description="SIDC APP-6D/MIL-STD-2525D de 20 dígitos")
    affiliation: Txt = None
    dimension: Txt = None
    function_id: Txt = None
    confidence: Txt = None


class NatoForce(_M):
    friendly: Int = 0
    hostile: Int = 0
    neutral: Int = 0
    unknown: Int = 0


class NatoEnvironment(_M):
    domain: Txt = None
    weather_impact: Txt = None
    terrain_classification: Txt = None


class NatoSchema(_M):
    summary: Txt = None
    identified_entities: _items_of(NatoEntity) = Field(default_factory=list)  # type: ignore[valid-type]
    force_composition: NatoForce = Field(default_factory=NatoForce)
    operational_environment: NatoEnvironment = Field(default_factory=NatoEnvironment)
    tactical_graphics: Strs = Field(default_factory=list)
    limitations: Strs = Field(default_factory=list)


# ------------------------------------------------------------------ multi monitor
class MonComplexity(_M):
    level: Txt = None
    detail_density: Txt = None
    priority_agents: Strs = Field(default_factory=list)
    recommended_panels: Txt = None


class MonLayout(_M):
    monitor_count: Int = None
    primary_display: Txt = None
    secondary_displays: Anys = Field(default_factory=list)
    layout_type: Txt = None


class MonDensity(_M):
    critical_data_points: Strs = Field(default_factory=list)
    recommended_zoom_areas: Strs = Field(default_factory=list)
    declutter_suggestions: Strs = Field(default_factory=list)


class MonAlert(_M):
    priority: Txt = None
    description: Txt = None
    panel: Txt = None
    action: Txt = None


class MultiMonitorSchema(_M):
    summary: Txt = None
    scene_complexity: MonComplexity = Field(default_factory=MonComplexity)
    layout_recommendation: MonLayout = Field(default_factory=MonLayout)
    information_density: MonDensity = Field(default_factory=MonDensity)
    alert_priorities: _items_of(MonAlert) = Field(default_factory=list)  # type: ignore[valid-type]
    limitations: Strs = Field(default_factory=list)
