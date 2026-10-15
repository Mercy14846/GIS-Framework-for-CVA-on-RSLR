"""Indicator standardisation to the 1-5 scale (higher = more vulnerable)."""

from __future__ import annotations

import numpy as np


def minmax_1_5(
    values: np.ndarray,
    invert: bool = False,
    lo: float | None = None,
    hi: float | None = None,
) -> np.ndarray:
    """Min-max scale to 1-5. Use invert=True where LOW raw values mean HIGH vulnerability
    (e.g. elevation). Pass fixed `lo`/`hi` so scales stay comparable across scenarios."""
    v = np.asarray(values, dtype=float)
    lo = np.nanmin(v) if lo is None else lo
    hi = np.nanmax(v) if hi is None else hi
    if hi == lo:
        return np.full_like(v, 3.0)
    s = 1.0 + 4.0 * np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    return 6.0 - s if invert else s
