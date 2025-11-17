from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ServiceConfig
from .schemas import ForecastRun
from .services.open_meteo import fetch_and_aggregate_forecast, fetch_and_aggregate_historical
from .storage.forecast_store import ForecastStore


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CONFIG = ServiceConfig()
STORE = ForecastStore(DATA_DIR, CONFIG)
app = FastAPI(
    title="MRT Weather Summary API",
    description="Aggregates Open-Meteo data into daily summaries tailored for Duddon & Furness MRT.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)


@app.get("/api/forecast/latest", response_model=ForecastRun)
async def latest_forecast() -> ForecastRun:
    latest = STORE.latest()
    if latest is None:
        latest = await fetch_and_aggregate_forecast(CONFIG)
        STORE.add_run(latest)
    return latest


@app.get("/api/forecast/runs")
async def all_runs() -> JSONResponse:
    return JSONResponse(content=[run.model_dump() for run in STORE.all_runs()])


@app.post("/api/forecast/run", response_model=ForecastRun)
async def refresh_forecast() -> ForecastRun:
    run = await fetch_and_aggregate_forecast(CONFIG)
    STORE.add_run(run)
    return run


@app.get("/api/forecast/historical", response_model=ForecastRun)
async def get_historical(days: int = 7) -> ForecastRun:
    """Get historical weather data for the past N days (max 30)."""
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 30")
    return await fetch_and_aggregate_historical(CONFIG, days)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
