Place real layers under `data/raw/` (git-ignored) and processed outputs under `data/processed/`.
Record each layer in `backend/src/coastal_dss/ingestion/catalogue.py` with source, CRS,
resolution and uncertainty. `data/reference/` holds small committed reference files.
