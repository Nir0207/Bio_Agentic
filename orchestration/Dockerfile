FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /opt/orchestration

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY orchestration/pyproject.toml orchestration/README.md ./
COPY orchestration/__init__.py ./__init__.py
COPY orchestration/app ./app
COPY orchestration/nodes ./nodes
COPY orchestration/tools ./tools
COPY orchestration/prompts ./prompts
COPY orchestration/schemas ./schemas
COPY orchestration/services ./services
COPY orchestration/docs ./docs
COPY orchestration/tests ./tests

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

WORKDIR /workspace

CMD ["python", "-m", "orchestration.app.cli", "run", "sample"]
