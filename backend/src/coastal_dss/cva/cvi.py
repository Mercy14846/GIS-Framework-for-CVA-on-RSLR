"""Coastal Vulnerability Index: CVI = sum_i (w_i * S_i)."""

from __future__ import annotations

import numpy as np


def cvi(indicators: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    """Weighted linear combination of standardised (1-5) indicators."""
    if set(indicators) != set(weights):
        raise ValueError("indicators and weights must have identical keys")
    total = sum(weights.values())
    if not np.isclose(total, 1.0, atol=1e-6):
        raise ValueError(f"weights must sum to 1 (got {total:.4f})")
    return sum(weights[k] * indicators[k] for k in indicators)
