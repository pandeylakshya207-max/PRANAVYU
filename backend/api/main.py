"""
PRANAVYU — FastAPI Backend
Exposes all agent outputs via REST API.
"""
from __future__ import annotations
import os
import time
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.agents.orchestrator import run_full_pipeline, build_workflow
from backend.data.synthetic import (
    generate_live_readings, generate_weather,
    get_emission_sources, get_wards, POLICY_OUTCOMES
)
from backend.models.schemas import PRANAVYUState


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PRANAVYU API",
    description="Multi-agent Urban Air Quality Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for pipeline results (refreshed every 15 min)
_cache: dict[str, Any] = {}
_cache_time: dict[str, float] = {}
CACHE_TTL = 900  # 15 minutes


def _get_cached(city: str) -> dict[str, Any] | None:
    t = _cache_time.get(city, 0)
    if time.time() - t < CACHE_TTL and city in _cache:
        return _cache[city]
    return None


def _set_cached(city: str, data: dict[str, Any]) -> None:
    _cache[city] = data
    _cache_time[city] = time.time()


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "PRANAVYU", "timestamp": datetime.utcnow().isoformat()}


# ─── Pipeline ─────────────────────────────────────────────────────────────────

@app.get("/api/pipeline/{city}")
def run_pipeline(
    city: str = "Bengaluru",
    refresh: bool = Query(False, description="Force refresh, bypass cache"),
) -> dict:
    """Run full 6-agent pipeline for a city."""
    cached = _get_cached(city)
    if cached and not refresh:
        return {"source": "cache", "data": cached}
    result = run_full_pipeline(city)
    _set_cached(city, result)
    return {"source": "live", "data": result}


# ─── Live Data ────────────────────────────────────────────────────────────────

@app.get("/api/readings/{city}")
def get_readings(city: str = "Bengaluru") -> dict:
    """Live AQI readings for all wards."""
    readings = generate_live_readings(city)
    return {
        "city": city,
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(readings),
        "readings": [r.model_dump() for r in readings],
    }


@app.get("/api/weather/{city}")
def get_weather(city: str = "Bengaluru") -> dict:
    """Current weather snapshot."""
    w = generate_weather(city)
    return w.model_dump()


@app.get("/api/sources/{city}")
def get_sources(city: str = "Bengaluru") -> dict:
    """Emission sources registry."""
    sources = get_emission_sources(city)
    return {
        "city": city,
        "count": len(sources),
        "sources": [s.model_dump() for s in sources],
    }


@app.get("/api/wards/{city}")
def get_wards_endpoint(city: str = "Bengaluru") -> dict:
    """Ward list with coordinates."""
    wards = get_wards(city)
    return {
        "city": city,
        "count": len(wards),
        "wards": [w.model_dump() for w in wards],
    }


# ─── Attribution ──────────────────────────────────────────────────────────────

@app.get("/api/attribution/{city}")
def get_attribution(
    city: str = "Bengaluru",
    ward_id: Optional[str] = Query(None),
) -> dict:
    """Source attribution results, optionally filtered by ward."""
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    results = cached.get("attribution_results", [])
    if ward_id:
        results = [r for r in results if r.get("ward_id") == ward_id]

    return {
        "city": city,
        "ward_id": ward_id,
        "count": len(results),
        "attribution_results": results,
    }


# ─── Forecasting ──────────────────────────────────────────────────────────────

@app.get("/api/forecast/{city}")
def get_forecast(
    city: str = "Bengaluru",
    ward_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=72),
) -> dict:
    """Ward-level AQI forecasts."""
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    forecasts = cached.get("ward_forecasts", [])
    if ward_id:
        forecasts = [f for f in forecasts if f.get("ward_id") == ward_id]

    # Trim forecast points to requested hours
    for fc in forecasts:
        if "forecast_points" in fc:
            fc["forecast_points"] = fc["forecast_points"][:hours]

    return {
        "city": city,
        "ward_id": ward_id,
        "forecast_hours": hours,
        "count": len(forecasts),
        "ward_forecasts": forecasts,
    }


# ─── Enforcement ──────────────────────────────────────────────────────────────

@app.get("/api/enforcement/{city}")
def get_enforcement(city: str = "Bengaluru") -> dict:
    """Enforcement intelligence plan."""
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    plan = cached.get("enforcement_plan")
    return {
        "city": city,
        "enforcement_plan": plan,
    }


class DispatchRequest(BaseModel):
    action_id: str
    inspector_id: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/enforcement/dispatch")
def dispatch_inspector(req: DispatchRequest) -> dict:
    """Mark an enforcement action as dispatched."""
    # In production: write to DB and notify inspector via SMS/app
    return {
        "status": "dispatched",
        "action_id": req.action_id,
        "dispatched_at": datetime.utcnow().isoformat(),
        "inspector_id": req.inspector_id or "auto-assigned",
        "message": "Inspector dispatch request logged. Confirmation sent via SMS.",
    }


# ─── Citizen Advisories ───────────────────────────────────────────────────────

@app.get("/api/advisories/{city}")
def get_advisories(
    city: str = "Bengaluru",
    language: Optional[str] = Query(None, description="en/kn/ta/hi"),
    ward_id: Optional[str] = Query(None),
    high_risk_only: bool = Query(False),
) -> dict:
    """Citizen health advisories."""
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    advisories = cached.get("advisories", [])

    if language:
        advisories = [a for a in advisories if a.get("language") == language]
    if ward_id:
        advisories = [a for a in advisories if a.get("ward_id") == ward_id]
    if high_risk_only:
        advisories = [a for a in advisories if a.get("health_risk") in ("High", "Very High", "Severe")]

    return {
        "city": city,
        "filters": {"language": language, "ward_id": ward_id, "high_risk_only": high_risk_only},
        "count": len(advisories),
        "advisories": advisories,
    }


# ─── Cross-City Intelligence ──────────────────────────────────────────────────

@app.get("/api/cross-city/{city}")
def get_cross_city(city: str = "Bengaluru") -> dict:
    """Cross-city policy recommendations."""
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    return {
        "city": city,
        "recommendations": cached.get("cross_city_recommendations", []),
        "policy_database": [p.model_dump() for p in POLICY_OUTCOMES],
    }


# ─── Dashboard Summary ────────────────────────────────────────────────────────

@app.get("/api/dashboard/{city}")
def get_dashboard(city: str = "Bengaluru") -> dict:
    """
    All-in-one dashboard endpoint.
    Returns aggregated summary statistics for the frontend.
    """
    cached = _get_cached(city)
    if not cached:
        cached = run_full_pipeline(city)
        _set_cached(city, cached)

    readings = cached.get("live_readings", [])
    attributions = cached.get("attribution_results", [])
    forecasts = cached.get("ward_forecasts", [])
    plan = cached.get("enforcement_plan", {})
    advisories = cached.get("advisories", [])

    # Summary stats
    aqis = [r.get("aqi", 0) for r in readings if r.get("aqi")]
    avg_aqi = round(sum(aqis) / len(aqis), 1) if aqis else 0
    max_aqi = round(max(aqis), 1) if aqis else 0

    # High risk wards
    high_risk = [
        f for f in forecasts
        if f.get("health_risk") in ("High", "Very High", "Severe")
    ]

    # Enforcement summary
    actions = plan.get("actions", []) if plan else []

    # Agent trace
    trace = cached.get("agent_trace", [])

    return {
        "city": city,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "avg_aqi": avg_aqi,
            "max_aqi": max_aqi,
            "wards_monitored": len(readings),
            "high_risk_wards": len(high_risk),
            "enforcement_actions_pending": len(actions),
            "advisories_dispatched": len([a for a in advisories if a.get("language") == "en"]),
            "estimated_aqi_reduction_possible": plan.get("total_estimated_aqi_reduction", 0) if plan else 0,
        },
        "readings": readings,
        "attribution_results": attributions,
        "ward_forecasts": [
            {
                "ward_id": f.get("ward_id"),
                "ward_name": f.get("ward_name"),
                "peak_aqi": f.get("peak_aqi"),
                "health_risk": f.get("health_risk"),
                "peak_time": f.get("peak_time"),
                "key_drivers": f.get("key_drivers", []),
                "forecast_24h": (f.get("forecast_points") or [])[:24],
            }
            for f in forecasts
        ],
        "enforcement_plan": plan,
        "advisories_en": [a for a in advisories if a.get("language") == "en"],
        "cross_city_recommendations": cached.get("cross_city_recommendations", []),
        "agent_trace": trace,
    }


# ─── Agent Trace (for LangSmith-style display) ───────────────────────────────

@app.get("/api/trace/{city}")
def get_trace(city: str = "Bengaluru") -> dict:
    """Return agent execution trace for transparency dashboard."""
    cached = _get_cached(city)
    if not cached:
        return {"city": city, "trace": [], "message": "No trace yet. Run /api/pipeline/{city} first."}
    return {
        "city": city,
        "completed_agents": cached.get("completed_agents", []),
        "errors": cached.get("errors", []),
        "trace": cached.get("agent_trace", []),
    }
