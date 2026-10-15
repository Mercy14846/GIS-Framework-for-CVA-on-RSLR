import numpy as np
import pytest

from coastal_dss.rslr.gmslr import gmslr_m
from coastal_dss.rslr.model import inundation, rslr_m


def test_gmslr_anchor_and_interpolation():
    assert gmslr_m("ssp585", 2050) == pytest.approx(0.23)
    assert 0.23 < gmslr_m("ssp585", 2075) < 0.77
    with pytest.raises(KeyError):
        gmslr_m("nope", 2050)


def test_rslr_adds_subsidence_from_baseline():
    rate = np.array([10.0, 0.0])  # mm/yr
    out = rslr_m(0.2, rate, 2055, include_subsidence=True)  # 50 yrs after 2005
    assert out == pytest.approx([0.2 + 0.5, 0.2])


def test_global_only_ignores_subsidence():
    out = rslr_m(0.2, np.array([40.0]), 2100, include_subsidence=False)
    assert out == pytest.approx([0.2])


def test_inundation_splits_connected_and_unconnected():
    # Column 0 is sea. A low channel (row 1) runs inland from it; a low hollow (row 3,
    # col 4) is walled off by high ground.
    elev = np.array(
        [
            [-1, 5.0, 5.0, 5.0, 5.0],
            [-1, 0.5, 0.5, 5.0, 5.0],
            [-1, 5.0, 5.0, 5.0, 5.0],
            [-1, 5.0, 5.0, 5.0, 0.4],
        ],
        dtype=float,
    )
    sea = elev < 0
    connected, unconnected = inundation(elev, 1.0, sea)
    assert connected[1, 1] and connected[1, 2]
    assert unconnected[3, 4] and not connected[3, 4]
    assert not (connected & sea).any() and not (unconnected & sea).any()
