/** Locale number with at most `digits` decimals (1,284,766 / 186.7). */
export const fmt = (n: number, digits = 0) => n.toLocaleString(undefined, { maximumFractionDigits: digits });

/** Water level above high tide, always signed and in 0.25 m steps: "+0.50 m". */
export const fmtWater = (m: number) => `+${m.toFixed(2)} m`;
