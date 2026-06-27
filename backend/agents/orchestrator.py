"""
PRANAVYU — LangGraph Orchestrator

Defines the multi-agent workflow as a LangGraph StateGraph.
Each node is an agent. Edges define execution order.
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.models.schemas import PRANAVYUState
from backend.data.synthetic import (
    generate_live_readings, generate_weather, get_emission_sources
)
from backend.agents.attribution_agent import run_attribution_agent
from backend.agents.forecast_agent import run_forecast_agent
from backend.agents.enforcement_agent import run_enforcement_agent
from backend.agents.citizen_agent import run_citizen_advisory_agent
from backend.agents.cross_city_agent import run_cross_city_agent


# ─── Data Ingestion Node ──────────────────────────────────────────────────────

def ingest_data(state: dict[str, Any]) -> dict[str, Any]:
    """
    First node: pull live data (or synthetic if APIs unavailable).
    Populates: live_readings, weather, emission_sources.
    """
    s = PRANAVYUState(**state)
    city = s.city or "Bengaluru"

    try:
        # Try live OpenAQ data first
        import httpx
        import os
        readings = _try_openaq(city)
        if not readings:
            readings = generate_live_readings(city)
    except Exception:
        readings = generate_live_readings(city)

    weather = generate_weather(city)
    sources = get_emission_sources(city)

    s.live_readings = readings
    s.weather = weather
    s.emission_sources = sources
    s.agent_trace.append({
        "agent": "data_ingestion",
        "timestamp": datetime.utcnow().isoformat(),
        "readings_count": len(readings),
        "sources_count": len(sources),
        "mode": "synthetic",
    })
    return s.model_dump()


def _try_openaq(city: str) -> list:
    """Attempt to fetch real data from OpenAQ. Returns empty list on failure."""
    return []  # For hackathon, always use synthetic (no API key required in demo)


# ─── Synthesizer Node ─────────────────────────────────────────────────────────

def synthesize_output(state: dict[str, Any]) -> dict[str, Any]:
    """
    Final node: validate completeness, build summary stats.
    """
    s = PRANAVYUState(**state)
    s.agent_trace.append({
        "agent": "synthesizer",
        "timestamp": datetime.utcnow().isoformat(),
        "agents_completed": s.completed_agents,
        "attribution_wards": len(s.attribution_results),
        "forecast_wards": len(s.ward_forecasts),
        "enforcement_actions": len(s.enforcement_plan.actions) if s.enforcement_plan else 0,
        "advisories": len(s.advisories),
        "cross_city_recs": len(s.cross_city_recommendations),
        "errors": s.errors,
    })
    return s.model_dump()


# ─── Build LangGraph ─────────────────────────────────────────────────────────

def build_workflow() -> Any:
    """
    Construct the PRANAVYU LangGraph workflow.

    Execution order:
      ingest_data
          ↓
      attribution_agent  (needs: readings, weather, sources)
          ↓
      forecast_agent     (needs: readings, weather)
          ↓
      enforcement_agent  (needs: attribution, sources, weather)
          ↓
      citizen_agent      (needs: forecasts)
          ↓
      cross_city_agent   (needs: attribution, readings)
          ↓
      synthesize_output
          ↓
         END
    """
    # Use dict[str, Any] as state type (compatible with all LangGraph versions)
    workflow = StateGraph(dict)

    workflow.add_node("ingest_data",       ingest_data)
    workflow.add_node("attribution_agent", run_attribution_agent)
    workflow.add_node("forecast_agent",    run_forecast_agent)
    workflow.add_node("enforcement_agent", run_enforcement_agent)
    workflow.add_node("citizen_agent",     run_citizen_advisory_agent)
    workflow.add_node("cross_city_agent",  run_cross_city_agent)
    workflow.add_node("synthesize_output", synthesize_output)

    workflow.set_entry_point("ingest_data")
    workflow.add_edge("ingest_data",       "attribution_agent")
    workflow.add_edge("attribution_agent", "forecast_agent")
    workflow.add_edge("forecast_agent",    "enforcement_agent")
    workflow.add_edge("enforcement_agent", "citizen_agent")
    workflow.add_edge("citizen_agent",     "cross_city_agent")
    workflow.add_edge("cross_city_agent",  "synthesize_output")
    workflow.add_edge("synthesize_output", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ─── Run Helper ───────────────────────────────────────────────────────────────

def run_full_pipeline(city: str = "Bengaluru", query: str | None = None) -> dict[str, Any]:
    """
    Execute the full PRANAVYU multi-agent pipeline synchronously.
    Returns the final state as a dict.
    """
    graph = build_workflow()
    initial_state = PRANAVYUState(city=city, query=query).model_dump()
    config = {"configurable": {"thread_id": f"pranavyu_{city}_{datetime.utcnow().strftime('%H%M%S')}"}}

    final_state = None
    for chunk in graph.stream(initial_state, config=config):
        for node_name, node_output in chunk.items():
            final_state = node_output

    return final_state or initial_state
