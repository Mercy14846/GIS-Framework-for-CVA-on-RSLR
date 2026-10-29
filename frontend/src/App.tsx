import { useEffect, useRef, useState } from "react";
import ComparePanel from "./components/ComparePanel";
import ControlPanel from "./components/ControlPanel";
import HorizonSlider from "./components/HorizonSlider";
import Intro, { introSeen } from "./components/Intro";
import Legend from "./components/Legend";
import MapView from "./components/MapView";
import SummaryPanel from "./components/SummaryPanel";
import TabRail from "./components/TabRail";
import WaterLevelSlider from "./components/WaterLevelSlider";
import { snapWaterLevel, useUrlState } from "./hooks/useUrlState";
import { fetchAssessment, fetchCompare } from "./lib/api";
import { fmtWater } from "./lib/format";
import { PATHWAY_LABEL, type AssessmentResponse, type CompareResponse } from "./types";

export default function App() {
  const [view, update] = useUrlState();
  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [opacity, setOpacity] = useState(0.85);
  const [shared, setShared] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [introOpen, setIntroOpen] = useState(() => !introSeen());
  const initial = useRef<[number, number]>([view.lng, view.lat]);
  const initialZoom = useRef(view.zoom);
  // A link without a map position opens fitted to the study area; a shared link keeps its view.
  const fitOnLoad = useRef(!/[#&/]lng=/.test(window.location.hash));

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    fetchAssessment(view, ac.signal)
      .then((d) => { setData(d); setError(null); })
      .catch((e: Error) => { if (e.name !== "AbortError") setError("Could not reach the analysis API. Is the backend running?"); })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, [view.pathway, view.year, view.subsidence, view.waterLevel]); // eslint-disable-line react-hooks/exhaustive-deps

  // Every pathway with and without subsidence: feeds the Scenarios chart and the "added by subsidence" figures.
  useEffect(() => {
    const ac = new AbortController();
    fetchCompare(view, ac.signal).then(setCompare).catch(() => undefined);
    return () => ac.abort();
  }, [view.year, view.waterLevel]); // eslint-disable-line react-hooks/exhaustive-deps

  const sources = data?.sources ?? [];
  const synthetic = sources.filter((s) => s.status === "synthetic");
  const current = compare && compare.year === view.year && compare.water_level === view.waterLevel ? compare : null;

  const share = async () => {
    try { await navigator.clipboard.writeText(window.location.href); } catch { /* clipboard unavailable */ }
    setShared(true);
    setTimeout(() => setShared(false), 2000);
  };

  const subsidenceText = view.subsidence ? "with subsidence" : "no subsidence";
  const scenarioLegend = view.tab === "scenarios"
    ? <ComparePanel view={view} data={current} />
    : <Legend tab={view.tab} />;

  return (
    <div className="app">
      <header className="top">
        <h1>Lagos Coastal Vulnerability Viewer</h1>
        <span className="scn" aria-label="Current scenario">
          <b>{PATHWAY_LABEL[view.pathway]}</b> · {view.year} · {subsidenceText} · water {fmtWater(view.waterLevel)}
        </span>
        <span className="tag">Screening-level tool</span>
        <button className="help" onClick={() => setIntroOpen(true)} aria-label="About this viewer">?</button>
      </header>
      {data?.data_mode === "demo" && (
        <div className="demo" role="note">Demonstration data: synthetic placeholder layers, not real measurements for Lagos.</div>
      )}
      {data && data.data_mode !== "demo" && synthetic.length > 0 && (
        <div className="demo" role="note">
          USGS remote-sensing layers loaded. Still synthetic placeholders: {synthetic.map((s) => s.label).join(", ")}.
        </div>
      )}
      <TabRail tab={view.tab} onChange={(tab) => update({ tab })} />
      <main className="stage">
        <MapView
          tab={view.tab}
          base={view.base}
          cells={data?.cells ?? null}
          bbox={data?.bbox ?? null}
          fitOnLoad={fitOnLoad.current}
          center={initial.current}
          zoom={initialZoom.current}
          opacity={opacity}
          sources={sources}
          onMove={(lng, lat, zoom) => update({ lng, lat, zoom })}
        />
        {/* Scenario gauges, then the legend (or comparison) beside them on desktop. */}
        <div className="left-col">
          <div className="gauges panel" role="group" aria-label="Time and water level">
            <HorizonSlider year={view.year} onChange={(year) => update({ year })} />
            {view.tab !== "vulnerability" && (
              <WaterLevelSlider value={view.waterLevel} onChange={(m) => update({ waterLevel: snapWaterLevel(m) })} />
            )}
          </div>
          <div className="desk-only">{scenarioLegend}</div>
        </div>
        {loading && <div className="busy" role="status"><span className="spin" aria-hidden="true" />Updating map…</div>}
        {/* On narrow screens the legend and controls collapse into a bottom sheet; on desktop the wrappers are display: contents. */}
        <div className={`sheet ${sheetOpen ? "open" : ""}`}>
          <button className="sheet-toggle" aria-expanded={sheetOpen} aria-controls="sheet-body" onClick={() => setSheetOpen((o) => !o)}>
            {sheetOpen ? "Hide legend & controls" : "Legend & controls"}
          </button>
          <div className="sheet-body" id="sheet-body">
            <div className="phone-only">{scenarioLegend}</div>
            <ControlPanel view={view} opacity={opacity} onChange={update} onOpacity={setOpacity} onShare={share} shared={shared} sources={sources} />
          </div>
        </div>
        {error && <div className="error" role="alert">{error}</div>}
        <SummaryPanel tab={view.tab} view={view} s={data?.summary ?? null} compare={current} cells={data?.cells ?? null} loading={loading} />
      </main>
      <Intro open={introOpen} onClose={() => setIntroOpen(false)} />
    </div>
  );
}
