"""
PRANAVYU — Synthetic Data Generator
Produces realistic demo data for Bengaluru (and other cities).
Used when live APIs are unavailable or for evaluation/testing.
"""
from __future__ import annotations
import random
import math
from datetime import datetime, timedelta
from typing import Optional
from backend.models.schemas import (
    AQIReading, WeatherSnapshot, EmissionSource,
    Ward, PolicyOutcome
)


# ─── Bengaluru Wards (real approximate coords) ───────────────────────────────

BENGALURU_WARDS: list[dict] = [
    {"ward_id": "BLR_001", "ward_name": "Whitefield",      "lat": 12.9698, "lon": 77.7499, "population": 280000, "vulnerability_score": 0.45},
    {"ward_id": "BLR_002", "ward_name": "HSR Layout",      "lat": 12.9116, "lon": 77.6389, "population": 195000, "vulnerability_score": 0.60},
    {"ward_id": "BLR_003", "ward_name": "Peenya",          "lat": 13.0284, "lon": 77.5194, "population": 165000, "vulnerability_score": 0.75},
    {"ward_id": "BLR_004", "ward_name": "Marathahalli",    "lat": 12.9591, "lon": 77.6974, "population": 220000, "vulnerability_score": 0.55},
    {"ward_id": "BLR_005", "ward_name": "Koramangala",     "lat": 12.9352, "lon": 77.6245, "population": 150000, "vulnerability_score": 0.50},
    {"ward_id": "BLR_006", "ward_name": "Yelahanka",       "lat": 13.1005, "lon": 77.5963, "population": 185000, "vulnerability_score": 0.40},
    {"ward_id": "BLR_007", "ward_name": "Bellandur",       "lat": 12.9259, "lon": 77.6746, "population": 175000, "vulnerability_score": 0.55},
    {"ward_id": "BLR_008", "ward_name": "Rajajinagar",     "lat": 12.9954, "lon": 77.5568, "population": 140000, "vulnerability_score": 0.65},
    {"ward_id": "BLR_009", "ward_name": "Electronic City", "lat": 12.8399, "lon": 77.6770, "population": 210000, "vulnerability_score": 0.45},
    {"ward_id": "BLR_010", "ward_name": "Hebbal",          "lat": 13.0358, "lon": 77.5970, "population": 130000, "vulnerability_score": 0.55},
    {"ward_id": "BLR_011", "ward_name": "Indiranagar",     "lat": 12.9784, "lon": 77.6408, "population": 125000, "vulnerability_score": 0.50},
    {"ward_id": "BLR_012", "ward_name": "Kadugodi",        "lat": 12.9935, "lon": 77.7571, "population": 155000, "vulnerability_score": 0.55},
]

# ─── Synthetic Emission Sources ───────────────────────────────────────────────

EMISSION_SOURCES: list[dict] = [
    # Industrial — Peenya (heavy industrial zone)
    {"source_id": "SRC_001", "name": "Peenya Cement Batching Plant A", "category": "industrial",
     "lat": 13.0290, "lon": 77.5185, "ward_id": "BLR_003",
     "permit_status": "valid", "historical_violation_rate": 0.72,
     "typical_peak_hour_start": 22, "typical_peak_hour_end": 3,
     "description": "Large cement batching plant, PM2.5 primary source"},

    {"source_id": "SRC_002", "name": "Peenya Steel Rolling Mill", "category": "industrial",
     "lat": 13.0276, "lon": 77.5201, "ward_id": "BLR_003",
     "permit_status": "valid", "historical_violation_rate": 0.58,
     "typical_peak_hour_start": 23, "typical_peak_hour_end": 4,
     "description": "Steel rolling, high SO2 and particulate emissions"},

    {"source_id": "SRC_003", "name": "Rajajinagar Foundry", "category": "industrial",
     "lat": 12.9960, "lon": 77.5560, "ward_id": "BLR_008",
     "permit_status": "expired", "historical_violation_rate": 0.85,
     "typical_peak_hour_start": 21, "typical_peak_hour_end": 2,
     "description": "Metal casting foundry, permit expired Dec 2024"},

    # Construction sites
    {"source_id": "SRC_004", "name": "Whitefield Metro Construction", "category": "construction",
     "lat": 12.9710, "lon": 77.7480, "ward_id": "BLR_001",
     "permit_status": "valid", "historical_violation_rate": 0.35,
     "typical_peak_hour_start": 7, "typical_peak_hour_end": 18,
     "description": "Metro Phase 3 extension, high dust generation"},

    {"source_id": "SRC_005", "name": "HSR Layout Apartment Complex", "category": "construction",
     "lat": 12.9125, "lon": 77.6380, "ward_id": "BLR_002",
     "permit_status": "valid", "historical_violation_rate": 0.42,
     "typical_peak_hour_start": 8, "typical_peak_hour_end": 17,
     "description": "28-floor residential complex under construction"},

    {"source_id": "SRC_006", "name": "Bellandur Road Widening", "category": "construction",
     "lat": 12.9265, "lon": 77.6750, "ward_id": "BLR_007",
     "permit_status": "valid", "historical_violation_rate": 0.28,
     "typical_peak_hour_start": 9, "typical_peak_hour_end": 16,
     "description": "BBMP road widening project, earthmoving active"},

    # Traffic hotspots
    {"source_id": "SRC_007", "name": "Marathahalli Junction", "category": "traffic",
     "lat": 12.9562, "lon": 77.7009, "ward_id": "BLR_004",
     "permit_status": "none", "historical_violation_rate": 0.0,
     "typical_peak_hour_start": 8, "typical_peak_hour_end": 10,
     "description": "Peak-hour diesel vehicle congestion, 80k vehicles/day"},

    {"source_id": "SRC_008", "name": "Tumkur Road Corridor", "category": "traffic",
     "lat": 13.0280, "lon": 77.5190, "ward_id": "BLR_003",
     "permit_status": "none", "historical_violation_rate": 0.0,
     "typical_peak_hour_start": 7, "typical_peak_hour_end": 10,
     "description": "Heavy freight vehicles, major arterial route"},

    # Waste burning
    {"source_id": "SRC_009", "name": "Kadugodi Landfill", "category": "burning",
     "lat": 12.9940, "lon": 77.7560, "ward_id": "BLR_012",
     "permit_status": "none", "historical_violation_rate": 0.90,
     "typical_peak_hour_start": 4, "typical_peak_hour_end": 7,
     "description": "Illegal waste burning, early morning pattern"},
]


# ─── AQI Category Helper ─────────────────────────────────────────────────────

def aqi_category(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"


# ─── Realistic AQI model (time-of-day + seasonal + source-driven) ────────────

def _base_aqi_for_ward(ward_id: str, hour: int, day_offset: int = 0) -> float:
    """AQI baseline: real trained model (city-level trend) x ward-level
    relative multiplier (domain knowledge — industrial wards run higher)
    x diurnal pattern (time-of-day)."""
    from backend.data.city_model import predict_city_baseline

    # Relative ward multipliers, normalized around 1.0 (avg of old constants).
    # Peenya (BLR_003) stays highest — industrial area; Electronic City
    # (BLR_006) stays lowest — tech park, less industrial/traffic load.
    ward_relative: dict[str, float] = {
        "BLR_001": 1.04, "BLR_002": 0.93, "BLR_003": 1.39,
        "BLR_004": 1.11, "BLR_005": 0.86, "BLR_006": 0.75,
        "BLR_007": 1.00, "BLR_008": 1.14, "BLR_009": 0.79,
        "BLR_010": 0.96, "BLR_011": 0.82, "BLR_012": 1.07,
    }
    rel = ward_relative.get(ward_id, 1.00)

    city_baseline = predict_city_baseline(day_offset=day_offset)
    b = city_baseline * rel

    # Diurnal pattern: morning peak (8-10), evening peak (18-20), night industrial (22-2)
    if 8 <= hour <= 10:   diurnal = 1.35
    elif 18 <= hour <= 20: diurnal = 1.25
    elif hour >= 22 or hour <= 2: diurnal = 1.20  # industrial
    elif 11 <= hour <= 14: diurnal = 0.85
    else:                  diurnal = 1.00

    noise = random.gauss(0, 8)
    return max(25.0, b * diurnal + noise)


def generate_live_readings(
    city: str = "Bengaluru",
    timestamp: Optional[datetime] = None
) -> list[AQIReading]:
    """Generate synthetic live AQI readings for all wards."""
    if timestamp is None:
        timestamp = datetime.utcnow()
    hour = timestamp.hour
    readings: list[AQIReading] = []

    for ward in BENGALURU_WARDS:
        aqi_val = _base_aqi_for_ward(ward["ward_id"], hour)
        pm25 = aqi_val * 0.42 + random.gauss(0, 3)
        pm10 = pm25 * 1.85 + random.gauss(0, 5)
        no2 = aqi_val * 0.18 + random.gauss(0, 2)

        readings.append(AQIReading(
            station_id=f"CAAQMS_{ward['ward_id']}",
            station_name=f"{ward['ward_name']} Monitoring Station",
            city=city,
            ward_id=ward["ward_id"],
            lat=ward["lat"],
            lon=ward["lon"],
            timestamp=timestamp,
            pm25=round(max(5.0, pm25), 1),
            pm10=round(max(10.0, pm10), 1),
            no2=round(max(2.0, no2), 1),
            o3=round(random.uniform(20, 60), 1),
            co=round(random.uniform(0.5, 3.0), 2),
            so2=round(random.uniform(5, 25), 1),
            aqi=round(aqi_val, 1),
            aqi_category=aqi_category(aqi_val),
        ))
    return readings


def generate_weather(
    city: str = "Bengaluru",
    timestamp: Optional[datetime] = None
) -> WeatherSnapshot:
    """Generate realistic Bengaluru weather."""
    if timestamp is None:
        timestamp = datetime.utcnow()
    hour = timestamp.hour

    # Bengaluru typical: mild, SW monsoon direction
    wind_dir = 220 + random.gauss(0, 25)   # SW dominant
    wind_speed = random.uniform(1.5, 6.0)
    temp = 24 + 4 * math.sin((hour - 6) * math.pi / 12)  # peaks ~3PM
    mixing_height = 200 + 600 * max(0, math.sin((hour - 6) * math.pi / 14))

    return WeatherSnapshot(
        city=city,
        timestamp=timestamp,
        temperature=round(temp, 1),
        humidity=round(random.uniform(45, 75), 1),
        wind_speed=round(wind_speed, 1),
        wind_direction=round(wind_dir % 360, 1),
        mixing_height=round(mixing_height, 0),
        pressure=round(random.uniform(1008, 1018), 1),
    )


def get_emission_sources(city: str = "Bengaluru") -> list[EmissionSource]:
    """Return all known emission sources for the city."""
    sources = []
    for s in EMISSION_SOURCES:
        sources.append(EmissionSource(
            source_id=s["source_id"],
            name=s["name"],
            category=s["category"],
            lat=s["lat"],
            lon=s["lon"],
            city=city,
            ward_id=s["ward_id"],
            permit_status=s["permit_status"],
            historical_violation_rate=s["historical_violation_rate"],
            typical_peak_hour_start=s["typical_peak_hour_start"],
            typical_peak_hour_end=s["typical_peak_hour_end"],
            description=s["description"],
        ))
    return sources


def get_wards(city: str = "Bengaluru") -> list[Ward]:
    return [
        Ward(city=city, **{k: v for k, v in w.items()})
        for w in BENGALURU_WARDS
    ]


def generate_historical_readings(
    ward_id: str,
    hours_back: int = 72
) -> list[tuple[datetime, float]]:
    """Generate historical AQI time series for a ward (for forecasting)."""
    now = datetime.utcnow()
    series = []
    for i in range(hours_back, 0, -1):
        ts = now - timedelta(hours=i)
        aqi = _base_aqi_for_ward(ward_id, ts.hour, day_offset=i // 24)
        series.append((ts, round(aqi, 1)))
    return series


# ─── Policy Outcomes Corpus ───────────────────────────────────────────────────

POLICY_OUTCOMES: list[PolicyOutcome] = [
    PolicyOutcome(city="Pune", policy_name="Mandatory mist cannon on construction sites",
                  policy_type="construction_dust",
                  implementation_date="2023-01", aqi_before=175.0, aqi_after=148.0,
                  delta_aqi=-27.0, confidence="High",
                  source="Maharashtra SPCB Annual Report 2023"),
    PolicyOutcome(city="Delhi", policy_name="Odd-Even vehicle restriction (peak hours)",
                  policy_type="vehicle_restriction",
                  implementation_date="2023-11", aqi_before=310.0, aqi_after=278.0,
                  delta_aqi=-32.0, confidence="Medium",
                  source="DPCC Monitoring Data Nov 2023"),
    PolicyOutcome(city="Chennai", policy_name="Construction activity ban 6AM-10AM",
                  policy_type="construction_dust",
                  implementation_date="2024-01", aqi_before=155.0, aqi_after=132.0,
                  delta_aqi=-23.0, confidence="High",
                  source="TNPCB Q1 2024 Report"),
    PolicyOutcome(city="Mumbai", policy_name="Night truck movement ban within city limits",
                  policy_type="vehicle_restriction",
                  implementation_date="2023-06", aqi_before=195.0, aqi_after=168.0,
                  delta_aqi=-27.0, confidence="Medium",
                  source="MPCB Annual Report 2023"),
    PolicyOutcome(city="Hyderabad", policy_name="Real-time CCTV monitoring at industrial units",
                  policy_type="industrial_monitoring",
                  implementation_date="2024-03", aqi_before=185.0, aqi_after=152.0,
                  delta_aqi=-33.0, confidence="High",
                  source="TSPCB Quarterly Bulletin Q2 2024"),
    PolicyOutcome(city="Kolkata", policy_name="Brick kiln modernisation (zigzag technology)",
                  policy_type="industrial_upgrade",
                  implementation_date="2022-10", aqi_before=230.0, aqi_after=190.0,
                  delta_aqi=-40.0, confidence="High",
                  source="WBPCB Monitoring Report 2023"),
]
