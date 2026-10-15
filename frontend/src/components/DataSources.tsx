import type { DataSource, SourceStatus } from "../types";

const BADGE: Record<SourceStatus, string> = { observed: "Observed", derived: "Derived", synthetic: "Synthetic" };

/** Provenance of every analysis layer, so decision makers can see what rests on real data. */
export default function DataSources({ sources }: { sources: DataSource[] }) {
  if (!sources.length) return null;
  const real = sources.filter((s) => s.status !== "synthetic").length;
  return (
    <details className="sources">
      <summary>
        Data sources <span className="sources-count">{real} of {sources.length} real</span>
      </summary>
      <ul>
        {sources.map((s) => (
          <li key={s.layer}>
            <div className="src-head">
              <span>{s.label}</span>
              <span className={`badge ${s.status}`}>{BADGE[s.status]}</span>
            </div>
            <div className="src-body">
              {s.source}
              {s.units && <> · {s.units}</>}
            </div>
            {(s.method || s.scenes?.length || s.note) && (
              <div className="src-more">
                {s.method && <div>{s.method}</div>}
                {s.scenes && s.scenes.length > 0 && <div>Scenes: {s.scenes.join(", ")}</div>}
                {s.note && <div>{s.note}</div>}
              </div>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
}
