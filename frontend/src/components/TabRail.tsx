import { TABS, type Tab } from "../types";

const META: Record<Tab, { label: string; hint: string; icon: string }> = {
  rslr: { label: "Sea Level Rise", hint: "RSLR inundation", icon: "M12 3c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11z" },
  vulnerability: { label: "Vulnerability", hint: "CVI classes", icon: "M4 20V10l5-3 6 4 5-3v12zM4 20h16" },
  impact: { label: "Impact", hint: "Exposure", icon: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 8a8 8 0 0 1 16 0z" },
  scenarios: { label: "Scenarios", hint: "Compare", icon: "M4 6h16M4 12h10M4 18h16" },
};

export default function TabRail({ tab, onChange }: { tab: Tab; onChange: (t: Tab) => void }) {
  return (
    <nav className="rail" aria-label="Viewer tabs">
      {TABS.map((id) => (
        <button key={id} className={`rail-btn ${tab === id ? "active" : ""}`} onClick={() => onChange(id)} aria-pressed={tab === id} title={META[id].hint}>
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" aria-hidden="true">
            <path d={META[id].icon} />
          </svg>
          <span>{META[id].label}</span>
        </button>
      ))}
    </nav>
  );
}
