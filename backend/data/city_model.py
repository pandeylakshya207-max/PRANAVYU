"""
city_model.py — Wraps the trained RandomForest model (aqi_model.pkl) and
exposes predict_city_baseline(), used by synthetic.py / forecast_agent.py
in place of the old hardcoded per-ward constant.

The model was trained on real Bangalore CPCB data (2018-2024) — see
ml/train_model.py. It predicts CITY-LEVEL daily AQI. Ward-level and
hourly variation are still applied on top as domain-knowledge multipliers,
since the training data doesn't have ward or hourly granularity.
"""
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd

_MODEL_PATH = Path(__file__).parent / "aqi_model.pkl"
_HISTORY_PATH = Path(__file__).parent / "bangalore_aqi.csv"

_model = None
_history: list[float] | None = None


def _load():
    global _model, _history
    if _model is None:
        with open(_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    if _history is None:
        df = pd.read_csv(_HISTORY_PATH)
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y")
        df = df.sort_values("Date")
        # last 30 real AQI readings — used to seed lag features
        _history = df["AQI"].tail(30).tolist()


def predict_city_baseline(day_offset: int = 0) -> float:
    """
    Predict Bengaluru's city-level AQI for `day_offset` days from now.

    Cached per day_offset: a 72-hour forecast across 12 wards calls this
    864 times but only needs 3 distinct answers (day_offset 0, 1, 2) since
    the prediction doesn't depend on ward or hour. Without this cache, the
    pipeline recomputed the full recursive forecast from scratch on every
    single call — 34s instead of <10s. Caching brought it back under budget.
    """
    return _predict_city_baseline_cached(day_offset)


@lru_cache(maxsize=8)
def _predict_city_baseline_cached(day_offset: int) -> float:
    _load()
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

        prediction = float(_model.predict(features)[0])
        history.append(prediction)  # feed forward for next step

    return prediction
