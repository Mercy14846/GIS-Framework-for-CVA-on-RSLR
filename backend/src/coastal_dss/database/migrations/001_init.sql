-- Schema sketch for the PostGIS-backed provider (see docs/architecture.md).
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS dataset (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source TEXT NOT NULL,
  resolution TEXT,
  crs TEXT,
  coverage TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  uncertainty_note TEXT,
  ingested_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scenario_run (
  id BIGSERIAL PRIMARY KEY,
  pathway TEXT NOT NULL,
  year INT NOT NULL,
  include_subsidence BOOLEAN NOT NULL,
  weights JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (pathway, year, include_subsidence, weights)
);

CREATE TABLE IF NOT EXISTS cell_result (
  run_id BIGINT REFERENCES scenario_run(id) ON DELETE CASCADE,
  geom geometry(Polygon, 4326) NOT NULL,
  rslr_m REAL, depth_m REAL, state TEXT, cvi REAL, cvi_class SMALLINT
);
CREATE INDEX IF NOT EXISTS cell_result_geom_idx ON cell_result USING GIST (geom);
