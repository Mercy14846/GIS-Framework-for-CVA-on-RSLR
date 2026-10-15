"""Orchestrates the analytical engine: RSLR -> inundation -> CVA/CVI -> impact.

Separated from the API so the same workflow can run from background jobs or notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product

import numpy as np

from coastal_dss.core.constants import (
    BASELINE_YEAR,
    CVI_CLASSES,
    HORIZONS,
    LAGOS_MHHW_M,
    PATHWAYS,
)
from coastal_dss.cva.ahp import ahp_weights
from coastal_dss.cva.classify import classify, jenks_breaks
from coastal_dss.cva.cvi import cvi
from coastal_dss.cva.standardise import minmax_1_5
from coastal_dss.impact.exposure import exposure_summary
from coastal_dss.providers import get_provider
from coastal_dss.rslr.gmslr import gmslr_m
from coastal_dss.rslr.model import inundation, rslr_m
from coastal_dss.scenarios.registry import Scenario

# PLACEHOLDER expert priorities (sum arbitrary). Replace with the pairwise matrix elicited
# from experts; the matrix is built from ratios so it is perfectly consistent (CR = 0).
PRIORITIES = {
    "rslr": 5.0,
    "elevation": 4.0,
    "shoreline_change": 3.0,
    "slope": 2.0,
    "geomorphology": 2.0,
    "population_density": 3.0,
    "infrastructure_proximity": 2.0,
}


def default_weights() -> tuple[dict[str, float], float]:
    names = list(PRIORITIES)
    p = np.array([PRIORITIES[n] for n in names])
    matrix = p[:, None] / p[None, :]
    w, cr = ahp_weights(matrix)
    return dict(zip(names, w.tolist(), strict=True)), cr


@dataclass
class Assessment:
    scenario: Scenario
    rslr: np.ndarray
    surface: np.ndarray  # water surface above MSL: high tide + RSLR + water level
    connected: np.ndarray
    unconnected: np.ndarray
    cvi: np.ndarray
    cvi_class: np.ndarray
    summary: dict


def _rslr_bounds() -> tuple[float, float]:
    p = get_provider()
    hi = max(gmslr_m(k, HORIZONS[-1]) for k in PATHWAYS)
    hi += float(p.subsidence_rate_mm_yr().max()) * (HORIZONS[-1] - BASELINE_YEAR) / 1000.0
    return 0.0, hi


def _raw_cvi(sc: Scenario) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    p = get_provider()
    level = rslr_m(
        gmslr_m(sc.pathway, sc.year), p.subsidence_rate_mm_yr(), sc.year, sc.include_subsidence
    )
    layers = {k: minmax_1_5(v, invert=inv) for k, (v, inv) in p.indicator_layers().items()}
    lo, hi = _rslr_bounds()
    layers["rslr"] = minmax_1_5(level, lo=lo, hi=hi)
    weights, _ = default_weights()
    return level, cvi(layers, weights), p.sea_mask(), p.elevation_m()


@lru_cache(maxsize=1)
def reference_breaks() -> np.ndarray:
    """Natural breaks pooled over every scenario so classes mean the same in all views."""
    pooled = []
    for pw, yr, sub in product(PATHWAYS, HORIZONS, (True, False)):
        _, v, sea, _ = _raw_cvi(Scenario(pw, yr, sub))
        pooled.append(v[~sea])
    return jenks_breaks(np.concatenate(pooled), k=5)


@lru_cache(maxsize=64)
def assess(sc: Scenario) -> Assessment:
    sc.validate()
    p = get_provider()
    level, v, sea, elev = _raw_cvi(sc)
    # Flooding uses the full water surface; vulnerability (CVI) stays on long-term RSLR only.
    surface = level + LAGOS_MHHW_M + sc.water_level_m
    connected, unconnected = inundation(elev, surface, sea)
    classes = classify(v, reference_breaks())
    summary = exposure_summary(
        connected, p.population(), p.grid.cell_area_km2, p.built_up_fraction()
    )
    summary["unconnected_area_km2"] = float(unconnected.sum() * p.grid.cell_area_km2)
    summary["mean_rslr_m"] = float(level[~sea].mean())
    summary["max_rslr_m"] = float(level[~sea].max())
    summary["water_level_m"] = sc.water_level_m
    summary["high_or_very_high_area_km2"] = float(
        ((classes >= 4) & ~sea).sum() * p.grid.cell_area_km2
    )
    return Assessment(sc, level, surface, connected, unconnected, v, classes, summary)


def class_label(idx: int) -> str:
    return CVI_CLASSES[idx - 1]
