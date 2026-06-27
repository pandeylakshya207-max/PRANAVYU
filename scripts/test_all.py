"""
PRANAVYU — Comprehensive Test Suite
Run: python3 -m pytest scripts/test_all.py -v
Or:  python3 scripts/test_all.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback
from datetime import datetime

PASS = "✅"
FAIL = "❌"
results = []

def test(name, fn):
    try:
        fn()
        results.append((PASS, name))
        print(f"  {PASS}  {name}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"  {FAIL}  {name}")
        print(f"       {e}")
        traceback.print_exc()


# ─── Schema Tests ─────────────────────────────────────────────────────────────

def test_schemas():
    from backend.models.schemas import (
        PRANAVYUState, AQIReading, WeatherSnapshot, EmissionSource,
        AttributionResult, WardForecast, EnforcementAction, CitizenAdvisory
    )
    state = PRANAVYUState(city="Bengaluru")
    assert state.city == "Bengaluru"
    assert state.live_readings == []
    assert state.errors == []

def test_schema_serialization():
    from backend.models.schemas import PRANAVYUState
    state = PRANAVYUState(city="Chennai")
    d = state.model_dump()
    state2 = PRANAVYUState(**d)
    assert state2.city == "Chennai"


# ─── Synthetic Data Tests ─────────────────────────────────────────────────────

def test_synthetic_readings():
    from backend.data.synthetic import generate_live_readings
    readings = generate_live_readings("Bengaluru")
    assert len(readings) == 12
    for r in readings:
        assert r.aqi is not None
        assert 0 < r.aqi < 600
        assert r.pm25 is not None
        assert r.lat != 0.0
        assert r.lon != 0.0

def test_synthetic_weather():
    from backend.data.synthetic import generate_weather
    w = generate_weather()
    assert 0 <= w.wind_direction <= 360
    assert w.wind_speed >= 0
    assert w.mixing_height > 0
    assert 0 < w.humidity <= 100

def test_synthetic_sources():
    from backend.data.synthetic import get_emission_sources
    sources = get_emission_sources()
    assert len(sources) > 5
    for s in sources:
        assert s.source_id
        assert s.category in ("industrial", "construction", "traffic", "burning", "other")
        assert 0 <= s.historical_violation_rate <= 1

def test_synthetic_wards():
    from backend.data.synthetic import get_wards
    wards = get_wards()
    assert len(wards) == 12
    for w in wards:
        assert w.ward_id.startswith("BLR_")
        assert w.population > 0

def test_historical_readings():
    from backend.data.synthetic import generate_historical_readings
    series = generate_historical_readings("BLR_001", hours_back=48)
    assert len(series) == 48
    for ts, aqi in series:
        assert isinstance(ts, datetime)
        assert aqi > 0


# ─── Dispersion Model Tests ───────────────────────────────────────────────────

def test_haversine():
    from backend.utils.dispersion import haversine_km
    # Bengaluru to Mysore: ~128km straight-line (great-circle), ~144km by road
    dist = haversine_km(12.9716, 77.5946, 12.2958, 76.6394)
    assert 115 < dist < 145, f"Expected ~128km, got {dist:.1f}km"

def test_bearing():
    from backend.utils.dispersion import bearing_deg
    # Due east: bearing should be ~90
    b = bearing_deg(0, 0, 0, 1)
    assert 85 < b < 95, f"East bearing should be ~90, got {b}"

def test_gaussian_concentration():
    from backend.utils.dispersion import gaussian_ground_concentration, STABILITY_D
    c = gaussian_ground_concentration(Q=1000, u=4.0, x_km=1.0, y_m=0, H=10)
    assert c > 0
    # Concentration should decrease with distance
    c_near = gaussian_ground_concentration(Q=1000, u=4.0, x_km=0.5, y_m=0, H=10)
    c_far  = gaussian_ground_concentration(Q=1000, u=4.0, x_km=5.0, y_m=0, H=10)
    assert c_near > c_far, "Concentration should decrease with distance"

def test_attribution_computation():
    from backend.utils.dispersion import compute_source_attribution, aggregate_by_category
    from backend.data.synthetic import get_emission_sources
    sources = [
        {"source_id": s.source_id, "name": s.name, "category": s.category,
         "lat": s.lat, "lon": s.lon, "historical_violation_rate": s.historical_violation_rate}
        for s in get_emission_sources()
    ]
    contribs = compute_source_attribution(
        receptor_lat=13.0284, receptor_lon=77.5194,
        sources=sources, wind_direction=270, wind_speed=3.0,
        hour=22, aqi_value=200.0
    )
    assert len(contribs) > 0
    cats = aggregate_by_category(contribs)
    total = sum(cats.values())
    assert abs(total - 1.0) < 0.01, f"Fractions should sum to 1, got {total}"


# ─── Agent Tests ──────────────────────────────────────────────────────────────

def test_attribution_agent():
    from backend.agents.attribution_agent import run_attribution_agent
    from backend.models.schemas import PRANAVYUState
    from backend.data.synthetic import generate_live_readings, generate_weather, get_emission_sources

    state = PRANAVYUState(
        city="Bengaluru",
        live_readings=generate_live_readings(),
        weather=generate_weather(),
        emission_sources=get_emission_sources(),
    ).model_dump()

    result = run_attribution_agent(state)
    assert len(result["attribution_results"]) == 12
    for r in result["attribution_results"]:
        assert r["ward_id"]
        assert r["current_aqi"] > 0
        assert len(r["attributions"]) > 0
        total = sum(a["contribution_fraction"] for a in r["attributions"])
        assert abs(total - 1.0) < 0.05, f"Attribution fractions should sum to ~1, got {total}"
    assert "attribution_agent" in result["completed_agents"]

def test_forecast_agent():
    from backend.agents.forecast_agent import run_forecast_agent
    from backend.models.schemas import PRANAVYUState
    from backend.data.synthetic import generate_live_readings, generate_weather

    state = PRANAVYUState(
        city="Bengaluru",
        live_readings=generate_live_readings(),
        weather=generate_weather(),
    ).model_dump()

    result = run_forecast_agent(state)
    assert len(result["ward_forecasts"]) == 12
    for f in result["ward_forecasts"]:
        assert len(f["forecast_points"]) == 72
        assert f["peak_aqi"] > 0
        assert f["health_risk"] in ("Low","Moderate","High","Very High","Severe")
    assert "forecast_agent" in result["completed_agents"]

def test_enforcement_agent():
    from backend.agents.enforcement_agent import run_enforcement_agent
    from backend.agents.attribution_agent import run_attribution_agent
    from backend.models.schemas import PRANAVYUState
    from backend.data.synthetic import generate_live_readings, generate_weather, get_emission_sources

    state = PRANAVYUState(
        city="Bengaluru",
        live_readings=generate_live_readings(),
        weather=generate_weather(),
        emission_sources=get_emission_sources(),
    ).model_dump()
    state = run_attribution_agent(state)
    result = run_enforcement_agent(state)

    assert result["enforcement_plan"] is not None
    actions = result["enforcement_plan"]["actions"]
    assert len(actions) > 0
    # Priority ranks should be 1,2,3...
    ranks = [a["priority_rank"] for a in actions]
    assert ranks == sorted(ranks)
    # All actions should have source
    for a in actions:
        assert a["source"]
        assert 0 <= a["violation_probability"] <= 1
    assert "enforcement_agent" in result["completed_agents"]

def test_citizen_agent():
    from backend.agents.citizen_agent import run_citizen_advisory_agent
    from backend.agents.forecast_agent import run_forecast_agent
    from backend.models.schemas import PRANAVYUState
    from backend.data.synthetic import generate_live_readings, generate_weather

    state = PRANAVYUState(
        city="Bengaluru",
        live_readings=generate_live_readings(),
        weather=generate_weather(),
    ).model_dump()
    state = run_forecast_agent(state)
    result = run_citizen_advisory_agent(state)

    advisories = result["advisories"]
    assert len(advisories) > 0
    for a in advisories:
        assert a["ward_id"]
        assert a["language"] in ("en","kn","ta","hi","bn")
        assert len(a["message_short"]) <= 160, "SMS message too long"
        assert a["health_risk"] in ("Low","Moderate","High","Very High","Severe")
    assert "citizen_agent" in result["completed_agents"]

def test_cross_city_agent():
    from backend.agents.cross_city_agent import run_cross_city_agent
    from backend.agents.attribution_agent import run_attribution_agent
    from backend.models.schemas import PRANAVYUState
    from backend.data.synthetic import generate_live_readings, generate_weather, get_emission_sources

    state = PRANAVYUState(
        city="Bengaluru",
        live_readings=generate_live_readings(),
        weather=generate_weather(),
        emission_sources=get_emission_sources(),
    ).model_dump()
    state = run_attribution_agent(state)
    result = run_cross_city_agent(state)

    recs = result["cross_city_recommendations"]
    assert len(recs) > 0
    for r in recs:
        assert r["recommendation"]
        assert r["expected_delta_aqi"] < 0  # should be reduction
        assert len(r["evidence_cities"]) > 0
    assert "cross_city_agent" in result["completed_agents"]


# ─── Full Pipeline Test ───────────────────────────────────────────────────────

def test_full_pipeline():
    from backend.agents.orchestrator import run_full_pipeline
    result = run_full_pipeline("Bengaluru")

    assert result is not None
    assert len(result.get("attribution_results", [])) == 12
    assert len(result.get("ward_forecasts", [])) == 12
    assert result.get("enforcement_plan") is not None
    assert len(result.get("advisories", [])) > 0
    assert len(result.get("cross_city_recommendations", [])) > 0
    assert len(result.get("errors", [])) == 0

def test_pipeline_speed():
    import time
    from backend.agents.orchestrator import run_full_pipeline
    start = time.time()
    run_full_pipeline("Bengaluru")
    elapsed = time.time() - start
    assert elapsed < 10.0, f"Pipeline too slow: {elapsed:.2f}s (should be <10s)"
    print(f"       Pipeline time: {elapsed:.3f}s")


# ─── API Tests ────────────────────────────────────────────────────────────────

def test_fastapi_imports():
    from backend.api.main import app
    routes = [r.path for r in app.routes]
    assert "/health" in routes
    assert "/api/dashboard/{city}" in routes
    assert "/api/attribution/{city}" in routes
    assert "/api/enforcement/{city}" in routes
    assert "/api/advisories/{city}" in routes

def test_api_health():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "PRANAVYU"

def test_api_readings():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/readings/Bengaluru")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 12
    assert len(data["readings"]) == 12

def test_api_dashboard():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/dashboard/Bengaluru")
    assert resp.status_code == 200
    data = resp.json()
    summary = data["summary"]
    assert summary["wards_monitored"] == 12
    assert summary["avg_aqi"] > 0
    assert summary["enforcement_actions_pending"] >= 0

def test_api_attribution():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/attribution/Bengaluru")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 12

def test_api_ward_filter():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/attribution/Bengaluru?ward_id=BLR_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1

def test_api_enforcement():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/enforcement/Bengaluru")
    assert resp.status_code == 200
    plan = resp.json()["enforcement_plan"]
    assert plan is not None
    assert len(plan["actions"]) > 0

def test_api_advisories():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.get("/api/advisories/Bengaluru?language=en")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    for a in data["advisories"]:
        assert a["language"] == "en"

def test_api_dispatch():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    client = TestClient(app)
    resp = client.post("/api/enforcement/dispatch", json={"action_id": "TEST_001", "inspector_id": "INS_42"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "dispatched"
    assert data["action_id"] == "TEST_001"


# ─── Run All ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  PRANAVYU — Full Test Suite")
    print("═"*55 + "\n")

    print("📦 SCHEMA TESTS")
    test("Schema creation",       test_schemas)
    test("Schema serialization",  test_schema_serialization)

    print("\n🎲 SYNTHETIC DATA TESTS")
    test("Live readings",         test_synthetic_readings)
    test("Weather snapshot",      test_synthetic_weather)
    test("Emission sources",      test_synthetic_sources)
    test("Ward data",             test_synthetic_wards)
    test("Historical series",     test_historical_readings)

    print("\n🌬️ DISPERSION MODEL TESTS")
    test("Haversine distance",    test_haversine)
    test("Bearing computation",   test_bearing)
    test("Gaussian concentration",test_gaussian_concentration)
    test("Source attribution",    test_attribution_computation)

    print("\n🤖 AGENT TESTS")
    test("Attribution agent",     test_attribution_agent)
    test("Forecast agent",        test_forecast_agent)
    test("Enforcement agent",     test_enforcement_agent)
    test("Citizen advisory agent",test_citizen_agent)
    test("Cross-city agent",      test_cross_city_agent)

    print("\n⚡ PIPELINE TESTS")
    test("Full pipeline",         test_full_pipeline)
    test("Pipeline speed",        test_pipeline_speed)

    print("\n🌐 API TESTS")
    test("FastAPI imports",       test_fastapi_imports)
    test("Health endpoint",       test_api_health)
    test("Readings endpoint",     test_api_readings)
    test("Dashboard endpoint",    test_api_dashboard)
    test("Attribution endpoint",  test_api_attribution)
    test("Ward filter",           test_api_ward_filter)
    test("Enforcement endpoint",  test_api_enforcement)
    test("Advisories endpoint",   test_api_advisories)
    test("Dispatch endpoint",     test_api_dispatch)

    # Summary
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)
    total  = len(results)

    print("\n" + "═"*55)
    print(f"  Results: {passed}/{total} passed  |  {failed} failed")
    print("═"*55 + "\n")

    if failed > 0:
        print("FAILED TESTS:")
        for r in results:
            if r[0] == FAIL:
                print(f"  {r[1]}: {r[2] if len(r)>2 else ''}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED ✅")
        sys.exit(0)
