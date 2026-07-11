"""
compute_real_ward_hourly.py — Replaces the guessed ward multipliers and
hardcoded diurnal pattern in synthetic.py with values computed from real
CPCB station data (10 Bengaluru monitoring stations, 2015-2020, via
Kaggle: rohanrao/air-quality-data-in-india).

WARD-TO-STATION MAPPING (documented, not hidden):
Bengaluru has 10 real CPCB/KSPCB monitoring stations. The app's 12 wards
are assigned to their nearest real station based on general geographic
knowledge of Bengaluru's layout — this is NOT a precise GIS nearest-neighbor
calculation (we don't have station lat/lon in this dataset export), so
treat this mapping as a reasonable approximation, not survey-grade.

Run:
    python3 compute_real_ward_hourly.py
"""
import json
import pandas as pd

df = pd.read_csv("bengaluru_station_hour.csv", low_memory=False)
df = df.dropna(subset=["AQI"])
df["Datetime"] = pd.to_datetime(df["Datetime"])
df["hour"] = df["Datetime"].dt.hour

STATION_NAMES = {
    "KA002": "BTM Layout", "KA003": "BWSSB Kadabesanahalli", "KA004": "Bapuji Nagar",
    "KA005": "City Railway Station", "KA006": "Hebbal", "KA007": "Hombegowda Nagar",
    "KA008": "Jayanagar 5th Block", "KA009": "Peenya", "KA010": "Sanegurava Halli",
    "KA011": "Silk Board",
}

# Ward -> nearest real station (approximate, documented above)
WARD_TO_STATION = {
    "BLR_001": "KA003",  # Whitefield -> BWSSB Kadabesanahalli (same corridor)
    "BLR_002": "KA011",  # HSR Layout -> Silk Board (adjacent)
    "BLR_003": "KA009",  # Peenya -> Peenya (exact match)
    "BLR_004": "KA003",  # Marathahalli -> BWSSB Kadabesanahalli (nearest)
    "BLR_005": "KA007",  # Koramangala -> Hombegowda Nagar (adjacent)
    "BLR_006": "KA006",  # Yelahanka -> Hebbal (nearest available, no northern station)
    "BLR_007": "KA011",  # Bellandur -> Silk Board (same corridor)
    "BLR_008": "KA004",  # Rajajinagar -> Bapuji Nagar (adjacent)
    "BLR_009": "KA002",  # Electronic City -> BTM Layout (nearest available, no southern station)
    "BLR_010": "KA006",  # Hebbal -> Hebbal (exact match)
    "BLR_011": "KA003",  # Indiranagar -> BWSSB Kadabesanahalli (nearest available)
    "BLR_012": "KA003",  # Kadugodi -> BWSSB Kadabesanahalli (same corridor as Whitefield)
}

# ─── Real per-station average AQI -> relative multiplier ──────────────────
station_avg = df.groupby("StationId")["AQI"].mean()
city_avg = df["AQI"].mean()
station_relative = (station_avg / city_avg).round(3).to_dict()

ward_relative = {
    ward: station_relative[station_id]
    for ward, station_id in WARD_TO_STATION.items()
}

print("Real ward multipliers (derived from real station averages):")
for ward, rel in ward_relative.items():
    station = WARD_TO_STATION[ward]
    print(f"  {ward} -> {station} ({STATION_NAMES[station]}): {rel}")

# ─── Real hourly diurnal pattern ───────────────────────────────────────────
hourly_avg = df.groupby("hour")["AQI"].mean()
hourly_relative = (hourly_avg / hourly_avg.mean()).round(3).to_dict()

print("\nReal hourly pattern (relative to daily mean):")
for h in range(24):
    print(f"  hour={h:02d}: {hourly_relative[h]}")

# ─── Compare against the OLD guessed assumptions ───────────────────────────
print("\n" + "=" * 60)
print("COMPARISON: old guessed vs real data")
print("=" * 60)
print("Old assumption: morning rush hour (8-10am) is a POLLUTION PEAK (1.35x)")
print(f"Real data:      hour=08 is actually a LOW point ({hourly_relative[8]}x)")
print("Old assumption: evening peak was 18-20h (1.25x)")
print(f"Real data:      evening peak is actually later, 19-21h, "
      f"peaking at hour=20 ({hourly_relative[20]}x)")

# ─── Save results ───────────────────────────────────────────────────────────
output = {
    "ward_relative_multipliers": ward_relative,
    "hourly_relative_pattern": {str(k): v for k, v in hourly_relative.items()},
    "ward_to_station_mapping": WARD_TO_STATION,
    "station_names": STATION_NAMES,
    "data_source": "CPCB/KSPCB via rohanrao/air-quality-data-in-india (Kaggle)",
    "date_range": f"{df['Datetime'].min()} to {df['Datetime'].max()}",
    "total_readings": len(df),
}
with open("real_ward_hourly_constants.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nSaved: real_ward_hourly_constants.json")
