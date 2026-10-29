import { useState } from "react";
import { fmt, fmtWater } from "../lib/format";
import { PATHWAYS, PATHWAY_HINT, PATHWAY_LABEL, type CompareResponse, type ViewState } from "../types";

// Validated pair (dataviz validate_palette.js, light): CVD ΔE 19.9; orange is < 3:1 so every bar carries a value label.
const GLOBAL = "#2b83ba";
const ADDED = "#e97132";

type Metric = "flooded_area_km2" | "population_exposed";
const METRICS: { key: Metric; title: string; unit: (n: number) => string }[] = [
  { key: "flooded_area_km2", title: "Flooded area", unit: (n) => `${fmt(n)} km²` },
  { key: "population_exposed", title: "People in flooded areas", unit: (n) => fmt(n) },
];

/** Global sea-level rise alone vs the extra flooding from subsidence, per pathway: one small multiple per measure. */
export default function ComparePanel({ view, data }: { view: ViewState; data: CompareResponse | null }) {
  const [tip, setTip] = useState<{ text: string; x: number; y: number } | null>(null);
  if (!data) return <aside className="panel compare" aria-label="Scenario comparison"><h4>Scenario comparison</h4><p className="note">Loading…</p></aside>;

  const value = (pw: string, sub: boolean, k: Metric) => data.rows.find((r) => r.pathway === pw && r.subsidence === sub)?.[k] ?? 0;
  const show = (text: string) => (e: React.MouseEvent) => {
    const box = (e.currentTarget.closest(".compare") as HTMLElement).getBoundingClientRect();
    setTip({ text, x: e.clientX - box.left, y: e.clientY - box.top });
  };

  return (
    <aside className="panel compare" aria-label="Scenario comparison" onMouseLeave={() => setTip(null)}>
      <h4>What subsidence adds, {data.year}</h4>
      <p className="lead">Water level {fmtWater(data.water_level)} above high tide.</p>
      <div className="key" aria-hidden="true">
        <span><i style={{ background: GLOBAL }} />Global sea-level rise</span>
        <span><i style={{ background: ADDED }} />Added by subsidence</span>
      </div>
      {METRICS.map((m) => {
        const max = Math.max(...PATHWAYS.map((p) => value(p, true, m.key)), 1);
        return (
          <figure className="bars" key={m.key}>
            <figcaption>{m.title}</figcaption>
            {PATHWAYS.map((p) => {
              const base = value(p, false, m.key);
              const total = Math.max(base, value(p, true, m.key));
              const cur = p === view.pathway;
              return (
                <div className={`bar-row ${cur ? "cur" : ""}`} key={p}>
                  <span className="bar-name">{PATHWAY_LABEL[p]}<small>{PATHWAY_HINT[p]}</small></span>
                  <span className="bar-track">
                    <span className="seg-g" style={{ width: `${(base / max) * 100}%`, background: GLOBAL }}
                      onMouseMove={show(`${PATHWAY_LABEL[p]} · global sea-level rise only: ${m.unit(base)}`)} />
                    {total > base && (
                      <span className="seg-a" style={{ width: `${((total - base) / max) * 100}%`, background: ADDED }}
                        onMouseMove={show(`${PATHWAY_LABEL[p]} · added by subsidence: +${m.unit(total - base)}`)} />
                    )}
                    <span className="bar-val">{m.unit(total)}</span>
                  </span>
                </div>
              );
            })}
          </figure>
        );
      })}
      {tip && <div className="tip" style={{ left: tip.x, top: tip.y }} role="tooltip">{tip.text}</div>}
      <details className="as-table">
        <summary>Show as table</summary>
        <table>
          <thead><tr><th>Pathway</th><th>Subsidence</th><th>Flooded km²</th><th>People</th></tr></thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={`${r.pathway}${r.subsidence}`} className={r.pathway === view.pathway && r.subsidence === view.subsidence ? "cur" : ""}>
                <td>{PATHWAY_LABEL[r.pathway]}</td>
                <td>{r.subsidence ? "Included" : "Excluded"}</td>
                <td>{fmt(r.flooded_area_km2)}</td>
                <td>{fmt(r.population_exposed)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <p className="note">The orange part is what an assessment using global sea-level rise alone would miss.</p>
    </aside>
  );
}
