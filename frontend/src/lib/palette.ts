import type { Tab } from "../types";

export const CVI_COLORS = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"] as const;
export const CVI_LABELS = ["Very low", "Low", "Moderate", "High", "Very high"] as const;

/** MapLibre paint expressions per tab. Cells are land cells with state/depth/cvi_class/population. */
export function fillPaint(tab: Tab): { color: unknown; opacity: unknown } {
  if (tab === "vulnerability") {
    return {
      color: ["match", ["get", "cvi_class"], 1, CVI_COLORS[0], 2, CVI_COLORS[1], 3, CVI_COLORS[2], 4, CVI_COLORS[3], CVI_COLORS[4]],
      opacity: 0.68,
    };
  }
  if (tab === "impact") {
    return {
      color: ["interpolate", ["linear"], ["get", "population"], 0, "#e7d4f2", 2000, "#a85fc9", 6000, "#5b1a82"],
      opacity: ["case", ["==", ["get", "state"], "connected"], 0.78, 0],
    };
  }
  // rslr + scenarios: connected flooding in blues by depth, unconnected low-lying land in green
  return {
    color: [
      "case",
      ["==", ["get", "state"], "unconnected"],
      "#5cb85c",
      ["interpolate", ["linear"], ["get", "depth_m"], 0, "#a8d8f5", 1, "#2b83ba", 3, "#08306b"],
    ],
    opacity: ["case", ["==", ["get", "state"], "dry"], 0, 0.72],
  };
}
