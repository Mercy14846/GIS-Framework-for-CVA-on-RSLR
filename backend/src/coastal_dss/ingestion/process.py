"""Turn fetched rasters into analysis-grid layers: data/processed/<layer>.tif + manifest.json.

Every input is first warped onto one fine grid (~1 arc-second, the SRTM spacing) that nests
exactly inside the analysis grid, so aggregation is a block mean with no second resampling.

| Layer              | Method                                                              |
|--------------------|---------------------------------------------------------------------|
| elevation          | SRTM mean over land pixels of each cell; sea cells = -1             |
| slope              | SRTM slope (degrees) at ~30 m, mean over land pixels                |
| sea_mask           | Landsat MNDWI > 0 water that is connected to the open sea (south)   |
| built_up           | Share of pixels with NDBI > 0, NDVI < 0.25 and not water            |
| geomorphology      | 1-5 proxy class from elevation, NDVI wetness and distance to sea    |
| shoreline_change   | Net land lost to sea-connected water per year, early TM vs recent   |
| population         | Optional: data/raw/external/population.tif (e.g. GRID3), summed     |
| subsidence         | Optional: data/raw/external/subsidence.tif (InSAR, mm/yr), averaged |

Landsat Collection 2 Level-2 surface reflectance = DN * 0.0000275 - 0.2. Pixels flagged as
fill, dilated cloud, cirrus, cloud or cloud shadow in QA_PIXEL (bits 0-4) are dropped and the
remaining observations are combined with a per-pixel median.
"""

from __future__ import annotations

import datetime as dt
import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage

from coastal_dss.providers.base import Grid

try:  # rasterio is optional (`ingest` extra); core.geo must load it first (PROJ data)
    from coastal_dss.core.geo import rasterio

    from_bounds = rasterio.transform.from_bounds
    Resampling, reproject = rasterio.warp.Resampling, rasterio.warp.reproject
except ImportError:  # pragma: no cover - reported when process() is called
    rasterio = None

LANDSAT_QA_REJECT = 0b11111  # fill, dilated cloud, cirrus, cloud, cloud shadow
SR_SCALE, SR_OFFSET = 0.0000275, -0.2
COASTAL_ZONE_M = 3000.0
BEACH_ZONE_M = 500.0


def grid_transform(grid: Grid, width: int | None = None, height: int | None = None):
    """Affine transform of `grid`'s bounds at width x height pixels (default: one per cell)."""
    return from_bounds(grid.lon0, grid.lat0, grid.lon1, grid.lat1,
                       width or grid.nx, height or grid.ny)


@dataclass(frozen=True)
class Fine:
    grid: Grid
    fx: int
    fy: int

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.ny * self.fy, self.grid.nx * self.fx

    @property
    def transform(self):
        return grid_transform(self.grid, self.shape[1], self.shape[0])

    @property
    def pixel_m(self) -> tuple[float, float]:
        """(dy, dx) of one fine pixel in metres."""
        g = self.grid
        lat = np.radians((g.lat0 + g.lat1) / 2)
        return g.dlat / self.fy * 110_570.0, g.dlon / self.fx * 111_320.0 * np.cos(lat)


def fine_for(grid: Grid, arcsec: float = 1.0) -> Fine:
    return Fine(grid, max(1, round(grid.dlon * 3600 / arcsec)), max(1, round(grid.dlat * 3600 / arcsec)))


def _require_rasterio() -> None:
    if rasterio is None:
        raise RuntimeError("raster processing needs rasterio: pip install -e 'backend[ingest]'")


def warp(paths: list[Path], fine: Fine, resampling, nodata: float | None = None) -> np.ndarray:
    """Mosaic `paths` onto the fine grid (first valid value wins). NaN where nothing covers."""
    out = np.full(fine.shape, np.nan, dtype="float32")
    for p in paths:
        with rasterio.open(p) as src:
            tmp = np.full(fine.shape, np.nan, dtype="float32")
            reproject(
                source=rasterio.band(src, 1),
                destination=tmp,
                src_nodata=src.nodata if nodata is None else nodata,
                dst_transform=fine.transform,
                dst_crs="EPSG:4326",
                dst_nodata=np.nan,
                resampling=resampling,
            )
        fill = np.isnan(out) & ~np.isnan(tmp)
        out[fill] = tmp[fill]
    return out


def block(a: np.ndarray, fine: Fine, how: str = "mean") -> np.ndarray:
    g = fine.grid
    b = a.reshape(g.ny, fine.fy, g.nx, fine.fx)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN blocks -> NaN
        if how == "sum":
            return np.nansum(b, axis=(1, 3))
        return np.nanmean(b, axis=(1, 3))


def _ratio(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return (a - b) / (a + b)


def landsat_composite(scenes: list[dict], bands: dict[str, str], raw_dir: Path, fine: Fine) -> dict:
    """Median MNDWI, NDVI and NDBI over the cloud-free observations of `scenes`."""
    stacks: dict[str, list[np.ndarray]] = {"mndwi": [], "ndvi": [], "ndbi": []}
    for s in scenes:
        files = [raw_dir / f for f in s.get("files", [])]
        by_role = {}
        for role, suffix in bands.items():
            hit = [f for f in files if f.stem.upper().endswith(suffix.upper())]
            if hit:
                by_role[role] = hit[0]
        if set(by_role) != set(bands):
            continue
        qa = warp([by_role["qa"]], fine, Resampling.nearest, nodata=1)
        ok = ~np.isnan(qa) & ((np.nan_to_num(qa, nan=1).astype("uint16") & LANDSAT_QA_REJECT) == 0)
        sr = {}
        for role in ("green", "red", "nir", "swir1"):
            dn = warp([by_role[role]], fine, Resampling.bilinear, nodata=0)
            r = dn * SR_SCALE + SR_OFFSET
            r[~ok] = np.nan
            sr[role] = r
        stacks["mndwi"].append(_ratio(sr["green"], sr["swir1"]))
        stacks["ndvi"].append(_ratio(sr["nir"], sr["red"]))
        stacks["ndbi"].append(_ratio(sr["swir1"], sr["nir"]))
    if not stacks["mndwi"]:
        return {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        out = {k: np.nanmedian(np.stack(v), axis=0) for k, v in stacks.items()}
        out["n_obs"] = np.sum(~np.isnan(np.stack(stacks["mndwi"])), axis=0)
    return out


def sea_connected(water: np.ndarray) -> np.ndarray:
    """Water bodies that touch the southern (Atlantic) edge of the study area."""
    labels, n = ndimage.label(water, structure=np.ones((3, 3)))
    if n == 0:
        return np.zeros_like(water, dtype=bool)
    keep = np.unique(labels[-1][labels[-1] > 0])
    if keep.size == 0:  # no water on the south edge: fall back to the largest water body
        keep = [int(np.argmax(np.bincount(labels.ravel())[1:])) + 1]
    return np.isin(labels, keep)


def _years(scenes: list[dict]) -> float | None:
    ys = [int(s["date"][:4]) + (int(s["date"][5:7]) - 0.5) / 12 for s in scenes if s.get("date")]
    return float(np.mean(ys)) if ys else None


def process(raw_dir: Path, out_dir: Path, grid: Grid, log=print) -> dict:
    """Build every layer the inputs allow and write them with a provenance manifest."""
    _require_rasterio()
    fetch = json.loads((raw_dir / "usgs" / "fetch_manifest.json").read_text(encoding="utf-8"))
    usgs = raw_dir / "usgs"
    fine = fine_for(grid)
    dy, dx = fine.pixel_m
    layers: dict[str, np.ndarray] = {}
    meta: dict[str, dict] = {}

    dem_entry = fetch.get("dem") or {}
    dem_files = [usgs / f for s in dem_entry.get("scenes", []) for f in s.get("files", [])]
    if not dem_files:
        raise RuntimeError("no DEM files in fetch_manifest.json; run the fetch step first")
    dem = warp(dem_files, fine, Resampling.bilinear)
    log(f"DEM: {len(dem_files)} file(s), fine grid {fine.shape[1]}x{fine.shape[0]}")

    recent = landsat_composite(
        fetch.get("landsat_recent", {}).get("scenes", []),
        fetch.get("landsat_recent", {}).get("bands", {}), usgs, fine,
    )
    if recent:
        water = np.where(np.isnan(recent["mndwi"]), np.nan_to_num(dem, nan=0) <= 0.5,
                         recent["mndwi"] > 0)
        log(f"Landsat recent: median of up to {int(recent['n_obs'].max())} clear observation(s)")
    else:
        water = np.nan_to_num(dem, nan=0) <= 0.5
        log("Landsat recent: none usable; water from DEM <= 0.5 m (coarse)")
    water = water.astype(bool)
    sea_fine = sea_connected(water)
    sea = block(sea_fine.astype("float32"), fine) > 0.5

    land_dem = np.where(sea_fine, np.nan, dem)
    elev = block(land_dem, fine)
    elev = np.where(np.isnan(elev), block(dem, fine), elev)
    elev = np.where(sea, -1.0, np.nan_to_num(elev, nan=0.0))
    gy, gx = np.gradient(np.nan_to_num(dem, nan=0.0), dy, dx)
    slope_fine = np.degrees(np.arctan(np.hypot(gx, gy)))
    slope = np.nan_to_num(block(np.where(sea_fine, np.nan, slope_fine), fine), nan=0.0)
    layers |= {"elevation": elev, "slope": slope, "sea_mask": sea.astype("float32")}
    dem_meta = {
        "dataset": dem_entry.get("dataset"),
        "scenes": [s.get("displayId") for s in dem_entry.get("scenes", [])],
    }
    meta["elevation"] = {**dem_meta, "status": "observed", "units": "m above EGM96 (~MSL)",
                         "source": "USGS SRTM 1 Arc-Second Global",
                         "method": "mean of land pixels per cell; sea = -1",
                         "note": "SRTM is a surface model (~2000); buildings and trees bias it up."}
    meta["slope"] = {**dem_meta, "status": "derived", "units": "degrees",
                     "source": "USGS SRTM 1 Arc-Second Global", "method": "30 m slope, cell mean"}

    rec_entry = fetch.get("landsat_recent") or {}
    rec_meta = {"dataset": rec_entry.get("dataset"),
                "scenes": [f"{s.get('displayId')} ({s.get('date')})" for s in rec_entry.get("scenes", [])]}
    meta["sea_mask"] = {**rec_meta, "status": "observed" if recent else "derived",
                        "source": "USGS Landsat 8-9 C2 L2" if recent else "USGS SRTM",
                        "method": "MNDWI > 0, connected to the southern sea edge, > 50% of cell"}

    dist_sea = ndimage.distance_transform_edt(~sea_fine, sampling=(dy, dx))
    if recent:
        ndvi = recent["ndvi"]
        built = (recent["ndbi"] > 0) & (ndvi < 0.25) & ~water
        layers["built_up"] = np.where(sea, 0.0, block(built.astype("float32"), fine))
        meta["built_up"] = {**rec_meta, "status": "derived", "units": "fraction of cell",
                            "source": "USGS Landsat 8-9 C2 L2",
                            "method": "NDBI > 0 and NDVI < 0.25, not water (spectral proxy)"}
    else:
        ndvi = np.full(fine.shape, np.nan, dtype="float32")

    cls = np.ones(fine.shape, dtype="float32")
    e = np.nan_to_num(dem, nan=99.0)
    cls[e < 10] = 2
    cls[e < 5] = 3
    cls[(np.nan_to_num(ndvi) > 0.4) & (e < 3)] = 4
    cls[(dist_sea < BEACH_ZONE_M) & (e < 3)] = 5
    geo = block(np.where(sea_fine, np.nan, cls), fine)
    layers["geomorphology"] = np.nan_to_num(geo, nan=5.0)
    meta["geomorphology"] = {**dem_meta, "status": "derived", "units": "class 1-5 (5 = most exposed)",
                             "source": "SRTM + Landsat",
                             "method": "5 = within 500 m of sea and < 3 m; 4 = vegetated wetland "
                                       "< 3 m; 3 = < 5 m; 2 = < 10 m; 1 = higher ground"}

    early_entry = fetch.get("landsat_early") or {}
    early = landsat_composite(early_entry.get("scenes", []), early_entry.get("bands", {}), usgs, fine)
    y1, y0 = _years(rec_entry.get("scenes", [])), _years(early_entry.get("scenes", []))
    if recent and early and y1 and y0 and y1 > y0:
        early_water = np.where(np.isnan(early["mndwi"]), water, early["mndwi"] > 0).astype(bool)
        early_sea = sea_connected(early_water)
        coastal = (dist_sea < COASTAL_ZONE_M) | (
            ndimage.distance_transform_edt(~early_sea, sampling=(dy, dx)) < COASTAL_ZONE_M)
        lost = np.where(coastal, sea_fine.astype("float32") - early_sea.astype("float32"), 0.0)
        cell_m = float(np.sqrt(grid.cell_area_km2) * 1000)
        rate = block(lost, fine) * cell_m / (y1 - y0)
        layers["shoreline_change"] = np.nan_to_num(rate, nan=0.0)
        meta["shoreline_change"] = {
            "status": "derived", "units": "m/yr of land lost to the sea (negative = accretion)",
            "source": "USGS Landsat 4-5 TM and 8-9 OLI C2 L2",
            "dataset": f"{early_entry.get('dataset')} -> {rec_entry.get('dataset')}",
            "scenes": [f"{s.get('displayId')} ({s.get('date')})" for s in early_entry.get("scenes", [])]
            + rec_meta["scenes"],
            "method": f"change in sea-connected water {y0:.0f}-{y1:.0f}, within 3 km of the shore",
        }

    ext = raw_dir / "external"
    for name, how, units, src in (
        ("population", Resampling.sum, "people per cell", "external population raster"),
        ("subsidence", Resampling.average, "mm/yr (positive = sinking)", "external InSAR raster"),
    ):
        p = ext / f"{name}.tif"
        if p.exists():
            layers[name] = np.nan_to_num(_to_grid(p, grid, how), nan=0.0)
            meta[name] = {"status": "observed", "units": units, "source": src, "file": p.name,
                          "method": f"resampled to the analysis grid ({how.name})"}

    out_dir.mkdir(parents=True, exist_ok=True)
    tf = grid_transform(grid)
    for name, arr in layers.items():
        with rasterio.open(out_dir / f"{name}.tif", "w", driver="GTiff", height=grid.ny,
                           width=grid.nx, count=1, dtype="float32", crs="EPSG:4326",
                           transform=tf, compress="deflate") as dst:
            dst.write(arr.astype("float32"), 1)
        meta[name]["file"] = f"{name}.tif"
    manifest = {
        "grid": {"lon0": grid.lon0, "lat0": grid.lat0, "lon1": grid.lon1, "lat1": grid.lat1,
                 "nx": grid.nx, "ny": grid.ny},
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "fetched_at": (fetch.get("_meta") or {}).get("fetched_at"),
        "layers": meta,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"Wrote {len(layers)} layer(s) to {out_dir}")
    return manifest


def _to_grid(path: Path, grid: Grid, resampling) -> np.ndarray:
    out = np.full((grid.ny, grid.nx), np.nan, dtype="float32")
    with rasterio.open(path) as src:
        reproject(
            source=rasterio.band(src, 1), destination=out, src_nodata=src.nodata,
            dst_transform=grid_transform(grid),
            dst_crs="EPSG:4326", dst_nodata=np.nan, resampling=resampling,
        )
    return out
