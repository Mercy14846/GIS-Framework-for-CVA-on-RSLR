"""Background job entry points (Celery or RQ). Heavy raster workflows run here, not in the API.

Install the `jobs` extra and register `precompute_scenarios` with the worker. It warms the
assessment cache for every scenario so the viewer responds instantly.
"""

from __future__ import annotations

from itertools import product

from coastal_dss.core.constants import HORIZONS, PATHWAYS
from coastal_dss.scenarios.registry import Scenario
from coastal_dss.services.assessment import assess


def precompute_scenarios() -> int:
    n = 0
    for pw, yr, sub in product(PATHWAYS, HORIZONS, (True, False)):
        assess(Scenario(pw, yr, sub))
        n += 1
    return n
