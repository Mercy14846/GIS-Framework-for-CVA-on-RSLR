"""Fetch the USGS remote-sensing inputs for the Lagos study area through M2M.

Products (all over the analysis bounding box):

- `dem`            SRTM 1 Arc-Second Global (~30 m), the elevation and slope source.
- `landsat_recent` Landsat 8-9 OLI/TIRS Collection 2 Level-2 surface reflectance, the least
                   cloudy dry-season scenes of the last few years: water, built-up, vegetation.
- `landsat_early`  Landsat 4-5 TM Collection 2 Level-2 from 1984-1992: the historical water line
                   for shoreline change.

Only the bands the processing needs are downloaded (single-band GeoTIFFs, not the ~1 GB
bundles). Files land in data/raw/usgs/<product>/<scene>/ and every scene is recorded in
data/raw/usgs/fetch_manifest.json, which `process` reads.
"""

from __future__ import annotations

import datetime as dt
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from coastal_dss.ingestion.usgs_m2m import BBox, M2MClient, band_files, product_file

# Lagos dry season (harmattan) has the fewest clouds.
DRY_SEASON = (11, 12, 1, 2, 3)


@dataclass(frozen=True)
class LandsatSpec:
    dataset: str
    start: str
    end: str
    bands: dict[str, str]  # role -> band suffix
    max_cloud: int = 30
    n_scenes: int = 4
    months: tuple[int, ...] = DRY_SEASON
    kind: str = "landsat"


@dataclass(frozen=True)
class DemSpec:
    keyword: str = "srtm"
    collection: str = r"1 arc-?second global"
    prefer: tuple[str, ...] = ("GeoTIFF", "BIL", "DTED")
    kind: str = "dem"
    bands: dict[str, str] = field(default_factory=dict)


def default_products(today: dt.date | None = None) -> dict[str, LandsatSpec | DemSpec]:
    today = today or dt.date.today()
    return {
        "dem": DemSpec(),
        "landsat_recent": LandsatSpec(
            dataset="landsat_ot_c2_l2",
            start=f"{today.year - 3}-01-01",
            end=today.isoformat(),
            bands={"green": "SR_B3", "red": "SR_B4", "nir": "SR_B5", "swir1": "SR_B6",
                   "qa": "QA_PIXEL"},
        ),
        "landsat_early": LandsatSpec(
            dataset="landsat_tm_c2_l2",
            start="1984-01-01",
            end="1992-12-31",
            bands={"green": "SR_B2", "red": "SR_B3", "nir": "SR_B4", "swir1": "SR_B5",
                   "qa": "QA_PIXEL"},
            n_scenes=3,
        ),
    }


def _cloud(scene: dict) -> float:
    try:
        return float(scene.get("cloudCover"))
    except (TypeError, ValueError):
        return 101.0


def _date(scene: dict) -> str:
    tc = scene.get("temporalCoverage") or {}
    return str(tc.get("startDate") or scene.get("acquisitionDate") or "")[:10]


def select_scenes(scenes: list[dict], n: int) -> list[dict]:
    """Least cloudy first; ties broken by most recent."""
    usable = [s for s in scenes if _cloud(s) <= 100]
    return sorted(usable, key=lambda s: (_cloud(s), -int(_date(s).replace("-", "") or 0)))[:n]


def plan(client: M2MClient, bbox: BBox, products: dict | None = None) -> dict:
    """Search only: which dataset and scenes each product would use. No downloads."""
    products = products or default_products()
    out: dict = {}
    for name, spec in products.items():
        if isinstance(spec, DemSpec):
            dataset = client.resolve_dataset(spec.keyword, spec.collection)
            scenes = client.scene_search(dataset, bbox, max_results=20)
        else:
            dataset = spec.dataset
            found = client.scene_search(
                dataset, bbox, start=spec.start, end=spec.end, max_cloud=spec.max_cloud,
                months=spec.months, max_results=200,
            )
            scenes = select_scenes(found, spec.n_scenes)
        out[name] = {
            "kind": spec.kind,
            "dataset": dataset,
            "bands": spec.bands,
            "scenes": [
                {"entityId": s["entityId"], "displayId": s.get("displayId") or s["entityId"],
                 "date": _date(s), "cloudCover": _cloud(s) if _cloud(s) <= 100 else None}
                for s in scenes
            ],
        }
    return out


def fetch(
    client: M2MClient, bbox: BBox, raw_dir: Path, products: dict | None = None, log=print
) -> dict:
    """Search, download and record every product. Returns the fetch manifest."""
    products = products or default_products()
    manifest = plan(client, bbox, products)
    label = "lagos-dss-" + dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M%S")
    try:
        for name, entry in manifest.items():
            spec = products[name]
            ids = [s["entityId"] for s in entry["scenes"]]
            if not ids:
                log(f"[{name}] no scenes found in {entry['dataset']}")
                continue
            log(f"[{name}] {entry['dataset']}: {len(ids)} scene(s)")
            options = client.download_options(entry["dataset"], ids)
            files = (
                product_file(options, spec.prefer)
                if isinstance(spec, DemSpec)
                else band_files(options, spec.bands.values())
            )
            urls = client.request_files(files, f"{label}-{name}")
            by_scene = {s["entityId"]: s for s in entry["scenes"]}
            for s in entry["scenes"]:
                s["files"] = []
            for url in urls.values():
                path = client.fetch(url, raw_dir / name / "_incoming")
                scene = _match_scene(path.name, by_scene) or entry["scenes"][0]
                dest = raw_dir / name / scene["displayId"]
                dest.mkdir(parents=True, exist_ok=True)
                final = dest / path.name
                path.replace(final)
                for f in _unpack(final):
                    scene["files"].append(str(f.relative_to(raw_dir)).replace("\\", "/"))
                log(f"  {final.name}")
    finally:
        client.cleanup(label)
    manifest["_meta"] = {
        "bbox": [bbox.lon0, bbox.lat0, bbox.lon1, bbox.lat1],
        "fetched_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "source": "USGS EROS M2M API",
    }
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "fetch_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _match_scene(filename: str, scenes: dict[str, dict]) -> dict | None:
    up = filename.upper()
    for s in scenes.values():
        if s["displayId"].upper() in up or s["entityId"].upper() in up:
            return s
    return None


def _unpack(path: Path) -> list[Path]:
    """Extract zip archives (SRTM is often zipped); return the raster files."""
    if path.suffix.lower() != ".zip":
        return [path]
    with zipfile.ZipFile(path) as z:
        z.extractall(path.parent)
        names = [path.parent / n for n in z.namelist() if not n.endswith("/")]
    path.unlink()
    rasters = [p for p in names if p.suffix.lower() in {".tif", ".tiff", ".bil", ".hgt", ".dt2"}]
    return rasters or names
