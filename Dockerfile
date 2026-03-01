FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install only what the worker needs — no PyTorch/sentence-transformers
RUN uv pip install --system \
    requests \
    pydantic \
    psycopg2-binary

# Copy application source
COPY domain/         ./domain/
COPY services/       ./services/
COPY infrastructure/ ./infrastructure/
COPY workers/        ./workers/
COPY config/         ./config/
COPY main.py         ./main.py

ENV PYTHONPATH="/app"

CMD ["python", "main.py"]