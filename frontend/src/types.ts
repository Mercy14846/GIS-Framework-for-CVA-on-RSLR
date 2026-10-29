export type Tab = "rslr" | "vulnerability" | "impact" | "scenarios";
export const TABS: Tab[] = ["rslr", "vulnerability", "impact", "scenarios"];
export type Basemap = "satellite" | "streets" | "dark" | "light";
export const BASEMAPS: Basemap[] = ["satellite", "streets", "dark", "light"];
export const BASEMAP_LABEL: Record<Basemap, string> = { satellite: "Satellite", streets: "Streets", dark: "Dark", light: "Light" };
export type Pathway = "ssp245" | "ssp585";
export const PATHWAY_LABEL: Record<Pathway, string> = { ssp245: "SSP2-4.5", ssp585: "SSP5-8.5" };
export const PATHWAYS = Object.keys(PATHWAY_LABEL) as Pathway[];
/** Plain-language name for each pathway, shown under its code. */
export const PATHWAY_HINT: Record<Pathway, string> = { ssp245: "Intermediate", ssp585: "High emissions" };
export const HORIZONS = [2030, 2050, 2100] as const;
export type Horizon = (typeof HORIZONS)[number];

/** Water level above Lagos high tide (MHHW) in metres: NOAA's water-level action, in metric. */
export const WATER_LEVEL_MAX = 3;
export const WATER_LEVEL_STEP = 0.25;

export interface ViewState {
  tab: Tab;
  year: Horizon;
  pathway: Pathway;
  subsidence: boolean;
  waterLevel: number;
  base: Basemap;
  lng: number;
  lat: number;
  zoom: number;
}

export interface Summary {
  flooded_area_km2: number;
  unconnected_area_km2: number;
  population_exposed: number;
  population_total: number;
  population_exposed_pct: number;
  built_up_area_at_risk_km2: number;
  mean_rslr_m: number;
  max_rslr_m: number;
  high_or_very_high_area_km2: number;
  water_level_m: number;
}

export type SourceStatus = "observed" | "derived" | "synthetic";

/** Where one analysis layer comes from (GET /api/v1/sources, also on every assessment). */
export interface DataSource {
  layer: string;
  label: string;
  status: SourceStatus;
  source: string;
  dataset?: string;
  scenes?: string[];
  method?: string;
  units?: string;
  note?: string;
}

export interface AssessmentResponse {
  scenario: { pathway: Pathway; year: number; subsidence: boolean; water_level: number };
  data_mode: string;
  sources: DataSource[];
  bbox: [number, number, number, number];
  summary: Summary;
  cells: GeoJSON.FeatureCollection;
}

export interface CompareRow extends Summary {
  pathway: Pathway;
  subsidence: boolean;
}
export interface CompareResponse {
  year: number;
  water_level: number;
  rows: CompareRow[];
}


/** Properties of one grid cell in the /assessment GeoJSON (land cells only). */
export interface CellProperties {
  state: "connected" | "unconnected" | "dry";
  depth_m: number;
  elevation_m: number;
  rslr_m: number;
  population: number;
  cvi: number;
  cvi_class: number;
  cvi_label: string;
}
