from fastapi import APIRouter, HTTPException, Query

from coastal_dss.api.geojson import bbox, cells_geojson
from coastal_dss.providers import get_provider
from coastal_dss.scenarios.registry import Scenario
from coastal_dss.services.assessment import assess

router = APIRouter()

WATER_LEVEL = Query(0.0, description="Water level above Lagos high tide (MHHW), metres")


def _scenario(pathway: str, year: int, subsidence: bool, water_level: float = 0.0) -> Scenario:
    try:
        return Scenario(pathway, year, subsidence, water_level).validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _echo(pathway: str, year: int, subsidence: bool, water_level: float) -> dict:
    return {"pathway": pathway, "year": year, "subsidence": subsidence, "water_level": water_level}


@router.get("/assessment")
def get_assessment(
    pathway: str = Query("ssp585"),
    year: int = Query(2050),
    subsidence: bool = Query(True),
    water_level: float = WATER_LEVEL,
) -> dict:
    """Cells (state, depth, CVI class) plus the exposure summary for one scenario."""
    a = assess(_scenario(pathway, year, subsidence, water_level))
    p = get_provider()
    return {
        "scenario": _echo(pathway, year, subsidence, water_level),
        "data_mode": p.mode,
        "sources": p.sources(),
        "bbox": bbox(p),
        "summary": a.summary,
        "cells": cells_geojson(p, a),
    }


@router.get("/impact")
def get_impact(
    pathway: str = Query("ssp585"),
    year: int = Query(2050),
    subsidence: bool = Query(True),
    water_level: float = WATER_LEVEL,
) -> dict:
    return {
        "scenario": _echo(pathway, year, subsidence, water_level),
        "summary": assess(_scenario(pathway, year, subsidence, water_level)).summary,
    }


@router.get("/compare")
def compare(
    year: int = Query(2050),
    subsidence: bool = Query(True),
    water_level: float = WATER_LEVEL,
) -> dict:
    """Both pathways, with and without subsidence, for the Scenarios tab."""
    rows = []
    for pw in ("ssp245", "ssp585"):
        for sub in (True, False):
            s = assess(_scenario(pw, year, sub, water_level)).summary
            rows.append({"pathway": pw, "subsidence": sub, **s})
    return {"year": year, "water_level": water_level, "rows": rows}
