FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app/gdsGraph

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY gdsGraph/pyproject.toml gdsGraph/README.md ./
COPY gdsGraph/gds ./gds
COPY gdsGraph/docs ./docs
COPY gdsGraph/tests ./tests

RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -e .

CMD ["python", "-m", "gds.app.cli", "run", "all"]
