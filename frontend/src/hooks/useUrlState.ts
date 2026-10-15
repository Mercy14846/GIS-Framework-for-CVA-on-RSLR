import { useCallback, useEffect, useState } from "react";
import { BASEMAPS, HORIZONS, PATHWAYS, TABS, WATER_LEVEL_MAX, WATER_LEVEL_STEP, type Horizon, type ViewState } from "../types";

const DEFAULTS: ViewState = { tab: "rslr", year: 2050, pathway: "ssp585", subsidence: true, waterLevel: 0, base: "satellite", lng: 3.47, lat: 6.5, zoom: 10.2 };

/** Snap to the 0.25 m steps the API accepts, clamped to 0-3 m. */
export const snapWaterLevel = (v: number) =>
  Number.isFinite(v) ? Math.min(WATER_LEVEL_MAX, Math.max(0, Math.round(v / WATER_LEVEL_STEP) * WATER_LEVEL_STEP)) : 0;

const oneOf = <T extends string>(v: string | null, allowed: readonly T[], fallback: T): T =>
  allowed.includes(v as T) ? (v as T) : fallback;

function parse(hash: string): ViewState {
  const p = new URLSearchParams(hash.replace(/^#\/?/, ""));
  const year = Number(p.get("year"));
  const num = (k: string, d: number) => (Number.isFinite(Number(p.get(k))) && p.get(k) !== null ? Number(p.get(k)) : d);
  return {
    tab: oneOf(p.get("tab"), TABS, DEFAULTS.tab),
    year: (HORIZONS as readonly number[]).includes(year) ? (year as Horizon) : DEFAULTS.year,
    pathway: oneOf(p.get("pathway"), PATHWAYS, DEFAULTS.pathway),
    subsidence: p.get("sub") !== "0",
    waterLevel: snapWaterLevel(num("wl", DEFAULTS.waterLevel)),
    base: oneOf(p.get("base"), BASEMAPS, DEFAULTS.base),
    lng: num("lng", DEFAULTS.lng),
    lat: num("lat", DEFAULTS.lat),
    zoom: num("z", DEFAULTS.zoom),
  };
}

function serialise(v: ViewState): string {
  const p = new URLSearchParams({
    tab: v.tab, year: String(v.year), pathway: v.pathway, sub: v.subsidence ? "1" : "0", wl: v.waterLevel.toFixed(2), base: v.base,
    lng: v.lng.toFixed(4), lat: v.lat.toFixed(4), z: v.zoom.toFixed(2),
  });
  return `#/${p}`;
}

/** The whole map state lives in the URL hash so any view can be shared as a link (as NOAA's viewer does). */
export function useUrlState(): [ViewState, (patch: Partial<ViewState>) => void] {
  const [state, setState] = useState<ViewState>(() => parse(window.location.hash));

  useEffect(() => {
    const onHash = () => setState(parse(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const update = useCallback((patch: Partial<ViewState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      window.history.replaceState(null, "", serialise(next));
      return next;
    });
  }, []);

  return [state, update];
}
