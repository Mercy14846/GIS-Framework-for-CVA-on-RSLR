"""Ingest USGS remote-sensing data for the Lagos study area.

    python -m coastal_dss.ingestion plan       # search only: datasets and scenes that would be used
    python -m coastal_dss.ingestion fetch      # download into data/raw/usgs
    python -m coastal_dss.ingestion process    # build data/processed/*.tif + manifest.json
    python -m coastal_dss.ingestion all        # fetch + process

Then start the API with DSS_DATA_MODE=raster. Credentials: DSS_USGS_USERNAME and
DSS_USGS_TOKEN (environment or backend/.env).
"""

from __future__ import annotations

import argparse
import json
import sys

from coastal_dss.core.config import get_settings
from coastal_dss.core.constants import STUDY_AREA
from coastal_dss.ingestion.usgs_m2m import BBox, M2MClient, M2MError
from coastal_dss.providers.base import Grid


def _client() -> M2MClient:
    s = get_settings()
    return M2MClient(s.usgs_username, s.usgs_token.get_secret_value())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m coastal_dss.ingestion", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "fetch", "process", "all"])
    args = ap.parse_args(argv)

    s = get_settings()
    bbox = BBox(*STUDY_AREA)
    grid = Grid(*STUDY_AREA, nx=s.grid_nx, ny=s.grid_ny)
    raw = s.data_dir / "raw"
    try:
        if args.command == "plan":
            from coastal_dss.ingestion.usgs_fetch import plan

            with _client() as c:
                print(json.dumps(plan(c, bbox), indent=2))
        if args.command in ("fetch", "all"):
            from coastal_dss.ingestion.usgs_fetch import fetch

            with _client() as c:
                fetch(c, bbox, raw / "usgs")
        if args.command in ("process", "all"):
            from coastal_dss.ingestion.process import process

            process(raw, s.data_dir / "processed", grid)
            print("Done. Start the API with DSS_DATA_MODE=raster to use these layers.")
    except M2MError as exc:
        print(f"USGS M2M error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
