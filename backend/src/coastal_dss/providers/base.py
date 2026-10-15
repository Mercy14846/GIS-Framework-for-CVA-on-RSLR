"""Data provider contract.

The science and API layers depend only on this protocol. `DemoProvider` serves synthetic
placeholder data; a `RasterProvider` (GeoTIFF / PostGIS) will implement the same interface
when real layers are ingested, with no change to services, API or frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Grid:
    lon0: float
    lat0: float
    lon1: float
    lat1: float
    nx: int
    ny: int

    @property
    def dlon(self) -> float:
        return (self.lon1 - self.lon0) / self.nx

    @property
    def dlat(self) -> float:
        return (self.lat1 - self.lat0) / self.ny

    @property
    def cell_area_km2(self) -> float:
        lat_mid = np.radians((self.lat0 + self.lat1) / 2)
        return (self.dlon * 111.32 * np.cos(lat_mid)) * (self.dlat * 110.57)


class DataProvider(Protocol):
    mode: str
    grid: Grid

    def elevation_m(self) -> np.ndarray: ...
    def subsidence_rate_mm_yr(self) -> np.ndarray: ...
    def sea_mask(self) -> np.ndarray: ...
    def population(self) -> np.ndarray: ...
    def built_up_fraction(self) -> np.ndarray: ...
    def indicator_layers(self) -> dict[str, tuple[np.ndarray, bool]]:
        """Raw non-RSLR indicators as {name: (values, invert)}; invert=True when low = vulnerable."""
        ...
