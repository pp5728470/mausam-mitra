"""Centralized weather-category compatibility matrix for correlation."""

from __future__ import annotations

# Canonical category keys used for matching.
CATEGORY_ALIASES: dict[str, str] = {
    "heavy rainfall": "heavy_rainfall",
    "heavy rain": "heavy_rainfall",
    "rainfall": "heavy_rainfall",
    "rain": "heavy_rainfall",
    "flood / waterlogging": "flood_waterlogging",
    "flood/waterlogging": "flood_waterlogging",
    "flood": "flood_waterlogging",
    "waterlogging": "flood_waterlogging",
    "waterlog": "flood_waterlogging",
    "storm / strong winds": "storm",
    "storm/strong winds": "storm",
    "storm": "storm",
    "strong winds": "storm",
    "severe storm": "storm",
    "severe weather": "storm",
    "lightning": "lightning",
    "extreme heat": "extreme_heat",
    "heat": "extreme_heat",
    "heat-related warning": "extreme_heat",
    "heat stress": "extreme_heat",
    "dense fog": "dense_fog",
    "visibility / dense fog": "dense_fog",
    "fog": "dense_fog",
    "landslide": "landslide",
    "hailstorm": "hailstorm",
    "hail": "hailstorm",
}

# Compatible pairs (symmetric). Same category is always compatible.
COMPATIBLE_PAIRS: set[tuple[str, str]] = {
    ("heavy_rainfall", "flood_waterlogging"),
    ("heavy_rainfall", "storm"),
    ("storm", "lightning"),
    ("storm", "hailstorm"),
    ("heavy_rainfall", "lightning"),
    ("flood_waterlogging", "storm"),
}

# Explicitly incompatible pairs.
INCOMPATIBLE_PAIRS: set[tuple[str, str]] = {
    ("extreme_heat", "dense_fog"),
    ("extreme_heat", "landslide"),
    ("extreme_heat", "flood_waterlogging"),
    ("dense_fog", "landslide"),
}


def normalize_category(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    key = raw.strip().lower()
    if key in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[key]
    for alias, canonical in CATEGORY_ALIASES.items():
        if alias in key or key in alias:
            return canonical
    return None


def category_compatibility_score(
    category_a: str | None, category_b: str | None
) -> tuple[float, str]:
    """Return (0–100 score, reason). Neutral 50 when unknown."""
    a = normalize_category(category_a)
    b = normalize_category(category_b)
    if a is None or b is None:
        return 50.0, "Category unavailable — neutral compatibility."
    if a == b:
        return 100.0, "Same weather category."
    pair = tuple(sorted((a, b)))
    if pair in {tuple(sorted(p)) for p in COMPATIBLE_PAIRS}:
        return 95.0, "Compatible weather categories."
    if pair in {tuple(sorted(p)) for p in INCOMPATIBLE_PAIRS}:
        return 10.0, "Incompatible weather categories."
    return 40.0, "Unrelated categories — weak compatibility."


def cluster_category_score(categories: list[str | None]) -> tuple[float, str]:
    """Score a multi-report cluster by pairwise compatibility."""
    known = [c for c in (normalize_category(x) for x in categories) if c]
    if len(known) < 2:
        return 50.0, "Insufficient category data for cluster scoring."
    scores: list[float] = []
    for i, a in enumerate(known):
        for b in known[i + 1 :]:
            score, _ = category_compatibility_score(a, b)
            scores.append(score)
    if not scores:
        return 50.0, "Insufficient category pairs."
    avg = sum(scores) / len(scores)
    if avg >= 80:
        reason = "Strong category compatibility across the cluster."
    elif avg >= 50:
        reason = "Moderate category compatibility across the cluster."
    else:
        reason = "Weak category compatibility across the cluster."
    return round(avg, 1), reason
