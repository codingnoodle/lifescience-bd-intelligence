# BD Intelligence Tool

A pharma BD decision intelligence tool using LangGraph multi-agent system.

## Overview

This tool enables VC associates to analyze drug assets and receive data-driven GO/NO-GO BD recommendations. It uses a multi-agent architecture powered by Claude Sonnet 4 to:

1. **Research Planning** - Creates a comprehensive analysis strategy
2. **Scientific Analysis** - Evaluates mechanism of action, clinical data, and safety
3. **Market Analysis** - Assesses commercial potential and competitive landscape
4. **Synthesis** - Calculates PTRS-based valuation and provides final recommendation

## Architecture

```
Development Setup (2 servers):

┌─────────────────┐         ┌──────────────────────────┐
│  Frontend       │  HTTP   │  Backend (FastAPI:8000)  │
│  (Vite:5173)    │────────>│  ├─ LangGraph agents     │
│  React UI       │         │  ├─ MCP clients          │
└─────────────────┘         │  └─ /analyze endpoint    │
                            └──────────────────────────┘
                                      │ MCP protocol
                                      ▼
                            ┌──────────────────────────┐
                            │  External MCP Servers    │
                            │  (Brave Search, etc.)    │
                            └──────────────────────────┘
```

**Tech Stack:**
- **Backend**: Python with LangGraph, FastAPI, MCP client SDK
- **LLM**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Package Manager**: uv
- **Frontend**: React + Vite (to be implemented)
- **Tools**: MCP clients for web search, databases, etc.

## Project Structure

```
bd-intelligence/
├── backend/
│   ├── agents/              # Agent modules (research_planner, science_agent, market_agent, synthesizer)
│   ├── tools/               # MCP tool wrappers
│   ├── graph.py             # LangGraph state graph
│   ├── main.py              # FastAPI entry point
│   ├── state.py             # Shared state schema (BDState)
│   └── ptrs_table.json      # PTRS lookup table by phase/therapeutic area
├── frontend/
│   └── src/
│       ├── components/
│       └── App.jsx
├── pyproject.toml
├── .python-version          # Pinned to 3.11
├── uv.lock
└── .env.example
```

## Setup

### Prerequisites

- Python 3.11
- uv package manager
- Anthropic API key

### Installation

1. **Clone the repository** (if not already done)

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up environment**:
   ```bash
   cd bd-intelligence
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Install dependencies**:
   ```bash
   uv sync
   ```

## Running the Backend

Start the FastAPI development server:

```bash
uv run uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "BD Intelligence API",
  "version": "0.1.0"
}
```

### `POST /analyze`
Analyze a drug asset and get BD recommendation.

**Request:**
```json
{
  "drug_asset_name": "Asset-XYZ-123"
}
```

**Response:**
```json
{
  "drug_asset_name": "Asset-XYZ-123",
  "recommendation": "GO - Strong commercial potential with manageable risk",
  "go_no_go": "GO",
  "reasoning": "...",
  "ptrs_score": 0.675,
  "clinical_stage": "phase3",
  "therapeutic_area": "oncology"
}
```

## PTRS Valuation

The tool uses a hardcoded PTRS (Probability of Technical and Regulatory Success) lookup table to estimate success probability based on:
- **Clinical Development Phase** (preclinical, IND-enabling, Phase 1, Phase 1/2, Phase 2, Phase 2b, Phase 3, NDA submitted)
- **Therapeutic Area** (oncology, immunology, neurology, rare disease, cardio-metabolic, infectious disease)

PTRS scores range from 0 (no chance) to 1 (certainty) and are used in NPV calculations for deal valuation.

## MCP Integration

The backend uses **MCP clients** (not separate servers) to access external tools and data sources.

### Available MCP Tools

Tools are configured in `backend/tools/mcp_client.py` and wrapped as LangChain tools in `backend/tools/langchain_tools.py`.

**Configured MCP Servers** (uncomment in code to enable):
- **Brave Search**: Web search for clinical trials, market data, news
- **Filesystem**: Read local data files and reports

### Adding New MCP Tools

1. Install the MCP server (if needed):
   ```bash
   npm install -g @modelcontextprotocol/server-brave-search
   ```

2. Add configuration in `backend/tools/mcp_client.py`:
   ```python
   self.server_configs["brave_search"] = StdioServerParameters(
       command="npx",
       args=["-y", "@modelcontextprotocol/server-brave-search"],
       env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
   )
   ```

3. Create LangChain wrapper in `backend/tools/langchain_tools.py`

4. Add to agent's tool list in the graph nodes

### Using Tools in Agents

```python
from backend.tools.langchain_tools import get_tools

# In agent node
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)
```

## Testing with Real Deals

The system includes a test suite based on **real pharma acquisitions** from 2025-2026. These provide ground truth for validating valuations and recommendations.

### Test Cases

1. **J&J / Intra-Cellular ($14.6B)** - Approved CNS asset valuation
2. **Servier / Day One ($2.5B)** - Multi-indication portfolio with platform value
3. **Novo / Akero ($5.2B)** - Emerging indication (MASH) with large market
4. **Jazz / Chimerix ($935M)** - Rare disease with small patient population

### Run Tests

```bash
# Start API server
uv run uvicorn backend.main:app --reload

# Run test suite (in another terminal)
uv run python tests/run_deal_tests.py
```

See [`tests/README.md`](tests/README.md) for detailed test documentation and calibration guidelines.

## Development Status

**Current Status**: Full system architecture implemented with agent stubs

**Implemented**:
- ✅ 5-agent LangGraph workflow (research, science, indications, market, synthesis)
- ✅ Multi-indication portfolio analysis
- ✅ PTRS calculation and portfolio valuation
- ✅ AWS Bedrock + Anthropic API support
- ✅ Tavily web search integration
- ✅ Real deal test suite for validation
- ✅ FastAPI with portfolio endpoints

**Next Steps**:
- [ ] Implement agent logic with LLM calls (replace stubs)
- [ ] Add web search for indication discovery
- [ ] Tune PTRS table and optionality premium
- [ ] Run test suite and calibrate
- [ ] Build React frontend
- [ ] Add authentication
- [ ] Implement caching and optimization

## License

Proprietary
