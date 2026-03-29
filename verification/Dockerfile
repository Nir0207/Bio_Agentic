FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /opt/verification

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY verification/pyproject.toml verification/README.md ./
COPY verification/__init__.py ./__init__.py
COPY verification/app ./app
COPY verification/schemas ./schemas
COPY verification/services ./services
COPY verification/nodes ./nodes
COPY verification/prompts ./prompts
COPY verification/docs ./docs
COPY verification/tests ./tests
COPY verification/payloads ./payloads

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

WORKDIR /workspace

CMD ["python", "-m", "verification.app.cli", "verify", "sample"]
