import numpy as np
import pytest

from coastal_dss.impact.exposure import exposure_summary


def test_exposure_summary():
    flooded = np.array([[True, False], [True, False]])
    pop = np.array([[100.0, 50.0], [300.0, 50.0]])
    out = exposure_summary(flooded, pop, cell_area_km2=2.0)
    assert out["population_exposed"] == 400.0
    assert out["flooded_area_km2"] == 4.0
    assert out["population_exposed_pct"] == pytest.approx(80.0)
