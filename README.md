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

- All layers come from `DemoProvider` (synthetic).
- `gmslr_ar6_placeholder.json` holds placeholder sea-level values, not IPCC AR6 output.
- AHP priorities in `services/assessment.py` are placeholders; replace them with the expert
  pairwise matrix and report the consistency ratio.
