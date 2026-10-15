import numpy as np
import pytest

from coastal_dss.cva.ahp import ahp_weights
from coastal_dss.cva.classify import classify, jenks_breaks
from coastal_dss.cva.cvi import cvi
from coastal_dss.cva.standardise import minmax_1_5


def test_minmax_range_and_invert():
    v = np.array([0.0, 5.0, 10.0])
    assert minmax_1_5(v).tolist() == [1.0, 3.0, 5.0]
    assert minmax_1_5(v, invert=True).tolist() == [5.0, 3.0, 1.0]


def test_fixed_bounds_clip():
    assert minmax_1_5(np.array([20.0]), lo=0, hi=10)[0] == 5.0


def test_ahp_consistent_matrix_recovers_priorities():
    p = np.array([3.0, 2.0, 1.0])
    w, cr = ahp_weights(p[:, None] / p[None, :])
    assert w == pytest.approx(p / p.sum(), abs=1e-6)
    assert cr == pytest.approx(0.0, abs=1e-6)


def test_ahp_rejects_non_reciprocal():
    with pytest.raises(ValueError):
        ahp_weights(np.array([[1, 2], [2, 1]]))


def test_cvi_weighted_sum_and_validation():
    s = {"a": np.array([1.0, 5.0]), "b": np.array([3.0, 3.0])}
    assert cvi(s, {"a": 0.5, "b": 0.5}).tolist() == [2.0, 4.0]
    with pytest.raises(ValueError):
        cvi(s, {"a": 0.9, "b": 0.5})


def test_jenks_finds_obvious_clusters():
    v = np.array([1, 1.1, 1.2, 5, 5.1, 5.2, 9, 9.1, 9.2, 13, 13.1, 13.2, 17, 17.1, 17.2])
    b = jenks_breaks(v, k=5)
    assert len(b) == 6
    classes = classify(v, b)
    assert sorted(set(classes.tolist())) == [1, 2, 3, 4, 5]
