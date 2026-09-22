"""Derive deterministic incident types and titles from correlated reports."""

from __future__ import annotations

from collections import Counter

from app.services.category_compatibility import normalize_category

# Canonical incident type labels for operators.
TYPE_LABELS: dict[str, str] = {
    "flood_waterlogging": "Flood / Waterlogging",
    "heavy_rainfall": "Heavy Rainfall",
    "storm": "Severe Storm",
    "lightning": "Severe Storm",
    "extreme_heat": "Extreme Heat",
    "dense_fog": "Dense Fog",
    "landslide": "Landslide",
    "hailstorm": "Severe Storm",
}

CITY_LOOKUP: list[tuple[float, float, float, str]] = [
    # lat, lng, radius_deg approx, city label
    (18.5204, 73.8567, 0.35, "Pune"),
    (19.0760, 72.8777, 0.40, "Mumbai"),
    (23.0225, 72.5714, 0.35, "Ahmedabad"),
    (26.1445, 91.7362, 0.35, "Guwahati"),
    (28.6139, 77.2090, 0.45, "Delhi"),
    (13.0827, 80.2707, 0.35, "Chennai"),
    (17.3850, 78.4867, 0.35, "Hyderabad"),
    (22.5726, 88.3639, 0.35, "Kolkata"),
    (25.5941, 85.1376, 0.30, "Patna"),
    (23.2599, 77.4126, 0.30, "Bhopal"),
    (12.9716, 77.5946, 0.35, "Bengaluru"),
    (26.9124, 75.7873, 0.30, "Jaipur"),
    (9.9312, 76.2673, 0.30, "Kochi"),
]

LOCALITY_HINTS: list[tuple[str, str]] = [
    ("hinjewadi", "Hinjewadi"),
    ("wakad", "Wakad"),
    ("tathawade", "Tathawade"),
    ("baner", "Baner"),
    ("andheri", "Andheri"),
    ("bandra", "Bandra"),
]


def derive_incident_type(categories: list[str | None]) -> str:
    keys = [normalize_category(c) for c in categories]
    keys = [k for k in keys if k]
    if not keys:
        return "Severe Weather"

    counts = Counter(keys)
    # Prefer flood/waterlogging when mixed with rainfall.
    if "flood_waterlogging" in counts and "heavy_rainfall" in counts:
        return TYPE_LABELS["flood_waterlogging"]
    if "storm" in counts and "lightning" in counts:
        return TYPE_LABELS["storm"]
    top = counts.most_common(1)[0][0]
    return TYPE_LABELS.get(top, "Severe Weather")


def nearest_city(latitude: float, longitude: float) -> str:
    best: tuple[float, str] | None = None
    for lat, lng, radius, city in CITY_LOOKUP:
        dist = abs(latitude - lat) + abs(longitude - lng)
        if dist <= radius and (best is None or dist < best[0]):
            best = (dist, city)
    return best[1] if best else "Regional"


def locality_from_texts(texts: list[str]) -> str | None:
    blob = " ".join(texts).lower()
    for needle, label in LOCALITY_HINTS:
        if needle in blob:
            return label
    return None


def derive_incident_title(
    *,
    latitude: float,
    longitude: float,
    incident_type: str,
    texts: list[str] | None = None,
) -> str:
    locality = locality_from_texts(texts or [])
    place = locality or nearest_city(latitude, longitude)
    # Short type fragment for title.
    type_bit = incident_type
    if incident_type == "Flood / Waterlogging":
        type_bit = "Waterlogging"
    elif incident_type == "Severe Storm":
        type_bit = "Severe Storm"
    return f"{place} {type_bit}"
