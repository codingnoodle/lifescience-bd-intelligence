# BD Intelligence — Multi-Agent System Architecture

## LangGraph Flow (auto-generated from compiled graph)

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
    __start__([START]):::first
    research_planner(research_planner)
    science_agent(science_agent)
    market_agent(market_agent)
    synthesizer(synthesizer)
    __end__([END]):::last

    __start__ --> research_planner;
    research_planner --> science_agent;
    science_agent --> market_agent;
    market_agent --> synthesizer;
    synthesizer --> __end__;

    classDef default fill:#f2f0ff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc
```

---

## Full Data Flow Diagram

```mermaid
flowchart TD
    U(["👤 VC Associate\n(browser)"])
    FS["FilterSidebar\nPhase · Launch Year · TA"]
    CW["ChatWindow\nfetch POST /analyze/stream"]

    U -->|types asset + indication| CW
    U -->|clicks chips| FS
    FS -->|appends to input| CW

    subgraph API["FastAPI  :8000  /analyze/stream  →  SSE"]
        direction TB
        INIT["BDState\n{ message, filters }"]

        subgraph LG["LangGraph — StateGraph(BDState)"]
            direction TB

            RP["🔵 research_planner\n─────────────────\nModel: Haiku 4.5\nTask: parse free text\n─────────────────\nOUT: asset_name\n     indications[]\n     ptrs_score (lookup)"]

            SA["🟢 science_agent\n─────────────────\nModel: Sonnet 4\nSearch: Tavily\n  · PubMed / FDA\n  · NEJM / Lancet\n  · ClinicalTrials.gov\n─────────────────\nOUT: science_score 0-10\n     science_rationale"]

            MA["🟣 market_agent\n─────────────────\nModel: Sonnet 4\nSearch: Tavily\n  · EvaluatePharma\n  · BioPharma Dive\n  · SEC / Fierce Pharma\n─────────────────\nOUT: market_score 0-10\n     peak_sales_bn\n     peak_sales_bn_adj\n     (PTRS × NPV discount)"]

            SY["🔴 synthesizer\n─────────────────\nModel: Sonnet 4\nNo external calls\n─────────────────\nOUT: composite_score\n     deal_range_low\n     deal_range_high\n     recommendation\n     summary (GP memo)"]

            RP -->|indications + PTRS| SA
            SA -->|+ science scores| MA
            MA -->|+ market scores + peak sales| SY
        end

        INIT --> RP
        SY --> RESULT["AnalyzeResult\n{ assetName, score,\n  scienceScore, marketScore,\n  indications[], dealRange,\n  summary }"]
    end

    CW -->|POST message + filters| INIT
    RESULT -->|SSE stream| CW

    subgraph UI["ResultCard"]
        RC1["GO / WATCH / NO-GO badge\nComposite score"]
        RC2["Science ██████ 7.5\nMarket  ████   6.2"]
        RC3["Indication waterfall\n↳ click → rationale"]
        RC4["Deal range  $2.1B – $3.8B"]
        RC5["GP summary paragraph"]
    end

    CW --> UI
```

---

## State Schema

```mermaid
classDiagram
    class BDState {
        +str message
        +dict filters
        +str drug_asset_name
        +List~Indication~ indications
        +str clarification_needed
        +float composite_score
        +float science_score
        +float market_score
        +float deal_range_low
        +float deal_range_high
        +str recommendation
        +str summary
    }

    class Indication {
        +str name
        +str therapeutic_area
        +str clinical_stage
        +bool is_primary
        +int launch_year
        +float ptrs_score
        +float science_score
        +str science_rationale
        +float market_score
        +str market_rationale
        +float peak_sales_bn
    }

    BDState "1" --> "many" Indication
```

---

## PTRS × NPV Discount (market_agent)

```mermaid
flowchart LR
    P["peak_sales_bn\n(undiscounted)"]
    PTRS["ptrs_score\n(from table:\nphase × TA)"]
    NPV["NPV discount\n1 / (1.10 ^ years_to_launch)"]
    ADJ["peak_sales_bn_adj\n= peak × ptrs × npv"]

    P --> ADJ
    PTRS --> ADJ
    NPV --> ADJ
    ADJ -->|"summed across\nall indications"| DEAL["Deal range\n2–4× total adj. peak sales"]
```

---

## Scoring Weights (synthesizer)

```mermaid
pie title Composite Score Weights
    "Science (60%)" : 60
    "Market (40%)" : 40
```

| Score | Recommendation |
|-------|---------------|
| ≥ 6.5 | **GO** |
| 4.5 – 6.4 | **WATCH** |
| < 4.5 | **NO-GO** |
