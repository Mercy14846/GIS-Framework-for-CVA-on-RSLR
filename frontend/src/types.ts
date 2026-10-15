export type Tab = "rslr" | "vulnerability" | "impact" | "scenarios";
export type Basemap = "satellite" | "streets" | "dark" | "light";
export const BASEMAPS: Basemap[] = ["satellite", "streets", "dark", "light"];
export const BASEMAP_LABEL: Record<Basemap, string> = { satellite: "Satellite", streets: "Streets", dark: "Dark", light: "Light" };
export type Pathway = "ssp245" | "ssp585";
export const HORIZONS = [2030, 2050, 2100] as const;
export type Horizon = (typeof HORIZONS)[number];

export interface ViewState {
  tab: Tab;
  year: Horizon;
  pathway: Pathway;
  subsidence: boolean;
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
}

export interface AssessmentResponse {
  scenario: { pathway: Pathway; year: number; subsidence: boolean };
  data_mode: string;
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
  rows: CompareRow[];
}

export const PATHWAY_LABEL: Record<Pathway, string> = {
  ssp245: "SSP2-4.5",
  ssp585: "SSP5-8.5",
};
