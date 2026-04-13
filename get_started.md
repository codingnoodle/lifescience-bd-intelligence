# BD Intelligence — Get Started

A multi-agent AI tool for VC associates to run pharma BD due diligence. Type a drug asset in plain English, get a GO/WATCH/NO-GO recommendation with deal range.

---

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.11 | `brew install python@3.11` or [python.org](https://python.org) |
| `uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node 18+ | `brew install node` or [nodejs.org](https://nodejs.org) |

---

## 1. Environment Setup

```bash
cd bd-intelligence
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# LLM provider: "anthropic" (direct API) or "bedrock" (AWS)
LLM_PROVIDER=bedrock

# If using AWS Bedrock
AWS_BEARER_TOKEN_BEDROCK=ABSK...    # Your bearer token (base64-encoded name:secret)
AWS_REGION=us-east-1

# If using Anthropic API directly
# ANTHROPIC_API_KEY=sk-ant-...

# Web search (required for science + market agents)
TAVILY_API_KEY=tvly-...
```

---

## 2. Install Backend Dependencies

```bash
cd bd-intelligence
uv sync
```

---

## 3. Install Frontend Dependencies

```bash
cd bd-intelligence/frontend
npm install
```

---

## 4. Start the Servers

Open **two terminal tabs** from the `bd-intelligence/` directory.

**Terminal 1 — Backend (FastAPI on port 8000):**
```bash
cd bd-intelligence
uv run uvicorn backend.main:app --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Terminal 2 — Frontend (Vite on port 5173):**
```bash
cd bd-intelligence/frontend
npm run dev
```

Expected output:
```
  VITE ready in ~300ms
  ➜  Local:   http://localhost:5173/
```

---

## 5. Open the App

Go to **http://localhost:5173** in your browser.

---

## 6. Try It

Type in the chat box (natural language, no special format required):

```
ARV-471 ER+ breast cancer Phase 3, launch 2027
```

```
Tovorafenib pediatric low-grade glioma Phase 2, launch 2026
```

```
Efruxifermin NASH/MASH Phase 2b and liver fibrosis Phase 2, launch 2029
```

You'll see:
- **GO / WATCH / NO-GO** badge with composite score
- Deal range estimate (e.g. $2.1B – $3.4B)
- Per-indication science score, market score, PTRS, and peak sales
- 3-4 sentence GP summary

Use the **left sidebar** to filter by clinical phase, launch year, and therapeutic area before running a query.

---

## Verify Setup (optional)

```bash
# Check backend health
curl http://localhost:8000/

# Run a test query from CLI
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "ARV-471 ER+ breast cancer Phase 3 launch 2027", "filters": {}}' \
  | python3 -m json.tool
```

---

## Architecture

```
Frontend (React + Vite :5173)
        │  POST /analyze
        ▼
Backend (FastAPI :8000)
        │
        ▼
LangGraph pipeline:
  research_planner  →  Haiku parses free text → extracts asset + indications + PTRS
  science_agent     →  Sonnet + Tavily → scores MOA / clinical evidence (0-10)
  market_agent      →  Sonnet + Tavily → estimates peak sales + NPV discount
  synthesizer       →  Sonnet → composite score, deal range, GP summary
```

**Models:**
- Haiku 4.5 — research planning (fast + cheap)
- Sonnet 4 — science, market, synthesis (reasoning)

**Data sources:**
- Tavily web search (PubMed, FDA, ClinicalTrials.gov, EvaluatePharma, BioPharma Dive)
- PTRS lookup table (`backend/ptrs_table.json`) by phase × therapeutic area

---

## Project Structure

```
bd-intelligence/
├── backend/
│   ├── agents/
│   │   ├── research_planner.py   # Haiku: parse free text → structured indications
│   │   ├── science_agent.py      # Sonnet: score MOA + clinical evidence
│   │   ├── market_agent.py       # Sonnet: estimate peak sales + NPV
│   │   └── synthesizer.py        # Sonnet: composite score + deal range + summary
│   ├── utils/
│   │   └── ptrs_lookup.py        # PTRS table lookup
│   ├── tools/
│   │   └── clinicaltrials.py     # CT.gov API client (fallback)
│   ├── graph.py                  # LangGraph state graph
│   ├── main.py                   # FastAPI app + /analyze endpoint
│   ├── state.py                  # BDState + Indication schema
│   ├── config.py                 # LLM initialization (Bedrock or Anthropic)
│   └── ptrs_table.json           # PTRS by phase × therapeutic area
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ChatWindow.jsx    # Chat UI + API call
│           ├── FilterSidebar.jsx # Phase / launch year / TA filters
│           └── ResultCard.jsx    # GO badge + deal range + indication waterfall
├── tests/
│   └── run_deal_tests.py         # Validation suite (4 real acquisitions)
├── .env.example
├── pyproject.toml
└── get_started.md                # This file
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'backend'` | Run uvicorn from `bd-intelligence/` root, not from inside `backend/` |
| `LLM_PROVIDER` stays as `anthropic` | Check `.env` is in `bd-intelligence/` and `load_dotenv()` runs before config |
| `ValidationException: model identifier invalid` | Use `us.` prefix for Haiku, `global.` prefix for Sonnet 4 on Bedrock |
| `ResourceNotFoundException: Legacy model` | Sonnet 3.7 is legacy — use `global.anthropic.claude-sonnet-4-20250514-v1:0` |
| `403` from ClinicalTrials.gov | Expected — cloud IPs are blocked; Tavily fetches CT.gov data instead |
| Science/market scores are `null` | LLM returned non-JSON — check backend logs for raw response |
| CORS error in browser | Backend must run on port 8000; frontend proxy is configured for that port |
