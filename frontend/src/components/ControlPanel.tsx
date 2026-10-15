import { BASEMAPS, BASEMAP_LABEL, PATHWAY_LABEL, type DataSource, type Pathway, type ViewState } from "../types";
import DataSources from "./DataSources";

interface Props {
  view: ViewState;
  opacity: number;
  onChange: (patch: Partial<ViewState>) => void;
  onOpacity: (v: number) => void;
  onShare: () => void;
  shared: boolean;
  sources: DataSource[];
}

export default function ControlPanel({ view, opacity, onChange, onOpacity, onShare, shared, sources }: Props) {
  return (
    <aside className="panel controls" aria-label="Scenario controls">
      <div className="field">
        <label>Emissions pathway</label>
        <div className="seg" role="radiogroup">
          {(Object.keys(PATHWAY_LABEL) as Pathway[]).map((p) => (
            <button key={p} role="radio" aria-checked={view.pathway === p} className={view.pathway === p ? "on" : ""} onClick={() => onChange({ pathway: p })}>
              {PATHWAY_LABEL[p]}
            </button>
          ))}
        </div>
      </div>
      <label className="check">
        <input type="checkbox" checked={view.subsidence} onChange={(e) => onChange({ subsidence: e.target.checked })} />
        <span>
          Include land subsidence
          <small>{view.subsidence ? "RSLR = sea-level rise + subsidence" : "Global sea-level rise only"}</small>
        </span>
      </label>
      <div className="field">
        <label>Basemap</label>
        <div className="seg four" role="radiogroup" aria-label="Basemap">
          {BASEMAPS.map((b) => (
            <button key={b} role="radio" aria-checked={view.base === b} className={view.base === b ? "on" : ""} onClick={() => onChange({ base: b })}>
              {BASEMAP_LABEL[b]}
            </button>
          ))}
        </div>
      </div>
      <div className="field">
        <label htmlFor="op">Layer opacity</label>
        <input id="op" type="range" min={0.2} max={1} step={0.05} value={opacity} onChange={(e) => onOpacity(Number(e.target.value))} />
      </div>
      <button className="btn" onClick={onShare}>{shared ? "Link copied" : "Share this view"}</button>
      <DataSources sources={sources} />
    </aside>
  );
}
