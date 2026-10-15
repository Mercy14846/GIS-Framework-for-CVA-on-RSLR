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


def test_layers_catalogue():
    assert len(client.get("/api/v1/layers").json()) == 13
