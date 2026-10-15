"""Grid -> GeoJSON serialisation (land cells only)."""

from __future__ import annotations

import numpy as np

from coastal_dss.providers.base import DataProvider
from coastal_dss.services.assessment import Assessment, class_label


def cells_geojson(provider: DataProvider, a: Assessment) -> dict:
    g = provider.grid
    elev = provider.elevation_m()
    pop = provider.population()
    sea = provider.sea_mask()
    feats = []
    for i in range(g.ny):
        lat_top = g.lat1 - i * g.dlat
        lat_bot = lat_top - g.dlat
        for j in range(g.nx):
            if sea[i, j]:
                continue
            lon_l = g.lon0 + j * g.dlon
            lon_r = lon_l + g.dlon
            state = (
                "connected"
                if a.connected[i, j]
                else "unconnected"
                if a.unconnected[i, j]
                else "dry"
            )
            depth = max(0.0, float(a.surface[i, j] - elev[i, j])) if state != "dry" else 0.0
            feats.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [lon_l, lat_bot],
                                [lon_r, lat_bot],
                                [lon_r, lat_top],
                                [lon_l, lat_top],
                                [lon_l, lat_bot],
                            ]
                        ],
                    },
                    "properties": {
                        "state": state,
                        "depth_m": round(depth, 2),
                        "elevation_m": round(float(elev[i, j]), 2),
                        "rslr_m": round(float(a.rslr[i, j]), 2),
                        "population": int(pop[i, j]),
                        "cvi": round(float(a.cvi[i, j]), 2),
                        "cvi_class": int(a.cvi_class[i, j]),
                        "cvi_label": class_label(int(a.cvi_class[i, j])),
                    },
                }
            )
    return {"type": "FeatureCollection", "features": feats}


def bbox(provider: DataProvider) -> list[float]:
    g = provider.grid
    return [g.lon0, g.lat0, g.lon1, g.lat1]


__all__ = ["bbox", "cells_geojson", "np"]
