import { useEffect, useState } from "react";
import { fetchCompare } from "../lib/api";
import { fmt, fmtWater } from "../lib/format";
import { PATHWAY_LABEL, type CompareResponse, type ViewState } from "../types";

export default function ComparePanel({ view }: { view: ViewState }) {
  const [data, setData] = useState<CompareResponse | null>(null);
  useEffect(() => {
    const ac = new AbortController();
    fetchCompare(view, ac.signal).then(setData).catch(() => undefined);
    return () => ac.abort();
  }, [view.year, view.waterLevel]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!data) return null;
  return (
    <aside className="panel compare" aria-label="Scenario comparison">
      <h4>Scenario comparison, {data.year} · water {fmtWater(data.water_level)}</h4>
      <table>
        <thead><tr><th>Pathway</th><th>Subsidence</th><th>Flooded km²</th><th>Pop. exposed</th></tr></thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={`${r.pathway}${r.subsidence}`} className={r.pathway === view.pathway && r.subsidence === view.subsidence ? "cur" : ""}>
              <td>{PATHWAY_LABEL[r.pathway]}</td>
              <td>{r.subsidence ? "Included" : "Excluded"}</td>
              <td>{r.flooded_area_km2.toFixed(0)}</td>
              <td>{fmt(r.population_exposed)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">Rows with subsidence excluded show what a global-only assessment would miss.</p>
    </aside>
  );
}
