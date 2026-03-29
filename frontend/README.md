# Pharma Frontend Integration UI

## Purpose
React + TypeScript interface for the pharma platform integration layer. The frontend connects only to backend APIs, provides auth, module pages, streaming consoles, and modular UI architecture using Zustand for state.

## Setup
1. Install dependencies:
   ```bash
   npm install
   ```
2. Create env file:
   ```bash
   cp .env.example .env
   ```

## Environment
- `VITE_API_URL=http://localhost:8000/api/v1`

## Run Locally
```bash
npm run dev
```

## Build
```bash
npm run build
```

## Run With Docker
```bash
cp .env.example .env
docker compose up --build
```

## Routes
- `/`
- `/login`
- `/register`
- `/dashboard` (protected)
- `/orchestration` (protected)
- `/verification` (protected)
- `/answering` (protected)
- `*`

## Architecture Notes
- React Router for navigation and route protection.
- Zustand stores: `authStore`, `appStore`.
- Service layer handles all API calls (`src/services`).
- Streaming events parsed through `useStreaming` + `StreamConsole` + `StreamStatusBar`.
- Material UI components with Tailwind layout/responsiveness.
