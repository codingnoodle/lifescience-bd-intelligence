# Local Setup

```bash
git clone https://github.com/codingnoodle/lifescience-bd-intelligence.git
cd lifescience-bd-intelligence
```

## Backend (FastAPI + LangGraph)

```bash
# From repo root:

# Install dependencies
uv sync

# Run the API server
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Run tests
uv run pytest tests/
uv run python tests/run_deal_tests.py
```

## Frontend (React + Vite + Tailwind)

```bash
# From repo root:
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev          # → http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Docker (both together)

```bash
# From repo root:

# Build and run both services
docker compose up --build

# Frontend → http://localhost:80
# Backend  → http://localhost:8000
```

## Environment

Copy `.env.example` to `.env` and set:

- `LLM_PROVIDER` — `anthropic` or `bedrock`
- `ANTHROPIC_API_KEY` or `AWS_BEARER_TOKEN_BEDROCK`
- `TAVILY_API_KEY`
