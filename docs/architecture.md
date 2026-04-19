# BD Intelligence -- Multi-Agent System Architecture

## Overview

BD Intelligence is a four-agent sequential pipeline built on LangGraph that analyzes pharma drug assets for business development decisions. It produces per-indication science and market assessments, three-scenario valuations with dual-view (if-success vs. risk-adjusted), buyer mapping, and bidding tension analysis.

**Models used:**
- Research planner: Claude Haiku 4.5 (via AWS Bedrock or Anthropic API)
- Science agent, market agent, synthesizer: Claude Sonnet 4 (via AWS Bedrock or Anthropic API)

**External data:** Tavily search API (used directly by science agent, market agent, and synthesizer -- no MCP servers are active).

---

## 1. LangGraph Flow

Sequential pipeline. Market agent reads `ptrs_adjusted` written by science agent, so the agents cannot run in parallel.

```mermaid
graph TD
    __start__([START]):::first
    research_planner["research_planner\n(Haiku 4.5)\nParse message, extract\nasset + indications"]
    science_agent["science_agent\n(Sonnet 4 + Tavily)\nPositioning profile,\nde-risking signals,\nPTRS, science score"]
    market_agent["market_agent\n(Sonnet 4 + Tavily)\nComparator, differentiation,\npeak sales, market score"]
    synthesizer["synthesizer\n(Sonnet 4 + Tavily)\nBuyer mapping, bidding tension,\n3-scenario valuation,\ncomposite score"]
    __end__([END]):::last

    __start__ --> research_planner
    research_planner --> science_agent
    science_agent --> market_agent
    market_agent --> synthesizer
    synthesizer --> __end__

    classDef default fill:#f2f0ff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc
```

---

## 2. Data Flow: User to API to Graph to Frontend

```mermaid
flowchart TD
    U["User (browser)"]
    FS["FilterSidebar\nPhase / Launch Year / TA"]
    CW["ChatWindow\nPOST /analyze/stream"]

    U -->|"types asset query"| CW
    U -->|"sets filter chips"| FS
    FS -->|"appends filters dict"| CW

    subgraph API["FastAPI :8000"]
        direction TB
        INIT["BDState\nmessage + filters"]

        subgraph GRAPH["LangGraph -- StateGraph(BDState)"]
            direction TB
            RP["research_planner"]
            SA["science_agent"]
            MA["market_agent"]
            SY["synthesizer"]
            RP --> SA --> MA --> SY
        end

        INIT --> RP
        SY --> BUILD["_build_result()\nsnake_case -> camelCase\nconversion"]
        BUILD --> RESULT["AnalyzeResponse JSON"]
    end

    CW -->|"POST {message, filters}"| INIT
    RESULT -->|"SSE events:\nprogress per node,\nthen done with payload"| CW

    subgraph UI["Frontend Components"]
        RC["ResultCard\nGO / WATCH / NO-GO badge\nComposite, science, market scores"]
        VW["ValuationWaterfall\n3 scenarios x 2 views\n(if-success / risk-adjusted)"]
        AP["AssumptionsPanel\nEditable PTRS, verdict,\npeak sales -> POST /recalculate"]
        RT["ReasoningTrace\nAgent step log"]
        DC["DiscoveryCard\nPipeline scan results"]
    end

    CW --> RC
    CW --> VW
    CW --> AP
    CW --> RT
    CW --> DC
```

---

## 3. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check (returns version 0.3.0) |
| POST | `/analyze` | Full synchronous analysis; returns `AnalyzeResponse` |
| POST | `/analyze/stream` | SSE streaming; emits `progress` events per node, then `done` with full result. Also handles `discovery` queries (pipeline scan mode). |
| POST | `/recalculate` | Re-runs from market agent onward with user overrides (e.g., edited PTRS or verdict from AssumptionsPanel). Skips research planner and science agent. |

### Request/Response Models

- **AnalyzeRequest**: `{ message: str, filters: dict }`
- **RecalculateRequest**: `{ asset_name: str, indications: list[dict], overrides: dict }`
- **AnalyzeResponse**: `{ message: str, result: AnalyzeResult | null }`
- **AnalyzeResult**: contains `assetName`, `compositeScore`, `scienceScore`, `marketScore`, `recommendation`, `indications[]`, three scenario objects, `buyers[]`, `biddingTension`, `summary`

---

## 4. State Schema

### BDState (top-level graph state)

```mermaid
classDiagram
    class BDState {
        <<TypedDict>>
        %% Input
        +str message
        +dict filters
        %% Research planner writes
        +str drug_asset_name
        +list~IndicationAnalysis~ indications
        +str clarification_needed
        +str research_plan
        %% Synthesizer writes
        +float composite_score
        +float science_score
        +float market_score
        +str recommendation
        +str summary
        +dict scenario_standalone
        +dict scenario_displacement
        +dict scenario_strategic
        +list~dict~ buyers
        +dict bidding_tension
        %% Metadata
        +list~dict~ messages
        +list~str~ errors
    }

    class IndicationAnalysis {
        <<TypedDict>>
        %% Research planner writes
        +str name
        +str phase
        +str therapeutic_area
        +int launch_year
        %% Science agent writes
        +dict positioning_profile
        +list~str~ de_risking_signals
        +float ptrs_base
        +float ptrs_adjusted
        +list~dict~ ptrs_breakdown
        +float science_score
        +str science_rationale
        %% Market agent writes
        +dict comparator
        +list~dict~ metric_comparison
        +str differentiation_verdict
        +float peak_sales_standalone_bn
        +float peak_sales_with_displacement_bn
        +float market_score
        +str market_rationale
        +str comparator_confidence
        %% Synthesizer computes
        +float peak_sales_risk_adjusted_bn
        +float peak_sales_if_succeed_bn
    }

    class ScenarioDict {
        <<dict>>
        +float if_success_bn
        +float risk_adjusted_bn
        +float deal_multiple
        +float predicted_upfront_bn
        +float predicted_cvr_bn
        +str derivation_string
    }

    class BuyerDict {
        <<dict>>
        +str name
        +float urgency_multiplier
        +str rationale
        +str confidence
    }

    class BiddingTensionDict {
        <<dict>>
        +float score
        +float premium
        +list~dict~ signals
        +str confidence
    }

    BDState "1" --> "*" IndicationAnalysis : indications
    BDState "1" --> "3" ScenarioDict : scenario_standalone\nscenario_displacement\nscenario_strategic
    BDState "1" --> "*" BuyerDict : buyers
    BDState "1" --> "1" BiddingTensionDict : bidding_tension
```

### Who writes what

| Field(s) | Written by |
|----------|-----------|
| `name`, `phase`, `therapeutic_area`, `launch_year` | research_planner |
| `positioning_profile`, `de_risking_signals`, `ptrs_base`, `ptrs_adjusted`, `ptrs_breakdown`, `science_score`, `science_rationale` | science_agent |
| `comparator`, `metric_comparison`, `differentiation_verdict`, `peak_sales_standalone_bn`, `peak_sales_with_displacement_bn`, `market_score`, `market_rationale`, `comparator_confidence` | market_agent |
| `peak_sales_risk_adjusted_bn`, `peak_sales_if_succeed_bn` (per-indication); all scenario dicts, `buyers`, `bidding_tension`, `composite_score`, `recommendation`, `summary` | synthesizer |

---

## 5. Valuation: Dual-View Three-Scenario Model

Every scenario produces two numbers side-by-side:
- **if_success_bn**: value assuming the drug succeeds (no PTRS discount)
- **risk_adjusted_bn**: expected value with PTRS probability discount

The gap between them shows the clinical risk.

```mermaid
flowchart LR
    subgraph PerIndication["Per-Indication Inputs"]
        PEAK_S["peak_sales_standalone_bn\n(annual, undiscounted)"]
        PEAK_D["peak_sales_with_displacement_bn\n(annual, undiscounted)"]
        PTRS["ptrs_adjusted\n(base + de-risking signals,\ncapped by phase)"]
        NPV["npv_discount\n= 1 / 1.10^years_to_launch"]
        REVMUL["revenue_multiplier\n4.0 standard\n5.0 orphan/rare\n3.0 competitive"]
    end

    subgraph Standalone["Scenario A: Standalone"]
        S_CV["commercial_value =\npeak_standalone x rev_mult"]
        S_IF["if_success =\nsum(cv x npv)"]
        S_RA["risk_adjusted =\nsum(cv x ptrs x npv)"]
        S_CV --> S_IF
        S_CV --> S_RA
        NPV --> S_IF
        NPV --> S_RA
        PTRS --> S_RA
        PEAK_S --> S_CV
        REVMUL --> S_CV
    end

    subgraph Displacement["Scenario B: Displacement"]
        D_CV["commercial_value =\npeak_displacement x rev_mult"]
        D_IF["if_success =\nsum(cv x npv)\n+ optionality premium"]
        D_RA["risk_adjusted =\nsum(cv x ptrs x npv)\n+ optionality premium"]
        D_CV --> D_IF
        D_CV --> D_RA
        NPV --> D_IF
        NPV --> D_RA
        PTRS --> D_RA
        PEAK_D --> D_CV
        REVMUL --> D_CV
    end

    subgraph Strategic["Scenario C: Strategic"]
        DM["deal_multiple =\nbase(phase)\n+ urgency_adj\n+ bidding_adj\n+ differentiation_adj"]
        ST_IF["if_success =\nsum(peak_displacement)\nx deal_multiple"]
        ST_RA["risk_adjusted =\nif_success\nx weighted_avg_ptrs"]
        CVR["CVR split:\nupfront + contingent\n(20-40% if applicable)"]
        DM --> ST_IF
        PEAK_D --> ST_IF
        ST_IF --> ST_RA
        PTRS --> ST_RA
        ST_IF --> CVR
    end
```

### Deal Multiple Calculation (Strategic Scenario)

Base multiple by phase:

| Phase | Base Multiple |
|-------|-------------|
| Preclinical | 0.5 -- 1.0x |
| Phase 1 | 1.0 -- 1.5x |
| Phase 1/2 | 1.5 -- 2.5x |
| Phase 2 | 2.0 -- 3.5x |
| Phase 3 | 3.0 -- 5.0x |
| Marketed | 4.0 -- 8.0x |

Adjustments applied on top of base:

| Condition | Adjustment |
|-----------|-----------|
| Top buyer urgency >= 1.3 | +0.3x |
| Top buyer urgency >= 1.5 | +0.5x |
| Bidding tension >= 0.6 | +0.3x |
| Bidding tension >= 0.8 | +0.5x |
| best_in_class or new_class_creation | +0.3x |
| Platform / multi-indication | +0.3x |
| me_too or worse_in_class | -0.5x |

---

## 6. PTRS Computation

PTRS (Probability of Technical and Regulatory Success) is computed in Python (not by the LLM) via `ptrs_lookup.py`:

1. **Base PTRS**: looked up from `ptrs_table.json` by normalized `phase` x `therapeutic_area`
2. **De-risking adjustment**: additive bonuses from a fixed vocabulary of 9 signals, identified by the science agent LLM
3. **Cap**: hard ceiling per phase prevents unrealistic values

De-risking signals and their contributions:

| Signal | Contribution |
|--------|-------------|
| orphan_drug | +0.02 |
| fast_track | +0.03 |
| breakthrough_designation | +0.05 |
| patients_dosed_50plus | +0.03 |
| patients_dosed_100plus | +0.05 (mutually exclusive with 50plus) |
| best_in_class_efficacy | +0.07 |
| fda_registrational_alignment | +0.04 |
| biomarker_defined_population | +0.03 |
| platform_multi_indication | +0.02 |

Phase caps: preclinical 0.20, ind_enabling 0.25, phase1 0.45, phase1_2 0.55, phase2 0.65, phase2b 0.70, phase3 0.85, nda_submitted 0.95.

---

## 7. Scoring and Recommendation

```
composite_score = 0.60 x mean(science_scores) + 0.40 x mean(market_scores)
```

Adjusted +/- 1 for portfolio breadth (more indications = higher ceiling).

| Score | Recommendation |
|-------|---------------|
| >= 6.5 | **GO** |
| 4.5 -- 6.4 | **WATCH** |
| < 4.5 | **NO-GO** |

---

## 8. Buyer Analysis

The synthesizer runs four Tavily searches to gather buyer intelligence:
1. **Franchise fit**: which pharma companies have active franchises in the relevant TAs
2. **Deal velocity**: recent M&A activity for known patent-cliff buyers
3. **Analyst sentiment**: analyst coverage and price targets for the asset
4. **TA deal velocity**: total M&A volume in the therapeutic area

It combines this with a static buyer urgency table (`buyer_context.py`) containing patent cliff pressure and flush capital data for major pharma companies.

**Bidding tension** is scored 0--1 from four signals (each up to 0.25):
- Analyst coverage (3+ distinct mentions)
- Stock/deal movement (recent data readout buzz)
- Capable buyer count (3+ buyers with urgency >= 1.1)
- TA deal velocity (5+ deals > $1B in 12 months)

Premium mapping: 0.0--0.3 = 0%, 0.3--0.6 = 15%, 0.6--0.8 = 25%, 0.8--1.0 = 35%.

---

## 9. Frontend Components

| Component | Purpose |
|-----------|---------|
| `ChatWindow` | Main input; sends POST to `/analyze/stream`, displays SSE progress, routes result to child components |
| `ResultCard` | GO/WATCH/NO-GO badge, composite score, science and market score bars |
| `ValuationWaterfall` | Three scenarios (standalone, displacement, strategic) with if-success and risk-adjusted columns |
| `AssumptionsPanel` | Editable assumptions (PTRS, verdict, peak sales); triggers POST to `/recalculate` to re-run from market agent onward |
| `FilterSidebar` | Phase, launch year, and therapeutic area filter chips |
| `ReasoningTrace` | Displays agent step-by-step progress log |
| `DiscoveryCard` | Shows pipeline scan results when query type is "discovery" |
| `GuidedEntryForm` | Structured input form for asset details |

---

## 10. Discovery Mode

The `/analyze/stream` endpoint supports a second query type: **discovery**. When the research planner classifies the user message as a discovery query (e.g., "top Phase 2 oncology assets"), the stream endpoint:

1. Calls `run_discovery_agent(scan_criteria)` instead of running the full graph
2. Returns a list of candidate assets via the `DiscoveryCard` component
3. Users can then click "Run full diligence" on any candidate to trigger a full analysis

---

## 11. `/recalculate` Flow

When a user edits an assumption in the AssumptionsPanel:

1. Frontend sends current indications (with all science fields) plus the override to POST `/recalculate`
2. Backend applies the override to the specified indication field
3. Re-runs `run_market_agent()` (which reads the updated `ptrs_adjusted` and other science fields)
4. Re-runs `run_synthesizer()` on the market-enriched output
5. Returns the same `AnalyzeResult` shape as `/analyze`

This avoids a full pipeline re-run -- science agent results are preserved, only market and synthesis are recomputed.
