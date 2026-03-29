# Pharma Backend Integration Layer

## Purpose
This FastAPI service is the product-facing integration layer for platform phases (embeddings, graphML, modeling, orchestration, verification, answering). It exposes secure APIs for auth, orchestration, verification, and answering while keeping domain logic in service modules.

## Setup
1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment template:
   ```bash
   cp .env.example .env
   ```

## Env Configuration
- `APP_NAME`, `DEBUG`, `API_PREFIX`, `HOST`, `PORT`
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `SQLITE_DB_PATH` (auth DB only)
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- `LOG_LEVEL`

## Run Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Run With Docker
```bash
cp .env.example .env
docker compose up --build
```

## Default Test User
- Email: `admin@pharma.ai`
- Password: `admin123`
- Full name: `Admin User`

## API Routes
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/health`
- `POST /api/v1/orchestration/run`
- `POST /api/v1/orchestration/stream`
- `POST /api/v1/verification/run`
- `POST /api/v1/answering/run`
- `POST /api/v1/answering/stream`

## Streaming Notes
Streaming endpoints emit `text/event-stream` events with event types:
- `start`
- `progress`
- `partial_text`
- `payload`
- `done`
- `error`

Each request includes an `X-Request-ID` header and structured logs include request metadata for observability.
