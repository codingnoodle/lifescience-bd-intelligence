import React, { useState } from "react";

const VIEWS = ["Risk-adjusted", "If-succeed", "Side-by-side"];

function fmt(val) {
  if (val == null) return "—";
  return `$${Number(val).toFixed(1)}B`;
}

function delta(current, previous) {
  if (previous == null || current == null) return null;
  const d = current - previous;
  if (d <= 0) return null;
  return `+$${d.toFixed(1)}B`;
}

function ConfidenceDot({ level }) {
  const bg = level === "high" ? "bg-emerald-500" : level === "medium" ? "bg-amber-400" : "bg-gray-400";
  return <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1 align-middle ${bg}`} />;
}

function ScenarioRow({ name, badge, badgeStyle, math, mathColor, value, deltaText }) {
  return (
    <div className="grid grid-cols-[1fr_auto] gap-3.5 items-center py-2.5 border-b border-gray-200 last:border-b-0">
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-[13px] font-medium text-gray-900">{name}</span>
          <span className={`text-[10px] px-1.5 py-px rounded-full font-medium ${badgeStyle}`}>{badge}</span>
        </div>
        <div className={`text-[11px] leading-relaxed font-mono ${mathColor}`}>{math}</div>
      </div>
      <div className="text-right flex flex-col gap-0.5 items-end">
        <div className="text-lg font-medium text-gray-900 leading-none tabular-nums">{value}</div>
        {deltaText && <div className="text-[11px] text-emerald-600">{deltaText}</div>}
      </div>
    </div>
  );
}

function BarChart({ segments, maxVal, variant, dealMarkerBn }) {
  const colors =
    variant === "risk"
      ? ["bg-[#7F77DD]", "bg-[#534AB7]", "bg-[#3C3489]"]
      : ["bg-[#F2A623]", "bg-[#EF9F27]", "bg-[#BA7517]"];

  const pcts = segments.map((v) => Math.max(0, (v / maxVal) * 100));
  const totalPct = pcts.reduce((a, b) => a + b, 0);

  const dealPct = dealMarkerBn != null ? (dealMarkerBn / maxVal) * 100 : null;

  return (
    <div className="mt-3.5">
      <div className="flex items-center h-7 relative">
        {pcts.map((p, i) => (
          <div
            key={i}
            className={`h-5 ${colors[i]} ${i === 0 ? "rounded-l" : ""} ${i === pcts.length - 1 ? "rounded-r" : ""}`}
            style={{ width: `${p}%` }}
          />
        ))}

        {dealPct != null && (
          <div
            className="absolute h-9 -top-1"
            style={{ left: `${dealPct}%` }}
          >
            <div className="border-l-2 border-dashed border-red-500 h-full" />
            <div className="absolute -top-4 left-1 text-[10px] text-red-500 whitespace-nowrap font-medium">
              Real deal: {fmt(dealMarkerBn)}
            </div>
          </div>
        )}

        <div className="flex-1" />
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>$0</span>
        <span>${Math.round(maxVal / 3)}B</span>
        <span>${Math.round((maxVal * 2) / 3)}B</span>
        <span>${Math.round(maxVal)}B</span>
      </div>
    </div>
  );
}

function WaterfallCard({ variant, result, maxVal }) {
  const isRisk = variant === "risk";
  const { scenarioStandalone, scenarioDisplacement, scenarioStrategic } = result;

  const standaloneVal = isRisk ? scenarioStandalone.riskAdjustedBn : scenarioStandalone.ifSuccessBn;
  const displacementVal = isRisk ? scenarioDisplacement.riskAdjustedBn : scenarioDisplacement.ifSuccessBn;
  const strategicVal = isRisk ? scenarioStrategic.riskAdjustedBn : scenarioStrategic.ifSuccessBn;

  const ptrs = result.indications?.[0]?.ptrsAdjusted ?? "—";

  const headerBg = isRisk ? "bg-[#EEEDFE] text-[#3C3489]" : "bg-[#FAEEDA] text-[#854F0B]";
  const mathColor = isRisk ? "text-[#534AB7]" : "text-[#BA7517]";

  const standaloneDerivation = scenarioStandalone.derivationString ?? "";
  const displacementDerivation = scenarioDisplacement.derivationString ?? "";
  const strategicDerivation = scenarioStrategic.derivationString ?? "";

  const dealMarkerBn =
    !isRisk && scenarioStrategic.predictedUpfrontBn != null
      ? scenarioStrategic.predictedUpfrontBn + (scenarioStrategic.predictedCvrBn ?? 0)
      : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3.5 mb-2.5">
      <div className="flex justify-between items-baseline mb-3">
        <span className="text-[11px] font-medium text-gray-400 tracking-wider">
          {isRisk ? "RISK-ADJUSTED NPV" : "IF-SUCCEED SCENARIO"}
        </span>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${headerBg}`}>
          {isRisk ? `\u00D7 PTRS ${ptrs}%` : "assumes approval"}
        </span>
      </div>

      <ScenarioRow
        name="Standalone NPV"
        badge="asset only"
        badgeStyle="bg-gray-100 text-gray-500"
        math={standaloneDerivation}
        mathColor={mathColor}
        value={fmt(standaloneVal)}
      />
      <ScenarioRow
        name="+ Platform displacement"
        badge="incumbent disruption"
        badgeStyle="bg-[#E1F5EE] text-[#0F6E56]"
        math={displacementDerivation}
        mathColor={mathColor}
        value={fmt(displacementVal)}
        deltaText={delta(displacementVal, standaloneVal)}
      />
      <ScenarioRow
        name="+ Strategic buyer premium"
        badge="top buyer urgency"
        badgeStyle="bg-[#FAEEDA] text-[#854F0B]"
        math={strategicDerivation}
        mathColor={mathColor}
        value={fmt(strategicVal)}
        deltaText={delta(strategicVal, displacementVal)}
      />

      <BarChart
        segments={[standaloneVal, displacementVal - standaloneVal, strategicVal - displacementVal]}
        maxVal={maxVal}
        variant={variant}
        dealMarkerBn={!isRisk ? dealMarkerBn : null}
      />
    </div>
  );
}

function ComparisonTable({ result }) {
  const { scenarioStandalone, scenarioDisplacement, scenarioStrategic } = result;

  const riskStandalone = scenarioStandalone.riskAdjustedBn;
  const riskDisplacement = scenarioDisplacement.riskAdjustedBn;
  const riskStrategic = scenarioStrategic.riskAdjustedBn;

  const succeedStandalone = scenarioStandalone.ifSuccessBn;
  const succeedDisplacement = scenarioDisplacement.ifSuccessBn;
  const succeedStrategic = scenarioStrategic.ifSuccessBn;

  const predictedUpfront = scenarioStrategic.predictedUpfrontBn;
  const predictedCvr = scenarioStrategic.predictedCvrBn ?? 0;
  const dealTotal = predictedUpfront != null ? predictedUpfront + predictedCvr : null;

  const ceilingLow = Math.floor(succeedStrategic);
  const ceilingHigh = Math.ceil(dealTotal ?? succeedStrategic * 1.3);

  const comparatorConf = result.indications?.[0]?.comparatorConfidence ?? "medium";
  const diffConf = result.indications?.[0]?.differentiationVerdict === "differentiated" ? "high" : "medium";
  const buyerConf = result.buyers?.[0]?.confidence ?? "medium";
  const biddingConf = result.biddingTension?.confidence ?? "medium";

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3.5 mb-2.5">
      <div className="flex justify-between items-baseline mb-3">
        <span className="text-[11px] font-medium text-gray-400 tracking-wider">SIDE-BY-SIDE SUMMARY</span>
      </div>

      {/* Header row */}
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-center py-1.5 border-b border-gray-200">
        <span className="text-[10px] font-medium text-gray-400 tracking-wider">SCENARIO</span>
        <span className="text-[10px] font-medium text-[#534AB7] tracking-wider text-right min-w-[55px]">RISK-ADJ.</span>
        <span className="text-[10px] font-medium text-[#BA7517] tracking-wider text-right min-w-[55px]">IF-SUCCEED</span>
      </div>

      {/* Data rows */}
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-center py-1.5 border-b border-gray-200">
        <span className="text-xs text-gray-500">Standalone NPV</span>
        <span className="text-xs font-medium text-[#534AB7] text-right min-w-[55px] tabular-nums">{fmt(riskStandalone)}</span>
        <span className="text-xs font-medium text-[#BA7517] text-right min-w-[55px] tabular-nums">{fmt(succeedStandalone)}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-center py-1.5 border-b border-gray-200">
        <span className="text-xs text-gray-500">+ Platform displacement</span>
        <span className="text-xs font-medium text-[#534AB7] text-right min-w-[55px] tabular-nums">{fmt(riskDisplacement)}</span>
        <span className="text-xs font-medium text-[#BA7517] text-right min-w-[55px] tabular-nums">{fmt(succeedDisplacement)}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-center py-1.5 border-b border-gray-200">
        <span className="text-xs text-gray-500">+ Strategic buyer premium</span>
        <span className="text-xs font-medium text-[#534AB7] text-right min-w-[55px] tabular-nums">{fmt(riskStrategic)}</span>
        <span className="text-xs font-medium text-[#BA7517] text-right min-w-[55px] tabular-nums">{fmt(succeedStrategic)}</span>
      </div>

      {/* Ceiling row */}
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 items-center py-2 mt-1 border-t border-gray-300">
        <span className="text-xs text-gray-900 font-medium">Expected deal ceiling</span>
        <span className="text-xs font-medium text-[#534AB7] text-right min-w-[55px]">&mdash;</span>
        <span className="text-xs font-medium text-[#BA7517] text-right min-w-[55px] tabular-nums">
          ${ceilingLow}&ndash;{ceilingHigh}B
        </span>
      </div>

      {/* Confidence dots */}
      <div className="flex gap-2 flex-wrap mt-2.5 pt-2.5 border-t border-gray-200 text-[11px] text-gray-400">
        <span><ConfidenceDot level={comparatorConf} />Comparator {comparatorConf}</span>
        <span><ConfidenceDot level={diffConf} />Differentiation {diffConf}</span>
        <span><ConfidenceDot level={buyerConf} />Buyer urgency {buyerConf}</span>
        <span><ConfidenceDot level={biddingConf} />Bidding tension {biddingConf}</span>
      </div>
    </div>
  );
}

export default function ValuationWaterfall({ result }) {
  const [view, setView] = useState("Side-by-side");

  if (!result) return null;

  const { scenarioStrategic } = result;
  const strategicSucceed = scenarioStrategic?.ifSuccessBn ?? 0;
  const maxVal = Math.max(strategicSucceed, 9);

  return (
    <div className="py-1 text-[13px]">
      {/* Toggle */}
      <div className="flex bg-gray-100 rounded-full p-0.5 gap-0.5 text-[11px] mb-3.5 w-fit">
        {VIEWS.map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-3.5 py-1.5 rounded-full text-[11px] font-medium border-none cursor-pointer transition-colors ${
              view === v
                ? "bg-white text-gray-900 shadow-sm"
                : "bg-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Insight callout */}
      <div className="bg-blue-50 border border-blue-200 rounded-md px-3 py-2.5 mb-3.5 text-xs text-blue-700 leading-relaxed flex gap-2">
        <svg className="flex-shrink-0 mt-px" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4M12 8h.01" />
        </svg>
        <div>
          Deal prices are typically struck closer to the <b>if-succeed</b> case with risk borne by the buyer via CVRs or milestones.
          Use risk-adjusted for internal IC decisioning, if-succeed for estimating negotiation ceilings.
        </div>
      </div>

      {/* Waterfall cards */}
      {(view === "Risk-adjusted" || view === "Side-by-side") && (
        <WaterfallCard variant="risk" result={result} maxVal={maxVal} />
      )}
      {(view === "If-succeed" || view === "Side-by-side") && (
        <WaterfallCard variant="succeed" result={result} maxVal={maxVal} />
      )}

      {/* Comparison table */}
      {view === "Side-by-side" && <ComparisonTable result={result} />}
    </div>
  );
}
