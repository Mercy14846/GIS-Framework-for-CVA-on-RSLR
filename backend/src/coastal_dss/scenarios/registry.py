"""Scenario registry: the single place that enumerates what the viewer can request."""

from __future__ import annotations

from dataclasses import dataclass

from coastal_dss.core.constants import (
    HORIZONS,
    LAGOS_MHHW_M,
    PATHWAYS,
    WATER_LEVEL_MAX_M,
    WATER_LEVEL_STEP_M,
)


@dataclass(frozen=True)
class Scenario:
    pathway: str
    year: int
    include_subsidence: bool = True
    water_level_m: float = 0.0

    def validate(self) -> Scenario:
        if self.pathway not in PATHWAYS:
            raise ValueError(f"pathway must be one of {sorted(PATHWAYS)}")
        if self.year not in HORIZONS:
            raise ValueError(f"year must be one of {list(HORIZONS)}")
        steps = self.water_level_m / WATER_LEVEL_STEP_M
        if not 0.0 <= self.water_level_m <= WATER_LEVEL_MAX_M or abs(steps - round(steps)) > 1e-9:
            raise ValueError(
                f"water_level must be 0-{WATER_LEVEL_MAX_M} m in {WATER_LEVEL_STEP_M} m steps"
            )
        return self


def available() -> dict:
    return {
        "pathways": [{"id": k, "label": v} for k, v in PATHWAYS.items()],
        "horizons": list(HORIZONS),
        "water_level": {
            "datum": "MHHW",
            "mhhw_above_msl_m": LAGOS_MHHW_M,
            "max_m": WATER_LEVEL_MAX_M,
            "step_m": WATER_LEVEL_STEP_M,
        },
    }
