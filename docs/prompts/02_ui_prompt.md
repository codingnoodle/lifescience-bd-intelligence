# Prompt 2: Frontend UI Build

Copy this into Claude Code to build the React frontend.

---

## The Prompt

```
Build a React + Vite + Tailwind CSS frontend for the BD intelligence system.
The backend is already running at http://localhost:8000.

LAYOUT:
- Full-screen app with a left sidebar (FilterSidebar, 224px wide) and main area (ChatWindow)
- App.jsx holds shared state: filters{} and chatInput string

FILTER SIDEBAR (FilterSidebar.jsx):
- Three filter sections with clickable chip/pill buttons:
  * PHASE: Preclinical, Phase 1, Phase 2, Phase 3, NDA
  * LAUNCH YEAR: 2026, 2027, 2028, 2029, 2030, 2032+
  * THERAPEUTIC AREA: chips with deal volume hints, e.g. "Oncology / Hematology ($89B)"
- "Run scan with filters" button that assembles a natural language query from active chips
- RECENT ASSETS section with 3-4 clickable examples that prefill the chat input
- Chip component: rounded pill, blue when active, gray when inactive, shows optional hint text

CHAT WINDOW (ChatWindow.jsx):
- Welcome screen (shown when no messages):
  * Hero: "Pharma BD Decision Intelligence" title + subtitle explaining what it does
  * Three value prop cards with icons (dual-view valuation, editable assumptions, buyer mapping)
  * Four use-case cards in a 2x2 grid:
    1. "Deep-dive a known asset" — prefills chat input
    2. "Explore a preclinical asset" — opens guided entry form
    3. "Scan a therapeutic area" — prefills scan query
    4. "Benchmark vs recent deals" — prefills benchmark query
  * Quick-start pills: 3 example queries that fire immediately on click
  * Footer disclaimer about estimates
- Chat mode:
  * User bubbles (right, blue) and bot bubbles (left, gray border)
  * Bot bubbles contain ResultCard when result is present
  * Streaming: POST to /analyze/stream, parse SSE events
    - "progress" events show animated dots + status message
    - "done" event adds bot message with result
  * Input bar at bottom with Send button

RESULT CARD (ResultCard.jsx):
- Header: asset name + GO/WATCH/NO-GO badge with score
- Score bars: Science and Market (0-10, colored progress bars)
- ValuationWaterfall component (always visible)
- Tab bar: "Waterfall" | "Assumptions" — switches content below
- GP summary paragraph at bottom

VALUATION WATERFALL (ValuationWaterfall.jsx):
- Three-option toggle: "Risk-adjusted" / "If-succeed" / "Side-by-side" (default)
- Two waterfall cards:
  * Risk-adjusted (purple #534AB7 family): 3 scenario rows with purple math text
  * If-succeed (amber #BA7517 family): 3 scenario rows with amber math text
- Each scenario row: left (name + step badge + derivation formula), right (dollar value + delta)
- Stacked bar chart below each waterfall
- Side-by-side comparison table with both columns

ASSUMPTIONS PANEL (AssumptionsPanel.jsx):
- Card sections: Comparator, Differentiation (metric table), PTRS (signal breakdown with warning callout),
  Peak Sales (5-column table: indication/peak/PTRS/risk-adj purple/if-succeed amber),
  Likely Buyers (ranked with urgency), Bidding Tension (segmented bar), Final Summary (dual-value gradient card)
- Each card has confidence badge (high=green, medium=amber) and edit button
- Editing triggers POST to /recalculate endpoint

GUIDED ENTRY FORM (GuidedEntryForm.jsx):
- For preclinical assets with limited public data
- Fields: asset name, sponsor, modality dropdown, target/MOA, therapeutic area, indications (dynamic rows), differentiation textarea
- Submit assembles natural language query from form fields

The API returns this shape for results:
{
  assetName, compositeScore, scienceScore, marketScore, recommendation,
  indications: [{name, phase, ptrsAdjusted, ptrsBase, ptrsBreakdown, comparator, metricComparison,
    differentiationVerdict, peakSalesStandaloneBn, peakSalesWithDisplacementBn,
    peakSalesRiskAdjustedBn, peakSalesIfSucceedBn, scienceScore, marketScore}],
  scenarioStandalone: {ifSuccessBn, riskAdjustedBn, derivationString},
  scenarioDisplacement: {ifSuccessBn, riskAdjustedBn, derivationString},
  scenarioStrategic: {ifSuccessBn, riskAdjustedBn, dealMultiple, predictedUpfrontBn, predictedCvrBn, derivationString},
  buyers: [{name, urgencyMultiplier, rationale, confidence}],
  biddingTension: {score, premium, signals[], confidence},
  summary
}

Use Tailwind utility classes. No external component libraries. Use lucide-react for icons.
```

---

## What this produces

A complete React frontend with:
- Welcome screen with onboarding flow
- Real-time SSE streaming from the analysis pipeline
- Dual-view valuation waterfall (risk-adjusted vs if-succeed)
- Editable assumptions panel with recalculate capability
- Filter sidebar for therapeutic area scanning

## Next step

Run Prompt 3 to validate the system against real deals.
