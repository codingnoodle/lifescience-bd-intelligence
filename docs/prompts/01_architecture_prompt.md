# Prompt 1: Architecture Build

Copy this into Claude Code to scaffold the entire backend system in one shot.

---

## The Prompt

```
Build a pharma BD (business development) decision intelligence system that evaluates drug assets and produces deal valuations.

TECH STACK:
- Backend: Python, FastAPI, LangGraph (state graph), Claude Sonnet via LangChain
- Web search: Tavily API for real-time data (PubMed, ClinicalTrials.gov, FDA, EvaluatePharma)
- State management: LangGraph StateGraph with TypedDict shared state

ARCHITECTURE — 4-node sequential pipeline:
research_planner → science_agent → market_agent → synthesizer

Each node is a Python function that takes state, calls an LLM, and returns state updates.
Sequential because market_agent needs PTRS output from science_agent.

AGENT DESIGN — clear ownership boundaries:
1. Research planner (Haiku — fast/cheap): Parse free-text query into structured data
   - Classify query as "specific_asset" or "discovery" (pipeline scan)
   - Extract: asset_name, indications[] (name, phase, therapeutic_area, launch_year)
   - For discovery: extract scan_criteria (phase, TA, keywords)

2. Science agent (Sonnet): Assess the asset's intrinsic scientific properties
   - Search PubMed, ClinicalTrials.gov, conference abstracts via Tavily
   - Output structured positioning_profile: target, MOA, efficacy_metrics[], safety_metrics[], differentiation_claims[]
   - Identify de-risking signals from a FIXED vocabulary of 9 signals:
     orphan_drug, fast_track, breakthrough_designation, patients_dosed_50plus,
     patients_dosed_100plus, best_in_class_efficacy, fda_registrational_alignment,
     biomarker_defined_population, platform_multi_indication
   - LLM identifies signals, then PYTHON computes adjusted PTRS (never let LLM do math)
   - PTRS adjustment: start from base lookup table (phase × TA), add signal contributions, cap by phase
   - Output: positioning_profile, de_risking_signals, ptrs_base, ptrs_adjusted, ptrs_breakdown, science_score (0-10)

3. Market agent (Sonnet): Assess the competitive and commercial environment
   - Search for standard of care (SOC), competitor drugs, market sizing
   - Comparator discovery: find the dominant incumbent drug for this indication
   - Metric comparison: compare asset's efficacy/safety vs comparator using positioning_profile from science agent
   - Differentiation verdict (strict rubric):
     * best_in_class: 2+ metrics meaningfully better → 40-60% SOC displacement
     * better_in_class: 1 metric better → 20-40% displacement
     * new_class_creation: SOC is symptom-only, asset is disease-modifying → category expansion math
     * me_too: parity → standalone sizing only
     * worse_in_class: inferior → cap at niche
   - Output two peak sales: peak_sales_standalone_bn (own population) and peak_sales_with_displacement_bn (including SOC capture)
   - Reads ptrs_adjusted from state — does NOT recompute PTRS
   - Output: comparator, metric_comparison, differentiation_verdict, dual peak sales, market_score (0-10)

4. Synthesizer (Sonnet): Determine who will buy the asset and at what price
   - Buyer mapping: search for pharma companies with franchises in this TA
   - Use a hardcoded buyer urgency table (patent cliff data — refreshed quarterly):
     Merck 1.5x (Keytruda LOE 2028), BMS 1.3x, Pfizer 1.2x, etc.
   - Also a flush_buyer table for companies with excess capital:
     Eli Lilly 1.3x (GLP-1 cash), Novo Nordisk 1.25x
   - Combined urgency = max(cliff, flush) capped at 1.6x
   - Bidding tension score (0-1) from 4 signals (each 0.25):
     analyst coverage, stock movement, capable buyer count, TA deal velocity
   - Three-scenario valuation with DUAL VALUES (risk-adjusted + if-succeed):
     a. Standalone NPV: peak_standalone × revenue_multiplier × NPV_discount (with and without PTRS)
     b. Platform displacement: peak_displacement × revenue_multiplier × NPV_discount (with and without PTRS)
     c. Strategic deal price: peak_displacement × deal_multiple (varies by phase + urgency + bidding)
   - Deal multiple base: preclinical 0.5-1x, Ph1 1-1.5x, Ph1/2 1.5-2.5x, Ph2 2-3.5x, Ph3 3-5x
   - CVR detection: split upfront + CVR when platform has early-stage components
   - Output: buyers[], bidding_tension, 3 scenarios (each with if_success_bn + risk_adjusted_bn + derivation_string), composite_score, recommendation (GO/WATCH/NO-GO), summary

STATE SCHEMA (TypedDict):
- IndicationAnalysis: ~25 fields populated sequentially by each agent
- BDState: message, filters, drug_asset_name, indications[], scenarios, buyers, bidding_tension

API ENDPOINTS:
- POST /analyze — synchronous full analysis
- POST /analyze/stream — SSE streaming with progress events per agent node
- POST /recalculate — accepts state + user overrides, re-runs from market agent onward

KEY DESIGN PRINCIPLES:
- LLM reasons and extracts, Python calculates (PTRS math, NPV discount, revenue multiplier)
- Fixed vocabularies for structured extraction (de-risking signals, differentiation verdicts)
- No pre-computed dollar ranges in prompts (anti-anchoring — provide raw comparable deals instead)
- Every assumption must be traceable and editable
- Dual-view output: risk-adjusted shows expected value, if-succeed shows what buyers actually pay

Create the following files:
- backend/state.py (IndicationAnalysis TypedDict + BDState)
- backend/graph.py (StateGraph with 4 sequential nodes)
- backend/main.py (FastAPI with /analyze, /analyze/stream, /recalculate)
- backend/config.py (LLM initialization)
- backend/agents/research_planner.py
- backend/agents/science_agent.py
- backend/agents/market_agent.py
- backend/agents/synthesizer.py
- backend/utils/ptrs_lookup.py (base table + get_adjusted_ptrs with 9 signals)
- backend/utils/buyer_context.py (patent cliff + flush buyer tables)
```

---

## What this produces

After running this prompt, you should have a working backend with:
- A sequential LangGraph pipeline that compiles and runs
- Three specialized agents with clear ownership boundaries
- PTRS adjustment with de-risking signals
- Buyer mapping with urgency multipliers
- Three-scenario dual-view valuation
- SSE streaming endpoint for real-time progress

## Next step

Run Prompt 2 to build the frontend UI.
