import { useState } from "react";
import ValuationWaterfall from "./ValuationWaterfall";
import AssumptionsPanel from "./AssumptionsPanel";

function ScoreBadge({ score, recommendation }) {
  const rec = recommendation || (score >= 6.5 ? "GO" : score >= 4.5 ? "WATCH" : "NO-GO");
  const isGo = rec === "GO";
  const isWatch = rec === "WATCH";
  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold ${
        isGo
          ? "bg-green-50 text-green-700 border border-green-200"
          : isWatch
          ? "bg-yellow-50 text-yellow-700 border border-yellow-200"
          : "bg-red-50 text-red-700 border border-red-200"
      }`}
    >
      {rec} · {score}/10
    </span>
  );
}

function ScoreBar({ label, score, color }) {
  if (score == null) return null;
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400 w-16 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${(score / 10) * 100}%`, background: color }}
        />
      </div>
      <span className="text-xs font-medium text-gray-600 w-6 text-right">{score}</span>
    </div>
  );
}

const TABS = [
  { id: "waterfall", label: "Waterfall" },
  { id: "assumptions", label: "Assumptions" },
];

export default function ResultCard({ result, onRecalculate }) {
  const [activeTab, setActiveTab] = useState("waterfall");

  if (!result) return null;

  const {
    assetName,
    compositeScore,
    scienceScore,
    marketScore,
    recommendation,
    summary,
  } = result;

  const score = compositeScore ?? result.score;
  const hasWaterfall =
    result.scenarioStandalone || result.scenarioDisplacement || result.scenarioStrategic;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mt-2 w-full">
      {/* Header */}
      <div className="flex justify-between items-start gap-2 mb-3">
        <span className="font-semibold text-sm text-gray-900 leading-snug">{assetName}</span>
        {score != null && <ScoreBadge score={score} recommendation={recommendation} />}
      </div>

      {/* Composite score bars */}
      <div className="flex flex-col gap-1.5 mb-3 p-2 bg-gray-50 rounded-lg">
        <ScoreBar label="Science" score={scienceScore} color="#3B82F6" />
        <ScoreBar label="Market" score={marketScore} color="#8B5CF6" />
      </div>

      {/* Valuation waterfall — always visible */}
      {hasWaterfall && <ValuationWaterfall result={result} />}

      {/* Tab bar */}
      {hasWaterfall && (
        <>
          <div className="flex border-b border-gray-200 mt-3">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-xs font-medium transition-colors cursor-pointer ${
                  activeTab === tab.id
                    ? "text-gray-900 border-b-2 border-gray-900"
                    : "text-gray-400 hover:text-gray-600"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="mt-2">
            {activeTab === "waterfall" && (
              <div className="text-xs text-gray-400 py-2 text-center">
                Waterfall chart is shown above.
              </div>
            )}
            {activeTab === "assumptions" && (
              <AssumptionsPanel result={result} onRecalculate={onRecalculate} />
            )}
          </div>
        </>
      )}

      {/* GP summary */}
      {summary && (
        <p className="text-xs text-gray-500 leading-relaxed border-t border-gray-100 pt-2 mt-2">
          {summary}
        </p>
      )}
    </div>
  );
}
