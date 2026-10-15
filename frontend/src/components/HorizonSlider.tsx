import { HORIZONS, type Horizon } from "../types";

/** Vertical horizon selector: higher on the track = later year = more water, as in NOAA's water-level slider. */
export default function HorizonSlider({ year, onChange }: { year: Horizon; onChange: (y: Horizon) => void }) {
  const ordered = [...HORIZONS].reverse();
  return (
    <div className="slider" role="radiogroup" aria-label="Projection horizon">
      <div className="slider-title">HORIZON</div>
      <div className="slider-track">
        {ordered.map((y) => (
          <button key={y} role="radio" aria-checked={year === y} className={`stop ${year === y ? "on" : ""}`} onClick={() => onChange(y)}>
            <span className="dot" />
            <span>{y}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
