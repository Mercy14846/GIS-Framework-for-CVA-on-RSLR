import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useEffect, useRef } from "react";
import { MAPBOX_TOKEN, hasMapbox, styleFor } from "../lib/basemaps";
import { fillPaint } from "../lib/palette";
import type { Basemap, Tab } from "../types";

interface Props {
  tab: Tab;
  base: Basemap;
  cells: GeoJSON.FeatureCollection | null;
  center: [number, number];
  zoom: number;
  opacity: number;
  onMove: (lng: number, lat: number, zoom: number) => void;
}

const SRC = "cells";
const LAYER = "cells-fill";

// A placeholder keeps the Map constructor happy when no token is set; the fallback style
// never requests a mapbox:// resource, so this value is never sent to Mapbox.
mapboxgl.accessToken = MAPBOX_TOKEN ?? "pk.unconfigured";

export default function MapView({ tab, base, cells, center, zoom, opacity, onMove }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const ready = useRef(false);
  const latest = useRef({ tab, cells, opacity });
  latest.current = { tab, cells, opacity };

  const apply = () => {
    const m = map.current;
    if (!m || !ready.current || !m.getLayer(LAYER)) return;
    const { tab: t, cells: c, opacity: o } = latest.current;
    const src = m.getSource(SRC) as mapboxgl.GeoJSONSource | undefined;
    if (src && c) src.setData(c);
    const paint = fillPaint(t);
    m.setPaintProperty(LAYER, "fill-color", paint.color as never);
    m.setPaintProperty(LAYER, "fill-opacity", ["*", o, paint.opacity] as never);
  };

  // Mapbox drops custom layers whenever the style changes, so (re)add them on every style load,
  // beneath the first label layer so place names stay readable over the analysis.
  const install = () => {
    const m = map.current;
    if (!m) return;
    if (!m.getSource(SRC)) m.addSource(SRC, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    if (!m.getLayer(LAYER)) {
      const firstLabel = m.getStyle()?.layers?.find((l) => l.type === "symbol")?.id;
      m.addLayer({ id: LAYER, type: "fill", source: SRC, paint: { "fill-color": "#2b83ba", "fill-opacity": 0.7, "fill-antialias": false } }, firstLabel);
    }
    ready.current = true;
    apply();
  };

  useEffect(() => {
    if (!el.current) return;
    const m = new mapboxgl.Map({ container: el.current, style: styleFor(base), center, zoom, attributionControl: true });
    map.current = m;
    if (import.meta.env.DEV) (window as unknown as { __map: mapboxgl.Map }).__map = m;
    m.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "bottom-right");
    m.addControl(new mapboxgl.ScaleControl({ unit: "metric" }), "bottom-left");
    m.on("style.load", install);
    m.on("moveend", () => {
      const c = m.getCenter();
      onMove(c.lng, c.lat, m.getZoom());
    });
    // Keep the canvas matched to its container (initial layout, window resize, panel changes).
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(el.current);
    return () => {
      ro.disconnect();
      ready.current = false;
      m.remove();
    };
    // map is created once; later state flows through `apply` and the basemap effect
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // diff:false forces a full style reload, so "style.load" fires and our layers are re-installed
  // (with diffing, Mapbox would silently drop them without firing the event).
  const appliedBase = useRef(base);
  useEffect(() => {
    if (appliedBase.current === base) return;
    appliedBase.current = base;
    ready.current = false;
    map.current?.setStyle(styleFor(base), { diff: false } as Parameters<mapboxgl.Map["setStyle"]>[1]);
  }, [base]);

  useEffect(apply, [tab, cells, opacity]);

  return (
    <>
      {!hasMapbox() && (
        <div className="mapnote" role="note">Fallback basemap. Set VITE_MAPBOX_TOKEN to enable Mapbox styles.</div>
      )}
      <div ref={el} className="map" role="application" aria-label="Coastal vulnerability map" />
    </>
  );
}
