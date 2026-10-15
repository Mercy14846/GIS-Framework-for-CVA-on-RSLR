"""Real layers from data/processed (written by `coastal_dss.ingestion` from USGS M2M inputs).

Any layer that has not been ingested yet (population and subsidence have no USGS source) falls
back to the synthetic demo layer on the same grid, and `sources()` says so, so the viewer can
label exactly which numbers rest on placeholders.
"""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

import numpy as np

from coastal_dss.providers.base import LAYER_LABELS, Grid
from coastal_dss.providers.demo import DemoProvider


def _read(path: Path) -> np.ndarray:
    from coastal_dss.core.geo import rasterio

    with rasterio.open(path) as src:
        return src.read(1).astype(float)


class RasterProvider:
    mode = "raster"

    def __init__(self, processed_dir: Path) -> None:
        self.dir = processed_dir
        path = processed_dir / "manifest.json"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found: run `python -m coastal_dss.ingestion all` first"
            )
        self.manifest = json.loads(path.read_text(encoding="utf-8"))
        self.grid = Grid(**self.manifest["grid"])
        self._demo = DemoProvider(grid=self.grid)

    def _layer(self, name: str) -> np.ndarray | None:
        info = self.manifest["layers"].get(name)
        if not info:
            return None
        arr = _read(self.dir / info["file"])
        if arr.shape != (self.grid.ny, self.grid.nx):
            raise ValueError(f"{name}: shape {arr.shape} does not match the grid")
        return arr

    @cached_property
    def _layers(self) -> dict[str, np.ndarray | None]:
        return {name: self._layer(name) for name in LAYER_LABELS}

    def elevation_m(self) -> np.ndarray:
        e = self._layers["elevation"]
        return e if e is not None else self._demo.elevation_m()

    def sea_mask(self) -> np.ndarray:
        s = self._layers["sea_mask"]
        return s > 0.5 if s is not None else self._demo.sea_mask()

    def subsidence_rate_mm_yr(self) -> np.ndarray:
        s = self._layers["subsidence"]
        return s if s is not None else self._demo.subsidence_rate_mm_yr()

    @cached_property
    def _population(self) -> np.ndarray:
        p = self._layers["population"]
        p = p if p is not None else self._demo.population().copy()
        return np.where(self.sea_mask(), 0.0, p)

    def population(self) -> np.ndarray:
        return self._population

    def built_up_fraction(self) -> np.ndarray:
        b = self._layers["built_up"]
        return np.clip(b, 0, 1) if b is not None else self._demo.built_up_fraction()

    def indicator_layers(self) -> dict[str, tuple[np.ndarray, bool]]:
        demo = self._demo.indicator_layers()
        elev = self.elevation_m()

        def pick(name: str, fallback: str) -> np.ndarray:
            v = self._layers[name]
            return v if v is not None else demo[fallback][0]

        return {
            "elevation": (elev, True),
            "slope": (pick("slope", "slope"), True),
            "shoreline_change": (pick("shoreline_change", "shoreline_change"), False),
            "geomorphology": (pick("geomorphology", "geomorphology"), False),
            "population_density": (self.population(), False),
            "infrastructure_proximity": (self.built_up_fraction(), False),
        }

    def sources(self) -> list[dict]:
        out = []
        for name, label in LAYER_LABELS.items():
            info = self.manifest["layers"].get(name)
            if info:
                out.append({"layer": name, "label": label, **info})
            else:
                out.append({"layer": name, "label": label, "status": "synthetic",
                            "source": "Synthetic placeholder (not ingested yet)"})
        return out
