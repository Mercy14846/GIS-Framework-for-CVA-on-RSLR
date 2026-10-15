import { CVI_COLORS, CVI_LABELS } from "../lib/palette";
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
          <div className="ramp" style={{ background: "linear-gradient(90deg,#e7d4f2,#a85fc9,#5b1a82)" }} />
          <div className="ramp-lbl"><span>0</span><span>6,000+</span></div>
        </>
      ) : (
        <>
          <h4>Inundation depth</h4>
          <div className="ramp" style={{ background: "linear-gradient(90deg,#a8d8f5,#2b83ba,#08306b)" }} />
          <div className="ramp-lbl"><span>0 m</span><span>3 m+</span></div>
          <div className="row"><i style={{ background: "#5cb85c" }} />Low-lying, not connected to sea</div>
        </>
      )}
    </aside>
  );
}
