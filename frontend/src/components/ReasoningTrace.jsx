import React from "react";

function fmt(v) {
  if (v == null) return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return `$${n.toFixed(1)}B`;
}

function pct(v) {
  if (v == null) return "—";
  return `${Math.round(Number(v) * 100)}%`;
}

function Step({ action, children }) {
  return (
    <div className="ml-0.5 mb-2 border-l border-gray-200 pl-2.5 py-0.5">
      <div className="text-[11px] text-gray-400 font-mono mb-0.5">
        {"-> "}{action}
      </div>
      <div className="text-xs text-gray-800 leading-relaxed">{children}</div>
    </div>
  );
}

function DualBoxes({ leftLabel, leftValue, leftSub, rightLabel, rightValue, rightSub }) {
  return (
    <div className="grid grid-cols-2 gap-3 mt-2">
      <div className="bg-white border border-gray-200 rounded-md px-2.5 py-2">
        <div className="text-[10px] font-medium tracking-wide mb-1" style={{ color: "#534AB7" }}>
          {leftLabel}
        </div>
        <div className="text-[15px] font-medium text-gray-900 tabular-nums mb-0.5">
          {leftValue}
        </div>
        <div className="text-[10px] text-gray-400 font-mono">{leftSub}</div>
      </div>
      <div className="bg-white border border-gray-200 rounded-md px-2.5 py-2">
        <div className="text-[10px] font-medium tracking-wide mb-1" style={{ color: "#BA7517" }}>
          {rightLabel}
        </div>
        <div className="text-[15px] font-medium text-gray-900 tabular-nums mb-0.5">
          {rightValue}
        </div>
        <div className="text-[10px] text-gray-400 font-mono">{rightSub}</div>
      </div>
    </div>
  );
}

function ConclusionBox({ color, children }) {
  return (
    <div
      className="bg-gray-50 rounded-md px-2.5 py-2 mt-2 text-xs text-gray-800 leading-relaxed"
      style={{ borderLeft: `2px solid ${color}` }}
    >
      <div className="text-[10px] font-medium text-gray-400 tracking-wide mb-1">CONCLUSION</div>
      {children}
    </div>
  );
}

const PHASES = [
  { key: "science", dot: "#534AB7", letter: "S", label: "SCIENCE AGENT" },
  { key: "market", dot: "#0F6E56", letter: "M", label: "MARKET AGENT" },
  { key: "synthesis", dot: "#BA7517", letter: "B", label: "SYNTHESIS AGENT" },
];

export default function ReasoningTrace({ result }) {
  if (!result) return null;

  const ind = result.indications?.[0] || {};
  const buyers = result.buyers || [];
  const tension = result.biddingTension || {};
  const scStandalone = result.scenarioStandalone || {};
  const scDisplacement = result.scenarioDisplacement || {};
  const scStrategic = result.scenarioStrategic || {};

  const riskAdj = scStrategic.riskAdjustedBn;
  const ifSucceed = scStrategic.ifSuccessBn;

  const topBuyer = buyers[0] || {};
  const runnersUp = buyers.slice(1);

  const urgency = topBuyer.urgencyMultiplier ?? 1;
  const premium = tension.premium ?? 0;
  const multiplier = urgency * (1 + premium);

  const displacementRiskAdj = scDisplacement.riskAdjustedBn;
  const displacementIfSucceed = scDisplacement.ifSuccessBn;

  // Diagnostic: compare to a known deal price if available
  const realDealPrice = result.realDealPriceBn;
  let diagnosticNode = null;
  if (realDealPrice != null && ifSucceed != null) {
    const delta = ((realDealPrice - ifSucceed) / ifSucceed) * 100;
    const direction = delta >= 0 ? "above" : "below";
    const absDelta = Math.abs(delta).toFixed(0);
    diagnosticNode = (
      <div className="mt-2 px-2 py-1.5 bg-red-50 text-red-700 rounded-md text-[11px]">
        <span className="font-semibold">Real deal {fmt(realDealPrice)}</span> sits ~{absDelta}%{" "}
        {direction} if-succeed estimate.{" "}
        {delta > 20
          ? `Likely driver: top buyer's desperation paid over the rational if-succeed ceiling. Consider tuning urgency cap higher for acute-LOE buyers.`
          : delta < -10
            ? `The model may be overvaluing the asset. Consider reviewing comparator assumptions.`
            : `Estimate is within reasonable range of the observed deal price.`}
      </div>
    );
  }

  return (
    <div className="py-1 text-[13px]">
      {/* Header */}
      <div className="mb-4">
        <div className="text-sm font-medium text-gray-900 mb-0.5">
          How the agents got to {fmt(riskAdj)} risk-adj / {fmt(ifSucceed)} if-succeed
        </div>
        <div className="text-[11px] text-gray-400">
          {[
            ind.assetName,
            ind.company,
            ind.indication,
            ind.phase,
            realDealPrice != null ? `Real deal ${fmt(realDealPrice)}` : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </div>
      </div>

      {/* Framing callout */}
      <div className="bg-blue-50 border border-blue-200 rounded-md px-3 py-2.5 mb-3.5 text-xs text-blue-700 leading-relaxed">
        The agents compute both views in parallel.{" "}
        <span className="font-semibold">Risk-adjusted</span> uses PTRS discounting to reflect true
        expected value to a disciplined investor.{" "}
        <span className="font-semibold">If-succeed</span> assumes approval and models the buyer's
        strategic logic — usually closer to the actual deal price because buyers absorb the risk.
      </div>

      {/* Trace body */}
      <div className="bg-white border border-gray-200 rounded-lg px-4 py-4">
        {/* ── PHASE 1: SCIENCE ── */}
        <div className="relative pl-6 mb-4">
          {/* Connecting line */}
          <div
            className="absolute left-[7px] top-[18px] bottom-[-18px] w-px bg-gray-200"
            aria-hidden="true"
          />
          {/* Dot */}
          <div
            className="absolute left-0 top-1 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-medium text-white"
            style={{ backgroundColor: "#534AB7" }}
          >
            S
          </div>

          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-1">
            SCIENCE AGENT
          </div>
          <div className="text-[13px] font-medium text-gray-900 mb-1.5">
            Assessed the asset and quantified its de-risking
          </div>

          <Step action="Searched ClinicalTrials.gov">
            {ind.positioningProfile ? (
              <span>
                {ind.positioningProfile.trialName && (
                  <>{ind.positioningProfile.trialName} trial, </>
                )}
                {ind.positioningProfile.target && (
                  <>
                    Target: <span className="font-medium">{ind.positioningProfile.target}</span>,{" "}
                  </>
                )}
                {ind.positioningProfile.moa && (
                  <>
                    MOA: <span className="font-medium">{ind.positioningProfile.moa}</span>.{" "}
                  </>
                )}
                {ind.positioningProfile.keyEfficacy && (
                  <>
                    Key efficacy:{" "}
                    <span className="font-medium">{ind.positioningProfile.keyEfficacy}</span>.
                  </>
                )}
              </span>
            ) : (
              <span className="text-gray-400">No positioning profile available.</span>
            )}
          </Step>

          <Step action="Extracted de-risking signals">
            {ind.deRiskingSignals?.length > 0 ? (
              <span>{ind.deRiskingSignals.join(", ")}.</span>
            ) : (
              <span className="text-gray-400">No de-risking signals identified.</span>
            )}
          </Step>

          <Step action="Computed PTRS">
            Phase base PTRS: <span className="font-medium">{pct(ind.ptrsBase)}</span>. With signal
            adjustments:{" "}
            <span className="font-medium">{pct(ind.ptrsAdjusted)} adjusted</span>.
            {ind.ptrsBreakdown && (
              <span className="text-gray-400 text-[10px] ml-1">({ind.ptrsBreakdown})</span>
            )}
          </Step>

          <ConclusionBox color="#534AB7">
            PTRS matters only for the risk-adjusted view. The if-succeed view sets PTRS aside — it
            asks "how valuable would this be if it works?"
            <DualBoxes
              leftLabel="RISK-ADJ. PTRS"
              leftValue={pct(ind.ptrsAdjusted)}
              leftSub="applied to NPV"
              rightLabel="IF-SUCCEED PTRS"
              rightValue="100%"
              rightSub="assumes approval"
            />
          </ConclusionBox>
        </div>

        {/* ── PHASE 2: MARKET ── */}
        <div className="relative pl-6 mb-4">
          <div
            className="absolute left-[7px] top-[18px] bottom-[-18px] w-px bg-gray-200"
            aria-hidden="true"
          />
          <div
            className="absolute left-0 top-1 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-medium text-white"
            style={{ backgroundColor: "#0F6E56" }}
          >
            M
          </div>

          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-1">
            MARKET AGENT
          </div>
          <div className="text-[13px] font-medium text-gray-900 mb-1.5">
            Sized the opportunity under both risk lenses
          </div>

          <Step action={`Identified comparator`}>
            {ind.comparator ? (
              <>
                Identified <span className="font-medium">{ind.comparator.name || ind.comparator}</span>
                {ind.comparator.peakSalesBn != null && (
                  <> as dominant incumbent. Peak sales forecast:{" "}
                    <span className="font-medium">{fmt(ind.comparator.peakSalesBn)}</span>.
                  </>
                )}
                {ind.metricComparison && (
                  <span className="text-gray-400 text-[10px] ml-1">
                    ({ind.metricComparison})
                  </span>
                )}
              </>
            ) : (
              <span className="text-gray-400">No comparator identified.</span>
            )}
          </Step>

          <Step action="Applied differentiation rubric">
            {ind.differentiationVerdict ? (
              <>
                Verdict: <span className="font-medium">{ind.differentiationVerdict}</span>.
                {ind.differentiationVerdict.toLowerCase().includes("best") &&
                  " Unlocks displacement scenario."}
              </>
            ) : (
              <span className="text-gray-400">No differentiation verdict.</span>
            )}
          </Step>

          <Step action="Computed platform NPV both ways">
            {scStandalone.derivationString || scDisplacement.derivationString ? (
              <>
                {scStandalone.derivationString && <>{scStandalone.derivationString}. </>}
                {scDisplacement.derivationString && <>{scDisplacement.derivationString}.</>}
              </>
            ) : (
              <>
                Standalone peak sales: {fmt(ind.peakSalesStandaloneBn)}, with displacement:{" "}
                {fmt(ind.peakSalesWithDisplacementBn)}, discounted for launch timing.
              </>
            )}
          </Step>

          <ConclusionBox color="#0F6E56">
            Peak sales potential is the same in both views. The gap is entirely from PTRS
            discounting. Risk-adjusted captures expected value today; if-succeed captures value at
            the negotiation table.
            <DualBoxes
              leftLabel="RISK-ADJ. PLATFORM"
              leftValue={fmt(displacementRiskAdj)}
              leftSub={
                scDisplacement.derivationString
                  ? `peak x ${pct(ind.ptrsAdjusted)} x discount`
                  : `peak x ${pct(ind.ptrsAdjusted)} x discount`
              }
              rightLabel="IF-SUCCEED PLATFORM"
              rightValue={fmt(displacementIfSucceed)}
              rightSub="peak x discount only"
            />
          </ConclusionBox>
        </div>

        {/* ── PHASE 3: SYNTHESIS ── */}
        <div className="relative pl-6">
          {/* No connecting line on last phase */}
          <div
            className="absolute left-0 top-1 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-medium text-white"
            style={{ backgroundColor: "#BA7517" }}
          >
            B
          </div>

          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-1">
            SYNTHESIS AGENT
          </div>
          <div className="text-[13px] font-medium text-gray-900 mb-1.5">
            Layered in buyer premium — applied to both views
          </div>

          <Step action="Mapped capable buyers">
            {topBuyer.name ? (
              <>
                Top buyer: <span className="font-medium">{topBuyer.name}</span>, urgency{" "}
                <span className="font-medium">{topBuyer.urgencyMultiplier}x</span>
                {topBuyer.rationale && <> ({topBuyer.rationale})</>}.
                {runnersUp.length > 0 && (
                  <>
                    {" "}
                    Runners up:{" "}
                    {runnersUp
                      .map((b) => `${b.name} ${b.urgencyMultiplier}x`)
                      .join(", ")}
                    .
                  </>
                )}
              </>
            ) : (
              <span className="text-gray-400">No buyer mapping available.</span>
            )}
          </Step>

          <Step action="Scored bidding tension">
            {tension.signals?.length > 0 && (
              <>
                {tension.signals.length} signals present: {tension.signals.join(", ")}.{" "}
              </>
            )}
            Score <span className="font-medium">{tension.score ?? "—"}</span>
            {" -> "}
            <span className="font-medium">{pct(tension.premium)} premium</span>.
          </Step>

          <Step action="Multiplied through both views">
            Strategic multiplier = {urgency} x {(1 + premium).toFixed(2)} ={" "}
            <span className="font-medium">{multiplier.toFixed(2)}x</span>. Applied identically to
            risk-adj. and if-succeed platform values.
          </Step>

          <ConclusionBox color="#BA7517">
            {realDealPrice != null ? (
              <>
                The {fmt(realDealPrice)} real deal sits between our two views. This is the signal
                that the buyer priced the deal closer to the if-succeed case, absorbing the PTRS risk
                themselves — consistent with strategic buyers who need the asset to work.
              </>
            ) : (
              <>
                The real deal value sits between these two views. Risk-adjusted reflects disciplined
                expected value; if-succeed reflects what a strategic buyer will actually pay.
              </>
            )}
            <DualBoxes
              leftLabel="RISK-ADJ. STRATEGIC"
              leftValue={fmt(riskAdj)}
              leftSub={`${fmt(displacementRiskAdj)} x ${multiplier.toFixed(2)}x`}
              rightLabel="IF-SUCCEED STRATEGIC"
              rightValue={fmt(ifSucceed)}
              rightSub={`${fmt(displacementIfSucceed)} x ${multiplier.toFixed(2)}x`}
            />
            {diagnosticNode}
          </ConclusionBox>
        </div>

        {/* Expand hint */}
        <div className="text-[11px] text-blue-600 cursor-pointer mt-3 inline-block">
          Ask: "Why is if-succeed closer to the real deal?" or "Recompute with {topBuyer.name || "top buyer"} urgency at {((topBuyer.urgencyMultiplier || 1.5) + 0.3).toFixed(1)}x"
        </div>
      </div>
    </div>
  );
}
