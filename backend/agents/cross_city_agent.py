"""
PRANAVYU — Cross-City Learning Agent

Maintains institutional memory of air quality interventions across
Indian cities and recommends evidence-backed policies.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

from backend.models.schemas import (
    PRANAVYUState, CrossCityRecommendation, PolicyOutcome
)
from backend.data.synthetic import POLICY_OUTCOMES


def _find_relevant_outcomes(
    city: str,
    current_aqi: float,
    dominant_source: str,
) -> list[PolicyOutcome]:
    """Find policy outcomes relevant to the city's current situation."""
    # Exclude querying city's own outcomes
    relevant = [p for p in POLICY_OUTCOMES if p.city.lower() != city.lower()]

    # Filter by source type relevance
    source_to_policy: dict[str, list[str]] = {
        "construction": ["construction_dust"],
        "traffic":      ["vehicle_restriction"],
        "industrial":   ["industrial_monitoring", "industrial_upgrade"],
        "burning":      ["waste_management"],
    }
    relevant_types = source_to_policy.get(dominant_source, [])
    if relevant_types:
        relevant = [p for p in relevant if p.policy_type in relevant_types] or relevant

    # Sort by absolute AQI delta (most effective first)
    relevant.sort(key=lambda p: abs(p.delta_aqi), reverse=True)
    return relevant[:4]


def _make_recommendation(
    outcomes: list[PolicyOutcome],
    dominant_source: str,
    current_aqi: float,
) -> CrossCityRecommendation | None:
    if not outcomes:
        return None

    best = outcomes[0]
    evidence_cities = list({o.city for o in outcomes})
    avg_delta = sum(abs(o.delta_aqi) for o in outcomes) / len(outcomes)

    policy_descriptions: dict[str, str] = {
        "construction_dust": "Mandatory anti-dust measures for construction sites (mist cannons, debris netting, wheel washers)",
        "vehicle_restriction": "Time-based heavy vehicle restriction on arterial roads (6 AM – 10 PM)",
        "industrial_monitoring": "Real-time CCTV + continuous emission monitoring at industrial units",
        "industrial_upgrade": "Forced technology upgrade for high-pollution industrial units",
        "waste_management": "Zero-tolerance waste burning enforcement + community composting",
    }

    difficulty: dict[str, str] = {
        "construction_dust": "Medium",
        "vehicle_restriction": "Medium",
        "industrial_monitoring": "Low",
        "industrial_upgrade": "High",
        "waste_management": "Low",
    }

    rec_text = policy_descriptions.get(best.policy_type, f"Adopt {best.policy_name} from {best.city}")

    return CrossCityRecommendation(
        recommendation=rec_text,
        evidence_cities=evidence_cities,
        expected_delta_aqi=-round(avg_delta, 1),
        implementation_difficulty=difficulty.get(best.policy_type, "Medium"),
        policy_type=best.policy_type,
        supporting_outcomes=outcomes,
    )


def run_cross_city_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node: Cross-City Learning Agent.
    Generates policy recommendations based on what worked in comparable cities.
    """
    s = PRANAVYUState(**state)

    # Find dominant sources from attribution
    dominant_sources: list[str] = []
    if s.attribution_results:
        for result in s.attribution_results[:3]:
            if result.dominant_source not in dominant_sources:
                dominant_sources.append(result.dominant_source)

    if not dominant_sources:
        dominant_sources = ["industrial", "construction", "traffic"]

    avg_aqi = 0.0
    if s.live_readings:
        aqis = [r.aqi for r in s.live_readings if r.aqi]
        avg_aqi = sum(aqis) / len(aqis) if aqis else 150.0

    recommendations: list[CrossCityRecommendation] = []
    seen_types: set[str] = set()

    for source_type in dominant_sources:
        outcomes = _find_relevant_outcomes(s.city, avg_aqi, source_type)
        rec = _make_recommendation(outcomes, source_type, avg_aqi)
        if rec and rec.policy_type not in seen_types:
            recommendations.append(rec)
            seen_types.add(rec.policy_type)

    s.cross_city_recommendations = recommendations
    s.agent_trace.append({
        "agent": "cross_city_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "recommendations_generated": len(recommendations),
        "sources_analyzed": dominant_sources,
    })
    s.completed_agents.append("cross_city_agent")
    return s.model_dump()
