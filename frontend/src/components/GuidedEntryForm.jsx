import { useState } from "react";
import { Info } from "lucide-react";

const MODALITIES = [
  "ADC (antibody-drug conjugate)",
  "Bispecific antibody",
  "Small molecule (oral)",
  "Cell therapy (CAR-T, TCR)",
  "PROTAC / molecular glue",
  "mRNA / LNP",
  "Gene therapy (AAV)",
  "Radioligand",
  "Other / unsure",
];

const THERAPEUTIC_AREAS = [
  "Oncology",
  "Neurology",
  "Immunology",
  "Rare Disease",
  "Cardio / Metabolic",
  "Infectious Disease",
];

const PHASES = ["Preclinical", "IND-enabling", "Phase 1", "Phase 2", "Phase 3"];

const LAUNCH_YEARS = ["2026", "2027", "2028", "2029", "2030", "2032+"];

const emptyIndication = () => ({ name: "", phase: "Preclinical", launchYear: "2030" });

export default function GuidedEntryForm({ onSubmit, onBack }) {
  const [asset, setAsset] = useState("");
  const [sponsor, setSponsor] = useState("");
  const [modality, setModality] = useState(MODALITIES[0]);
  const [target, setTarget] = useState("");
  const [ta, setTa] = useState("Oncology");
  const [indications, setIndications] = useState([emptyIndication()]);
  const [differentiation, setDifferentiation] = useState("");

  const updateIndication = (i, field, value) => {
    setIndications((prev) => prev.map((ind, idx) => (idx === i ? { ...ind, [field]: value } : ind)));
  };

  const addIndication = () => setIndications((prev) => [...prev, emptyIndication()]);

  const removeIndication = (i) =>
    setIndications((prev) => prev.length > 1 ? prev.filter((_, idx) => idx !== i) : prev);

  const handleSubmit = () => {
    const parts = [];
    if (asset) parts.push(asset);
    if (sponsor) parts.push(`by ${sponsor}`);
    parts.push(modality);
    if (target) parts.push(`targeting ${target}`);
    parts.push(ta);

    const indParts = indications
      .filter((ind) => ind.name)
      .map((ind) => `${ind.name} (${ind.phase}, launch ${ind.launchYear})`);
    if (indParts.length) parts.push(`for ${indParts.join(", ")}`);
    if (differentiation) parts.push(`— ${differentiation}`);

    onSubmit(parts.join(" ") || `${modality} ${ta} preclinical asset`);
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Scrollable form body */}
      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* Breadcrumb */}
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 mb-4 transition-colors"
        >
          ← Back to welcome
        </button>

        <div className="text-[15px] font-medium text-gray-900 mb-1">Explore a preclinical asset</div>
        <div className="text-xs text-gray-500 mb-4 leading-relaxed">
          Fill in what you know — every field is optional. The less you provide, the more the agent
          will lean on analogue benchmarking and modality comps.
        </div>

        {/* Info banner */}
        <div className="flex gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2.5 mb-5 text-xs text-blue-700 leading-relaxed">
          <Info size={13} className="shrink-0 mt-0.5" />
          <div>
            For preclinical assets, we estimate deal value using <strong>analogue benchmarking</strong>:
            finding recent deals for similar modality + TA + stage, then adjusting for differentiation
            signals you provide.
          </div>
        </div>

        {/* Asset section */}
        <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2.5">ASSET</div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-gray-500 flex justify-between">
              Asset name <span className="text-gray-300 font-normal">optional</span>
            </label>
            <input
              type="text"
              placeholder="e.g. NBL-015, or leave blank"
              value={asset}
              onChange={(e) => setAsset(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-gray-500 flex justify-between">
              Sponsor / company <span className="text-gray-300 font-normal">optional</span>
            </label>
            <input
              type="text"
              placeholder="e.g. NovaRock Biotherapeutics"
              value={sponsor}
              onChange={(e) => setSponsor(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            />
          </div>
        </div>

        <div className="flex flex-col gap-1 mb-3">
          <label className="text-[11px] font-medium text-gray-500 flex justify-between">
            Modality <span className="text-gray-300 font-normal">recommended</span>
          </label>
          <select
            value={modality}
            onChange={(e) => setModality(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
          >
            {MODALITIES.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-gray-500 flex justify-between">
              Target / MOA <span className="text-gray-300 font-normal">optional</span>
            </label>
            <input
              type="text"
              placeholder="e.g. ROR1"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-gray-500 flex justify-between">
              Therapeutic area <span className="text-red-300 font-normal">required</span>
            </label>
            <select
              value={ta}
              onChange={(e) => setTa(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            >
              {THERAPEUTIC_AREAS.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-100 my-4" />

        {/* Indications */}
        <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-1">INDICATIONS</div>
        <div className="text-[11px] text-gray-400 mb-3">
          Add any indications you want included in the deal value calculation.
        </div>

        {indications.map((ind, i) => (
          <div key={i} className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2 mb-2 items-center">
            <input
              type="text"
              placeholder="Indication name"
              value={ind.name}
              onChange={(e) => updateIndication(i, "name", e.target.value)}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            />
            <select
              value={ind.phase}
              onChange={(e) => updateIndication(i, "phase", e.target.value)}
              className="px-2 py-2 text-xs border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            >
              {PHASES.map((p) => <option key={p}>{p}</option>)}
            </select>
            <select
              value={ind.launchYear}
              onChange={(e) => updateIndication(i, "launchYear", e.target.value)}
              className="px-2 py-2 text-xs border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 transition-colors"
            >
              {LAUNCH_YEARS.map((y) => <option key={y}>Launch {y}</option>)}
            </select>
            <button
              onClick={() => removeIndication(i)}
              className="px-2 py-2 text-xs border border-gray-200 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
            >
              ×
            </button>
          </div>
        ))}

        <button
          onClick={addIndication}
          className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1 mt-1 mb-4 transition-colors"
        >
          + Add another indication
        </button>

        <div className="border-t border-gray-100 my-4" />

        {/* Differentiation */}
        <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">
          DIFFERENTIATION SIGNALS{" "}
          <span className="text-gray-300 font-normal ml-1">optional — improves pricing accuracy</span>
        </div>
        <textarea
          rows={3}
          placeholder="Anything distinctive? e.g. novel linker chemistry, best-in-class potency data, conference abstract findings, published preprint, patent estate, KOL endorsement..."
          value={differentiation}
          onChange={(e) => setDifferentiation(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white outline-none focus:border-blue-300 resize-none transition-colors"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200 bg-gray-50">
        <button
          onClick={onBack}
          className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          Switch to quick chat →
        </button>
        <button
          onClick={handleSubmit}
          className="px-5 py-2 rounded-full bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Run diligence ↗
        </button>
      </div>
    </div>
  );
}
