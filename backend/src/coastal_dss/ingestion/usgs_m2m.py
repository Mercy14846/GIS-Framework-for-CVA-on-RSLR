"""Thin client for the USGS EROS Machine-to-Machine (M2M) API.

    login-token -> dataset-search -> scene-search -> download-options
                -> download-request -> download-retrieve (poll) -> HTTP GET -> logout

Requests follow the USGS M2M sample notebooks (code.usgs.gov/eros-user-services/
machine_to_machine): JSON POST bodies, the session key in the `X-Auth-Token` header, and
Landsat band files requested individually through `secondaryDownloads`.

Credentials come from DSS_USGS_USERNAME and DSS_USGS_TOKEN (an M2M application token from
https://ers.cr.usgs.gov/password/appgenerate, not the account password). They are never logged.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import httpx

API_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"


class M2MError(RuntimeError):
    """The API answered with an errorCode."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class M2MAuthError(M2MError):
    pass


@dataclass(frozen=True)
class BBox:
    lon0: float
    lat0: float
    lon1: float
    lat1: float

    def spatial_filter(self) -> dict:
        return {
            "filterType": "mbr",
            "lowerLeft": {"latitude": self.lat0, "longitude": self.lon0},
            "upperRight": {"latitude": self.lat1, "longitude": self.lon1},
        }


@dataclass(frozen=True)
class FileRequest:
    """One downloadable file: a whole product or a single band (secondary download)."""

    entity_id: str
    product_id: str
    name: str


class M2MClient:
    def __init__(
        self,
        username: str,
        token: str,
        *,
        base_url: str = API_URL,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 60.0,
    ) -> None:
        if not username or not token:
            raise M2MAuthError(
                "AUTH_MISSING",
                "set DSS_USGS_USERNAME and DSS_USGS_TOKEN (an M2M application token)",
            )
        self._username = username
        self._token = token
        self._sleep = sleep
        self._http = httpx.Client(
            base_url=base_url, transport=transport, timeout=timeout, follow_redirects=True
        )
        self._key: str | None = None

    # -- session --------------------------------------------------------------------------
    def __enter__(self) -> Self:
        self.login()
        return self

    def __exit__(self, *exc: object) -> None:
        try:
            if self._key:
                self.request("logout")
        finally:
            self._key = None
            self._http.close()

    def login(self) -> None:
        self._key = None
        self._key = self.request("login-token", {"username": self._username, "token": self._token})

    def request(self, endpoint: str, payload: dict | None = None, retries: int = 3) -> object:
        headers = {"X-Auth-Token": self._key} if self._key else {}
        for attempt in range(retries + 1):
            r = self._http.post(endpoint, json=payload or {}, headers=headers)
            try:
                body = r.json()
            except ValueError as exc:
                raise M2MError(
                    "NON_JSON", f"HTTP {r.status_code} from {endpoint}; M2M may be down"
                ) from exc
            code = body.get("errorCode")
            if not code:
                r.raise_for_status()
                return body.get("data")
            if code == "RATE_LIMIT" and attempt < retries:
                self._sleep(2.0 * (attempt + 1))
                continue
            msg = body.get("errorMessage") or ""
            if code.startswith("AUTH"):
                raise M2MAuthError(code, msg)
            raise M2MError(code, msg)
        raise AssertionError("unreachable")

    # -- discovery ------------------------------------------------------------------------
    def dataset_search(self, name: str, bbox: BBox | None = None) -> list[dict]:
        """Datasets whose name contains `name` (the API wraps it in wildcards)."""
        payload: dict = {"datasetName": name}
        if bbox:
            payload["spatialFilter"] = bbox.spatial_filter()
        return list(self.request("dataset-search", payload) or [])

    def resolve_dataset(self, keyword: str, collection_pattern: str) -> str:
        """Alias of the dataset whose collectionName matches `collection_pattern` (regex)."""
        pat = re.compile(collection_pattern, re.IGNORECASE)
        for d in self.dataset_search(keyword):
            if pat.search(d.get("collectionName") or "") or pat.search(d.get("datasetAlias") or ""):
                return d["datasetAlias"]
        raise M2MError("DATASET_NOT_FOUND", f"no dataset like {keyword!r} / {collection_pattern!r}")

    def scene_search(
        self,
        dataset: str,
        bbox: BBox,
        *,
        start: str | None = None,
        end: str | None = None,
        max_cloud: int | None = None,
        months: Iterable[int] | None = None,
        max_results: int = 100,
    ) -> list[dict]:
        scene_filter: dict = {"spatialFilter": bbox.spatial_filter()}
        if start and end:
            scene_filter["acquisitionFilter"] = {"start": start, "end": end}
        if max_cloud is not None:
            scene_filter["cloudCoverFilter"] = {"min": 0, "max": max_cloud, "includeUnknown": False}
        if months:
            scene_filter["seasonalFilter"] = sorted(set(months))
        data = self.request(
            "scene-search",
            {
                "datasetName": dataset,
                "sceneFilter": scene_filter,
                "maxResults": max_results,
                "metadataType": "summary",
            },
        )
        return list((data or {}).get("results") or [])

    # -- download -------------------------------------------------------------------------
    def download_options(self, dataset: str, entity_ids: list[str]) -> list[dict]:
        return list(
            self.request(
                "download-options",
                {"datasetName": dataset, "entityIds": entity_ids},
            )
            or []
        )

    def request_files(
        self, files: list[FileRequest], label: str, *, poll_s: float = 30.0, max_polls: int = 40
    ) -> dict[str, str]:
        """download-request, then poll download-retrieve until every file has a URL.

        Returns {downloadId: url}. Files the API is still preparing are polled for up to
        `max_polls * poll_s` seconds.
        """
        result = self.request(
            "download-request",
            {"downloads": [{"entityId": f.entity_id, "productId": f.product_id} for f in files],
             "label": label},
        ) or {}
        urls = {str(d["downloadId"]): d["url"] for d in result.get("availableDownloads") or []}
        pending = {str(d["downloadId"]) for d in result.get("preparingDownloads") or []}
        polls = 0
        while pending:
            if polls >= max_polls:
                raise M2MError("DOWNLOAD_TIMEOUT", f"{len(pending)} file(s) still being prepared")
            self._sleep(poll_s)
            polls += 1
            got = self.request("download-retrieve", {"label": label}) or {}
            for d in (got.get("available") or []) + (got.get("requested") or []):
                did = str(d["downloadId"])
                if did in pending and d.get("url"):
                    urls[did] = d["url"]
                    pending.discard(did)
        return urls

    def fetch(self, url: str, dest_dir: Path) -> Path:
        """Stream one file to dest_dir, named from Content-Disposition. Skips existing files."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        with self._http.stream("GET", url, headers={}, timeout=None) as r:
            r.raise_for_status()
            name = _filename(r.headers.get("content-disposition"), url)
            out = dest_dir / name
            if out.exists() and out.stat().st_size == int(r.headers.get("content-length") or -1):
                return out
            tmp = out.with_suffix(out.suffix + ".part")
            with tmp.open("wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
            tmp.replace(out)
        return out

    def cleanup(self, label: str) -> None:
        """Remove the download order so it does not linger in the user's M2M queue."""
        try:
            self.request("download-order-remove", {"label": label})
        except M2MError:
            pass


def _filename(content_disposition: str | None, url: str) -> str:
    if content_disposition:
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
        if m:
            return Path(m.group(1)).name
    return Path(httpx.URL(url).path).name or "download.bin"


def band_files(options: list[dict], band_suffixes: Iterable[str]) -> list[FileRequest]:
    """Pick single-band files (e.g. SR_B3, QA_PIXEL) from download-options secondaryDownloads."""
    wanted = tuple(band_suffixes)
    out: list[FileRequest] = []
    seen: set[str] = set()
    for product in options:
        for sec in product.get("secondaryDownloads") or []:
            name = sec.get("displayId") or ""
            stem = Path(name).stem.upper()
            if not sec.get("available") or name in seen:
                continue
            if any(stem.endswith(b.upper()) for b in wanted):
                out.append(FileRequest(sec["entityId"], sec["id"], name))
                seen.add(name)
    return out


def product_file(options: list[dict], prefer: Iterable[str] = ("GeoTIFF",)) -> list[FileRequest]:
    """One whole-product file per entity, preferring products whose name matches `prefer`."""
    by_entity: dict[str, list[dict]] = {}
    for o in options:
        if o.get("available"):
            by_entity.setdefault(o["entityId"], []).append(o)
    out = []
    for eid, opts in by_entity.items():
        ranked = sorted(
            opts,
            key=lambda o: next(
                (i for i, p in enumerate(prefer) if p.lower() in (o.get("productName") or "").lower()),
                len(tuple(prefer)),
            ),
        )
        best = ranked[0]
        out.append(FileRequest(eid, best["id"], best.get("productName") or eid))
    return out
