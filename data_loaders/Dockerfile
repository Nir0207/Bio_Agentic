FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app/data_loaders

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY data_loaders/requirements.txt data_loaders/pyproject.toml ./
COPY data_loaders/app ./app
COPY data_loaders/pipelines ./pipelines
COPY data_loaders/graph ./graph
COPY data_loaders/tests ./tests
COPY embeddings ./embeddings

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

CMD ["python", "-m", "app.cli", "run", "phase4"]
