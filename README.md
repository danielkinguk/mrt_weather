# MRT Weather Summary Service

A productivity-focused weather briefing for Duddon & Furness MRT. This repo pairs a Python API with a React/Vite front-end to deliver a mobile-friendly 7-day summary that highlights strong wind (>40 mph) and heavy rain (>20 mm).

## Project layout

- `backend/` – FastAPI service that fetches from Open-Meteo, aggregates hourly data into daily stats, caches the last 7 runs, and exposes `/api/forecast` endpoints.
- `frontend/` – Vite + React UI that consumes `/api/forecast/latest` and renders a responsive box table.
- `.github/copilot-instructions.md` – AI agent guidance.

## Running locally

### Backend API

```bash
cd backend
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

This exposes the `/api/forecast/*` endpoints and `/health`. The server reloads automatically when backend files change, so keep the scheduler (e.g., a cron job or `backend/scripts/run_fetch.py`) hitting `/api/forecast/run` twice daily (06:00 and 18:00 UK time) to refresh the stored runs.

### Frontend UI

```bash
cd frontend
npm run dev -- --host
```

Vite proxies `/api` to the backend, so start both services together for local development. The UI highlights wind >40 mph and rain >20 mm, matching the backend thresholds.

## Backend (Python)

### Setup

```bash
cd backend
python -m pip install -r requirements.txt
```

If you prefer Poetry:

```bash
cd backend
poetry install
```

### Run tests

```bash
cd backend
python -m pytest tests
```

### Start development server

```bash
cd backend
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual forecast fetch

The scheduled job should trigger the same logic twice daily (06:00 and 18:00 UK time) and keep only the most recent 7 runs. To run it locally:

```bash
cd backend
python scripts/run_fetch.py
```

On platforms like Cloud Run/Vercel, use a cron job or GitHub Actions to post to `/api/forecast/run` every 12 hours.

## Frontend (React + Vite)

### Setup & development

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000`, so run both backend and frontend simultaneously.

### Production build

```bash
cd frontend
npm run build
```

Serve the `frontend/dist` folder behind any static host (Netlify, Cloudflare Pages, etc.). Pointing the proxy to the backend URL (or configuring CORS on FastAPI) is required for production deployments.

## Configurable values

- **Location**: Defaults to `54.2586° N, 3.2145° W` but can be updated in `backend/app/config.py` or runtime configuration.
- **Thresholds**: High wind detection at >40 mph, heavy rain at >20 mm. These are surfaced to the UI via CSS classes and should be tunable in the config module.
- **Schedule**: The desired cron expression is `0 6,18 * * *`; you can adjust or replace it via your scheduler (GitHub Actions, cron, Cloud Scheduler, etc.).

## Testing & validation

- Backend: `pytest` already covers aggregation logic. Add more tests in `backend/tests/` when extending computation.
- Frontend: Run `npm run build` to ensure the Vite bundle succeeds.

## Next steps

1. Wire a persistent store (database or Google Sheet) if you need to scale beyond flat JSON in `backend/data/`.
2. Add hosted scheduler (Cloud Scheduler or GitHub Actions) to hit `/api/forecast/run` twice daily and alert on failures.
3. Layer in auth or admin controls if configuration must be locked down.
