import { BASEMAPS, BASEMAP_LABEL, PATHWAYS, PATHWAY_HINT, PATHWAY_LABEL, type DataSource, type ViewState } from "../types";
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
    <aside className="panel controls" aria-label="Scenario and map controls">
      <section className="group" aria-labelledby="grp-scenario">
        <h3 id="grp-scenario">Scenario</h3>
        <div className="field">
          <span id="pathway-label">Emissions pathway</span>
          <div className="seg tall" role="radiogroup" aria-labelledby="pathway-label">
            {PATHWAYS.map((p) => (
              <button key={p} role="radio" aria-checked={view.pathway === p} className={view.pathway === p ? "on" : ""} onClick={() => onChange({ pathway: p })}>
                <b>{PATHWAY_LABEL[p]}</b>
                <small>{PATHWAY_HINT[p]}</small>
              </button>
            ))}
          </div>
        </div>
        <label className="check">
          <input type="checkbox" checked={view.subsidence} onChange={(e) => onChange({ subsidence: e.target.checked })} />
          <span>
            Include land subsidence
            <small>{view.subsidence ? "Sea-level rise plus sinking land" : "Global sea-level rise only"}</small>
          </span>
        </label>
      </section>
      <section className="group" aria-labelledby="grp-map">
        <h3 id="grp-map">Map</h3>
        <div className="field">
          <span id="basemap-label">Basemap</span>
          <div className="seg four" role="radiogroup" aria-labelledby="basemap-label">
            {BASEMAPS.map((b) => (
              <button key={b} role="radio" aria-checked={view.base === b} className={view.base === b ? "on" : ""} onClick={() => onChange({ base: b })}>
                {BASEMAP_LABEL[b]}
              </button>
            ))}
          </div>
        </div>
        <div className="field">
          <label htmlFor="layer-opacity">Layer opacity <span className="val">{Math.round(opacity * 100)}%</span></label>
          <input id="layer-opacity" type="range" min={0.2} max={1} step={0.05} value={opacity} onChange={(e) => onOpacity(Number(e.target.value))} />
        </div>
      </section>
      <button className="btn" onClick={onShare} aria-live="polite">{shared ? "Link copied ✓" : "Share this view"}</button>
      <DataSources sources={sources} />
    </aside>
  );
}
