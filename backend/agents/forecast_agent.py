"""
PRANAVYU — Predictive AQI Forecasting Agent

Generates 72-hour ward-level AQI forecasts using:
- Historical pattern (diurnal + seasonal model)
- Current weather trend extrapolation
- Source emission schedule (known emission patterns)
- XGBoost-inspired feature engineering (rule-based for hackathon speed)
"""
from __future__ import annotations
import math
import random
from datetime import datetime, timedelta
from typing import Any

from backend.models.schemas import (
    PRANAVYUState, WardForecast, ForecastPoint
)
from backend.data.synthetic import _base_aqi_for_ward, BENGALURU_WARDS


def _aqi_category(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"


def _health_risk(aqi: float) -> str:
    if aqi <= 100: return "Low"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "High"
    if aqi <= 400: return "Very High"
    return "Severe"


def _wind_factor(hour: int, wind_speed: float, mixing_height: float) -> float:
    """
    Dispersion factor: higher wind + high mixing height = lower AQI.
    Returns multiplier (1.0 = neutral, <1 = cleaner, >1 = more polluted).
    """
    wind_factor = max(0.6, 1.0 - (wind_speed - 3.0) * 0.04)
    mix_factor = max(0.7, 1.0 - (mixing_height - 300) / 2000)
    return wind_factor * mix_factor


def _dominant_factor(hour: int, ward_id: str) -> str:
    """Identify what's driving pollution at this hour."""
    if 8 <= hour <= 10:
        return "morning traffic peak"
    elif 17 <= hour <= 20:
        return "evening traffic + boundary layer collapse"
    elif hour >= 21 or hour <= 3:
        if ward_id in ("BLR_003", "BLR_008"):
            return "industrial night operations"
        return "nighttime atmospheric stability"
    elif 4 <= hour <= 6:
        return "early morning burning + low mixing height"
    else:
        return "mixed urban emissions"


def _forecast_ward(
    ward: dict,
    current_aqi: float,
    current_weather_wind_speed: float,
    current_weather_mixing_height: float,
    start_time: datetime,
    hours: int = 72,
) -> WardForecast:
    """Generate hour-by-hour forecast for a single ward."""
    forecast_points: list[ForecastPoint] = []
    peak_aqi = 0.0
    peak_time = start_time

    for i in range(hours):
        future_time = start_time + timedelta(hours=i)
        hour = future_time.hour

        # Base from historical pattern
        base = _base_aqi_for_ward(ward["ward_id"], hour, day_offset=i // 24)

        # Smooth toward current observed value (for first 6 hours)
        if i < 6:
            blend = (6 - i) / 6
            base = base * (1 - blend) + current_aqi * blend

        # Apply wind/mixing dispersion effect
        # Wind speed decreases at night (calm), increases daytime
        future_wind = current_weather_wind_speed * (0.7 if hour < 6 or hour > 20 else 1.1)
        future_mix = current_weather_mixing_height * (0.5 if hour < 8 or hour > 18 else 1.2)
        disp_factor = _wind_factor(hour, future_wind, future_mix)

        predicted = base * disp_factor
        predicted = max(25.0, predicted)

        # Confidence intervals widen with time
        uncertainty = 15 + i * 0.8
        lower = max(10.0, predicted - uncertainty)
        upper = predicted + uncertainty

        # PM2.5 from AQI (approximate)
        pm25 = predicted * 0.42

        forecast_points.append(ForecastPoint(
            timestamp=future_time,
            predicted_aqi=round(predicted, 1),
            pm25_forecast=round(pm25, 1),
            confidence_lower=round(lower, 1),
            confidence_upper=round(upper, 1),
            dominant_factor=_dominant_factor(hour, ward["ward_id"]),
        ))

        if predicted > peak_aqi:
            peak_aqi = predicted
            peak_time = future_time

    key_drivers = _key_drivers(ward["ward_id"], current_aqi, current_weather_wind_speed)

    return WardForecast(
        ward_id=ward["ward_id"],
        ward_name=ward["ward_name"],
        city="Bengaluru",
        generated_at=start_time,
        forecast_points=forecast_points,
        peak_aqi=round(peak_aqi, 1),
        peak_time=peak_time,
        health_risk=_health_risk(peak_aqi),
        key_drivers=key_drivers,
    )


def _key_drivers(ward_id: str, current_aqi: float, wind_speed: float) -> list[str]:
    drivers = []
    if current_aqi > 200:
        drivers.append("High baseline pollution from industrial/traffic sources")
    if wind_speed < 2.5:
        drivers.append("Low wind speed reducing pollutant dispersal")
    if ward_id == "BLR_003":
        drivers.append("Proximity to Peenya industrial cluster")
    if ward_id in ("BLR_001", "BLR_004"):
        drivers.append("Active construction activity in ward")
    if ward_id == "BLR_012":
        drivers.append("Waste burning activity pattern detected")
    drivers.append("Nocturnal boundary layer compression (4-7 AM)")
    return drivers[:4]


def run_forecast_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node: Predictive AQI Agent.
    Reads live_readings, weather from state.
    Writes ward_forecasts to state.
    """
    s = PRANAVYUState(**state)

    if not s.live_readings:
        s.errors.append("forecast_agent: no live readings")
        s.completed_agents.append("forecast_agent")
        return s.model_dump()

    weather = s.weather
    wind_speed = weather.wind_speed if weather else 3.0
    mixing_height = weather.mixing_height if weather else 400.0
    now = datetime.utcnow()

    # Build quick lookup: ward_id → current AQI
    ward_aqi: dict[str, float] = {}
    for r in s.live_readings:
        if r.ward_id and r.aqi:
            ward_aqi[r.ward_id] = r.aqi

    from backend.data.synthetic import BENGALURU_WARDS
    forecasts: list[WardForecast] = []

    for ward in BENGALURU_WARDS:
        current = ward_aqi.get(ward["ward_id"], 150.0)
        fc = _forecast_ward(
            ward=ward,
            current_aqi=current,
            current_weather_wind_speed=wind_speed,
            current_weather_mixing_height=mixing_height,
            start_time=now,
            hours=72,
        )
        forecasts.append(fc)

    s.ward_forecasts = forecasts
    s.agent_trace.append({
        "agent": "forecast_agent",
        "timestamp": now.isoformat(),
        "wards_forecasted": len(forecasts),
        "forecast_hours": 72,
    })
    s.completed_agents.append("forecast_agent")
    return s.model_dump()
