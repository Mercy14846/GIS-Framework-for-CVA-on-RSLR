from fastapi import APIRouter, HTTPException, Query

from coastal_dss.api.geojson import bbox, cells_geojson
from coastal_dss.providers import get_provider
from coastal_dss.scenarios.registry import Scenario
from coastal_dss.services.assessment import assess

router = APIRouter()


def _scenario(pathway: str, year: int, subsidence: bool) -> Scenario:
    try:
        return Scenario(pathway, year, subsidence).validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/assessment")
def get_assessment(
    pathway: str = Query("ssp585"),
    year: int = Query(2050),
    subsidence: bool = Query(True),
) -> dict:
    """Cells (state, depth, CVI class) plus the exposure summary for one scenario."""
    a = assess(_scenario(pathway, year, subsidence))
    p = get_provider()
    return {
        "scenario": {"pathway": pathway, "year": year, "subsidence": subsidence},
        "data_mode": p.mode,
        "bbox": bbox(p),
        "summary": a.summary,
        "cells": cells_geojson(p, a),
    }


@router.get("/impact")
def get_impact(
    pathway: str = Query("ssp585"),
    year: int = Query(2050),
    subsidence: bool = Query(True),
) -> dict:
    return {
        "scenario": {"pathway": pathway, "year": year, "subsidence": subsidence},
        "summary": assess(_scenario(pathway, year, subsidence)).summary,
    }


@router.get("/compare")
def compare(year: int = Query(2050), subsidence: bool = Query(True)) -> dict:
    """Both pathways, with and without subsidence, for the Scenarios tab."""
    rows = []
    for pw in ("ssp245", "ssp585"):
        for sub in (True, False):
            s = assess(_scenario(pw, year, sub)).summary
            rows.append({"pathway": pw, "subsidence": sub, **s})
    return {"year": year, "rows": rows}
