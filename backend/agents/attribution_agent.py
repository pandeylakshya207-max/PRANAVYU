"""
PRANAVYU — Source Attribution Agent

Determines which emission sources are responsible for current AQI
at each ward using Gaussian reverse plume modeling + source profiling.
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Any

from backend.models.schemas import (
    PRANAVYUState, AttributionResult, SourceAttribution
)
from backend.utils.dispersion import (
    compute_source_attribution, aggregate_by_category
)


def run_attribution_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node: Source Attribution Agent.
    Reads live_readings, weather, emission_sources from state.
    Writes attribution_results to state.
    """
    s = PRANAVYUState(**state)

    if not s.live_readings:
        s.errors.append("attribution_agent: no live readings available")
        s.completed_agents.append("attribution_agent")
        return s.model_dump()

    weather = s.weather
    if weather is None:
        s.errors.append("attribution_agent: no weather data")
        s.completed_agents.append("attribution_agent")
        return s.model_dump()

    # Convert emission sources to dicts for dispersion model
    src_dicts = [
        {
            "source_id": src.source_id,
            "name": src.name,
            "category": src.category,
            "lat": src.lat,
            "lon": src.lon,
            "historical_violation_rate": src.historical_violation_rate,
        }
        for src in s.emission_sources
    ]

    hour = weather.timestamp.hour
    results: list[AttributionResult] = []

    for reading in s.live_readings:
        if reading.aqi is None:
            continue

        contribs = compute_source_attribution(
            receptor_lat=reading.lat,
            receptor_lon=reading.lon,
            sources=src_dicts,
            wind_direction=weather.wind_direction,
            wind_speed=weather.wind_speed,
            mixing_height=weather.mixing_height,
            hour=hour,
            aqi_value=reading.aqi,
        )

        category_fractions = aggregate_by_category(contribs)
        dominant = max(category_fractions, key=category_fractions.get) if category_fractions else "unknown"

        # Top 3 primary sources for the dominant category
        primary_sources = [
            c.source_name for c in contribs
            if c.category == dominant and c.normalized_fraction > 0.05
        ][:3]

        attributions = [
            SourceAttribution(
                source_category=cat,
                contribution_fraction=frac,
                confidence=max(
                    (c.confidence_contribution for c in contribs if c.category == cat),
                    default=0.5
                ),
                primary_sources=[
                    c.source_name for c in contribs
                    if c.category == cat and c.normalized_fraction > 0.02
                ][:2],
            )
            for cat, frac in sorted(category_fractions.items(), key=lambda x: -x[1])
        ]

        # Overall confidence: average of top 2 contributors
        top_conf = [a.confidence for a in attributions[:2]]
        overall_conf = round(sum(top_conf) / len(top_conf), 2) if top_conf else 0.5

        explanation = _build_explanation(
            ward_name=reading.station_name.replace(" Monitoring Station", ""),
            aqi=reading.aqi,
            category_fractions=category_fractions,
            primary_sources=primary_sources,
            wind_dir=weather.wind_direction,
            wind_speed=weather.wind_speed,
            hour=hour,
        )

        results.append(AttributionResult(
            ward_id=reading.ward_id or reading.station_id,
            ward_name=reading.station_name.replace(" Monitoring Station", ""),
            city=reading.city,
            timestamp=reading.timestamp,
            current_aqi=reading.aqi,
            attributions=attributions,
            overall_confidence=overall_conf,
            explanation=explanation,
            dominant_source=dominant,
        ))

    s.attribution_results = results
    s.agent_trace.append({
        "agent": "attribution_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "wards_processed": len(results),
        "wind_direction": weather.wind_direction,
        "wind_speed": weather.wind_speed,
    })
    s.completed_agents.append("attribution_agent")
    return s.model_dump()


def _build_explanation(
    ward_name: str,
    aqi: float,
    category_fractions: dict[str, float],
    primary_sources: list[str],
    wind_dir: float,
    wind_speed: float,
    hour: int,
) -> str:
    dominant = max(category_fractions, key=category_fractions.get) if category_fractions else "mixed"
    dom_pct = round(category_fractions.get(dominant, 0) * 100)

    wind_compass = _degrees_to_compass(wind_dir)
    time_context = "night-time" if hour >= 21 or hour <= 5 else ("morning rush" if 7 <= hour <= 10 else "daytime")

    src_text = ""
    if primary_sources:
        src_text = f", primarily from {primary_sources[0]}"
        if len(primary_sources) > 1:
            src_text += f" and {primary_sources[1]}"

    return (
        f"{ward_name} AQI is {aqi:.0f} ({_aqi_label(aqi)}). "
        f"During {time_context} with {wind_speed:.1f} m/s {wind_compass} winds, "
        f"{dom_pct}% of pollution is attributed to {dominant} sources{src_text}. "
        f"Attribution based on Gaussian plume modeling + source emission profiles."
    )


def _degrees_to_compass(deg: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((deg + 22.5) / 45) % 8
    return dirs[ix]


def _aqi_label(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"
