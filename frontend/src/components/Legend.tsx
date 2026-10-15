import { fmt } from "../lib/format";
import { CVI_COLORS, CVI_LABELS, DEPTH_RAMP, POP_RAMP, UNCONNECTED_COLOR, rampGradient } from "../lib/palette";
import type { Tab } from "../types";

export default function Legend({ tab }: { tab: Tab }) {
  return (
    <aside className="panel legend" aria-label="Legend">
      {tab === "vulnerability" ? (
        <>
          <h4>Coastal vulnerability (CVI)</h4>
          {CVI_COLORS.map((c, i) => (
            <div className="row" key={c}><i style={{ background: c }} />{CVI_LABELS[i]}</div>
          ))}
        </>
      ) : tab === "impact" ? (
        <>
          <h4>Population in flooded cells</h4>
          <div className="ramp" style={{ background: rampGradient(POP_RAMP) }} />
          <div className="ramp-lbl"><span>0</span><span>{fmt(POP_RAMP[POP_RAMP.length - 1][0])}+</span></div>
        </>
      ) : (
        <>
          <h4>Inundation depth</h4>
          <div className="ramp" style={{ background: rampGradient(DEPTH_RAMP) }} />
          <div className="ramp-lbl"><span>0 m</span><span>{DEPTH_RAMP[DEPTH_RAMP.length - 1][0]} m+</span></div>
          <div className="row"><i style={{ background: UNCONNECTED_COLOR }} />Low-lying, not connected to sea</div>
          <p className="note">Water surface = today's high tide (MHHW) + projected RSLR + water level.</p>
        </>
      )}
    </aside>
  );
}
