import { useState } from "react";

function ConfidencePill({ level }) {
  const styles = {
    high: "bg-green-50 text-green-700",
    medium: "bg-amber-50 text-amber-700",
    low: "bg-red-50 text-red-700",
  };
  return (
    <span
      className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${styles[level] || styles.low}`}
    >
      {level} confidence
    </span>
  );
}

function CardHeader({ label, confidence, editLabel, onEdit }) {
  return (
    <div className="flex items-center justify-between mb-1.5">
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] font-medium text-gray-500 tracking-wider">
          {label}
        </span>
        {confidence && <ConfidencePill level={confidence} />}
      </div>
      {onEdit && (
        <button
          onClick={onEdit}
          className="text-[11px] text-blue-500 hover:text-blue-700 cursor-pointer bg-transparent border-none p-0"
        >
          {editLabel || "Change"} &rarr;
        </button>
      )}
    </div>
  );
}

function AssumptionCard({ children, gradient }) {
  return (
    <div
      className={`border border-gray-200 rounded-lg px-3 py-2.5 mb-2 ${
        gradient
          ? ""
          : "bg-white"
      }`}
      style={
        gradient
          ? {
              background:
                "linear-gradient(to right, rgba(126,119,221,0.06), rgba(239,159,39,0.06))",
            }
          : undefined
      }
    >
      {children}
    </div>
  );
}

function formatBn(v) {
  if (v == null) return "--";
  return `$${Number(v).toFixed(1)}B`;
}

function formatPct(v) {
  if (v == null) return "--";
  const n = Number(v);
  return n <= 1 ? `${(n * 100).toFixed(0)}%` : `${n}%`;
}

function fireIcons(urgency) {
  // Return a string of fire markers based on urgency threshold
  if (urgency >= 1.4) return "\u2B50\u2B50\u2B50"; // high urgency
  if (urgency >= 1.2) return "\u2B50";
  return "\u2B50";
}

function fireOpacity(urgency) {
  if (urgency >= 1.4) return 1;
  return 0.3;
}

export default function AssumptionsPanel({ result, onRecalculate }) {
  const [editingField, setEditingField] = useState(null);
  const [editDraft, setEditDraft] = useState("");

  if (!result) return null;

  const indications = result.indications || [];
  const buyers = result.buyers || [];
  const tension = result.biddingTension;
  const scenarioStrategic = result.scenarioStrategic;
  const scenarioStandalone = result.scenarioStandalone;
  const scenarioDisplacement = result.scenarioDisplacement;

  // Use the first indication for comparator / differentiation / PTRS display
  const primary = indications[0] || {};
  const comp = primary.comparator || {};
  const metrics = primary.metricComparison || [];
  const breakdown = primary.ptrsBreakdown || [];

  const handleEdit = (indicationName, field, value) => {
    if (onRecalculate) {
      onRecalculate({ indication_name: indicationName, field, value });
    }
  };

  const startEdit = (key, currentValue) => {
    setEditingField(key);
    setEditDraft(String(currentValue ?? ""));
  };

  const submitEdit = (indicationName, field) => {
    setEditingField(null);
    const parsed = Number(editDraft);
    handleEdit(indicationName, field, isNaN(parsed) ? editDraft : parsed);
  };

  // Count better / worse metrics
  const betterCount = metrics.filter(
    (m) =>
      m.direction === "better" ||
      (m.direction || "").includes("meaningful") ||
      (m.direction || "").includes("modest")
  ).length;
  const worseCount = metrics.filter(
    (m) => m.direction === "worse"
  ).length;

  // Bidding tension segments
  const tensionScore = tension?.score || 0;
  const tensionSegments = 4;
  const filledSegments = Math.round(tensionScore * tensionSegments);
  const tensionPremium = tension?.premium || 0;
  const tensionSignals = tension?.signals || [];

  return (
    <div className="py-1 pb-2 text-[13px]">
      {/* Panel Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-sm font-medium text-gray-900">
            Assumptions behind this valuation
          </div>
          <div className="text-[11px] text-gray-500 mt-0.5">
            Every derivation below shows both views — risk-adjusted NPV and the
            if-succeed case. Edit any field to recalculate both.
          </div>
        </div>
        <button
          onClick={() => onRecalculate && onRecalculate({ rerun: true })}
          className="shrink-0 ml-3 px-3 py-1 rounded-full bg-blue-50 text-blue-600 border border-blue-200 text-[11px] font-medium cursor-pointer hover:bg-blue-100 transition-colors"
        >
          Re-run with overrides &#8635;
        </button>
      </div>

      {/* Comparator Card */}
      <AssumptionCard>
        <CardHeader
          label="IDENTIFIED COMPARATOR"
          confidence={primary.comparatorConfidence || "high"}
          editLabel="Change"
          onEdit={() => startEdit("comparator", comp.name)}
        />
        {editingField === "comparator" ? (
          <div className="flex items-center gap-2">
            <input
              autoFocus
              className="text-xs border border-blue-300 rounded px-2 py-1 w-48"
              value={editDraft}
              onChange={(e) => setEditDraft(e.target.value)}
              onBlur={() => submitEdit(primary.name, "comparator.name")}
              onKeyDown={(e) =>
                e.key === "Enter" &&
                submitEdit(primary.name, "comparator.name")
              }
            />
          </div>
        ) : (
          <div className="text-[13px] text-gray-900 leading-relaxed">
            <span className="font-medium">{comp.name || "--"}</span>
            {comp.sponsor && <> &middot; {comp.sponsor}</>}
            {(comp.peak_sales_bn || comp.peakSalesBn) != null && (
              <>
                {" "}
                &middot; 2030 peak sales forecast{" "}
                <span className="font-medium">
                  {formatBn(comp.peak_sales_bn || comp.peakSalesBn)}
                </span>
              </>
            )}
          </div>
        )}
        {comp.source && (
          <div className="text-[10px] text-gray-400 mt-1">
            Sources: {comp.source}
          </div>
        )}
      </AssumptionCard>

      {/* Differentiation Card */}
      <AssumptionCard>
        <CardHeader
          label="DIFFERENTIATION VERDICT"
          confidence={primary.comparatorConfidence || "high"}
          editLabel="Edit metrics"
          onEdit={() =>
            handleEdit(
              primary.name,
              "differentiation_verdict",
              primary.differentiationVerdict
            )
          }
        />
        <div className="text-[13px] text-gray-900 mb-1">
          <span className="font-medium">
            {(primary.differentiationVerdict || "").replace(/_/g, " ")}
          </span>
          {" "}
          &mdash; {betterCount} metric{betterCount !== 1 ? "s" : ""}{" "}
          meaningfully better, {worseCount} worse
        </div>
        {metrics.length > 0 && (
          <table className="w-full text-[11px] mt-1.5 border-collapse">
            <thead>
              <tr className="text-[10px] font-medium text-gray-500 border-b border-gray-200">
                <th className="text-left py-1 px-1.5 font-medium">Metric</th>
                <th className="text-left py-1 px-1.5 font-medium">
                  {primary.name || "Asset"}
                </th>
                <th className="text-left py-1 px-1.5 font-medium">
                  {comp.name || "Comparator"}
                </th>
                <th className="text-left py-1 px-1.5 font-medium">Direction</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m, i) => {
                const dir = m.direction || "";
                const isBetter =
                  dir === "better" ||
                  dir.includes("meaningful") ||
                  dir.includes("modest");
                return (
                  <tr
                    key={i}
                    className="border-b border-gray-100 last:border-0"
                  >
                    <td className="py-1 px-1.5 text-gray-600">{m.metric}</td>
                    <td className="py-1 px-1.5 text-gray-800">
                      {m.asset_value || m.assetValue}
                    </td>
                    <td className="py-1 px-1.5 text-gray-500">
                      {m.comparator_value || m.comparatorValue}
                    </td>
                    <td className="py-1 px-1.5">
                      <span
                        className={
                          isBetter
                            ? "text-green-600 font-medium"
                            : dir === "worse"
                            ? "text-red-600 font-medium"
                            : "text-gray-500"
                        }
                      >
                        {isBetter && "\u2191 "}
                        {dir === "worse" && "\u2193 "}
                        {dir}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </AssumptionCard>

      {/* PTRS Adjustment Card */}
      <AssumptionCard>
        <CardHeader
          label="PTRS ADJUSTMENT"
          confidence="high"
          editLabel="Override"
          onEdit={() => startEdit("ptrs", primary.ptrsAdjusted)}
        />
        {editingField === "ptrs" ? (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[13px] text-gray-600">Adjusted PTRS:</span>
            <input
              autoFocus
              className="text-xs border border-blue-300 rounded px-2 py-1 w-20"
              value={editDraft}
              onChange={(e) => setEditDraft(e.target.value)}
              onBlur={() => submitEdit(primary.name, "ptrs_adjusted")}
              onKeyDown={(e) =>
                e.key === "Enter" &&
                submitEdit(primary.name, "ptrs_adjusted")
              }
            />
          </div>
        ) : (
          <div className="text-[13px] text-gray-900 mb-1">
            Base Phase {primary.phase || "1"} oncology:{" "}
            <span className="font-medium">{formatPct(primary.ptrsBase)}</span>{" "}
            &rarr; Adjusted:{" "}
            <span className="font-medium">
              {formatPct(primary.ptrsAdjusted)}
            </span>
          </div>
        )}
        {breakdown.map((b, i) => (
          <div
            key={i}
            className="flex items-center justify-between py-0.5 text-[11px]"
          >
            <span className="text-gray-500">
              {(b.signal || "").replace(/_/g, " ")}
            </span>
            <span className="text-green-600 font-medium">
              +{typeof b.contribution === "number" && b.contribution < 1
                ? `${(b.contribution * 100).toFixed(0)}%`
                : `${b.contribution}%`}
            </span>
          </div>
        ))}
        <div className="mt-2 px-2.5 py-2 bg-amber-50 rounded-md text-[11px] text-amber-700 leading-relaxed">
          <span className="font-medium">
            Applied only to risk-adjusted view.
          </span>{" "}
          The if-succeed view assumes 100% probability — PTRS is set aside
          because the deal scenario presumes approval.
        </div>
      </AssumptionCard>

      {/* Peak Sales & NPV Table */}
      <AssumptionCard>
        <CardHeader
          label="PEAK SALES & NPV BY INDICATION"
          confidence="medium"
          editLabel="Adjust"
          onEdit={() =>
            handleEdit(primary.name, "peak_sales_with_displacement_bn", null)
          }
        />
        <table className="w-full text-[11px] mt-1.5 border-collapse">
          <thead>
            <tr className="text-[10px] font-medium text-gray-500 border-b border-gray-200">
              <th className="text-left py-1 px-1.5 font-medium">Indication</th>
              <th className="text-right py-1 px-1.5 font-medium">Peak $</th>
              <th className="text-right py-1 px-1.5 font-medium">PTRS</th>
              <th
                className="text-right py-1 px-1.5 font-medium"
                style={{ color: "#534AB7" }}
              >
                Risk-adj.
              </th>
              <th
                className="text-right py-1 px-1.5 font-medium"
                style={{ color: "#BA7517" }}
              >
                If-succeed
              </th>
            </tr>
          </thead>
          <tbody>
            {indications.map((ind, i) => (
              <tr
                key={i}
                className="border-b border-gray-100 last:border-0"
              >
                <td className="py-1 px-1.5 text-gray-700">{ind.name}</td>
                <td className="py-1 px-1.5 text-right tabular-nums text-gray-800">
                  {formatBn(ind.peakSalesWithDisplacementBn)}
                </td>
                <td className="py-1 px-1.5 text-right tabular-nums text-gray-800">
                  {formatPct(ind.ptrsAdjusted)}
                </td>
                <td
                  className="py-1 px-1.5 text-right tabular-nums font-medium"
                  style={{ color: "#534AB7" }}
                >
                  {formatBn(ind.peakSalesRiskAdjustedBn)}
                </td>
                <td
                  className="py-1 px-1.5 text-right tabular-nums font-medium"
                  style={{ color: "#BA7517" }}
                >
                  {formatBn(ind.peakSalesIfSucceedBn)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </AssumptionCard>

      {/* Likely Buyers Card */}
      {buyers.length > 0 && (
        <AssumptionCard>
          <CardHeader
            label="LIKELY BUYERS"
            confidence="medium"
            editLabel="Adjust"
            onEdit={() => handleEdit(null, "buyers", null)}
          />
          {buyers.map((b, i) => (
            <div
              key={i}
              className="grid items-center py-1.5 gap-x-2"
              style={{ gridTemplateColumns: "28px 1fr auto auto" }}
            >
              <span className="text-[10px] text-gray-400 text-center">
                {i + 1}
              </span>
              <div>
                <div className="text-[12px] font-medium text-gray-900">
                  {b.name}
                </div>
                <div className="text-[10px] text-gray-400 mt-px">
                  {b.rationale}
                </div>
              </div>
              <span className="text-[11px] text-gray-800 tabular-nums">
                {b.urgencyMultiplier}x
              </span>
              <span style={{ opacity: fireOpacity(b.urgencyMultiplier) }}>
                {"\uD83D\uDD25"}
              </span>
            </div>
          ))}
        </AssumptionCard>
      )}

      {/* Bidding Tension Card */}
      {tension && (
        <AssumptionCard>
          <CardHeader
            label="BIDDING TENSION SCORE"
            confidence={tension.confidence || "medium"}
            editLabel="Review signals"
            onEdit={() => handleEdit(null, "bidding_tension", null)}
          />
          <div className="text-[13px] text-gray-900 mb-1">
            <span className="font-medium">
              {tensionScore.toFixed(2)}
            </span>{" "}
            &rarr; applies{" "}
            <span className="font-medium">
              {(tensionPremium * 100).toFixed(0)}% bidding premium
            </span>{" "}
            to both views
          </div>
          {/* Segmented tension bar */}
          <div className="h-1.5 bg-gray-200 rounded-full mt-1.5 overflow-hidden flex">
            {Array.from({ length: tensionSegments }).map((_, i) => (
              <div
                key={i}
                className={`h-full ${
                  i < filledSegments ? "bg-amber-400" : "bg-gray-200"
                }`}
                style={{
                  width: `${100 / tensionSegments}%`,
                  borderRight:
                    i < tensionSegments - 1
                      ? "1px solid white"
                      : "none",
                }}
              />
            ))}
          </div>
          {/* Signal legend */}
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            {tensionSignals.map((s, i) => {
              const present =
                s.present !== undefined ? s.present : true;
              const label =
                s.label || (s.signal || "").replace(/_/g, " ");
              return (
                <span
                  key={i}
                  style={{ opacity: present ? 1 : 0.4 }}
                >
                  {present ? "\u2713" : "\u25CB"} {label}
                </span>
              );
            })}
          </div>
        </AssumptionCard>
      )}

      {/* Final Dual-Value Summary Card */}
      {scenarioStrategic && (
        <AssumptionCard gradient>
          <CardHeader label="FINAL STRATEGIC SCENARIO" />
          <div
            className="grid gap-3.5 mt-1.5 p-2.5 rounded-md"
            style={{
              gridTemplateColumns: "1fr 1fr",
              background: "var(--color-background-secondary, #f9fafb)",
            }}
          >
            {/* Risk-adjusted column */}
            <div className="flex flex-col gap-0.5">
              <div
                className="text-[10px] font-medium tracking-wider"
                style={{ color: "#534AB7" }}
              >
                RISK-ADJUSTED
              </div>
              <div className="text-[15px] font-medium text-gray-900 tabular-nums">
                {formatBn(scenarioStrategic.riskAdjustedBn)}
              </div>
              <div
                className="text-[10px] font-mono text-gray-400"
              >
                {scenarioStrategic.derivationString ||
                  (scenarioStandalone &&
                    `${formatBn(scenarioStandalone.riskAdjustedBn)} platform`)}
              </div>
            </div>
            {/* If-succeed column */}
            <div className="flex flex-col gap-0.5">
              <div
                className="text-[10px] font-medium tracking-wider"
                style={{ color: "#BA7517" }}
              >
                IF-SUCCEED
              </div>
              <div className="text-[15px] font-medium text-gray-900 tabular-nums">
                {formatBn(scenarioStrategic.ifSuccessBn)}
              </div>
              <div
                className="text-[10px] font-mono text-gray-400"
              >
                {scenarioStrategic.derivationString ||
                  (scenarioStandalone &&
                    `${formatBn(scenarioStandalone.ifSuccessBn)} platform`)}
              </div>
            </div>
          </div>
          <div className="mt-2 text-[11px] text-gray-500 leading-relaxed">
            Real deal lands between these two values — risk-adjusted reflects
            probability-weighted outcomes; if-succeed reflects the acquirer
            pricing in full approval confidence.
          </div>
        </AssumptionCard>
      )}
    </div>
  );
}
