"""Synthetic placeholder data over central Lagos. NOT real measurements.

Row 0 is the northern edge of the grid; the Atlantic coast lies to the south.
"""

from __future__ import annotations

from functools import cached_property

import numpy as np
from scipy import ndimage

from coastal_dss.providers.base import Grid


class DemoProvider:
    mode = "demo"
    grid = Grid(lon0=3.20, lat0=6.35, lon1=3.75, lat1=6.65, nx=60, ny=40)

    def __init__(self, seed: int = 7) -> None:
        self._rng = np.random.default_rng(seed)

    @cached_property
    def _xy(self) -> tuple[np.ndarray, np.ndarray]:
        x = (np.arange(self.grid.nx) + 0.5) / self.grid.nx
        y = 1.0 - (np.arange(self.grid.ny) + 0.5) / self.grid.ny  # 0 = south coast
        return np.meshgrid(x, y)

    @cached_property
    def _coast_y(self) -> np.ndarray:
        x, _ = self._xy
        return 0.20 + 0.04 * np.sin(2 * np.pi * 1.5 * x)

    @cached_property
    def _dist(self) -> np.ndarray:
        """Normalised distance inland from the coast (negative at sea)."""
        _, y = self._xy
        return y - self._coast_y

    def _smooth_noise(self, scale: float) -> np.ndarray:
        n = self._rng.normal(size=(self.grid.ny, self.grid.nx))
        n = ndimage.gaussian_filter(n, 2.0)
        return scale * n / np.abs(n).max()

    @cached_property
    def _elev(self) -> np.ndarray:
        x, y = self._xy
        d = np.clip(self._dist, 0, None)
        e = 0.2 + 9.0 * d**0.9 + self._smooth_noise(0.8)
        e -= 3.2 * np.exp(-(((x - 0.72) ** 2) + ((y - 0.55) ** 2)) / 0.004)  # unconnected hollow
        e = np.clip(e, 0.05, None)
        e[self._dist < 0] = -1.0
        return e

    def elevation_m(self) -> np.ndarray:
        return self._elev

    def sea_mask(self) -> np.ndarray:
        return self._dist < 0

    def subsidence_rate_mm_yr(self) -> np.ndarray:
        x, _ = self._xy
        d = np.clip(self._dist, 0, None)
        s = 2.0 + 38.0 * np.exp(-d / 0.08) * (0.6 + 0.4 * x)
        return np.clip(s + self._smooth_noise(2.0), 0.0, 40.0)

    @cached_property
    def _pop(self) -> np.ndarray:
        d = np.clip(self._dist, 0, None)
        p = 9000 * np.exp(-d / 0.28) * (0.6 + 0.8 * np.abs(self._smooth_noise(1.0)))
        p[self._dist < 0] = 0
        return p

    def population(self) -> np.ndarray:
        return self._pop

    def built_up_fraction(self) -> np.ndarray:
        return np.clip(self._pop / self._pop.max(), 0, 1)

    def indicator_layers(self) -> dict[str, tuple[np.ndarray, bool]]:
        d = np.clip(self._dist, 0, None)
        gy, gx = np.gradient(np.where(self.sea_mask(), 0, self._elev))
        slope = np.hypot(gx, gy)
        shoreline = 4.0 * np.exp(-d / 0.05) * (0.5 + np.abs(self._smooth_noise(1.0)))
        geomorph = np.where(d < 0.06, 5.0, np.where(d < 0.2, 3.0, 1.0))
        return {
            "elevation": (self._elev, True),
            "slope": (slope, True),
            "shoreline_change": (shoreline, False),
            "geomorphology": (geomorph, False),
            "population_density": (self._pop, False),
            "infrastructure_proximity": (self.built_up_fraction(), False),
        }
