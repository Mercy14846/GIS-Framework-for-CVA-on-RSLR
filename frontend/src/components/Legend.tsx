import { fmt } from "../lib/format";
import { CVI_COLORS, CVI_LABELS, DEPTH_RAMP, POP_RAMP, UNCONNECTED_COLOR, rampGradient } from "../lib/palette";
import type { Tab } from "../types";

export default function Legend({ tab }: { tab: Tab }) {
  return (
    <aside className="panel legend" aria-label="Legend">
      {tab === "vulnerability" ? (
        <>
          <h4>Coastal vulnerability (CVI)</h4>
          <p className="lead">How exposed and sensitive each area is, combining sea-level rise, elevation, slope, shoreline change, landforms, population and infrastructure.</p>
          {CVI_COLORS.map((c, i) => (
            <div className="row" key={c}><i style={{ background: c }} />{CVI_LABELS[i]}</div>
          ))}
        </>
      ) : tab === "impact" ? (
        <>
          <h4>People in flooded areas</h4>
          <p className="lead">Residents of cells flooded from the sea. Darker means more people.</p>
          <div className="ramp" style={{ background: rampGradient(POP_RAMP) }} />
          <div className="ramp-lbl"><span>0</span><span>{fmt(POP_RAMP[POP_RAMP.length - 1][0])}+ per cell</span></div>
        </>
      ) : (
        <>
          <h4>Flooding</h4>
          <p className="lead">Land below the projected water surface.</p>
          <div className="ramp" style={{ background: rampGradient(DEPTH_RAMP) }} />
          <div className="ramp-lbl"><span>0 m deep</span><span>{DEPTH_RAMP[DEPTH_RAMP.length - 1][0]} m+</span></div>
          <div className="row"><i style={{ background: DEPTH_RAMP[1][1] }} />Flooded from the sea</div>
          <div className="row"><i style={{ background: UNCONNECTED_COLOR }} />Low-lying, cut off from the sea</div>
          <div className="row"><i className="outline" />Study area</div>
          <p className="note">Water surface = today's high tide + projected sea-level rise + water level.</p>
        </>
      )}
    </aside>
  );
}
