"""
PRANAVYU — Enforcement Intelligence Agent

Translates source attribution + emission source profiles into
actionable, evidence-backed enforcement recommendations.

Key output: prioritized enforcement queue with optimal inspection windows.
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta
from typing import Any

from backend.models.schemas import (
    PRANAVYUState, EnforcementAction, EnforcementPlan,
    EmissionSource, AttributionResult
)


def _violation_probability(
    source: EmissionSource,
    hour: int,
    attribution_fraction: float,
) -> float:
    """
    Bayesian-inspired violation probability given:
    - Historical violation rate
    - Current hour vs peak violation window
    - Attribution (is the source actively contributing right now?)
    """
    base = source.historical_violation_rate

    # Time-of-day match: is current hour in peak violation window?
    start = source.typical_peak_hour_start
    end = source.typical_peak_hour_end

    def in_window(h: int, s: int, e: int) -> bool:
        if s <= e:
            return s <= h <= e
        return h >= s or h <= e  # wraps midnight

    time_match = in_window(hour, start, end)
    time_factor = 1.35 if time_match else 0.70

    # Attribution signal: if source is actively contributing → higher probability
    attrib_factor = 1.0 + attribution_fraction * 0.8

    # Permit penalty: expired permit → higher likelihood
    permit_factor = 1.25 if source.permit_status == "expired" else 1.0

    prob = base * time_factor * attrib_factor * permit_factor
    return round(min(0.97, prob), 3)


def _estimate_aqi_impact(
    source: EmissionSource,
    attribution_fraction: float,
    current_aqi: float,
) -> float:
    """Estimated AQI reduction if this source is stopped."""
    return round(current_aqi * attribution_fraction * 0.75, 1)


def _evidence_summary(
    source: EmissionSource,
    violation_prob: float,
    attribution: float,
    contributing_ward: str,
    current_aqi: float,
) -> str:
    pct = round(attribution * 100)
    start = source.typical_peak_hour_start
    end = source.typical_peak_hour_end
    end_str = f"{end:02d}:00"
    start_str = f"{start:02d}:00"

    lines = [
        f"Source: {source.name} ({source.category.title()})",
        f"Permit status: {source.permit_status.upper()}",
        f"Contribution to {contributing_ward}: {pct}% of AQI {current_aqi:.0f}",
        f"Historical violation rate: {source.historical_violation_rate * 100:.0f}%",
        f"Typical violation window: {start_str}–{end_str}",
        f"Violation probability NOW: {violation_prob * 100:.0f}%",
    ]
    return " | ".join(lines)


def run_enforcement_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node: Enforcement Intelligence Agent.
    Reads attribution_results, emission_sources, weather from state.
    Writes enforcement_plan to state.
    """
    s = PRANAVYUState(**state)

    if not s.attribution_results or not s.emission_sources:
        s.errors.append("enforcement_agent: missing attribution or source data")
        s.completed_agents.append("enforcement_agent")
        return s.model_dump()

    weather = s.weather
    hour = weather.timestamp.hour if weather else datetime.utcnow().hour

    # Build lookup: source_id → ward attribution fraction
    # A source can appear across multiple wards; take max contribution
    source_max_contrib: dict[str, tuple[float, AttributionResult]] = {}

    for result in s.attribution_results:
        for attr in result.attributions:
            for src in s.emission_sources:
                if src.category == attr.source_category:
                    existing = source_max_contrib.get(src.source_id)
                    if existing is None or attr.contribution_fraction > existing[0]:
                        source_max_contrib[src.source_id] = (
                            attr.contribution_fraction, result
                        )

    actions: list[EnforcementAction] = []
    total_aqi_reduction = 0.0

    for source in s.emission_sources:
        # Only industrial and burning sources get enforcement actions
        # Traffic hotspots are handled differently (signal optimization, not inspection)
        if source.category in ("traffic",):
            continue

        contrib_data = source_max_contrib.get(source.source_id)
        if contrib_data is None:
            contrib_frac = 0.1  # small default contribution
            best_result = s.attribution_results[0] if s.attribution_results else None
        else:
            contrib_frac, best_result = contrib_data

        if best_result is None:
            continue

        v_prob = _violation_probability(source, hour, contrib_frac)

        # Only include in queue if meaningful violation probability
        if v_prob < 0.25:
            continue

        aqi_impact = _estimate_aqi_impact(
            source, contrib_frac, best_result.current_aqi
        )

        evidence = _evidence_summary(
            source, v_prob, contrib_frac,
            best_result.ward_name, best_result.current_aqi
        )

        actions.append(EnforcementAction(
            source=source,
            violation_probability=v_prob,
            optimal_inspection_start=source.typical_peak_hour_start,
            optimal_inspection_end=source.typical_peak_hour_end,
            priority_rank=0,  # assigned after sort
            evidence_summary=evidence,
            contributing_aqi_ward=best_result.ward_name,
            estimated_aqi_impact=aqi_impact,
        ))
        total_aqi_reduction += aqi_impact

    # Sort by priority: violation_probability × estimated_aqi_impact
    actions.sort(
        key=lambda a: a.violation_probability * a.estimated_aqi_impact,
        reverse=True
    )
    for i, action in enumerate(actions):
        action.priority_rank = i + 1

    plan = EnforcementPlan(
        city=s.city,
        generated_at=datetime.utcnow(),
        actions=actions,
        total_estimated_aqi_reduction=round(total_aqi_reduction, 1),
    )

    s.enforcement_plan = plan
    s.agent_trace.append({
        "agent": "enforcement_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "actions_generated": len(actions),
        "total_estimated_aqi_reduction": plan.total_estimated_aqi_reduction,
    })
    s.completed_agents.append("enforcement_agent")
    return s.model_dump()
