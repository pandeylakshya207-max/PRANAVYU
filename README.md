# 🌬️ PRANAVYU
## Predictive Real-time Air quality Navigation & Attribution for Vigilant Urban intelligence

> **ET AI Hackathon 2026 | Problem #5: Urban Air Quality Intelligence**
> 
> Built by **Lakshya Pandey** | B.Tech CSE (AI & ML), Dayananda Sagar University | MIT CSAIL AI Research Contributor

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-purple?style=flat-square)
![LLaMA](https://img.shields.io/badge/LLaMA_3.3_70B-Groq-orange?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-27%2F27_passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

</div>

---

## 🎯 What is PRANAVYU?

PRANAVYU is a **multi-agent AI platform** that tells city administrators not just **what** the AQI is — but **why**, **who is responsible**, **what will happen in the next 72 hours**, and **exactly where to send enforcement teams tonight**.

**The gap it closes:** India has 900+ CAAQMS monitoring stations. Only 31% of cities have actionable response protocols linked to those readings. The data exists. The intelligence layer to act on it does not. PRANAVYU is that intelligence layer.

> *1.67 million Indians die from air pollution every year. Not because the data doesn't exist. Because no one can act on it fast enough. PRANAVYU changes that.*

---

## Current status

This is a hackathon prototype. What runs today:

- **Real:** the six-agent LangGraph pipeline, the FastAPI endpoints, the React dashboard, the Gaussian plume model, a forecast model trained on historical CPCB data for Bengaluru, and the test suite.
- **Synthetic:** the emission sources, and the ward readings whenever live data is unavailable. Source attribution and enforcement ranking therefore run on invented inputs.
- **Optional:** live readings from OpenAQ are tried first, and advisory text comes from a Groq-hosted model when an API key is set.
- **Not built:** live CPCB and weather feeds, satellite processing, a vector database, message delivery by WhatsApp or SMS, and any production database.

---

## 🏗️ Architecture

    Readings (OpenAQ when reachable, otherwise synthetic)
            |
            v
    LangGraph pipeline:
    ingestion -> attribution -> forecast -> enforcement -> advisory -> cross-city
            |
            v
    FastAPI endpoints -> React dashboard
    (map, attribution, forecast, enforcement queue, advisories, agent trace)

---

## ⚡ Key Capabilities

| Capability | What the prototype does |
|---|---|
| **Source attribution** | Estimates each source's share of a ward's pollution with a Gaussian plume model and Pasquill-Gifford stability classes. Runs on synthetic emission sources. |
| **72-hour forecast** | Projects AQI per ward from a city-level model trained on historical data, with per-ward and per-hour multipliers computed from real station readings. Error compounds over multiple days; see the limitations section below. |
| **Enforcement ranking** | Ranks sources for inspection by estimated violation probability and AQI impact. Inputs are synthetic. |
| **Citizen advisories** | Generates ward-level advisories in English, Kannada, Tamil and Hindi, limited to 160 characters. Uses a hosted language model when a key is configured and templates otherwise. Nothing is sent to anyone. |
| **Cross-city suggestions** | Returns policy measures from a small built-in set of outcomes in other Indian cities. |

---

## 🤖 The 6 Agents

| Agent | Role | Method |
|---|---|---|
| **Data ingestion** | Loads readings, weather and sources | OpenAQ when reachable, otherwise synthetic data |
| **Source attribution** | Shares of pollution per ward | Gaussian reverse plume, Pasquill-Gifford stability |
| **Forecast** | 72-hour ward-level AQI | Trained city model, ward and hourly multipliers, wind dispersion |
| **Enforcement** | Ranks inspection targets | Violation probability times AQI impact |
| **Citizen advisory** | Advisories in four languages | LLaMA 3.3 70B via Groq when configured, templates otherwise |
| **Cross-city** | Policy suggestions | Lookup over a built-in six-city set of outcomes |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent orchestration** | LangGraph (StateGraph) |
| **Language model** | LLaMA 3.3 70B via Groq, optional |
| **Backend** | FastAPI, Python 3.12 |
| **Frontend** | React 18, Recharts, Leaflet |
| **Dispersion model** | Custom Gaussian plume (SciPy) |
| **Forecast model** | scikit-learn RandomForest |
| **Containers** | Docker, docker-compose |

The compose file also starts Redis and Qdrant. The current code does not use either.

---

## 📊 Evaluation Metrics

Measured, and reproducible with `ml/train_model.py` (results saved in `ml/metrics.json`). City-level daily AQI for Bengaluru, 2,147 training days and 379 test days:

| Metric | Naive baseline (yesterday's value) | RandomForest |
|---|---|---|
| RMSE | 13.13 | 12.84 |
| MAE | 9.07 | 8.96 |
| R2 | n/a | 0.719 |

The model beats the baseline by 2.2% RMSE.

Other checks: 27 of 27 tests pass (`python3 scripts/test_all.py`), and SMS advisories are limited to 160 characters.

Not measured: the accuracy of source attribution (the sources are synthetic, so there is no ground truth), ward-level forecast error, and multi-day forecast error.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 22+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone
```bash
git clone https://github.com/pandeylakshya207-max/PRANAVYU.git
cd PRANAVYU
```

### 2. Configure
```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### 3. Run
```bash
chmod +x start.sh
./start.sh
```

### 4. Open
```
Dashboard → http://localhost:3000
API Docs  → http://localhost:8000/docs
```

### Docker (production)
```bash
docker-compose up -d
```

---

## 🌐 API Reference

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/dashboard/{city}` | GET | All-in-one dashboard data |
| `/api/attribution/{city}` | GET | Ward-level source attribution |
| `/api/forecast/{city}` | GET | 72h AQI forecasts |
| `/api/enforcement/{city}` | GET | Enforcement action queue |
| `/api/advisories/{city}` | GET | Citizen health advisories (language filter) |
| `/api/cross-city/{city}` | GET | Cross-city policy recommendations |
| `/api/enforcement/dispatch` | POST | Dispatch inspector to source |
| `/api/trace/{city}` | GET | Agent execution trace |
| `/health` | GET | Health check |

---

## 📁 Project Structure

```
PRANAVYU/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph multi-agent workflow
│   │   ├── attribution_agent.py   # Gaussian plume source attribution
│   │   ├── forecast_agent.py      # 72h predictive AQI forecast
│   │   ├── enforcement_agent.py   # Bayesian enforcement intelligence
│   │   ├── citizen_agent.py       # Multilingual health advisories
│   │   └── cross_city_agent.py    # RAG policy recommendations
│   ├── models/
│   │   └── schemas.py             # 15 Pydantic data models
│   ├── data/
│   │   └── synthetic.py           # 12 Bengaluru wards + 9 emission sources
│   ├── utils/
│   │   └── dispersion.py          # Gaussian plume physics model
│   └── api/
│       └── main.py                # 17 FastAPI endpoints
├── src/                           # React frontend
│   ├── components/
│   │   ├── AQIMap.jsx             # Leaflet ward heatmap (dark theme)
│   │   ├── AttributionPanel.jsx   # Source breakdown with confidence bars
│   │   ├── ForecastChart.jsx      # Recharts 72h forecast with CI bands
│   │   ├── EnforcementPanel.jsx   # One-click inspector dispatch UI
│   │   ├── AdvisoryPanel.jsx      # Multilingual advisory cards
│   │   ├── AgentTrace.jsx         # Live agent execution visualizer
│   │   └── StatsBar.jsx           # 7 KPI summary metrics
│   ├── hooks/useData.js           # API data fetching + demo data
│   └── App.jsx                    # Main dashboard layout
├── scripts/
│   └── test_all.py                # 27-test comprehensive suite
├── docker/                        # Dockerfiles + nginx config
├── start.sh                       # One-command startup
├── docker-compose.yml             # Full stack with Redis + Qdrant
└── requirements.txt               # Pinned Python dependencies
```

---

## 🎯 Business Model

> Hackathon pitch material. The figures in this section are estimates and have not been validated.

| Segment | Customer | Price | TAM |
|---------|---------|-------|-----|
| **B2G** | Municipal corporations (132 NCAP cities) | ₹2–8 crore/city/year | ₹660 crore/year |
| **B2B** | Industrial facilities under CPCB star-rating | ₹25–75 lakh/facility/year | ₹600 crore/year |
| **API** | Real estate, insurance, climate finance | Usage-based | ₹100 crore/year |

---

## 🧪 Running Tests

```bash
python3 scripts/test_all.py
```

```
📦 SCHEMA TESTS          ✅ ✅
🎲 SYNTHETIC DATA TESTS  ✅ ✅ ✅ ✅ ✅
🌬️ DISPERSION TESTS      ✅ ✅ ✅ ✅
🤖 AGENT TESTS           ✅ ✅ ✅ ✅ ✅
⚡ PIPELINE TESTS        ✅ ✅
🌐 API TESTS             ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅

Results: 27/27 passed | 0 failed ✅
```

---

## 🗺️ Roadmap

- [ ] Live CPCB CAAQMS API integration (replace synthetic data)
- [ ] Sentinel-5P satellite imagery processing pipeline
- [ ] WhatsApp Business API integration for citizen alerts
- [ ] IndicTrans2 integration for higher quality translations
- [ ] Multi-city support (Delhi, Mumbai, Chennai, Hyderabad)
- [ ] Mobile app (React Native)
- [ ] Carbon credit verification module
- [ ] CPCB CAAQMS official data partnership

---

## 🧠 Forecasting Model — Real Data & Honest Limitations

The city-level AQI baseline is predicted by a RandomForest model trained
on 2,556 days (2018–2024) of real Bangalore CPCB air quality data
(source: [cp099/India-Air-Quality-Dataset](https://github.com/cp099/India-Air-Quality-Dataset)).

**Results** (see `metrics.json`, reproducible via `ml/train_model.py`):
| Metric | Naive baseline (persistence) | RandomForest |
|---|---|---|
| RMSE | 13.13 | 12.84 |
| MAE | 9.07 | 8.96 |
| R² | — | 0.719 |

The model beats a naive "predict yesterday's value" baseline by **2.2% RMSE**.
Feature importance shows `lag_1` (yesterday's AQI) dominates at 84% —
AQI is highly autocorrelated day-to-day, which is why the improvement over
the naive baseline is modest rather than dramatic. Reported honestly rather
than rounded up.

### Ward-level and hourly patterns — now also real data, not guesses

Ward multipliers and the hourly diurnal pattern were originally hand-guessed.
They've since been replaced with values computed from **287,564 real hourly
readings across 10 actual CPCB/KSPCB monitoring stations in Bengaluru**
(2015–2020, via [rohanrao/air-quality-data-in-india](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india)
on Kaggle). See `ml/compute_real_ward_hourly.py` for the full computation.

**This corrected a wrong assumption in the original code.** The hardcoded
version assumed morning rush hour (8–10am) was a pollution *peak* (1.35x).
Real data shows hour 8 is actually the **lowest** point of the day (0.918x)
— morning boundary-layer mixing appears to disperse pollution, which then
re-accumulates as the layer collapses toward evening. The real evening peak
is later and milder than assumed (~19–21h at ~1.06–1.08x, not 18–20h at 1.25x).

**Ward-to-station mapping is approximate**, not precise GIS distance —
Bengaluru's 10 real monitoring stations were assigned to the app's 12 wards
based on general geographic knowledge (documented in
`ml/compute_real_ward_hourly.py`), since station lat/lon wasn't available
in this dataset export.

**What's real vs. what's still a heuristic:**
- ✅ City-level daily trend — real trained model, real data
- ✅ Ward-level relative multipliers — real station averages (approximate ward-to-station mapping)
- ✅ Hourly diurnal pattern — real station data, corrected a wrong assumption
- ⚠️ Multi-day forecasts are recursive (day 2's prediction feeds into day 3
  as if it were real), so forecast error compounds the further out you go

**Failure handling:** if the model file or history data is missing/corrupted,
`city_model.py` falls back to a fixed constant rather than crashing the API
(see `backend/data/city_model.py`, `health_check()`). CI runs
`scripts/check_model_health.py` on every push to catch this before it ships.

---

## 👨‍💻 Author

**Lakshya Pandey**
- B.Tech CSE (AI & ML) — Dayananda Sagar University, Bengaluru (Batch 2025–29)
- AI Research Contributor — MIT CSAIL (Education Vertical, Mantis AI Platform)
- Founder — Eduiing (Unified university application platform for India)
- 22+ National Hackathons across IITs, IIMs, and international events

[![GitHub](https://img.shields.io/badge/GitHub-pandeylakshya207--max-181717?style=flat-square&logo=github)](https://github.com/pandeylakshya207-max)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-lakshyapandey--ml-FFD21E?style=flat-square&logo=huggingface)](https://huggingface.co/lakshyapandey-ml)

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

**PRANAVYU — because every breath is data, and every death is preventable.**

*ET AI Hackathon 2026 | Problem #5: Urban Air Quality Intelligence*

</div>
