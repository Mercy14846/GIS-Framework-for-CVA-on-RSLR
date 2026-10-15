"""Relative sea level rise model (Objective i).

    RSLR(x, t) = GMSLR(t) + LSR(x) * (t - t0)

Sign convention: subsidence rate is POSITIVE when land is sinking (mm/yr). Uplift is negative.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from coastal_dss.core.constants import BASELINE_YEAR


def subsidence_offset_m(rate_mm_yr: np.ndarray | float, year: int) -> np.ndarray | float:
    """Cumulative land lowering in metres from the baseline year to `year`."""
    return np.asarray(rate_mm_yr) * (year - BASELINE_YEAR) / 1000.0


def rslr_m(
    gmslr: float,
    subsidence_rate_mm_yr: np.ndarray,
    year: int,
    include_subsidence: bool = True,
) -> np.ndarray:
    """RSLR surface in metres. Set include_subsidence=False for the global-only comparison."""
    base = np.full_like(np.asarray(subsidence_rate_mm_yr, dtype=float), gmslr)
    if include_subsidence:
        base = base + subsidence_offset_m(subsidence_rate_mm_yr, year)
    return base


def inundation(
    elevation_m: np.ndarray,
    level_m: float | np.ndarray,
    sea_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Bathtub inundation split into hydrologically connected and unconnected cells.

    A cell floods when elevation <= level. Flooded land connected to the sea (4-neighbour)
    is `connected`; low-lying land that is not connected is `unconnected` (it may still
    flood through drainage, so it is reported separately, as in the NOAA viewer).
    Land cells only: sea cells are excluded from both outputs.
    """
    level = np.asarray(level_m)
    candidate = (elevation_m <= level) | sea_mask
    labels, _ = ndimage.label(candidate)  # default structure = 4-connectivity
    sea_labels = np.unique(labels[sea_mask & (labels > 0)])
    connected_all = np.isin(labels, sea_labels)
    land = ~sea_mask
    connected = connected_all & land & candidate
    unconnected = candidate & land & ~connected_all
    return connected, unconnected
