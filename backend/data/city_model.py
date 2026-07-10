"""
city_model.py — Wraps the trained RandomForest model (aqi_model.pkl) and
exposes predict_city_baseline(), used by synthetic.py / forecast_agent.py
in place of the old hardcoded per-ward constant.

The model was trained on real Bangalore CPCB data (2018-2024) — see
ml/train_model.py. It predicts CITY-LEVEL daily AQI. Ward-level and
hourly variation are still applied on top as domain-knowledge multipliers,
since the training data doesn't have ward or hourly granularity.

FAILURE MODE: if the model file or history CSV is missing/corrupted, this
falls back to a fixed constant (140, the old hardcoded average) rather than
crashing the whole API. A monitoring warning is logged so the failure is
visible in production, but the service stays up — degraded, not dead.
"""
import logging
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent / "aqi_model.pkl"
_HISTORY_PATH = Path(__file__).parent / "bangalore_aqi.csv"
_FALLBACK_AQI = 140.0  # old hardcoded average, used only if the real model fails to load

_model = None
_history: list[float] | None = None
_load_failed = False


def _load() -> bool:
    """Returns True if model+history are ready to use, False if we should
    fall back. Only attempts loading once per process — if it fails, we
    don't retry on every request (that would be slow and pointless if the
    file is genuinely missing)."""
    global _model, _history, _load_failed

    if _load_failed:
        return False
    if _model is not None and _history is not None:
        return True

    try:
        with open(_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    except (FileNotFoundError, pickle.UnpicklingError, EOFError) as e:
        logger.error(f"[city_model] Failed to load model from {_MODEL_PATH}: {e}. "
                      f"Falling back to fixed AQI constant ({_FALLBACK_AQI}).")
        _load_failed = True
        return False

    try:
        df = pd.read_csv(_HISTORY_PATH)
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y")
        df = df.sort_values("Date")
        _history = df["AQI"].tail(30).tolist()
        if len(_history) < 7:
            raise ValueError(f"History too short ({len(_history)} rows) for reliable lag features")
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(f"[city_model] Failed to load history from {_HISTORY_PATH}: {e}. "
                      f"Falling back to fixed AQI constant ({_FALLBACK_AQI}).")
        _load_failed = True
        return False

    return True


def predict_city_baseline(day_offset: int = 0) -> float:
    """
    Predict Bengaluru's city-level AQI for `day_offset` days from now.

    Cached per day_offset: a 72-hour forecast across 12 wards calls this
    864 times but only needs 3 distinct answers (day_offset 0, 1, 2) since
    the prediction doesn't depend on ward or hour. Without this cache, the
    pipeline recomputed the full recursive forecast from scratch on every
    single call — 34s instead of <10s. Caching brought it back under budget.

    Falls back to a fixed constant if the model/data failed to load, so a
    missing file degrades the forecast quality rather than crashing the API.
    """
    if not _load():
        return _FALLBACK_AQI
    return _predict_city_baseline_cached(day_offset)


@lru_cache(maxsize=8)
def _predict_city_baseline_cached(day_offset: int) -> float:
    history = list(_history)  # local copy we can extend

    today = datetime.utcnow()
    prediction = history[-1]

    for step in range(day_offset + 1):
        target_date = today + timedelta(days=step)
        lag_1 = history[-1]
        lag_7 = history[-7] if len(history) >= 7 else history[0]
        lag_30 = history[-30] if len(history) >= 30 else history[0]
        rolling_mean_7 = sum(history[-7:]) / len(history[-7:])

        features = pd.DataFrame([{
            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_30": lag_30,
            "rolling_mean_7": rolling_mean_7,
            "day_of_week": target_date.weekday(),
            "month": target_date.month,
        }])

        try:
            prediction = float(_model.predict(features)[0])
        except Exception as e:
            logger.error(f"[city_model] Prediction failed at step {step}: {e}. "
                          f"Using last known value ({prediction:.1f}) instead.")
            # Don't crash mid-recursion — just hold the last good value steady.
            break

        history.append(prediction)

    return prediction


def health_check() -> dict:
    """Used by /health endpoint and CI to confirm the model is actually usable,
    not just that the files exist."""
    ok = _load()
    return {
        "model_loaded": ok,
        "fallback_active": _load_failed,
        "history_length": len(_history) if _history else 0,
    }
