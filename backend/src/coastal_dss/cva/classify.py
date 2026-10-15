"""Natural-breaks (Fisher-Jenks) classification into five vulnerability classes."""

from __future__ import annotations

import numpy as np


def jenks_breaks(values: np.ndarray, k: int = 5, max_samples: int = 400) -> np.ndarray:
    """Fisher-Jenks optimal breaks. Returns k+1 break values including min and max.

    Large inputs are subsampled by quantile for speed (O(k n^2) dynamic programme).
    """
    v = np.sort(np.asarray(values, dtype=float).ravel())
    v = v[~np.isnan(v)]
    if len(np.unique(v)) < k:
        return np.linspace(v.min(), v.max(), k + 1)
    if len(v) > max_samples:
        v = np.quantile(v, np.linspace(0, 1, max_samples))
    n = len(v)
    mat1 = np.zeros((n + 1, k + 1))
    mat2 = np.full((n + 1, k + 1), np.inf)
    mat1[1, 1:] = 1
    mat2[1, 1:] = 0
    for l in range(2, n + 1):
        s1 = s2 = w = 0.0
        for m in range(1, l + 1):
            i3 = l - m + 1
            val = v[i3 - 1]
            s2 += val * val
            s1 += val
            w += 1
            var = s2 - (s1 * s1) / w
            i4 = i3 - 1
            if i4 != 0:
                for j in range(2, k + 1):
                    if mat2[l, j] >= var + mat2[i4, j - 1]:
                        mat1[l, j] = i3
                        mat2[l, j] = var + mat2[i4, j - 1]
        mat1[l, 1] = 1
        mat2[l, 1] = var
    breaks = np.zeros(k + 1)
    breaks[k] = v[-1]
    breaks[0] = v[0]
    idx = n
    for j in range(k, 1, -1):
        idx = int(mat1[idx, j]) - 1
        breaks[j - 1] = v[idx - 1]
    return breaks


def classify(values: np.ndarray, breaks: np.ndarray) -> np.ndarray:
    """Class index 1..k for each value given k+1 breaks."""
    inner = np.asarray(breaks)[1:-1]
    return np.digitize(values, inner, right=True) + 1
