"""Import rasterio with its own PROJ and GDAL data.

Other GIS installs (PostGIS on Windows, QGIS, conda) often set PROJ_LIB and GDAL_DATA
system-wide. rasterio wheels bundle matching data, and pointing them at another PROJ version's
proj.db fails with "DATABASE.LAYOUT.VERSION ... comes from another PROJ installation".
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _use_bundled_data() -> None:
    spec = importlib.util.find_spec("rasterio")
    if spec is None or not spec.submodule_search_locations:
        return
    pkg = Path(next(iter(spec.submodule_search_locations)))
    proj, gdal = pkg / "proj_data", pkg / "gdal_data"
    if (proj / "proj.db").exists():
        os.environ["PROJ_DATA"] = os.environ["PROJ_LIB"] = str(proj)
    if gdal.is_dir():
        os.environ["GDAL_DATA"] = str(gdal)


_use_bundled_data()

import rasterio
import rasterio.transform
import rasterio.warp

__all__ = ["rasterio"]
