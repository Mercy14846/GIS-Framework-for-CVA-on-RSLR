"""Global mean sea-level rise (GMSLR) scenarios.

Values are read from a reference table and linearly interpolated between anchor years.
"""

from __future__ import annotations

import itertools
import json
from functools import lru_cache
from pathlib import Path

_REF = Path(__file__).with_name("gmslr_ar6_placeholder.json")


@lru_cache
def _table() -> dict[str, dict[int, float]]:
    raw = json.loads(_REF.read_text())
    return {k: {int(y): v for y, v in raw[k].items()} for k in raw if k.startswith("ssp")}


def gmslr_m(pathway: str, year: int) -> float:
    """GMSLR in metres relative to the 1995-2014 baseline for a pathway and year."""
    table = _table()
    if pathway not in table:
        raise KeyError(f"unknown pathway: {pathway}")
    years = sorted(table[pathway])
    if not years[0] <= year <= years[-1]:
        raise ValueError(f"year {year} outside supported range {years[0]}-{years[-1]}")
    for lo, hi in itertools.pairwise(years):
        if lo <= year <= hi:
            f = (year - lo) / (hi - lo)
            return table[pathway][lo] + f * (table[pathway][hi] - table[pathway][lo])
    return table[pathway][years[-1]]
