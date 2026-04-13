import { useState } from "react";

const PHASES = ["Preclinical", "Phase 1", "Phase 2", "Phase 3", "NDA"];
const LAUNCH_YEARS = ["2026", "2027", "2028", "2029", "2030", "2032+"];
// Ordered by 2025–2026 total deal volume (M&A + licensing)
const THERAPEUTIC_AREAS = [
  { label: "Oncology / Hematology", hint: "$89B" },
  { label: "Cardiometabolic / Obesity", hint: "$69B" },
  { label: "Neuroscience / CNS", hint: "$36B" },
  { label: "Rare Disease / Genetic", hint: "$21B" },
  { label: "Respiratory", hint: "$25B" },
  { label: "Infectious Disease", hint: "$11B" },
  { label: "Immunology / Autoimmune", hint: "$5B" },
];

const RECENT_ASSETS = [
  { label: "TERN-701 (BCR::ABL1, CML)", query: "TERN-701 allosteric BCR::ABL1 TKI CML Phase 1/2" },
  { label: "ARV-471 (ER+, Ph3)", query: "ARV-471 ER+ breast cancer Phase 3 launch 2027" },
  { label: "Metsera GLP-1 (obesity, Ph2b)", query: "Metsera ultra-long-acting GLP-1 obesity Phase 2b" },
  { label: "BNT-217 (ADC, NSCLC)", query: "BNT-217 ADC NSCLC" },
];

function Chip({ label, hint, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 rounded-full text-xs border transition-colors cursor-pointer flex items-center gap-1 ${
        active
          ? "bg-blue-50 border-blue-300 text-blue-700"
          : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50"
      }`}
    >
      {label}
      {hint && (
        <span className={`text-[10px] ${active ? "text-blue-400" : "text-gray-300"}`}>
          {hint}
        </span>
      )}
    </button>
  );
}

export default function FilterSidebar({ filters, onChange, onChipInsert, onScanWithFilters }) {
  const toggle = (key, value) => {
    const current = filters[key] || [];
    const updated = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onChange({ ...filters, [key]: updated });
    onChipInsert(value);
  };

  const buildScanQuery = () => {
    const phases = (filters.phases || []).join(", ");
    const tas = (filters.therapeuticAreas || []).join(", ");
    const years = (filters.launchYears || []).join(", ");
    const parts = [];
    if (phases) parts.push(`${phases}`);
    if (tas) parts.push(tas);
    if (years) parts.push(`launching ${years}`);
    return parts.length
      ? `top ${parts.join(" ")} assets`
      : "top Phase 2 oncology assets launching 2028";
  };

  return (
    <div className="w-56 min-w-56 bg-gray-50 border-r border-gray-200 flex flex-col p-4 gap-4 text-sm">
      {/* Phase filter */}
      <div>
        <div className="text-xs font-medium text-gray-400 tracking-wide mb-2">
          PHASE
        </div>
        <div className="flex flex-wrap gap-1">
          {PHASES.map((p) => (
            <Chip
              key={p}
              label={p}
              active={(filters.phases || []).includes(p)}
              onClick={() => toggle("phases", p)}
            />
          ))}
        </div>
      </div>

      <div className="border-t border-gray-200" />

      {/* Launch year */}
      <div>
        <div className="text-xs font-medium text-gray-400 tracking-wide mb-2">
          LAUNCH YEAR
        </div>
        <div className="flex flex-wrap gap-1">
          {LAUNCH_YEARS.map((y) => (
            <Chip
              key={y}
              label={y}
              active={(filters.launchYears || []).includes(y)}
              onClick={() => toggle("launchYears", y)}
            />
          ))}
        </div>
      </div>

      <div className="border-t border-gray-200" />

      {/* Therapeutic area */}
      <div>
        <div className="text-xs font-medium text-gray-400 tracking-wide mb-2">
          THERAPEUTIC AREA
        </div>
        <div className="flex flex-wrap gap-1">
          {THERAPEUTIC_AREAS.map((ta) => (
            <Chip
              key={ta.label}
              label={ta.label}
              hint={ta.hint}
              active={(filters.therapeuticAreas || []).includes(ta.label)}
              onClick={() => toggle("therapeuticAreas", ta.label)}
            />
          ))}
        </div>
        <button
          onClick={() => onScanWithFilters && onScanWithFilters(buildScanQuery())}
          className="mt-2 w-full px-3 py-1.5 rounded-md border border-blue-200 bg-blue-50 text-blue-700 text-[11px] font-medium hover:bg-blue-100 transition-colors text-center"
        >
          ▶ Run scan with filters
        </button>
      </div>

      <div className="border-t border-gray-200" />

      {/* Recent assets */}
      <div>
        <div className="text-xs font-medium text-gray-400 tracking-wide mb-2">
          RECENT ASSETS
        </div>
        <div className="flex flex-col gap-2">
          {RECENT_ASSETS.map((a) => (
            <button
              key={a.label}
              onClick={() => onChipInsert(a.query)}
              className="text-xs text-left text-gray-500 hover:text-gray-800 cursor-pointer transition-colors"
            >
              ▸ {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
