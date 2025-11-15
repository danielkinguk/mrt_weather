from dataclasses import dataclass


@dataclass
class ServiceConfig:
    latitude: float = 54.2586
    longitude: float = -3.2145
    timezone: str = "Europe/London"
    max_runs: int = 7
    wind_threshold_mph: float = 40.0
    rain_threshold_mm: float = 20.0
    schedule_cron: str = "0 6,18 * * *"
    max_forecast_days: int = 7
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    valley_elevation_m: float = 100.0  # Valley/base elevation in meters
    felltop_elevation_m: float = 800.0  # Fell-top elevation in meters
