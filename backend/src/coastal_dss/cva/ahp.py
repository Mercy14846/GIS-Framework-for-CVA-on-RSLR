"""Analytic Hierarchy Process weighting with a consistency check."""

from __future__ import annotations

import numpy as np

# Saaty random consistency index by matrix size.
_RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def ahp_weights(pairwise: np.ndarray) -> tuple[np.ndarray, float]:
    """Return (weights, consistency_ratio) from a reciprocal pairwise comparison matrix.

    A consistency ratio below 0.10 is conventionally acceptable.
    """
    a = np.asarray(pairwise, dtype=float)
    n = a.shape[0]
    if a.shape != (n, n):
        raise ValueError("pairwise matrix must be square")
    if not np.allclose(a * a.T, 1.0, atol=1e-6):
        raise ValueError("pairwise matrix must be reciprocal (a_ij * a_ji = 1)")
    eigvals, eigvecs = np.linalg.eig(a)
    k = int(np.argmax(eigvals.real))
    w = np.abs(eigvecs[:, k].real)
    w = w / w.sum()
    lam = eigvals[k].real
    ci = (lam - n) / (n - 1) if n > 2 else 0.0
    ri = _RI.get(n, 1.49)
    cr = ci / ri if ri else 0.0
    return w, float(cr)
