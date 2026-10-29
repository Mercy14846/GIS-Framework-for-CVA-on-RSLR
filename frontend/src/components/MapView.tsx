import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { MAPBOX_TOKEN, hasMapbox, styleFor } from "../lib/basemaps";
import { fillPaint } from "../lib/palette";
import type { Basemap, CellProperties, DataSource, Tab } from "../types";
import CellInspector from "./CellInspector";

interface Props {
  tab: Tab;
  base: Basemap;
  cells: GeoJSON.FeatureCollection | null;
  bbox: [number, number, number, number] | null;
  fitOnLoad: boolean;
  center: [number, number];
  zoom: number;
  opacity: number;
  sources: DataSource[];
  onMove: (lng: number, lat: number, zoom: number) => void;
}

const SRC = "cells";
const LAYER = "cells-fill";
const SEL = "cells-selected";
const AREA = "study-area";
// Matches the max-width: 820px block in styles.css, where the readout docks above the summary strip.
const NARROW = "(max-width: 820px)";

type BBox = [number, number, number, number];

const outline = (b: BBox): GeoJSON.Feature => ({
  type: "Feature",
  properties: {},
  geometry: { type: "Polygon", coordinates: [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]] },
});

/** Keep the study area clear of the floating panels: gauges and legend at left, controls at right, stats below. */
const fitPadding = (m: mapboxgl.Map, narrow: boolean) => {
  const { clientWidth: w, clientHeight: h } = m.getContainer();
  const p = narrow ? { top: 190, bottom: 130, left: 16, right: 16 } : { top: 40, bottom: 130, left: 230, right: 280 };
  // Mapbox rejects padding larger than the canvas; fall back to a small margin on cramped screens.
  return w - p.left - p.right < 120 || h - p.top - p.bottom < 120 ? 16 : p;
};

/** Move to the study area. cameraForBounds + jumpTo/easeTo, because fitBounds would keep its padding
 *  as persistent map padding and shift the centre that is written to shared links. */
const frame = (m: mapboxgl.Map, b: BBox, narrow: boolean, duration = 0) => {
  const cam = m.cameraForBounds(b, { padding: fitPadding(m, narrow) });
  if (cam) m.easeTo({ ...cam, duration });
};

/** Map button that refits the view to the study area. */
class HomeControl implements mapboxgl.IControl {
  private box?: HTMLDivElement;
  constructor(private onClick: () => void) {}
  onAdd() {
    this.box = document.createElement("div");
    this.box.className = "mapboxgl-ctrl mapboxgl-ctrl-group";
    const b = document.createElement("button");
    b.type = "button";
    b.className = "home-ctrl";
    b.title = "Zoom to study area";
    b.setAttribute("aria-label", "Zoom to study area");
    b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';
    b.addEventListener("click", this.onClick);
    this.box.appendChild(b);
    return this.box;
  }
  onRemove() { this.box?.remove(); }
}

// A placeholder keeps the Map constructor happy when no token is set; the fallback style
// never requests a mapbox:// resource, so this value is never sent to Mapbox.
mapboxgl.accessToken = MAPBOX_TOKEN ?? "pk.unconfigured";

export default function MapView({ tab, base, cells, bbox, fitOnLoad, center, zoom, opacity, sources, onMove }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const ready = useRef(false);
  // The selected cell is kept by feature id (generateId: its index in the grid), so the readout
  // follows scenario changes; `at` is where the desktop popup is anchored.
  const [sel, setSel] = useState<{ id: number; at: mapboxgl.LngLat } | null>(null);
  const [narrow, setNarrow] = useState(() => window.matchMedia(NARROW).matches);
  const [popupEl] = useState(() => document.createElement("div"));
  const popup = useRef<mapboxgl.Popup | null>(null);
  const dock = useRef<HTMLDivElement>(null);
  const latest = useRef({ tab, cells, opacity, sel, bbox, narrow });
  latest.current = { tab, cells, opacity, sel, bbox, narrow };
  const fitted = useRef(!fitOnLoad);

  // Frame the study area once, when the bbox first arrives (not on Mapbox "load", which waits for every
  // basemap tile). resize() first so the camera is computed for the canvas's real size.
  // Skipped when the link carried its own map position.
  const fitOnce = () => {
    const m = map.current;
    const { bbox: b, narrow: n } = latest.current;
    if (!m || !b || fitted.current) return;
    fitted.current = true;
    m.resize();
    frame(m, b, n);
  };

  const apply = () => {
    const m = map.current;
    if (!m || !ready.current || !m.getLayer(LAYER)) return;
    const { tab: t, cells: c, opacity: o, sel: s, bbox: b } = latest.current;
    const src = m.getSource(SRC) as mapboxgl.GeoJSONSource | undefined;
    if (src && c) src.setData(c);
    if (b) (m.getSource(AREA) as mapboxgl.GeoJSONSource | undefined)?.setData(outline(b));
    const paint = fillPaint(t);
    m.setPaintProperty(LAYER, "fill-color", paint.color as never);
    m.setPaintProperty(LAYER, "fill-opacity", ["*", o, paint.opacity] as never);
    m.setFilter(SEL, ["==", ["id"], s?.id ?? -1]);
  };

  // Pick the land cell under a screen point; a point with no cell (sea, lagoon) clears the selection.
  const inspectAt = (point: mapboxgl.PointLike) => {
    const m = map.current;
    if (!m || !ready.current) return;
    const f = m.queryRenderedFeatures(point, { layers: [LAYER] })[0];
    setSel(f && typeof f.id === "number" ? { id: f.id, at: m.unproject(point) } : null);
  };

  // Mapbox drops custom layers whenever the style changes, so (re)add them on every style load,
  // beneath the first label layer so place names stay readable over the analysis.
  const install = () => {
    const m = map.current;
    if (!m) return;
    if (!m.getSource(SRC)) m.addSource(SRC, { type: "geojson", data: { type: "FeatureCollection", features: [] }, generateId: true });
    const firstLabel = m.getStyle()?.layers?.find((l) => l.type === "symbol")?.id;
    if (!m.getLayer(LAYER)) {
      m.addLayer({ id: LAYER, type: "fill", source: SRC, paint: { "fill-color": "#2b83ba", "fill-opacity": 0.7, "fill-antialias": false } }, firstLabel);
    }
    if (!m.getSource(AREA)) m.addSource(AREA, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    if (!m.getLayer(AREA)) {
      m.addLayer({ id: AREA, type: "line", source: AREA, paint: { "line-color": "#ffffff", "line-width": 1.5, "line-opacity": 0.85, "line-dasharray": [3, 2] } }, firstLabel);
    }
    if (!m.getLayer(SEL)) {
      m.addLayer({ id: SEL, type: "line", source: SRC, filter: ["==", ["id"], -1], paint: { "line-color": "#e97132", "line-width": 3 } }, firstLabel);
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
    m.addControl(new HomeControl(() => {
      const { bbox: b, narrow: n } = latest.current;
      if (b) frame(m, b, n, 600);
    }), "bottom-right");
    // Bottom-right, so the scale bar stays clear of the summary strip along the bottom-left.
    m.addControl(new mapboxgl.ScaleControl({ unit: "metric" }), "bottom-right");
    m.getCanvas().setAttribute("aria-label", "Coastal vulnerability map. Arrow keys pan; Enter inspects the cell at the centre; Escape closes it.");
    m.on("style.load", install);
    // Mapbox turns taps into click events, so this covers mouse and touch.
    m.on("click", (e) => inspectAt(e.point));
    m.on("mouseenter", LAYER, () => { m.getCanvas().style.cursor = "pointer"; });
    m.on("mouseleave", LAYER, () => { m.getCanvas().style.cursor = ""; });
    m.on("moveend", () => {
      const c = m.getCenter();
      onMove(c.lng, c.lat, m.getZoom());
    });
    // Keep the canvas matched to its container (initial layout, window resize, panel changes).
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(el.current);
    const mq = window.matchMedia(NARROW);
    const onMq = () => setNarrow(mq.matches);
    mq.addEventListener("change", onMq);
    return () => {
      mq.removeEventListener("change", onMq);
      ro.disconnect();
      ready.current = false;
      popup.current?.remove();
      popup.current = null;
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

  useEffect(apply, [tab, cells, opacity, sel, bbox]);

  useEffect(fitOnce, [bbox]); // eslint-disable-line react-hooks/exhaustive-deps

  // Desktop: anchor a Mapbox popup at the picked point and portal the React readout into it.
  useEffect(() => {
    const m = map.current;
    if (!m || !sel || narrow) {
      popup.current?.remove();
      popup.current = null;
      return;
    }
    popup.current ??= new mapboxgl.Popup({ closeButton: false, closeOnClick: false, maxWidth: "300px", offset: 10, focusAfterOpen: false, className: "cell-popup" }).setDOMContent(popupEl);
    popup.current.setLngLat(sel.at).addTo(m);
  }, [sel, narrow, popupEl]);

  // Phones: the docked readout covers the bottom of the map, so pan a hidden selection up into view.
  useEffect(() => {
    const m = map.current;
    if (!m || !sel || !narrow || !dock.current) return;
    const top = dock.current.offsetTop;
    const y = m.project(sel.at).y;
    if (y > top - 24) m.panBy([0, y - (top - 48)]);
  }, [sel, narrow]);

  const close = () => {
    setSel(null);
    map.current?.getCanvas().focus();
  };

  // Keyboard: Enter/Space inspects the cell under the map centre (pan there with the arrow keys), Escape closes.
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const m = map.current;
    if (!m) return;
    if ((e.key === "Enter" || e.key === " ") && e.target === m.getCanvas()) {
      e.preventDefault();
      const c = m.getContainer();
      inspectAt([c.clientWidth / 2, c.clientHeight / 2]);
    } else if (e.key === "Escape" && sel) {
      close();
    }
  };
  const cell = sel && cells ? (cells.features[sel.id]?.properties as CellProperties | undefined) : undefined;
  const readout = cell && <CellInspector cell={cell} sources={sources} onClose={close} />;

  return (
    <>
      {!hasMapbox() && (
        <div className="mapnote" role="note">Fallback basemap. Set VITE_MAPBOX_TOKEN to enable Mapbox styles.</div>
      )}
      <div
        ref={el}
        className="map"
        role="application"
        aria-label="Coastal vulnerability map"
        onKeyDown={onKeyDown}
      />
      {readout && (narrow ? <div className="inspect-dock" ref={dock}>{readout}</div> : createPortal(readout, popupEl))}
    </>
  );
}
