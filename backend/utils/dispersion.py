"""
PRANAVYU — Atmospheric Dispersion & Source Attribution Engine

Implements Gaussian plume dispersion model to attribute observed AQI
to upstream emission sources, given wind vector and source locations.

Reference: EPA Gaussian Plume Model, Seinfeld & Pandis (2016) Ch. 18
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional


# ─── Stability Classes (Pasquill-Gifford) ────────────────────────────────────

@dataclass
class DispersionCoefficients:
    """
    Pasquill-Gifford dispersion sigma coefficients.
    Simplified power-law form: sigma = a * x^b (x in km, sigma in m)
    """
    sigma_y_a: float
    sigma_y_b: float
    sigma_z_a: float
    sigma_z_b: float


# Stability class D (neutral, typical urban daytime)
STABILITY_D = DispersionCoefficients(
    sigma_y_a=0.22, sigma_y_b=0.89,
    sigma_z_a=0.16, sigma_z_b=0.82
)

# Stability class F (stable, typical night calm)
STABILITY_F = DispersionCoefficients(
    sigma_y_a=0.08, sigma_y_b=0.86,
    sigma_z_a=0.06, sigma_z_b=0.62
)


def _sigmas(x_km: float, coeff: DispersionCoefficients) -> tuple[float, float]:
    """Return (sigma_y, sigma_z) in meters given downwind distance in km."""
    x_km = max(x_km, 0.05)  # minimum 50m to avoid division issues
    sy = coeff.sigma_y_a * (x_km ** coeff.sigma_y_b) * 1000
    sz = coeff.sigma_z_a * (x_km ** coeff.sigma_z_b) * 1000
    return sy, sz


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Bearing from point 1 to point 2 in degrees (0=N, 90=E)."""
    d_lon = math.radians(lon2 - lon1)
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    x = math.sin(d_lon) * math.cos(lat2r)
    y = (math.cos(lat1r) * math.sin(lat2r) -
         math.sin(lat1r) * math.cos(lat2r) * math.cos(d_lon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def angular_difference(a: float, b: float) -> float:
    """Signed angular difference a-b in [-180, 180]."""
    diff = (a - b + 180) % 360 - 180
    return diff


def gaussian_ground_concentration(
    Q: float,              # emission rate, arbitrary units (e.g. μg/s)
    u: float,              # wind speed m/s
    x_km: float,           # downwind distance km
    y_m: float,            # crosswind offset m
    H: float = 20.0,       # effective stack height m
    stability: DispersionCoefficients = STABILITY_D,
    mixing_height: float = 500.0,
) -> float:
    """
    Gaussian plume ground-level concentration at (x, y, z=0).
    Returns concentration in same units as Q / (m² · s).
    Applies reflection at mixing_height.
    """
    if x_km <= 0 or u < 0.1:
        return 0.0

    sy, sz = _sigmas(x_km, stability)
    sz = min(sz, mixing_height / 2)  # cap at mixing layer

    term1 = Q / (2 * math.pi * sy * sz * u)
    term2 = math.exp(-0.5 * (y_m / sy) ** 2)

    # Vertical: ground reflection + lid reflection
    term3 = math.exp(-0.5 * ((H) / sz) ** 2) + math.exp(-0.5 * ((2 * mixing_height - H) / sz) ** 2)

    return term1 * term2 * term3


# ─── Source Attribution ───────────────────────────────────────────────────────

@dataclass
class SourceContribution:
    source_id: str
    source_name: str
    category: str
    distance_km: float
    downwind: bool          # is receptor downwind of source?
    angular_offset: float   # degrees off the wind axis
    raw_score: float        # unnormalized contribution
    normalized_fraction: float = 0.0
    confidence_contribution: float = 0.0


def compute_source_attribution(
    receptor_lat: float,
    receptor_lon: float,
    sources: list[dict],           # list with keys: lat, lon, source_id, name, category, historical_violation_rate
    wind_direction: float,         # degrees, FROM which direction wind blows (meteorological)
    wind_speed: float,             # m/s
    mixing_height: float = 500.0,
    hour: int = 12,
    aqi_value: float = 150.0,
) -> list[SourceContribution]:
    """
    For each emission source, compute its estimated contribution to the receptor's AQI.

    Wind direction convention: meteorological (direction wind comes FROM).
    Transport direction = wind_direction + 180° (where pollutants go TO).
    """
    # Transport direction: where particles move TO
    transport_dir = (wind_direction + 180) % 360

    # Stability: night with low wind → F (stable), daytime → D (neutral)
    if (hour < 6 or hour >= 21) and wind_speed < 3:
        stability = STABILITY_F
    else:
        stability = STABILITY_D

    # Emission rate proxy: higher for industrial/burning at night
    def emission_rate(cat: str, h: int, viol_rate: float) -> float:
        base = {"industrial": 1000, "burning": 800, "construction": 400, "traffic": 300, "other": 200}
        b = base.get(cat, 300)
        # Night multiplier for industrial (violation pattern)
        if cat == "industrial" and (h >= 22 or h <= 3):
            b *= (1.5 + viol_rate)
        elif cat == "burning" and (h >= 4 and h <= 7):
            b *= 1.8
        elif cat == "traffic" and (8 <= h <= 10 or 17 <= h <= 20):
            b *= 1.6
        return b

    contributions: list[SourceContribution] = []

    for src in sources:
        dist_km = haversine_km(src["lat"], src["lon"], receptor_lat, receptor_lon)
        if dist_km < 0.05:
            dist_km = 0.05

        # Only consider sources within 15km
        if dist_km > 15.0:
            continue

        # Bearing from source to receptor
        bearing_src_to_rec = bearing_deg(src["lat"], src["lon"], receptor_lat, receptor_lon)

        # Is receptor downwind of source?
        # Source emits in transport_dir; receptor is downwind if bearing ≈ transport_dir
        angle_off = abs(angular_difference(bearing_src_to_rec, transport_dir))
        downwind = angle_off < 60  # within 60° of wind axis

        # Crosswind offset
        y_m = dist_km * 1000 * math.sin(math.radians(angle_off))

        # x is the along-wind distance
        x_km = dist_km * abs(math.cos(math.radians(angle_off)))
        x_km = max(x_km, 0.05)

        Q = emission_rate(
            src["category"], hour,
            src.get("historical_violation_rate", 0.5)
        )

        conc = gaussian_ground_concentration(
            Q=Q, u=max(wind_speed, 0.5),
            x_km=x_km, y_m=y_m,
            H=15.0,  # effective source height (ground-level for construction/traffic; ~20m for industrial)
            stability=stability,
            mixing_height=mixing_height,
        )

        # Downwind bonus: receptor must be reasonably downwind to get high score
        directional_weight = max(0.05, math.cos(math.radians(angle_off))) if downwind else 0.05

        raw_score = conc * directional_weight * (1 + src.get("historical_violation_rate", 0.5))

        contributions.append(SourceContribution(
            source_id=src["source_id"],
            source_name=src["name"],
            category=src["category"],
            distance_km=round(dist_km, 2),
            downwind=downwind,
            angular_offset=round(angle_off, 1),
            raw_score=raw_score,
        ))

    # Normalize to fractions
    total = sum(c.raw_score for c in contributions)
    if total > 0:
        for c in contributions:
            c.normalized_fraction = round(c.raw_score / total, 3)

    # Confidence: based on wind speed + number of downwind sources identified
    n_downwind = sum(1 for c in contributions if c.downwind)
    conf_base = min(0.95, 0.55 + wind_speed * 0.04 + n_downwind * 0.05)
    for c in contributions:
        c.confidence_contribution = conf_base if c.downwind else conf_base * 0.6

    # Sort by contribution
    contributions.sort(key=lambda c: c.raw_score, reverse=True)
    return contributions


def aggregate_by_category(contributions: list[SourceContribution]) -> dict[str, float]:
    """Sum normalized fractions by category."""
    cats: dict[str, float] = {}
    for c in contributions:
        cats[c.category] = cats.get(c.category, 0.0) + c.normalized_fraction
    # Normalize again (ensure sum = 1)
    total = sum(cats.values())
    if total > 0:
        cats = {k: round(v / total, 3) for k, v in cats.items()}
    return cats
