import { useEffect, useRef } from "react";

const KEY = "dss-intro-seen";

/** True once the viewer has dismissed the intro in this browser (storage may be unavailable). */
export const introSeen = () => {
  try { return localStorage.getItem(KEY) === "1"; } catch { return false; }
};

/** First-visit orientation, like the NOAA viewer's launch screen; reopened from the header "?". */
export default function Intro({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  const done = () => {
    try { localStorage.setItem(KEY, "1"); } catch { /* storage unavailable */ }
    onClose();
  };

  return (
    <dialog ref={ref} className="intro" aria-labelledby="intro-title" onClose={done} onClick={(e) => e.target === ref.current && done()}>
      <h2 id="intro-title">Explore coastal flood risk in Lagos</h2>
      <p>
        See which parts of Lagos could flood as the sea rises and the land sinks, how vulnerable each area is,
        and how many people live there.
      </p>
      <ol>
        <li><b>Set the scenario.</b> Choose a year on <i>Horizon</i>, raise the <i>Water level</i> for tides and storm
          surges, and pick an emissions pathway.</li>
        <li><b>Switch views.</b> <i>Sea Level Rise</i> shows flooding, <i>Vulnerability</i> the risk index,
          <i> Impact</i> the people affected, and <i>Scenarios</i> compares pathways.</li>
        <li><b>Click any cell</b> on the map for its numbers. <i>Share this view</i> copies a link to exactly what you see.</li>
      </ol>
      <p className="intro-note">A screening-level tool: results show the scale of potential flooding, not exact locations.</p>
      <button className="btn" onClick={done} autoFocus>Start exploring</button>
    </dialog>
  );
}
