"""
train_model.py — Real AQI forecasting model for PRANAVYU, trained on
actual CPCB (Central Pollution Control Board) data for Bangalore, 2018-2024.

This REPLACES the rule-based `_base_aqi_for_ward()` synthetic baseline in
forecast_agent.py with a real regression model trained on real historical
AQI readings.

Data source: CPCB via cp099/India-Air-Quality-Dataset (CC BY 4.0)
https://github.com/cp099/India-Air-Quality-Dataset

Run:
    python3 train_model.py
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import json

# ─── 1. Load real data ────────────────────────────────────────────────────
df = pd.read_csv("bangalore_aqi.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y")
df = df.sort_values("Date").reset_index(drop=True)

print(f"Loaded {len(df)} days of real Bangalore AQI data")
print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# ─── 2. Feature engineering ───────────────────────────────────────────────
# Lag features: what was AQI 1, 7, and 30 days ago?
df["lag_1"] = df["AQI"].shift(1)
df["lag_7"] = df["AQI"].shift(7)
df["lag_30"] = df["AQI"].shift(30)

# Rolling average: smoothed recent trend
df["rolling_mean_7"] = df["AQI"].shift(1).rolling(window=7).mean()

# Calendar features: day-of-week and month capture weekly/seasonal patterns
df["day_of_week"] = df["Date"].dt.dayofweek
df["month"] = df["Date"].dt.month

# Drop rows with NaN (first 30 days won't have lag_30 etc.)
df = df.dropna().reset_index(drop=True)

FEATURES = ["lag_1", "lag_7", "lag_30", "rolling_mean_7", "day_of_week", "month"]
TARGET = "AQI"

# ─── 3. Time-based train/test split (NOT random — this is a time series) ──
# Using random split would leak future info into training. We hold out the
# most recent 15% of days as a genuine "predict the future" test.
split_idx = int(len(df) * 0.85)
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_test, y_test = test_df[FEATURES], test_df[TARGET]

print(f"\nTrain: {len(train_df)} days ({train_df['Date'].min().date()} to {train_df['Date'].max().date()})")
print(f"Test:  {len(test_df)} days ({test_df['Date'].min().date()} to {test_df['Date'].max().date()})")

# ─── 4. Baseline: naive "persistence" model ────────────────────────────────
# The simplest possible forecast: "tomorrow's AQI = today's AQI".
# Any real model MUST beat this, or it's not adding value.
baseline_pred = X_test["lag_1"]
baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
baseline_mae = mean_absolute_error(y_test, baseline_pred)

# ─── 5. Train the real model ───────────────────────────────────────────────
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=8,
    min_samples_leaf=5,
    random_state=42,
)
model.fit(X_train, y_train)

model_pred = model.predict(X_test)
model_rmse = np.sqrt(mean_squared_error(y_test, model_pred))
model_mae = mean_absolute_error(y_test, model_pred)
model_r2 = r2_score(y_test, model_pred)

# ─── 6. Report results ─────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("RESULTS: Real model vs. naive baseline")
print("=" * 55)
print(f"{'Metric':<20}{'Baseline (persistence)':<25}{'RandomForest':<15}")
print(f"{'RMSE':<20}{baseline_rmse:<25.2f}{model_rmse:<15.2f}")
print(f"{'MAE':<20}{baseline_mae:<25.2f}{model_mae:<15.2f}")
print(f"{'R²':<20}{'—':<25}{model_r2:<15.3f}")

improvement = 100 * (1 - model_rmse / baseline_rmse)
print(f"\nRMSE improvement over naive baseline: {improvement:.1f}%")

# ─── 7. Feature importance — which signals actually matter? ───────────────
importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
print("\nFeature importance:")
for feat, imp in importances:
    print(f"  {feat:<18}{imp:.3f}")

# ─── 8. Save model and metrics ─────────────────────────────────────────────
with open("aqi_model.pkl", "wb") as f:
    pickle.dump(model, f)

metrics = {
    "baseline_rmse": round(baseline_rmse, 2),
    "baseline_mae": round(baseline_mae, 2),
    "model_rmse": round(model_rmse, 2),
    "model_mae": round(model_mae, 2),
    "model_r2": round(model_r2, 3),
    "rmse_improvement_pct": round(improvement, 1),
    "train_days": len(train_df),
    "test_days": len(test_df),
    "data_source": "CPCB via cp099/India-Air-Quality-Dataset",
    "date_range": f"{df['Date'].min().date()} to {df['Date'].max().date()}",
}
with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("\nSaved: aqi_model.pkl, metrics.json")
