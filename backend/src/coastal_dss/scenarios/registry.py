"""Scenario registry: the single place that enumerates what the viewer can request."""

from __future__ import annotations

from dataclasses import dataclass

from coastal_dss.core.constants import HORIZONS, PATHWAYS


@dataclass(frozen=True)
class Scenario:
    pathway: str
    year: int
    include_subsidence: bool = True

    def validate(self) -> Scenario:
        if self.pathway not in PATHWAYS:
            raise ValueError(f"pathway must be one of {sorted(PATHWAYS)}")
        if self.year not in HORIZONS:
            raise ValueError(f"year must be one of {list(HORIZONS)}")
        return self


def available() -> dict:
    return {
        "pathways": [{"id": k, "label": v} for k, v in PATHWAYS.items()],
        "horizons": list(HORIZONS),
    }
