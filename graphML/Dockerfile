FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /opt/graphML

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY graphML/pyproject.toml graphML/README.md ./
COPY graphML/__init__.py ./__init__.py
COPY graphML/app ./app
COPY graphML/projections ./projections
COPY graphML/algorithms ./algorithms
COPY graphML/writers ./writers
COPY graphML/validation ./validation
COPY graphML/docs ./docs
COPY graphML/tests ./tests

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

WORKDIR /workspace

CMD ["python", "-m", "graphML.app.cli", "run", "all"]
