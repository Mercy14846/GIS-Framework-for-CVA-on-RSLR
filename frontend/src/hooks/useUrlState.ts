import { useCallback, useEffect, useState } from "react";
import { HORIZONS, type Horizon, type Pathway, type Tab, type ViewState } from "../types";

const DEFAULTS: ViewState = { tab: "rslr", year: 2050, pathway: "ssp585", subsidence: true, lng: 3.47, lat: 6.5, zoom: 10.2 };
const TABS: Tab[] = ["rslr", "vulnerability", "impact", "scenarios"];

/** The whole map state lives in the URL hash so any view can be shared as a link (as NOAA's viewer does). */
function parse(hash: string): ViewState {
  const p = new URLSearchParams(hash.replace(/^#\/?/, ""));
  const year = Number(p.get("year"));
  const num = (k: string, d: number) => (Number.isFinite(Number(p.get(k))) && p.get(k) !== null ? Number(p.get(k)) : d);
  return {
    tab: TABS.includes(p.get("tab") as Tab) ? (p.get("tab") as Tab) : DEFAULTS.tab,
    year: (HORIZONS as readonly number[]).includes(year) ? (year as Horizon) : DEFAULTS.year,
    pathway: p.get("pathway") === "ssp245" ? ("ssp245" as Pathway) : DEFAULTS.pathway,
    subsidence: p.get("sub") !== "0",
    lng: num("lng", DEFAULTS.lng),
    lat: num("lat", DEFAULTS.lat),
    zoom: num("z", DEFAULTS.zoom),
  };
}

function serialise(v: ViewState): string {
  const p = new URLSearchParams({
    tab: v.tab, year: String(v.year), pathway: v.pathway, sub: v.subsidence ? "1" : "0",
    lng: v.lng.toFixed(4), lat: v.lat.toFixed(4), z: v.zoom.toFixed(2),
  });
  return `#/${p}`;
}

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
