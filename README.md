# GIS Framework for Coastal Vulnerability Assessment under RSLR, Lagos

An interactive decision-support platform that turns **relative sea level rise (RSLR)** and
**land subsidence** into measurable **vulnerability, impact and hotspot evidence** for coastal
Lagos. It implements Objective iv of the MTech proposal *A GIS-Based Decision Support Framework
for Coastal Vulnerability Assessment under Relative Sea Level Rise in Lagos, Nigeria*, and is
modelled on the interaction design of the NOAA Sea Level Rise Viewer.

> **Status: working prototype on synthetic placeholder data.** The viewer shows a clear
> "Demonstration data" banner. Real layers (DEM, InSAR/GNSS subsidence, GRID3 population, OSM
> infrastructure) plug in through the provider interface without changing the API or the UI.

## Run it

```bash
docker compose up --build          # viewer at http://localhost:8080
```

or locally:

```bash
make setup
make dev-api      # http://localhost:8000/docs
make dev-web      # http://localhost:5173
make test
```

## Mapbox basemap

The viewer uses Mapbox GL JS with four basemaps (Satellite, Streets, Dark, Light). Create a
free public token at <https://account.mapbox.com>, restrict it to your site URLs, then:

```bash
echo "VITE_MAPBOX_TOKEN=pk.your_token" > frontend/.env.local   # local dev
VITE_MAPBOX_TOKEN=pk.your_token docker compose up --build      # Docker
```

Without a token the viewer falls back to an Esri satellite basemap and shows a notice.

## Real data from USGS (M2M API)

The platform can replace the synthetic layers with USGS remote-sensing data for the study
area, fetched through the [EROS Machine-to-Machine API](https://m2m.cr.usgs.gov/):

| Input (USGS dataset) | Layers built from it |
|---|---|
| SRTM 1 Arc-Second Global (~30 m) | elevation, slope |
| Landsat 8-9 OLI C2 Level-2, least cloudy dry-season scenes of the last 3 years | sea and lagoon mask (MNDWI), built-up share (NDBI/NDVI), wetland class |
| Landsat 4-5 TM C2 Level-2, 1984-1992 | shoreline change (land lost to the sea per year) |

You need a USGS ERS account with M2M access and an **application token**
(<https://ers.cr.usgs.gov/password/appgenerate>). Put them in `backend/.env` (git-ignored):

```bash
DSS_USGS_USERNAME=your_ers_username
DSS_USGS_TOKEN=your_m2m_application_token
```

Then:

```bash
cd backend && pip install -e ".[ingest]"
python -m coastal_dss.ingestion plan      # which datasets and scenes would be used (no download)
python -m coastal_dss.ingestion all       # download into data/raw/usgs, build data/processed
DSS_DATA_MODE=raster uvicorn coastal_dss.api.main:app --port 8000
```

Only the needed Landsat bands are downloaded (not the 1 GB bundles). Every layer carries its
provenance (dataset, scene IDs and dates, method), shown in the viewer under **Data sources**
with an Observed / Derived / Synthetic badge. USGS has no population or subsidence product:
drop a GRID3/WorldPop raster at `data/raw/external/population.tif` and an InSAR rate raster
(mm/yr) at `data/raw/external/subsidence.tif` and re-run `process`; until then those two
layers stay synthetic and the viewer says so.

## What it does

| Viewer tab | Proposal objective | What you see |
|---|---|---|
| Sea Level Rise | i | `RSLR(x,t) = GMSLR(t) + LSR(x)`; inundation depth; low-lying unconnected areas flagged separately |
| Vulnerability | ii | CVI = Σ(wᵢ·Sᵢ), indicators standardised 1–5, AHP weights, five natural-break classes |
| Impact | iii | Population, built-up area and flooded area exposed |
| Scenarios | iv | SSP2-4.5 vs SSP5-8.5, with vs without subsidence, side by side |

The "with / without subsidence" toggle shows how much risk is missed when only global
sea-level rise is used. Every view is a shareable URL.

## Repository layout

```
backend/   Python analytical engine and FastAPI service (src/coastal_dss)
frontend/  React + TypeScript + MapLibre viewer
data/      reference data and (git-ignored) raw/processed layers
deployment/ Dockerfiles and nginx config
docs/      architecture and decision records
```

See [docs/architecture.md](docs/architecture.md) for module boundaries and the path from demo
data to real data.

## Known placeholders (replace before any real use)

- By default all layers come from `DemoProvider` (synthetic); see "Real data from USGS" above.
- `gmslr_ar6_placeholder.json` holds placeholder sea-level values, not IPCC AR6 output.
- AHP priorities in `services/assessment.py` are placeholders; replace them with the expert
  pairwise matrix and report the consistency ratio.
