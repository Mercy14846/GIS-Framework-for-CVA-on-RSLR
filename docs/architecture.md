# Architecture

## Principles

1. **Science is separate from delivery.** The analytical engine has no web or UI imports, so
   the same code runs from the API, background jobs or a notebook.
2. **One seam for data.** Everything depends on the `DataProvider` protocol. Demo data and real
   data are interchangeable; nothing above the provider changes when real layers arrive.
3. **The URL is the state.** Pathway, horizon, tab, subsidence toggle and map position live in
   the URL, so any view can be shared or cited.
4. **Honest about uncertainty.** Placeholder data is labelled in the UI; unconnected low-lying
   land is shown separately from connected inundation.

## Data flow

```mermaid
flowchart LR
  P[DataProvider<br/>demo | raster/PostGIS] --> R[rslr<br/>RSLR = GMSLR + LSR]
  R --> I[inundation<br/>connected vs unconnected]
  P --> C[cva<br/>standardise, AHP, CVI, classes]
  R --> C
  I --> X[impact<br/>exposure statistics]
  C --> X
  X --> S[services.assessment]
  S --> A[FastAPI /api/v1]
  A --> W[React + MapLibre viewer]
  S -.-> J[jobs<br/>precompute scenarios]
```

## Backend modules (`backend/src/coastal_dss`)

| Module | Responsibility | Proposal |
|---|---|---|
| `providers` | `DataProvider` protocol, `DemoProvider` | 3.4 input |
| `ingestion` | Dataset catalogue with provenance and status | 3.4, data table |
| `rslr` | GMSLR lookup, RSLR surface, inundation and connectivity | 3.1 |
| `cva` | Min-max 1–5 standardisation, AHP weights, CVI, natural-break classes | 3.2 |
| `impact` | Zonal exposure statistics | 3.3 |
| `scenarios` | Allowed pathway/horizon combinations | 3.4 |
| `services` | Orchestrates the workflow, caches results | 3.4 engine |
| `api` | HTTP surface, GeoJSON encoding | 3.4 output |
| `jobs` | Scenario precompute (Celery or RQ) | 3.4 background jobs |
| `database` | PostGIS schema for the raster provider | 3.4 database |

## API (`/api/v1`)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Status, version, data mode |
| `GET /scenarios` | Pathways, horizons, AHP weights and consistency ratio |
| `GET /layers` | Dataset catalogue with provenance |
| `GET /sources` | Per-layer source of the running provider: observed, derived or synthetic |
| `GET /assessment?pathway&year&subsidence` | Summary statistics and GeoJSON cells |
| `GET /impact?pathway&year&subsidence` | Exposure statistics only (no geometry) |
| `GET /compare?year` | Summaries across pathways with and without subsidence |

## Frontend (`frontend/src`)

`App` owns data fetching and state; `components/` are presentational (`MapView`, `TabRail`,
`HorizonSlider`, `ControlPanel`, `Legend`, `SummaryPanel`, `ComparePanel`); `hooks/useUrlState`
syncs view state with the URL; `lib/api` is the only network code; `lib/basemaps` maps the four basemap choices to Mapbox styles (or the
Esri fallback when no token is set).

## From demo to real data

1. `python -m coastal_dss.ingestion all` fetches SRTM and Landsat C2 L2 through the USGS M2M
   API (`ingestion/usgs_m2m.py`, `usgs_fetch.py`) and builds analysis-grid GeoTIFFs with a
   provenance `manifest.json` (`ingestion/process.py`).
2. `RasterProvider` (same protocol) reads them; layers not yet ingested fall back to the demo
   layer and are reported as `synthetic` by `GET /sources` and in every assessment.
3. Set `DSS_DATA_MODE=raster`. No change to services or the science modules.
4. Replace placeholder GMSLR (IPCC AR6) and AHP priorities.
5. Add validation against flood records and Sentinel-1/2 extents.

## Deployment

`docker compose up --build` starts the API, an nginx-served viewer that proxies `/api`, and
PostGIS and Redis for the raster provider and jobs. CI runs lint, tests and builds on every push.
