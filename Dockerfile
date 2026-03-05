FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install all dependencies directly into system Python
RUN pip install --no-cache-dir \
    requests \
    pydantic \
    psycopg2-binary \
    fastapi \
    "uvicorn[standard]" \
    boto3

# Copy application source
COPY domain/         ./domain/
COPY services/       ./services/
COPY infrastructure/ ./infrastructure/
COPY workers/        ./workers/
COPY monitoring/     ./monitoring/
COPY api/            ./api/
COPY config/         ./config/
COPY main.py         ./main.py

ENV PYTHONPATH="/app"

CMD ["python", "main.py"]