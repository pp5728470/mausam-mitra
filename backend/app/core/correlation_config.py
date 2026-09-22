"""Centralized Phase 7 correlation configuration and weights."""

from __future__ import annotations

# Deterministic factor weights (must sum to 1.0).
CORRELATION_WEIGHTS: dict[str, float] = {
    "spatial": 0.30,
    "temporal": 0.20,
    "category": 0.20,
    "evidence": 0.15,
    "density": 0.10,
    "duplicate": 0.05,
}

# Candidate search defaults (overridable via settings / API).
DEFAULT_CORRELATION_RADIUS_KM = 5.0
DEFAULT_CORRELATION_WINDOW_MINUTES = 90
DEFAULT_CORRELATION_SCORE_THRESHOLD = 70.0
DEFAULT_MIN_INDEPENDENT_REPORTS = 2

# Text similarity above this → treat as likely duplicate (not independent).
DUPLICATE_SIMILARITY_THRESHOLD = 0.72

# Spatial score bands (distance_km → score).
SPATIAL_BANDS: list[tuple[float, float]] = [
    (1.0, 100.0),
    (2.5, 85.0),
    (5.0, 65.0),
]

# Temporal score bands (delta_minutes → score).
TEMPORAL_BANDS: list[tuple[float, float]] = [
    (20.0, 100.0),
    (45.0, 85.0),
    (90.0, 65.0),
]
