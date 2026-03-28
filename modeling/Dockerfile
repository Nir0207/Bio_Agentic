FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /opt/modeling

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY modeling/pyproject.toml modeling/README.md ./
COPY modeling/__init__.py ./__init__.py
COPY modeling/app ./app
COPY modeling/data ./data
COPY modeling/features ./features
COPY modeling/training ./training
COPY modeling/inference ./inference
COPY modeling/validation ./validation
COPY modeling/docs ./docs
COPY modeling/tests ./tests

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

WORKDIR /workspace

CMD ["python", "-m", "modeling.app.cli", "run", "all"]
