import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import { fillPaint } from "../lib/palette";
import type { Tab } from "../types";

interface Props {
  tab: Tab;
  cells: GeoJSON.FeatureCollection | null;
  center: [number, number];
  zoom: number;
  opacity: number;
  onMove: (lng: number, lat: number, zoom: number) => void;
}

const SRC = "cells";
const LAYER = "cells-fill";

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    imagery: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 18,
      attribution: "Imagery © Esri, Maxar, Earthstar Geographics",
    },
  },
  layers: [
    { id: "bg", type: "background", paint: { "background-color": "#0b1d2e" } },
    { id: "imagery", type: "raster", source: "imagery" },
  ],
};

export default function MapView({ tab, cells, center, zoom, opacity, onMove }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const ready = useRef(false);
  const latest = useRef({ tab, cells, opacity });
  latest.current = { tab, cells, opacity };

  const apply = () => {
    const m = map.current;
    if (!m || !ready.current) return;
    const { tab: t, cells: c, opacity: o } = latest.current;
    const src = m.getSource(SRC) as maplibregl.GeoJSONSource | undefined;
    if (src && c) src.setData(c);
    const paint = fillPaint(t);
    m.setPaintProperty(LAYER, "fill-color", paint.color as never);
    m.setPaintProperty(LAYER, "fill-opacity", ["*", o, paint.opacity] as never);
  };

  useEffect(() => {
    if (!el.current) return;
    const m = new maplibregl.Map({ container: el.current, style: STYLE, center, zoom, attributionControl: { compact: true } });
    map.current = m;
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    m.on("load", () => {
      m.addSource(SRC, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      m.addLayer({ id: LAYER, type: "fill", source: SRC, paint: { "fill-color": "#2b83ba", "fill-opacity": 0.7, "fill-antialias": false } });
      ready.current = true;
      apply();
    });
    m.on("moveend", () => {
      const c = m.getCenter();
      onMove(c.lng, c.lat, m.getZoom());
    });
    return () => {
      ready.current = false;
      m.remove();
    };
    // map is created once; later state flows through `apply`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(apply, [tab, cells, opacity]);

  return <div ref={el} className="map" role="application" aria-label="Coastal vulnerability map" />;
}
