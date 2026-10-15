import type { StyleSpecification } from "mapbox-gl";
import type { Basemap } from "../types";

export const MAPBOX_TOKEN: string | undefined = import.meta.env.VITE_MAPBOX_TOKEN || undefined;

/** Mapbox-hosted styles, one per basemap choice. */
const MAPBOX_STYLE: Record<Basemap, string> = {
  satellite: "mapbox://styles/mapbox/satellite-streets-v12",
  streets: "mapbox://styles/mapbox/streets-v12",
  dark: "mapbox://styles/mapbox/dark-v11",
  light: "mapbox://styles/mapbox/light-v11",
};

/** Used only when no token is configured, so the viewer never shows a blank map. */
const FALLBACK: StyleSpecification = {
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

export const hasMapbox = () => Boolean(MAPBOX_TOKEN);
export const styleFor = (b: Basemap): string | StyleSpecification => (MAPBOX_TOKEN ? MAPBOX_STYLE[b] : FALLBACK);
