FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# Copy application code
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
