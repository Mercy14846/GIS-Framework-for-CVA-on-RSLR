import { fmtWater } from "../lib/format";
import { WATER_LEVEL_MAX, WATER_LEVEL_STEP } from "../types";

const TICKS = Array.from({ length: WATER_LEVEL_MAX / 0.5 + 1 }, (_, i) => WATER_LEVEL_MAX - i * 0.5);

/**
 * NOAA-style water-level action, in metres for Lagos: extra water above today's high tide (MHHW)
 * for spring tides and storm surge, added on top of the projected relative sea-level rise.
 */
export default function WaterLevelSlider({ value, onChange }: { value: number; onChange: (m: number) => void }) {
  return (
    <div className="slider wl" aria-label="Water level">
      <div className="slider-title">WATER LEVEL</div>
      <div className="wl-value">{fmtWater(value)}</div>
      <div className="wl-body">
        <input
          type="range"
          min={0}
          max={WATER_LEVEL_MAX}
          step={WATER_LEVEL_STEP}
          value={value}
          aria-label="Water level above high tide"
          aria-valuetext={value === 0 ? "Today's high tide" : `${value.toFixed(2)} metres above high tide`}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <div className="wl-ticks" aria-hidden="true">
          {TICKS.map((t) => (
            <span key={t} className={Math.abs(t - value) < 1e-9 ? "on" : ""}>{t === 0 ? "High tide" : `${t} m`}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
