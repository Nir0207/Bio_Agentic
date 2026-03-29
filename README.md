# Omics Agentic Platform

Single-source project documentation for all major folders.

## Common Setup

- Env file: use root `/.env` (template: `/.env.example`)
- Backend run: `docker compose -f backend/docker-compose.yml up --build`
- Frontend run: `docker compose -f frontend/docker-compose.yml up --build`
- Backend URL: `http://localhost:8000`
- Frontend URL: `http://localhost:5173`

## Folder Guide

### backend:
Production FastAPI integration layer.
- Owns auth (SQLite + JWT), health, orchestration, verification, answering APIs
- Streaming endpoints for orchestration and answering
- Structured logging, request-id middleware, global error handlers
- Default test user: `admin@pharma.ai / admin123`

Key routes:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/health`
- `POST /api/v1/orchestration/run`
- `POST /api/v1/orchestration/stream`
- `POST /api/v1/verification/run`
- `POST /api/v1/answering/run`
- `POST /api/v1/answering/stream`

### frontend:
React + TypeScript product UI.
- Uses React Router + Zustand
- Uses Material UI + TailwindCSS
- Calls backend only through `src/services/*`
- Includes auth flow, protected routes, dashboard, orchestration/verification/answering pages, streaming console components

Main routes:
- `/`, `/login`, `/register`
- `/dashboard`, `/orchestration`, `/verification`, `/answering` (protected)

### orchestration:
Standalone orchestration phase (LangGraph-driven flow before verification/answering).
- Query normalization, graph retrieval, semantic retrieval, score merge/rank
- Evidence bundle creation
- Human review gate support
- Outputs structured payload for downstream modules

Run examples:
- `python -m orchestration.app.cli validate-tools`
- `python -m orchestration.app.cli run sample`
- `python -m orchestration.app.cli run all`

### verification:
Standalone claim verification phase.
- Consumes orchestration payload
- Produces claim-level verdicts, confidence, citations/provenance checks
- Supports human review actions for risk cases

Run examples:
- `python -m verification.app.cli verify sample`
- `python -m verification.app.cli run all`

### answering:
Standalone final answer generation phase.
- Consumes verified payload
- Produces final answer text + structured JSON + evidence appendix
- Supports answer styles and optional enrichment

Run examples:
- `python -m answering.app.cli answer sample`
- `python -m answering.app.cli run all`

### modeling:
Standalone ML scoring phase.
- Builds datasets from Neo4j graph features
- Trains/evaluates baseline models
- Logs to MLflow, optional model registration/writeback

Run examples:
- `python -m modeling.app.cli train baseline`
- `python -m modeling.app.cli run all`

### graphML:
Graph Data Science phase for graph analytics.
- Manages GDS projections
- Runs FastRP, Leiden, optional KNN
- Writes graph analytics outputs back to Neo4j

Run examples:
- `python -m graphML.app.cli estimate all`
- `python -m graphML.app.cli run all`

### gdsGraph:
Alternative/legacy GDS phase module (`gds` package).
- Similar GDS projection + FastRP/Leiden/KNN pipeline
- Uses shared root env and containerized execution

Run examples:
- `python -m gds.app.cli estimate all`
- `python -m gds.app.cli run all`

### data_loaders:
Graph ETL and embedding prep phase.
- Generates gold parquet tables
- Loads Neo4j graph schema/data
- Builds vector indexes and semantic embedding workflows

Run examples:
- `python -m app.cli run phase2`
- `python -m app.cli run phase3`
- `python -m app.cli run phase4`

### embeddings:
Embedding-focused utilities/assets used by retrieval stages.
- Supports semantic retrieval readiness for downstream orchestration/answering modules

### docs:
Project documentation artifacts and generated outputs.

## Docker Notes

- Each module keeps its own `docker-compose.yml`
- Compose files now load shared root env (`../.env` from module folders)
- No folder-level `.env` files are required
- Services are designed to run independently but can be orchestrated together via root-level scripts or manual compose commands
