import { fmt } from "../lib/format";
import { DEPTH_RAMP, DRY_COLOR, UNCONNECTED_COLOR } from "../lib/palette";
import type { CellProperties, DataSource } from "../types";

const STATE: Record<CellProperties["state"], { label: string; color: string }> = {
  connected: { label: "Flooded (connected to sea)", color: DEPTH_RAMP[1][1] },
  unconnected: { label: "Low-lying, not connected", color: UNCONNECTED_COLOR },
  dry: { label: "Dry", color: DRY_COLOR },
};

/** Per-cell readout for the map popup: the cell's assessment values plus where elevation comes from. */
export default function CellInspector({ cell, sources, onClose }: { cell: CellProperties; sources: DataSource[]; onClose: () => void }) {
  const elev = sources.find((s) => s.layer === "elevation");
  const synthetic = sources.filter((s) => s.status === "synthetic");
  const allSynthetic = sources.length > 0 && synthetic.length === sources.length;
  return (
    <section className="inspect" aria-label="Selected cell" aria-live="polite" onKeyDown={(e) => e.key === "Escape" && onClose()}>
      <header className="inspect-head">
        <span className="inspect-state"><i style={{ background: STATE[cell.state].color }} />{STATE[cell.state].label}</span>
        <button className="inspect-close" onClick={onClose} aria-label="Close cell details">×</button>
      </header>
      <dl>
        <dt>Flood depth</dt><dd>{cell.state === "dry" ? "—" : `${cell.depth_m.toFixed(2)} m`}</dd>
        <dt>Elevation</dt><dd>{cell.elevation_m.toFixed(2)} m</dd>
        <dt>Relative sea-level rise</dt><dd>{cell.rslr_m.toFixed(2)} m</dd>
        <dt>Vulnerability (CVI)</dt><dd>{cell.cvi.toFixed(2)} · {cell.cvi_label}</dd>
        <dt>Population</dt><dd>{fmt(cell.population)}</dd>
      </dl>
      {elev && elev.status !== "synthetic" && (
        <p className="inspect-src">
          Elevation: {elev.source}, <span className={`badge ${elev.status}`}>{elev.status}</span>
        </p>
      )}
      {synthetic.length > 0 && (
        <p className="inspect-warn" role="note">
          {allSynthetic ? "All layers are synthetic placeholders, not real measurements." : `Synthetic placeholder: ${synthetic.map((s) => s.label).join(", ")}.`}
        </p>
      )}
    </section>
  );
}
