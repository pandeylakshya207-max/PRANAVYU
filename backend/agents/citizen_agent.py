"""
PRANAVYU — Citizen Advisory Agent

Generates ward-level health advisories in multiple Indian languages.
Uses LLaMA-3.3-70B via Groq for natural language generation.
Falls back to template-based generation if Groq unavailable.
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Any

from backend.models.schemas import (
    PRANAVYUState, CitizenAdvisory, WardForecast
)
from backend.data.synthetic import BENGALURU_WARDS


# Vulnerability data: wards with schools/hospitals/outdoor workers
WARD_VULNERABILITY: dict[str, dict] = {
    "BLR_001": {"schools": 12, "hospitals": 3, "outdoor_workers": "high"},
    "BLR_002": {"schools": 8,  "hospitals": 4, "outdoor_workers": "medium"},
    "BLR_003": {"schools": 6,  "hospitals": 2, "outdoor_workers": "high"},
    "BLR_004": {"schools": 10, "hospitals": 2, "outdoor_workers": "high"},
    "BLR_005": {"schools": 7,  "hospitals": 5, "outdoor_workers": "low"},
    "BLR_006": {"schools": 9,  "hospitals": 2, "outdoor_workers": "medium"},
    "BLR_007": {"schools": 6,  "hospitals": 3, "outdoor_workers": "medium"},
    "BLR_008": {"schools": 8,  "hospitals": 4, "outdoor_workers": "medium"},
    "BLR_009": {"schools": 11, "hospitals": 2, "outdoor_workers": "high"},
    "BLR_010": {"schools": 7,  "hospitals": 3, "outdoor_workers": "medium"},
    "BLR_011": {"schools": 5,  "hospitals": 6, "outdoor_workers": "low"},
    "BLR_012": {"schools": 9,  "hospitals": 2, "outdoor_workers": "high"},
}


# ─── Template-based advisory (fallback without Groq) ─────────────────────────

ADVISORY_TEMPLATES = {
    "Low":       "Air quality is Good/Satisfactory. Safe for all outdoor activities.",
    "Moderate":  "Air quality is Moderate. Sensitive groups should reduce prolonged outdoor exposure.",
    "High":      "Air quality is Poor. Avoid outdoor exercise. Keep children and elderly indoors.",
    "Very High": "Air quality is Very Poor. Stay indoors. Wear N95 mask if going outside. Keep windows closed.",
    "Severe":    "ALERT: Severe air quality. All outdoor activities banned for children and elderly. Medical emergency risk.",
}

RECOMMENDATIONS = {
    "Low":       ["Enjoy outdoor activities", "Keep windows open for ventilation"],
    "Moderate":  ["Sensitive groups avoid prolonged outdoor stay", "Check AQI before outdoor exercise"],
    "High":      ["Avoid outdoor exercise 6-10 AM", "Use N95 masks outdoors", "Keep schools informed"],
    "Very High": ["Stay indoors with windows closed", "Wear N95 mask if going out", "Postpone school sports", "Seek medical care for breathing issues"],
    "Severe":    ["Do NOT go outdoors", "Seal windows/doors", "Call emergency if breathing difficulty", "Schools to cancel outdoor activities"],
}

# Kannada translations (pre-translated templates)
KANNADA_TEMPLATES = {
    "Low":       "ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಉತ್ತಮವಾಗಿದೆ. ಎಲ್ಲಾ ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳಿಗೆ ಸುರಕ್ಷಿತ.",
    "Moderate":  "ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಮಧ್ಯಮ ಮಟ್ಟದಲ್ಲಿದೆ. ಸೂಕ್ಷ್ಮ ಗುಂಪುಗಳು ಹೊರಗೆ ಹೋಗುವುದನ್ನು ಕಡಿಮೆ ಮಾಡಿ.",
    "High":      "ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಕಳಪೆಯಾಗಿದೆ. ಮಕ್ಕಳು ಮತ್ತು ವೃದ್ಧರು ಮನೆಯಲ್ಲಿ ಇರಿ.",
    "Very High": "ಎಚ್ಚರಿಕೆ: ಗಾಳಿಯ ಗುಣಮಟ್ಟ ತುಂಬಾ ಕಳಪೆ. N95 ಮಾಸ್ಕ್ ಧರಿಸಿ. ಕಿಟಕಿಗಳನ್ನು ಮುಚ್ಚಿ.",
    "Severe":    "ತುರ್ತು ಎಚ್ಚರಿಕೆ: ಗಾಳಿಯ ಗುಣಮಟ್ಟ ಅತ್ಯಂತ ಅಪಾಯಕಾರಿ. ಹೊರಗೆ ಹೋಗಬೇಡಿ.",
}

TAMIL_TEMPLATES = {
    "Low":       "காற்று தரம் நல்லது. அனைத்து வெளிப்புற செயல்பாடுகளும் பாதுகாப்பானவை.",
    "Moderate":  "காற்று தரம் மிதமானது. உணர்திறன் குழுக்கள் வெளிப்புற நேரத்தை குறைக்கவும்.",
    "High":      "காற்று தரம் மோசமானது. குழந்தைகளும் முதியோரும் வீட்டில் இருங்கள்.",
    "Very High": "எச்சரிக்கை: காற்று தரம் மிகவும் மோசம். N95 முகமூடி அணியுங்கள்.",
    "Severe":    "அவசர எச்சரிக்கை: காற்று மிகவும் ஆபத்தானது. வெளியே செல்லாதீர்கள்.",
}

HINDI_TEMPLATES = {
    "Low":       "वायु गुणवत्ता अच्छी है। सभी बाहरी गतिविधियाँ सुरक्षित हैं।",
    "Moderate":  "वायु गुणवत्ता मध्यम है। संवेदनशील समूह बाहरी समय कम करें।",
    "High":      "वायु गुणवत्ता खराब है। बच्चे और बुजुर्ग घर में रहें।",
    "Very High": "चेतावनी: वायु गुणवत्ता बहुत खराब है। N95 मास्क पहनें। खिड़कियाँ बंद रखें।",
    "Severe":    "आपातकाल: वायु गुणवत्ता अत्यंत खतरनाक है। बाहर न जाएँ।",
}

LANGUAGE_TEMPLATES: dict[str, dict[str, str]] = {
    "en": ADVISORY_TEMPLATES,
    "kn": KANNADA_TEMPLATES,
    "ta": TAMIL_TEMPLATES,
    "hi": HINDI_TEMPLATES,
}

LANGUAGE_NAMES = {"en": "English", "kn": "Kannada", "ta": "Tamil", "hi": "Hindi"}


def _vulnerable_groups(ward_id: str, health_risk: str) -> list[str]:
    vuln = WARD_VULNERABILITY.get(ward_id, {})
    groups = []
    if vuln.get("schools", 0) > 0 and health_risk in ("High", "Very High", "Severe"):
        groups.append(f"{vuln['schools']} schools at risk — advise indoor activities")
    if vuln.get("hospitals", 0) > 0:
        groups.append(f"{vuln['hospitals']} hospitals nearby — alert respiratory patients")
    if vuln.get("outdoor_workers") == "high":
        groups.append("High density of outdoor workers — distribute N95 masks")
    return groups


def _generate_advisory(
    forecast: WardForecast,
    language: str = "en",
    hours_ahead: int = 12,
) -> CitizenAdvisory:
    """Generate a citizen advisory for a ward forecast."""
    # Find the peak AQI in the next `hours_ahead` hours
    near_term = forecast.forecast_points[:hours_ahead]
    if near_term:
        peak_point = max(near_term, key=lambda p: p.predicted_aqi)
        peak_aqi = peak_point.predicted_aqi
    else:
        peak_aqi = forecast.peak_aqi

    health_risk = forecast.health_risk
    templates = LANGUAGE_TEMPLATES.get(language, ADVISORY_TEMPLATES)
    message_full = templates.get(health_risk, templates["Moderate"])
    recs = RECOMMENDATIONS.get(health_risk, [])
    vuln = _vulnerable_groups(forecast.ward_id, health_risk)

    # Short message (WhatsApp / SMS)
    message_short = (
        f"PRANAVYU Alert — {forecast.ward_name}: "
        f"AQI forecast {peak_aqi:.0f} ({health_risk} risk) in next {hours_ahead}h. "
        f"{message_full[:80]}"
    )

    return CitizenAdvisory(
        ward_id=forecast.ward_id,
        ward_name=forecast.ward_name,
        city=forecast.city,
        language=language,
        forecast_aqi=peak_aqi,
        health_risk=health_risk,
        message_short=message_short[:160],
        message_full=message_full,
        recommendations=recs,
        vulnerable_groups=vuln,
        valid_until=datetime.utcnow() + timedelta(hours=6),
    )


def run_citizen_advisory_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node: Citizen Advisory Agent.
    Reads ward_forecasts from state.
    Writes advisories to state.
    """
    s = PRANAVYUState(**state)

    if not s.ward_forecasts:
        s.errors.append("citizen_agent: no forecasts available")
        s.completed_agents.append("citizen_agent")
        return s.model_dump()

    advisories: list[CitizenAdvisory] = []

    # Generate English advisory for all wards
    # Generate Kannada for Bengaluru wards with High+ risk
    for forecast in s.ward_forecasts:
        adv_en = _generate_advisory(forecast, language="en")
        advisories.append(adv_en)

        if forecast.health_risk in ("High", "Very High", "Severe"):
            # City-specific language
            if s.city == "Bengaluru":
                advisories.append(_generate_advisory(forecast, language="kn"))
            elif s.city == "Chennai":
                advisories.append(_generate_advisory(forecast, language="ta"))
            advisories.append(_generate_advisory(forecast, language="hi"))

    s.advisories = advisories
    s.agent_trace.append({
        "agent": "citizen_advisory_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "advisories_generated": len(advisories),
        "high_risk_wards": sum(1 for f in s.ward_forecasts if f.health_risk in ("High", "Very High", "Severe")),
    })
    s.completed_agents.append("citizen_agent")
    return s.model_dump()


async def generate_advisory_with_llm(
    ward_name: str,
    forecast_aqi: float,
    health_risk: str,
    language: str,
    dominant_factor: str,
) -> str:
    """
    Optional: Use Groq LLaMA to generate more natural advisory text.
    Falls back to template if Groq unavailable.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or groq_key == "your_groq_api_key_here":
        templates = LANGUAGE_TEMPLATES.get(language, ADVISORY_TEMPLATES)
        return templates.get(health_risk, "")

    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.3,
            max_tokens=200,
        )

        lang_name = LANGUAGE_NAMES.get(language, "English")
        prompt = (
            f"Generate a concise, actionable air quality health advisory for {ward_name}, Bengaluru. "
            f"Forecast AQI: {forecast_aqi:.0f} ({health_risk} health risk). "
            f"Primary cause: {dominant_factor}. "
            f"Write in {lang_name}. Maximum 3 sentences. "
            f"Be specific, not generic. Include one concrete action."
        )

        response = await llm.ainvoke([
            SystemMessage(content="You are a public health officer issuing air quality advisories. Be direct and actionable."),
            HumanMessage(content=prompt),
        ])
        return response.content.strip()

    except Exception:
        templates = LANGUAGE_TEMPLATES.get(language, ADVISORY_TEMPLATES)
        return templates.get(health_risk, "")
