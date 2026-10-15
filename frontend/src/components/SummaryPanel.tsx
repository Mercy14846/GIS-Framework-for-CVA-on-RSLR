import { fmt, fmtWater } from "../lib/format";
import type { Summary } from "../types";

export default function SummaryPanel({ s, loading }: { s: Summary | null; loading: boolean }) {
  const items = s
    ? [
        ["Flooded area", `${fmt(s.flooded_area_km2, 1)} km²`],
        ["Population exposed", `${fmt(s.population_exposed)} (${fmt(s.population_exposed_pct, 1)}%)`],
        ["Built-up area at risk", `${fmt(s.built_up_area_at_risk_km2, 1)} km²`],
        ["Mean RSLR", `${fmt(s.mean_rslr_m, 2)} m`],
        ["Water level above high tide", fmtWater(s.water_level_m)],
        ["High / very high vulnerability", `${fmt(s.high_or_very_high_area_km2, 0)} km²`],
      ]
    : [];
  return (
    <section className={`summary ${loading ? "loading" : ""}`} aria-live="polite" aria-label="Exposure summary">
      {items.map(([k, v]) => (
        <div className="stat" key={k}><div className="v">{v}</div><div className="k">{k}</div></div>
      ))}
    </section>
  );
}
