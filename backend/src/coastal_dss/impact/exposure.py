"""Impact assessment (Objective iii): exposure statistics by spatial overlay."""

from __future__ import annotations

import numpy as np


def exposure_summary(
    flooded: np.ndarray,
    population: np.ndarray,
    cell_area_km2: float,
    built_up_fraction: np.ndarray | None = None,
    road_km: np.ndarray | None = None,
) -> dict[str, float]:
    """Aggregate exposed population, area and (optionally) built-up area and roads."""
    out = {
        "flooded_area_km2": float(flooded.sum() * cell_area_km2),
        "population_exposed": float(population[flooded].sum()),
        "population_total": float(population.sum()),
    }
    out["population_exposed_pct"] = (
        100.0 * out["population_exposed"] / out["population_total"]
        if out["population_total"]
        else 0.0
    )
    if built_up_fraction is not None:
        out["built_up_area_at_risk_km2"] = float(
            (built_up_fraction * flooded).sum() * cell_area_km2
        )
    if road_km is not None:
        out["road_length_affected_km"] = float(road_km[flooded].sum())
    return out
