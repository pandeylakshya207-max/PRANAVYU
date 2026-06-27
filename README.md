# 🌬️ PRANAVYU
## Predictive Real-time Air quality Navigation & Attribution for Vigilant Urban intelligence

> **ET AI Hackathon 2026 | Problem #5: Urban Air Quality Intelligence**

---

## What is PRANAVYU?

PRANAVYU is a multi-agent AI platform that tells city administrators not just **what** the AQI is — but **why**, **who is responsible**, **what will happen in the next 72 hours**, and **exactly where to send enforcement teams tonight**.

**The gap it closes:** India has 900+ CAAQMS monitoring stations. Only 31% of cities have actionable response protocols linked to those readings. The data exists. The intelligence layer to act on it does not. PRANAVYU is that intelligence layer.

---

## Architecture

```
DATA SOURCES          6-AGENT PIPELINE (LangGraph)        OUTPUTS
────────────          ──────────────────────────────       ───────
CPCB CAAQMS    →   [Data Ingestion]                   → Live AQI Map
Sentinel-5P    →   [Attribution Agent]  ← Gaussian    → Source Attribution
IMD Weather    →   [Forecast Agent]     ← ML Model    → 72h Ward Forecast
OpenAQ         →   [Enforcement Agent] ← Bayesian     → Inspector Dispatch
OSM / Census   →   [Citizen Agent]     ← LLM (Groq)  → Multilingual Alerts
Permit DBs     →   [Cross-City Agent]  ← RAG          → Policy Intelligence
```

---

## Key Capabilities

| Capability | What it does |
|-----------|-------------|
| **Source Attribution** | Identifies which factories, construction sites, or roads are causing AQI spikes at ward level — using Gaussian reverse plume modeling + satellite thermal anomalies |
| **72h Forecast** | Predicts AQI at ward level 72 hours ahead using weather forecasts, emission schedules, and ML models |
| **Enforcement Intelligence** | Predicts *when* violators are most likely to be caught (night-time industrial patterns) and generates evidence-backed inspector dispatch orders |
| **Multilingual Advisories** | Auto-generates ward-level health advisories in English, Kannada, Tamil, Hindi — WhatsApp/SMS ready |
| **Cross-City Learning** | Recommends pollution control policies based on what worked in comparable Indian cities, with before/after evidence |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | LLaMA-3.3-70B via Groq |
| RAG / Vector DB | Qdrant + BAAI/bge-m3 |
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Recharts + Leaflet |
| Dispersion Model | Gaussian Plume (custom Scipy) |
| Databases | PostgreSQL + PostGIS, Redis |
| Data Sources | CPCB CAAQMS, Sentinel-5P, IMD, OpenAQ |

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 22+
- Git

### 1. Clone and setup
```bash
git clone https://github.com/your-team/pranavyu
cd pranavyu
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)
```

### 2. Start everything
```bash
chmod +x start.sh
./start.sh
```

### 3. Open the dashboard
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### Docker (production)
```bash
docker-compose up -d
```

---

## API Endpoints

| Endpoint | Description |
|---------|-------------|
| `GET /api/dashboard/{city}` | All-in-one dashboard data |
| `GET /api/attribution/{city}` | Ward-level source attribution |
| `GET /api/forecast/{city}` | 72h AQI forecasts |
| `GET /api/enforcement/{city}` | Enforcement action queue |
| `GET /api/advisories/{city}` | Citizen health advisories |
| `GET /api/cross-city/{city}` | Cross-city policy recommendations |
| `POST /api/enforcement/dispatch` | Dispatch inspector |
| `GET /api/trace/{city}` | Agent execution trace |

---

## Running Tests

```bash
python3 scripts/test_all.py
# Expected: 27/27 tests passed
```

---

## Project Structure

```
pranavyu/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py       # LangGraph multi-agent workflow
│   │   ├── attribution_agent.py  # Source attribution (Gaussian plume)
│   │   ├── forecast_agent.py     # 72h predictive AQI forecast
│   │   ├── enforcement_agent.py  # Enforcement intelligence
│   │   ├── citizen_agent.py      # Multilingual advisories
│   │   └── cross_city_agent.py   # Policy recommendations
│   ├── models/
│   │   └── schemas.py            # All Pydantic data models
│   ├── data/
│   │   └── synthetic.py          # Data generation + demo data
│   ├── utils/
│   │   └── dispersion.py         # Gaussian plume model
│   └── api/
│       └── main.py               # FastAPI application
├── src/                          # React frontend
│   ├── components/
│   │   ├── AQIMap.jsx            # Leaflet ward heatmap
│   │   ├── AttributionPanel.jsx  # Source attribution UI
│   │   ├── ForecastChart.jsx     # Recharts forecast visualization
│   │   ├── EnforcementPanel.jsx  # Enforcement dispatch UI
│   │   ├── AdvisoryPanel.jsx     # Citizen advisories UI
│   │   ├── AgentTrace.jsx        # Multi-agent execution trace
│   │   └── StatsBar.jsx          # Summary statistics
│   ├── hooks/useData.js          # API data fetching hooks
│   └── App.jsx                   # Main dashboard layout
├── scripts/
│   └── test_all.py               # 27-test comprehensive suite
├── docker/                       # Docker configs
├── start.sh                      # One-command startup
├── requirements.txt
└── docker-compose.yml
```

---

## Evaluation Metrics

| Judging Criterion | PRANAVYU's Claim |
|------------------|-----------------|
| **Innovation** | First product to combine ward-level causal attribution + predictive enforcement scheduling in India |
| **Business Impact** | B2G: ₹660 crore TAM (132 NCAP cities × ₹5 crore/yr) |
| **Technical Excellence** | 6-agent LangGraph pipeline, Gaussian plume physics, 27/27 tests |
| **Scalability** | Stateless FastAPI agents → Cloud Run auto-scale → 132 cities |
| **User Experience** | Government dashboard + citizen WhatsApp + IVR in 4 languages |

---

## Team

**The Encoders** | ET AI Hackathon 2026

---

*PRANAVYU — because every breath is data, and every death is preventable.*
