import { useEffect, useRef, useState } from "react";
import ComparePanel from "./components/ComparePanel";
import ControlPanel from "./components/ControlPanel";
import HorizonSlider from "./components/HorizonSlider";
import Legend from "./components/Legend";
import MapView from "./components/MapView";
import SummaryPanel from "./components/SummaryPanel";
import TabRail from "./components/TabRail";
import { useUrlState } from "./hooks/useUrlState";
import { fetchAssessment } from "./lib/api";
import { PATHWAY_LABEL, type AssessmentResponse } from "./types";

export default function App() {
  const [view, update] = useUrlState();
  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [opacity, setOpacity] = useState(0.85);
  const [shared, setShared] = useState(false);
  const initial = useRef<[number, number]>([view.lng, view.lat]);
  const initialZoom = useRef(view.zoom);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    fetchAssessment(view, ac.signal)
      .then((d) => { setData(d); setError(null); })
      .catch((e: Error) => { if (e.name !== "AbortError") setError("Could not reach the analysis API. Is the backend running?"); })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, [view.pathway, view.year, view.subsidence]); // eslint-disable-line react-hooks/exhaustive-deps

  const share = async () => {
    try { await navigator.clipboard.writeText(window.location.href); } catch { /* clipboard unavailable */ }
    setShared(true);
    setTimeout(() => setShared(false), 2000);
  };

  return (
    <div className="app">
      <header className="top">
        <h1>Lagos Coastal Vulnerability Viewer</h1>
        <span className="scn">{PATHWAY_LABEL[view.pathway]} · {view.year} · {view.subsidence ? "with subsidence" : "global only"}</span>
        <span className="tag">Screening-level tool</span>
      </header>
      {data?.data_mode === "demo" && (
        <div className="demo" role="note">Demonstration data: synthetic placeholder layers, not real measurements for Lagos.</div>
      )}
      <TabRail tab={view.tab} onChange={(tab) => update({ tab })} />
      <main className="stage">
        <MapView
          tab={view.tab}
          base={view.base}
          cells={data?.cells ?? null}
          center={initial.current}
          zoom={initialZoom.current}
          opacity={opacity}
          onMove={(lng, lat, zoom) => update({ lng, lat, zoom })}
        />
        <HorizonSlider year={view.year} onChange={(year) => update({ year })} />
        <ControlPanel view={view} opacity={opacity} onChange={update} onOpacity={setOpacity} onShare={share} shared={shared} />
        {view.tab === "scenarios" ? <ComparePanel view={view} /> : <Legend tab={view.tab} />}
        {error && <div className="error" role="alert">{error}</div>}
        <SummaryPanel s={data?.summary ?? null} loading={loading} />
      </main>
    </div>
  );
}
