"""
check_model_health.py — Sanity check for the trained AQI model, run in CI
on every push. Fails the build if the model can't load, gives implausible
predictions, or the data files are missing/corrupted.

This is what separates "a model I trained once" from "a model in a system
that keeps working." Run manually with:
    python scripts/check_model_health.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.city_model import health_check, predict_city_baseline


def main():
    print("=" * 50)
    print("MODEL HEALTH CHECK")
    print("=" * 50)

    status = health_check()
    print(f"Model loaded:     {status['model_loaded']}")
    print(f"Fallback active:  {status['fallback_active']}")
    print(f"History length:   {status['history_length']} days")

    if not status["model_loaded"]:
        print("\n❌ FAIL: Model failed to load — check aqi_model.pkl and bangalore_aqi.csv exist")
        sys.exit(1)

    if status["fallback_active"]:
        print("\n❌ FAIL: Fallback is active — real model is not being used")
        sys.exit(1)

    # Sanity check: predictions for the next 3 days should be plausible
    # AQI values. If the model is corrupted or misconfigured, it could
    # silently return nonsense (negative numbers, AQI of 1e10, etc.)
    print("\nSanity-checking predictions for day_offset 0, 1, 2:")
    all_plausible = True
    for day_offset in [0, 1, 2]:
        pred = predict_city_baseline(day_offset=day_offset)
        plausible = 0 < pred < 500  # AQI scale genuinely tops out around 500
        status_icon = "✅" if plausible else "❌"
        print(f"  {status_icon} day_offset={day_offset}: AQI = {pred:.1f}")
        if not plausible:
            all_plausible = False

    if not all_plausible:
        print("\n❌ FAIL: Model produced an implausible AQI value")
        sys.exit(1)

    print("\n✅ ALL HEALTH CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
