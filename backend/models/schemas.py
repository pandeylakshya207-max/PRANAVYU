"""
PRANAVYU — Core Pydantic schemas used across all agents and API endpoints.
All types are defined here to avoid circular imports.
"""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ─── Geographic primitives ────────────────────────────────────────────────────

class Coordinates(BaseModel):
    lat: float
    lon: float


class Ward(BaseModel):
    ward_id: str
    ward_name: str
    city: str
    lat: float
    lon: float
    population: int = 0
    vulnerability_score: float = 0.5  # 0-1, higher = more vulnerable


# ─── AQI & Sensor Data ────────────────────────────────────────────────────────

class AQIReading(BaseModel):
    station_id: str
    station_name: str
    city: str
    ward_id: Optional[str] = None
    lat: float
    lon: float
    timestamp: datetime
    pm25: Optional[float] = None    # μg/m³
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    aqi: Optional[float] = None
    aqi_category: Optional[str] = None  # Good/Satisfactory/Moderate/Poor/Very Poor/Severe


class WeatherSnapshot(BaseModel):
    city: str
    timestamp: datetime
    temperature: float          # Celsius
    humidity: float             # %
    wind_speed: float           # m/s
    wind_direction: float       # degrees (0=N, 90=E, 180=S, 270=W)
    mixing_height: float = 500  # meters — boundary layer height
    pressure: float = 1013.0   # hPa


# ─── Source Attribution ───────────────────────────────────────────────────────

class SourceAttribution(BaseModel):
    source_category: str        # industrial/traffic/construction/burning/other
    contribution_fraction: float  # 0-1, sum across categories = 1
    confidence: float           # 0-1
    primary_sources: list[str] = Field(default_factory=list)  # specific source names/IDs


class AttributionResult(BaseModel):
    ward_id: str
    ward_name: str
    city: str
    timestamp: datetime
    current_aqi: float
    attributions: list[SourceAttribution]
    overall_confidence: float
    explanation: str
    dominant_source: str


# ─── Emission Sources ─────────────────────────────────────────────────────────

class EmissionSource(BaseModel):
    source_id: str
    name: str
    category: str              # industrial/construction/traffic_hotspot/burning
    lat: float
    lon: float
    city: str
    ward_id: str
    permit_status: str = "valid"  # valid/expired/none
    historical_violation_rate: float = 0.0  # 0-1
    typical_peak_hour_start: int = 22  # 24hr format
    typical_peak_hour_end: int = 2
    description: str = ""


# ─── Forecasting ─────────────────────────────────────────────────────────────

class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_aqi: float
    pm25_forecast: float
    confidence_lower: float
    confidence_upper: float
    dominant_factor: str       # what's driving this forecast


class WardForecast(BaseModel):
    ward_id: str
    ward_name: str
    city: str
    generated_at: datetime
    forecast_points: list[ForecastPoint]  # 72 hourly points
    peak_aqi: float
    peak_time: datetime
    health_risk: str           # Low/Moderate/High/Very High/Severe
    key_drivers: list[str]


# ─── Enforcement ─────────────────────────────────────────────────────────────

class EnforcementAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: EmissionSource
    violation_probability: float   # 0-1
    optimal_inspection_start: int  # hour (0-23)
    optimal_inspection_end: int
    priority_rank: int
    evidence_summary: str
    contributing_aqi_ward: str
    estimated_aqi_impact: float    # μg/m³ PM2.5 if source stopped
    dispatched: bool = False


class EnforcementPlan(BaseModel):
    city: str
    generated_at: datetime
    actions: list[EnforcementAction]
    total_estimated_aqi_reduction: float


# ─── Citizen Advisories ───────────────────────────────────────────────────────

class CitizenAdvisory(BaseModel):
    ward_id: str
    ward_name: str
    city: str
    language: str              # en/kn/ta/hi/bn/te
    forecast_aqi: float
    health_risk: str
    message_short: str         # SMS / WhatsApp first line (<160 chars)
    message_full: str          # Full advisory
    recommendations: list[str]
    vulnerable_groups: list[str]  # schools/hospitals/outdoor workers in ward
    valid_until: datetime


# ─── Cross-City Intelligence ──────────────────────────────────────────────────

class PolicyOutcome(BaseModel):
    city: str
    policy_name: str
    policy_type: str           # construction_dust/vehicle_restriction/industrial
    implementation_date: str
    aqi_before: float
    aqi_after: float
    delta_aqi: float
    confidence: str
    source: str


class CrossCityRecommendation(BaseModel):
    recommendation: str
    evidence_cities: list[str]
    expected_delta_aqi: float
    implementation_difficulty: str  # Low/Medium/High
    policy_type: str
    supporting_outcomes: list[PolicyOutcome]


# ─── Master Agent State (LangGraph) ───────────────────────────────────────────

class PRANAVYUState(BaseModel):
    """
    Shared state object passed between all agents in the LangGraph workflow.
    Each agent reads from and writes to this object.
    """
    # Input
    city: str = "Bengaluru"
    target_wards: list[str] = Field(default_factory=list)
    query: Optional[str] = None          # optional natural language query

    # Data layer outputs
    live_readings: list[AQIReading] = Field(default_factory=list)
    weather: Optional[WeatherSnapshot] = None
    emission_sources: list[EmissionSource] = Field(default_factory=list)

    # Agent outputs
    attribution_results: list[AttributionResult] = Field(default_factory=list)
    ward_forecasts: list[WardForecast] = Field(default_factory=list)
    enforcement_plan: Optional[EnforcementPlan] = None
    advisories: list[CitizenAdvisory] = Field(default_factory=list)
    cross_city_recommendations: list[CrossCityRecommendation] = Field(default_factory=list)

    # Meta
    errors: list[str] = Field(default_factory=list)
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)
    completed_agents: list[str] = Field(default_factory=list)
