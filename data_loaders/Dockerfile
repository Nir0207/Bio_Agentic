FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
COPY app ./app
COPY pipelines ./pipelines
COPY graph ./graph
COPY tests ./tests

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

CMD ["python", "-m", "app.cli", "run", "all"]
