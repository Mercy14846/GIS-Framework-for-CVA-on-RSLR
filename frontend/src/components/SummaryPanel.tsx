import { useMemo } from "react";
import { fmt, fmtWater } from "../lib/format";
import { CVI_COLORS, CVI_LABELS } from "../lib/palette";
import type { CellProperties, CompareResponse, Summary, Tab, ViewState } from "../types";

interface Props {
  tab: Tab;
  view: ViewState;
  s: Summary | null;
  compare: CompareResponse | null;
  cells: GeoJSON.FeatureCollection | null;
  loading: boolean;
}

interface Stat { k: string; v: string; sub?: string }

/** How much subsidence changes a figure for the current pathway: (with − without), never negative. */
function subsidenceEffect(compare: CompareResponse | null, view: ViewState, key: "flooded_area_km2" | "population_exposed") {
  const row = (sub: boolean) => compare?.rows.find((r) => r.pathway === view.pathway && r.subsidence === sub);
  const withS = row(true), without = row(false);
  return withS && without ? Math.max(0, withS[key] - without[key]) : null;
}

const effectText = (delta: number | null, on: boolean, unit: (n: number) => string) =>
  delta === null ? undefined : on ? `${unit(delta)} of this from subsidence` : `${unit(delta)} more with subsidence`;

/** Headline figures for the active tab: one hero number, then supporting stats. */
export default function SummaryPanel({ tab, view, s, compare, cells, loading }: Props) {
  // Share of land cells in each CVI class (the grid is equal-area, so counts are area shares).
  const classShare = useMemo(() => {
    const n = [0, 0, 0, 0, 0];
    for (const f of cells?.features ?? []) n[(f.properties as CellProperties).cvi_class - 1]++;
    const total = n.reduce((a, b) => a + b, 0);
    return total ? n.map((c) => c / total) : null;
  }, [cells]);

  if (!s) return <section className={`summary ${loading ? "loading" : ""}`} aria-label="Exposure summary" />;

  const km2 = (n: number) => `${fmt(n, n < 10 ? 1 : 0)} km²`;
  const people = (n: number) => `${fmt(n)} people`;
  const floodFx = effectText(subsidenceEffect(compare, view, "flooded_area_km2"), view.subsidence, (n) => `+${km2(n)}`);
  const popFx = effectText(subsidenceEffect(compare, view, "population_exposed"), view.subsidence, (n) => `+${people(n)}`);
  const highShare = classShare ? classShare[3] + classShare[4] : null;

  let hero: Stat;
  let rest: Stat[];
  if (tab === "vulnerability") {
    hero = { k: "High or very high vulnerability", v: km2(s.high_or_very_high_area_km2), sub: highShare === null ? undefined : `${fmt(highShare * 100, 0)}% of the study area` };
    rest = [{ k: "Mean relative sea-level rise", v: `${fmt(s.mean_rslr_m, 2)} m` }];
  } else if (tab === "impact") {
    hero = { k: "People in flooded areas", v: fmt(s.population_exposed), sub: popFx };
    rest = [
      { k: "Share of residents", v: `${fmt(s.population_exposed_pct, 1)}%` },
      { k: "Built-up area at risk", v: km2(s.built_up_area_at_risk_km2) },
      { k: "Flooded area", v: km2(s.flooded_area_km2) },
    ];
  } else {
    hero = { k: "Flooded from the sea", v: km2(s.flooded_area_km2), sub: floodFx };
    rest = [
      { k: "Low-lying, cut off", v: km2(s.unconnected_area_km2) },
      { k: "People in flooded areas", v: fmt(s.population_exposed), sub: tab === "scenarios" ? popFx : undefined },
      { k: "Mean sea-level rise", v: `${fmt(s.mean_rslr_m, 2)} m` },
      { k: "Water level above high tide", v: fmtWater(s.water_level_m) },
    ];
  }

  return (
    <section className={`summary ${loading ? "loading" : ""}`} aria-live="polite" aria-label="Exposure summary">
      <div className="stat hero">
        <div className="v">{hero.v}</div>
        <div className="k">{hero.k}</div>
        {hero.sub && <div className="sub">{hero.sub}</div>}
      </div>
      {tab === "vulnerability" && classShare && (
        <div className="stat dist" aria-label="Share of the study area by vulnerability class">
          <div className="k">Area by vulnerability class</div>
          <div className="dist-bar">
            {classShare.map((p, i) => p > 0 && (
              <span key={i} style={{ flexGrow: p, background: CVI_COLORS[i] }} title={`${CVI_LABELS[i]}: ${fmt(p * 100, 0)}%`} />
            ))}
          </div>
          <div className="dist-lbl"><span>Very low</span><span>Very high</span></div>
        </div>
      )}
      {rest.map((x) => (
        <div className="stat" key={x.k}>
          <div className="v">{x.v}</div>
          <div className="k">{x.k}</div>
          {x.sub && <div className="sub">{x.sub}</div>}
        </div>
      ))}
    </section>
  );
}
