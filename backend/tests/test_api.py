from fastapi.testclient import TestClient

from coastal_dss.api.main import app

client = TestClient(app)


def test_health_and_scenarios():
    assert client.get("/api/v1/health").json()["status"] == "ok"
    s = client.get("/api/v1/scenarios").json()
    assert s["horizons"] == [2030, 2050, 2100]
    assert s["ahp"]["consistency_ratio"] < 0.1


def test_assessment_shape_and_monotonic_exposure():
    r = client.get("/api/v1/assessment", params={"pathway": "ssp585", "year": 2100}).json()
    assert r["cells"]["features"] and r["data_mode"] == "demo"
    early = client.get("/api/v1/impact", params={"pathway": "ssp585", "year": 2030}).json()
    late = client.get("/api/v1/impact", params={"pathway": "ssp585", "year": 2100}).json()
    assert late["summary"]["flooded_area_km2"] >= early["summary"]["flooded_area_km2"]


def test_subsidence_increases_exposure():
    with_s = client.get("/api/v1/impact", params={"year": 2100, "subsidence": True}).json()
    without = client.get("/api/v1/impact", params={"year": 2100, "subsidence": False}).json()
    assert with_s["summary"]["mean_rslr_m"] > without["summary"]["mean_rslr_m"]
    assert with_s["summary"]["flooded_area_km2"] >= without["summary"]["flooded_area_km2"]


def test_invalid_scenario_rejected():
    assert client.get("/api/v1/assessment", params={"year": 1999}).status_code == 422


def test_water_level_raises_flooding_but_not_vulnerability():
    calm = client.get("/api/v1/impact", params={"year": 2050, "water_level": 0}).json()
    surge = client.get("/api/v1/impact", params={"year": 2050, "water_level": 1.5}).json()
    assert surge["summary"]["water_level_m"] == 1.5
    assert surge["summary"]["flooded_area_km2"] > calm["summary"]["flooded_area_km2"]
    assert surge["summary"]["population_exposed"] >= calm["summary"]["population_exposed"]
    # CVI reflects long-term RSLR only; a transient water level must not change it.
    assert (
        surge["summary"]["high_or_very_high_area_km2"]
        == calm["summary"]["high_or_very_high_area_km2"]
    )


def test_water_level_depth_and_compare():
    params = {"year": 2030, "water_level": 2.0}
    cells = client.get("/api/v1/assessment", params=params).json()["cells"]["features"]
    wet = [f["properties"] for f in cells if f["properties"]["state"] != "dry"]
    assert wet and all(p["depth_m"] >= 0 for p in wet)
    cmp = client.get("/api/v1/compare", params=params).json()
    assert cmp["water_level"] == 2.0 and all(r["water_level_m"] == 2.0 for r in cmp["rows"])


def test_water_level_out_of_range_or_off_step_rejected():
    for wl in (-0.25, 3.25, 0.3):
        r = client.get("/api/v1/assessment", params={"water_level": wl})
        assert r.status_code == 422


def test_demo_provider_is_deterministic():
    import numpy as np

    from coastal_dss.providers import get_provider

    p = get_provider()
    assert np.array_equal(p.subsidence_rate_mm_yr(), p.subsidence_rate_mm_yr())
    a, b = p.indicator_layers(), p.indicator_layers()
    assert all(np.array_equal(a[k][0], b[k][0]) for k in a)


def test_scenarios_advertise_water_level():
    wl = client.get("/api/v1/scenarios").json()["water_level"]
    assert wl["datum"] == "MHHW" and wl["max_m"] == 3.0 and wl["step_m"] == 0.25


def test_layers_catalogue():
    assert len(client.get("/api/v1/layers").json()) == 13
