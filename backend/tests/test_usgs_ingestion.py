"""USGS M2M ingestion: client protocol, fetch, processing and the raster provider.

A mock M2M server (httpx.MockTransport) serves synthetic GeoTIFFs: an SRTM-like DEM in
EPSG:4326 and Landsat-like bands in UTM 31N, with the coast at 6.45 N today, at 6.44 N in
the 1980s, a lagoon joined to the sea by a channel and a built-up district.
"""

from __future__ import annotations

import io
import json

import numpy as np
import pytest

httpx = pytest.importorskip("httpx")

from coastal_dss.ingestion.usgs_m2m import (
    BBox,
    M2MAuthError,
    M2MClient,
    band_files,
)

BBOX = BBox(3.20, 6.35, 3.75, 6.65)


def _json(data=None, code=None, msg=None):
    return httpx.Response(200, json={"data": data, "errorCode": code, "errorMessage": msg})


def test_client_requires_credentials():
    with pytest.raises(M2MAuthError):
        M2MClient("", "")


def test_client_auth_retry_and_preparing_downloads(tmp_path):
    calls = []
    state = {"rate_limited": False}

    def handler(req: httpx.Request) -> httpx.Response:
        ep = req.url.path.rsplit("/", 1)[-1]
        calls.append((ep, req.headers.get("x-auth-token")))
        if req.url.host == "dds.test":
            return httpx.Response(200, content=b"tif",
                                  headers={"content-disposition": 'attachment; filename="A_SR_B3.TIF"'})
        body = json.loads(req.content or b"{}")
        if ep == "login-token":
            assert body == {"username": "u", "token": "t"}
            return _json("KEY")
        if ep == "scene-search" and not state["rate_limited"]:
            state["rate_limited"] = True
            return _json(code="RATE_LIMIT", msg="slow down")
        if ep == "scene-search":
            f = body["sceneFilter"]
            assert f["spatialFilter"]["lowerLeft"] == {"latitude": 6.35, "longitude": 3.2}
            assert f["cloudCoverFilter"]["max"] == 20 and f["seasonalFilter"] == [1, 2]
            return _json({"results": [{"entityId": "E1"}]})
        if ep == "download-request":
            return _json({"availableDownloads": [{"downloadId": 1, "url": "https://dds.test/1"}],
                          "preparingDownloads": [{"downloadId": 2}]})
        if ep == "download-retrieve":
            return _json({"available": [{"downloadId": 2, "url": "https://dds.test/2"}],
                          "requested": []})
        return _json(None)

    sleeps = []
    with M2MClient("u", "t", transport=httpx.MockTransport(handler), sleep=sleeps.append) as c:
        found = c.scene_search("landsat_ot_c2_l2", BBOX, max_cloud=20, months=[2, 1])
        assert found == [{"entityId": "E1"}]
        urls = c.request_files([], "lbl", poll_s=0)
        out = c.fetch(urls["1"], tmp_path)
    assert out.name == "A_SR_B3.TIF" and out.read_bytes() == b"tif"
    assert urls == {"1": "https://dds.test/1", "2": "https://dds.test/2"}
    assert calls[0] == ("login-token", None)
    assert all(tok == "KEY" for ep, tok in calls[1:] if ep not in ("1", "2"))
    assert calls[-1][0] == "logout" and sleeps  # rate limit and polling both waited


def test_band_files_picks_requested_bands_only():
    options = [{"entityId": "S", "id": "bundle", "available": True, "secondaryDownloads": [
        {"entityId": f"L2SR_X_{b}_TIF", "id": f"p{b}", "displayId": f"X_{b}.TIF", "available": ok}
        for b, ok in (("SR_B3", True), ("SR_B6", True), ("SR_B7", True), ("QA_PIXEL", True),
                      ("SR_B5", False))
    ]}]
    names = [f.name for f in band_files(options, ["SR_B3", "SR_B6", "SR_B5", "QA_PIXEL"])]
    assert names == ["X_SR_B3.TIF", "X_SR_B6.TIF", "X_QA_PIXEL.TIF"]


# --- end to end ---------------------------------------------------------------------------

pytest.importorskip("rasterio")
from coastal_dss.core.geo import rasterio

from_bounds, from_origin = rasterio.transform.from_bounds, rasterio.transform.from_origin
warp_xy = rasterio.warp.transform


def _is_water(lon, lat, coast):
    lagoon = (lat > 6.50) & (lat < 6.55) & (lon > 3.30) & (lon < 3.60)
    channel = (lon > 3.40) & (lon < 3.43) & (lat < 6.52)
    return (lat < coast) | lagoon | channel


def _tif(arr, crs, transform, dtype, nodata=None) -> bytes:
    buf = io.BytesIO()
    with rasterio.MemoryFile() as mem:
        with mem.open(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                      dtype=dtype, crs=crs, transform=transform, nodata=nodata) as dst:
            dst.write(arr.astype(dtype), 1)
        buf.write(mem.read())
    return buf.getvalue()


def _dem() -> bytes:
    n = 360
    lon, lat = np.meshgrid(3.0 + (np.arange(n) + 0.5) / n, 7.0 - (np.arange(n) + 0.5) / n)
    elev = np.clip((lat - 6.45) * 100, 0, None)
    elev[_is_water(lon, lat, 6.45)] = 0
    return _tif(elev, "EPSG:4326", from_bounds(3, 6, 4, 7, n, n), "int16", nodata=-32768)


def _landsat_bands(coast: float, cloud_box: bool) -> dict[str, bytes]:
    res, x0, y1, w, h = 90.0, 515_000.0, 740_000.0, 760, 460
    tf = from_origin(x0, y1, res, res)
    xs, ys = np.meshgrid(x0 + (np.arange(w) + 0.5) * res, y1 - (np.arange(h) + 0.5) * res)
    lon, lat = warp_xy("EPSG:32631", "EPSG:4326", xs.ravel(), ys.ravel())
    lon, lat = np.array(lon).reshape(h, w), np.array(lat).reshape(h, w)
    water = _is_water(lon, lat, coast)
    built = ~water & (lon > 3.33) & (lon < 3.45) & (lat > 6.56) & (lat < 6.62)
    refl = {
        "green": np.full((h, w), 0.08),
        "red": np.where(built, 0.15, 0.05),
        "nir": np.where(water, 0.02, np.where(built, 0.20, 0.35)),
        "swir1": np.where(water, 0.01, np.where(built, 0.30, 0.18)),
    }
    dn = {k: (v - (-0.2)) / 0.0000275 for k, v in refl.items()}
    qa = np.full((h, w), 21824)
    if cloud_box:  # a cloud over the built district; the other scene must fill it
        qa[(lon > 3.30) & (lon < 3.50) & (lat > 6.55)] = 22280  # bit 3 set
        for v in dn.values():
            v[(lon > 3.30) & (lon < 3.50) & (lat > 6.55)] = 40000
    out = {k: _tif(v, "EPSG:32631", tf, "uint16", nodata=0) for k, v in dn.items()}
    out["qa"] = _tif(qa, "EPSG:32631", tf, "uint16", nodata=1)
    return out


OT = {"green": "SR_B3", "red": "SR_B4", "nir": "SR_B5", "swir1": "SR_B6", "qa": "QA_PIXEL"}
TM = {"green": "SR_B2", "red": "SR_B3", "nir": "SR_B4", "swir1": "SR_B5", "qa": "QA_PIXEL"}
SCENES = {
    "landsat_ot_c2_l2": [("LC09_L2SP_191055_20240115_20240116_02_T1", "2024-01-15", 5.0, True),
                         ("LC08_L2SP_191055_20231229_20240108_02_T1", "2023-12-29", 9.0, False),
                         ("LC08_L2SP_191055_20221220_20221230_02_T1", "2022-12-20", 60.0, False)],
    "landsat_tm_c2_l2": [("LT05_L2SP_191055_19870110_20200917_02_T1", "1987-01-10", 3.0, False)],
}


def mock_usgs() -> httpx.MockTransport:
    files: dict[str, bytes] = {"n06_e003_1arc_v3.tif": _dem()}
    for ds, scenes in SCENES.items():
        bands = OT if ds.startswith("landsat_ot") else TM
        for did, _, _, cloud in scenes:
            data = _landsat_bands(6.45 if ds.startswith("landsat_ot") else 6.44, cloud)
            for role, suffix in bands.items():
                files[f"{did}_{suffix}.TIF"] = data[role]
    ids = {}

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.host == "dds.test":
            name = req.url.path.rsplit("/", 1)[-1]
            return httpx.Response(200, content=files[name],
                                  headers={"content-disposition": f'attachment; filename="{name}"'})
        ep = req.url.path.rsplit("/", 1)[-1]
        body = json.loads(req.content or b"{}")
        if ep == "login-token":
            return _json("KEY")
        if ep == "dataset-search":
            return _json([{"datasetAlias": "srtm_void", "collectionName": "SRTM Void Filled"},
                          {"datasetAlias": "srtm_1", "collectionName": "SRTM 1 Arc-Second Global"}])
        if ep == "scene-search":
            ds = body["datasetName"]
            if ds == "srtm_1":
                return _json({"results": [{"entityId": "SRTM1N06E003V3", "displayId": "N06E003"}]})
            cmax = body["sceneFilter"]["cloudCoverFilter"]["max"]
            return _json({"results": [
                {"entityId": f"E-{did}", "displayId": did, "cloudCover": str(cc),
                 "temporalCoverage": {"startDate": f"{d} 00:00:00"}}
                for did, d, cc, _ in SCENES[ds] if cc <= cmax]})
        if ep == "download-options":
            if body["datasetName"] == "srtm_1":
                return _json([{"id": "dted", "entityId": "SRTM1N06E003V3", "available": True,
                               "productName": "DTED 1 Arc-second", "secondaryDownloads": []},
                              {"id": "gtif", "entityId": "SRTM1N06E003V3", "available": True,
                               "productName": "GeoTIFF 1 Arc-second", "secondaryDownloads": []}])
            out = []
            for eid in body["entityIds"]:
                did = eid[2:]
                out.append({"id": "bundle", "entityId": eid, "available": True,
                            "productName": "Landsat Collection 2 Level-2 Product Bundle",
                            "secondaryDownloads": [
                                {"id": f"p_{n}", "entityId": f"L2_{n}", "displayId": n,
                                 "available": True}
                                for n in files if n.startswith(did)]})
            return _json(out)
        if ep == "download-request":
            avail, prep = [], []
            for i, d in enumerate(body["downloads"]):
                name = "n06_e003_1arc_v3.tif" if d["productId"] == "gtif" else d["productId"][2:]
                assert d["productId"] != "dted"
                ids[str(len(ids) + 1)] = name
                rec = {"downloadId": len(ids), "url": f"https://dds.test/{name}"}
                (prep if i % 2 else avail).append(rec)
            return _json({"availableDownloads": avail, "preparingDownloads":
                          [{"downloadId": r["downloadId"]} for r in prep],
                          "_prep": prep})
        if ep == "download-retrieve":
            return _json({"available": [{"downloadId": int(k), "url": f"https://dds.test/{v}"}
                                        for k, v in ids.items()], "requested": []})
        return _json(None)

    return httpx.MockTransport(handler)


@pytest.fixture
def ingested(tmp_path, monkeypatch):
    from coastal_dss.ingestion import usgs_fetch
    from coastal_dss.ingestion.process import process
    from coastal_dss.providers.base import Grid

    raw = tmp_path / "raw"
    with M2MClient("u", "t", transport=mock_usgs(), sleep=lambda s: None) as c:
        products = usgs_fetch.default_products()
        manifest = usgs_fetch.fetch(c, BBOX, raw / "usgs", products, log=lambda *a: None)
    grid = Grid(3.20, 6.35, 3.75, 6.65, nx=55, ny=30)
    processed = process(raw, tmp_path / "processed", grid, log=lambda *a: None)
    return tmp_path, manifest, processed


def test_fetch_selects_clear_scenes_and_bands(ingested):
    root, manifest, _ = ingested
    rec = manifest["landsat_recent"]
    assert [s["date"] for s in rec["scenes"]] == ["2024-01-15", "2023-12-29"]  # 60% cloud dropped
    assert all(len(s["files"]) == 5 for s in rec["scenes"])
    assert manifest["dem"]["dataset"] == "srtm_1"
    assert manifest["dem"]["scenes"][0]["files"] == ["dem/N06E003/n06_e003_1arc_v3.tif"]
    saved = json.loads((root / "raw" / "usgs" / "fetch_manifest.json").read_text())
    assert saved["_meta"]["source"] == "USGS EROS M2M API"


def test_processed_layers_match_the_landscape(ingested):
    from coastal_dss.providers.raster import RasterProvider

    root, _, processed = ingested
    assert {"elevation", "slope", "sea_mask", "built_up", "geomorphology",
            "shoreline_change"} <= set(processed["layers"])
    p = RasterProvider(root / "processed")
    sea, elev = p.sea_mask(), p.elevation_m()
    assert sea[-1].all() and not sea[0].any()  # Atlantic to the south, land to the north
    lagoon_row = int((6.65 - 6.525) / 0.01)
    assert sea[lagoon_row, int((3.50 - 3.20) / 0.01)]  # lagoon joined via the channel
    assert elev[0].mean() > elev[18][~sea[18]].mean() > 0 and (elev[sea] == -1).all()
    built = p.built_up_fraction()
    assert built[5, 18] > 0.8 and built[5, 45] < 0.1  # despite the cloud in one scene
    shore = p.indicator_layers()["shoreline_change"][0]
    coast_row = int((6.65 - 6.445) / 0.01)
    assert shore[coast_row].max() > 5  # ~1 km lost over ~37 years
    by_layer = {s["layer"]: s for s in p.sources()}
    assert by_layer["elevation"]["status"] == "observed"
    assert by_layer["population"]["status"] == "synthetic"
    assert by_layer["subsidence"]["status"] == "synthetic"
    assert (p.population()[sea] == 0).all()


def test_api_serves_raster_layers(ingested, monkeypatch):
    from fastapi.testclient import TestClient

    from coastal_dss.api.main import app
    from coastal_dss.core.config import get_settings
    from coastal_dss.providers import get_provider
    from coastal_dss.services import assessment

    root, _, _ = ingested
    monkeypatch.setenv("DSS_DATA_MODE", "raster")
    monkeypatch.setenv("DSS_DATA_DIR", str(root))
    caches = (get_settings, get_provider, assessment.assess, assessment.reference_breaks)
    for f in caches:
        f.cache_clear()
    try:
        client = TestClient(app)
        r = client.get("/api/v1/assessment", params={"year": 2100, "water_level": 1}).json()
        assert r["data_mode"] == "raster" and r["bbox"] == [3.2, 6.35, 3.75, 6.65]
        assert len(r["cells"]["features"]) > 0 and r["summary"]["flooded_area_km2"] > 0
        src = client.get("/api/v1/sources").json()
        assert {s["status"] for s in src["layers"]} >= {"observed", "derived", "synthetic"}
    finally:
        monkeypatch.undo()
        for f in caches:
            f.cache_clear()
