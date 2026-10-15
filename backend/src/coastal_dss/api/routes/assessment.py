from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from coastal_dss.api.geojson import bbox, cells_geojson
from coastal_dss.providers import get_provider
from coastal_dss.scenarios.registry import Scenario
from coastal_dss.services.assessment import assess

router = APIRouter()

Year = Annotated[int, Query()]
WaterLevel = Annotated[
    float, Query(description="Water level above Lagos high tide (MHHW), metres")
]


def _validated(sc: Scenario) -> Scenario:
    try:
        return sc.validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def scenario_params(
    pathway: Annotated[str, Query()] = "ssp585",
    year: Year = 2050,
    subsidence: Annotated[bool, Query()] = True,
    water_level: WaterLevel = 0.0,
) -> Scenario:
    return _validated(Scenario(pathway, year, subsidence, water_level))


ScenarioDep = Annotated[Scenario, Depends(scenario_params)]


def _echo(sc: Scenario) -> dict:
    return {
        "pathway": sc.pathway,
        "year": sc.year,
        "subsidence": sc.include_subsidence,
        "water_level": sc.water_level_m,
    }


@router.get("/assessment")
def get_assessment(sc: ScenarioDep) -> dict:
    """Cells (state, depth, CVI class) plus the exposure summary for one scenario."""
    a = assess(sc)
    p = get_provider()
    return {
        "scenario": _echo(sc),
        "data_mode": p.mode,
        "sources": p.sources(),
        "bbox": bbox(p),
        "summary": a.summary,
        "cells": cells_geojson(p, a),
    }


@router.get("/impact")
def get_impact(sc: ScenarioDep) -> dict:
    """Exposure statistics only (no geometry)."""
    return {"scenario": _echo(sc), "summary": assess(sc).summary}


@router.get("/compare")
def compare(year: Year = 2050, water_level: WaterLevel = 0.0) -> dict:
    """Both pathways, with and without subsidence, for the Scenarios tab."""
    rows = []
    for pw in ("ssp245", "ssp585"):
        for sub in (True, False):
            s = assess(_validated(Scenario(pw, year, sub, water_level))).summary
            rows.append({"pathway": pw, "subsidence": sub, **s})
    return {"year": year, "water_level": water_level, "rows": rows}
