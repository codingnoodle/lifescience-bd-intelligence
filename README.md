# BD Decision Intelligence

A multi-agent pharma BD valuation system that evaluates drug assets and produces dual-view deal pricing with buyer mapping.

## What it does

Type any drug asset and get:
- **Science profile** — positioning, de-risking signals, adjusted PTRS
- **Comparator analysis** — SOC discovery, metric comparison, differentiation verdict
- **Three-scenario valuation** — standalone NPV, platform displacement, strategic deal price
- **Buyer mapping** — likely acquirers ranked by urgency (patent cliff + flush capital + deal velocity)
- **Dual-view output** — risk-adjusted (PTRS applied) and if-succeed (assumes approval) side by side

## Architecture

```
research_planner → science_agent → market_agent → synthesizer
```

Sequential pipeline — market agent reads PTRS from science agent, synthesizer reads everything.

Three agents do the analytical work:
- **Science agent** — searches PubMed/ClinicalTrials.gov, builds positioning profile, identifies de-risking signals, computes adjusted PTRS
- **Market agent** — discovers comparators, runs metric comparison, determines differentiation verdict (best/better/me-too/worse/new-class-creation), sizes dual peak sales
- **Synthesizer** — maps buyers (patent cliff + flush capital tables), scores bidding tension, computes deal multiple, produces three scenarios with derivation math

The research planner is a lightweight classifier that routes queries (specific asset vs. discovery scan).

**Tech stack**: FastAPI + LangGraph + Claude Sonnet (backend), React + Vite + Tailwind (frontend)

## Project structure

```
bd-intelligence/
├── backend/
│   ├── agents/           # science_agent, market_agent, synthesizer, research_planner, discovery_agent
│   ├── utils/            # ptrs_lookup, buyer_context, deal_benchmarks
│   ├── tools/            # Tavily search wrappers
│   ├── graph.py          # LangGraph sequential pipeline
│   ├── main.py           # FastAPI: /analyze, /analyze/stream, /recalculate
│   └── state.py          # IndicationAnalysis TypedDict + BDState
├── frontend/
│   └── src/components/   # ChatWindow, ResultCard, ValuationWaterfall, AssumptionsPanel, FilterSidebar
├── docs/
│   ├── agent_logic.md    # Detailed scoring rubric, formulas, tuning guide
│   └── stategraph.png    # Auto-generated graph visualization
└── tests/                # Real deal validation suite
```

## Setup

```bash
# Backend
cd bd-intelligence
cp .env.example .env     # add ANTHROPIC_API_KEY and TAVILY_API_KEY
uv sync
uv run uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`.

## API

### `POST /analyze/stream` (primary)
SSE endpoint — streams progress events then final result.

```json
{"message": "TERN-701 allosteric BCR::ABL1 TKI CML Phase 1/2", "filters": {}}
```

### `POST /recalculate`
Re-runs from market agent onward with user overrides (e.g. edited PTRS, changed comparator).

```json
{
  "asset_name": "TERN-701",
  "indications": [...],
  "overrides": {"indication_name": "CML", "field": "ptrs_adjusted", "value": 0.35}
}
```

## Valuation methodology

Each scenario shows **two values**:

| Scenario | Risk-adjusted | If-succeed |
|---|---|---|
| Standalone NPV | peak x PTRS x rev_mult x NPV | peak x rev_mult x NPV |
| Platform displacement | + SOC capture, PTRS applied | + SOC capture, no PTRS |
| Strategic deal price | deal_multiple x PTRS | deal_multiple (what buyer pays) |

Deal multiple = base(phase) + urgency_adj + bidding_adj + differentiation_adj. See `docs/agent_logic.md` for the full formula.

## Key files

| File | What it does |
|---|---|
| `utils/ptrs_lookup.py` | Base PTRS table + `get_adjusted_ptrs()` with 9 de-risking signals |
| `utils/buyer_context.py` | Patent cliff (12 buyers) + flush capital (3 buyers) tables |
| `utils/deal_benchmarks.json` | 20 M&A + 7 licensing deals from 2025-2026 |
| `agents/synthesizer.py` | Buyer mapping, bidding tension, three-scenario output |
| `docs/agent_logic.md` | Complete scoring rubric, formulas, tuning guide |
