FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /opt/answering

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY answering/pyproject.toml answering/README.md ./
COPY answering/__init__.py ./__init__.py
COPY answering/app ./app
COPY answering/schemas ./schemas
COPY answering/services ./services
COPY answering/prompts ./prompts
COPY answering/renderers ./renderers
COPY answering/docs ./docs
COPY answering/tests ./tests
COPY answering/payloads ./payloads

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

WORKDIR /workspace

CMD ["python", "-m", "answering.app.cli", "answer", "sample"]
