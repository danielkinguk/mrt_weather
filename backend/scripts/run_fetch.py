import asyncio
from pathlib import Path

from backend.app.config import ServiceConfig
from backend.app.services.open_meteo import fetch_and_aggregate_forecast
from backend.app.storage.forecast_store import ForecastStore


async def main() -> None:
    config = ServiceConfig()
    data_dir = Path(__file__).resolve().parents[1] / "data"
    store = ForecastStore(data_dir, config)

    run = await fetch_and_aggregate_forecast(config)
    store.add_run(run)
    print(f"Stored forecast run: {run.run_timestamp.isoformat()} UTC")


if __name__ == "__main__":
    asyncio.run(main())
