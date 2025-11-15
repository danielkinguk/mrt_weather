from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

import httpx
from zoneinfo import ZoneInfo

from ..config import ServiceConfig
from ..schemas import ForecastDay, ForecastRun, HourlyForecast


def _mps_to_mph(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 2.23693629, 1)


def _dominant_weather_code(codes: list[int]) -> int | None:
    if not codes:
        return None
    counter = Counter(codes)
    return counter.most_common(1)[0][0]


def _dominant_wind_direction(directions: list[int]) -> int | None:
    """Calculate dominant wind direction from a list of directions in degrees."""
    if not directions:
        return None

    # Use circular mean for wind direction
    # Convert to radians, calculate mean, convert back
    import math
    sin_sum = sum(math.sin(math.radians(d)) for d in directions)
    cos_sum = sum(math.cos(math.radians(d)) for d in directions)

    mean_direction = math.degrees(math.atan2(sin_sum, cos_sum))

    # Normalize to 0-360
    if mean_direction < 0:
        mean_direction += 360

    return round(mean_direction)


def _to_local_date(timestamp: str, tz: ZoneInfo) -> datetime.date:
    return datetime.fromisoformat(timestamp).astimezone(tz).date()


def _aggregate_hourly(hourly: dict[str, list[Any]], tz: ZoneInfo, max_days: int) -> list[ForecastDay]:
    grouped: dict[datetime.date, dict[str, list[float]]] = {}

    for idx, ts in enumerate(hourly.get("time", [])):
        date_key = _to_local_date(ts, tz)
        if len(grouped) >= max_days and date_key not in grouped:
            continue

        grouped.setdefault(date_key, {
            "temp_min": [],
            "temp_max": [],
            "wind": [],
            "gust": [],
            "precip": [],
            "weather": [],
        })

        if idx < len(hourly.get("temperature_2m", [])):
            grouped[date_key]["temp_min"].append(hourly["temperature_2m"][idx])
            grouped[date_key]["temp_max"].append(hourly["temperature_2m"][idx])
        if idx < len(hourly.get("windspeed_10m", [])):
            grouped[date_key]["wind"].append(hourly["windspeed_10m"][idx])
        if idx < len(hourly.get("windgusts_10m", [])):
            grouped[date_key]["gust"].append(hourly["windgusts_10m"][idx])
        if idx < len(hourly.get("precipitation", [])):
            grouped[date_key]["precip"].append(hourly["precipitation"][idx])
        if idx < len(hourly.get("weathercode", [])):
            grouped[date_key]["weather"].append(hourly["weathercode"][idx])

    days: list[ForecastDay] = []
    for date_key in sorted(grouped.keys())[:max_days]:
        bucket = grouped[date_key]
        days.append(
            ForecastDay(
                date=date_key,
                min_temp_c=min(bucket["temp_min"]) if bucket["temp_min"] else None,
                max_temp_c=max(bucket["temp_max"]) if bucket["temp_max"] else None,
                max_wind_mph=_mps_to_mph(max(bucket["wind"])) if bucket["wind"] else None,
                max_gust_mph=_mps_to_mph(max(bucket["gust"])) if bucket["gust"] else None,
                precipitation_mm=round(sum(bucket["precip"]), 1) if bucket["precip"] else None,
                weather_code=_dominant_weather_code(bucket["weather"]),
            )
        )
    return days


def aggregate_hourly_to_daily(hourly: dict[str, list[Any]], tz: ZoneInfo, max_days: int) -> list[ForecastDay]:
    return _aggregate_hourly(hourly, tz, max_days)


def _extract_today_hourly(hourly: dict[str, list[Any]], tz: ZoneInfo) -> list[HourlyForecast]:
    """Extract hourly forecast for today only."""
    today = datetime.now(tz).date()
    hourly_forecasts: list[HourlyForecast] = []

    for idx, ts in enumerate(hourly.get("time", [])):
        dt = datetime.fromisoformat(ts).astimezone(tz)
        if dt.date() != today:
            continue

        hourly_forecasts.append(
            HourlyForecast(
                time=dt,
                temperature_c=hourly.get("temperature_2m", [])[idx] if idx < len(hourly.get("temperature_2m", [])) else None,
                wind_mph=_mps_to_mph(hourly.get("windspeed_10m", [])[idx]) if idx < len(hourly.get("windspeed_10m", [])) else None,
                wind_direction=int(hourly.get("wind_direction_10m", [])[idx]) if idx < len(hourly.get("wind_direction_10m", [])) else None,
                gust_mph=_mps_to_mph(hourly.get("windgusts_10m", [])[idx]) if idx < len(hourly.get("windgusts_10m", [])) else None,
                precipitation_mm=hourly.get("precipitation", [])[idx] if idx < len(hourly.get("precipitation", [])) else None,
                weather_code=hourly.get("weathercode", [])[idx] if idx < len(hourly.get("weathercode", [])) else None,
                apparent_temperature_c=hourly.get("apparent_temperature", [])[idx] if idx < len(hourly.get("apparent_temperature", [])) else None,
                freezing_level_m=hourly.get("freezing_level_height", [])[idx] if idx < len(hourly.get("freezing_level_height", [])) else None,
            )
        )

    return hourly_forecasts


def _aggregate_dual_elevation(
    valley_hourly: dict[str, list[Any]],
    felltop_hourly: dict[str, list[Any]],
    daily: dict[str, list[Any]],
    tz: ZoneInfo,
    max_days: int
) -> list[ForecastDay]:
    """Aggregate hourly data for both valley and fell-top elevations."""
    valley_grouped: dict[datetime.date, dict[str, list[float]]] = {}
    felltop_grouped: dict[datetime.date, dict[str, list[float]]] = {}

    # Group valley data by day
    for idx, ts in enumerate(valley_hourly.get("time", [])):
        date_key = _to_local_date(ts, tz)
        if len(valley_grouped) >= max_days and date_key not in valley_grouped:
            continue

        valley_grouped.setdefault(date_key, {
            "temp_min": [],
            "temp_max": [],
            "wind": [],
            "gust": [],
            "wind_dir": [],
            "precip": [],
            "weather": [],
            "freezing": [],
        })

        if idx < len(valley_hourly.get("temperature_2m", [])):
            valley_grouped[date_key]["temp_min"].append(valley_hourly["temperature_2m"][idx])
            valley_grouped[date_key]["temp_max"].append(valley_hourly["temperature_2m"][idx])
        if idx < len(valley_hourly.get("windspeed_10m", [])):
            valley_grouped[date_key]["wind"].append(valley_hourly["windspeed_10m"][idx])
        if idx < len(valley_hourly.get("windgusts_10m", [])):
            valley_grouped[date_key]["gust"].append(valley_hourly["windgusts_10m"][idx])
        if idx < len(valley_hourly.get("wind_direction_10m", [])):
            valley_grouped[date_key]["wind_dir"].append(valley_hourly["wind_direction_10m"][idx])
        if idx < len(valley_hourly.get("precipitation", [])):
            valley_grouped[date_key]["precip"].append(valley_hourly["precipitation"][idx])
        if idx < len(valley_hourly.get("weathercode", [])):
            valley_grouped[date_key]["weather"].append(valley_hourly["weathercode"][idx])
        if idx < len(valley_hourly.get("freezing_level_height", [])):
            valley_grouped[date_key]["freezing"].append(valley_hourly["freezing_level_height"][idx])

    # Group fell-top data by day
    for idx, ts in enumerate(felltop_hourly.get("time", [])):
        date_key = _to_local_date(ts, tz)
        if len(felltop_grouped) >= max_days and date_key not in felltop_grouped:
            continue

        felltop_grouped.setdefault(date_key, {
            "temp_min": [],
            "temp_max": [],
            "wind": [],
            "gust": [],
            "wind_dir": [],
        })

        if idx < len(felltop_hourly.get("temperature_2m", [])):
            felltop_grouped[date_key]["temp_min"].append(felltop_hourly["temperature_2m"][idx])
            felltop_grouped[date_key]["temp_max"].append(felltop_hourly["temperature_2m"][idx])
        if idx < len(felltop_hourly.get("windspeed_10m", [])):
            felltop_grouped[date_key]["wind"].append(felltop_hourly["windspeed_10m"][idx])
        if idx < len(felltop_hourly.get("windgusts_10m", [])):
            felltop_grouped[date_key]["gust"].append(felltop_hourly["windgusts_10m"][idx])
        if idx < len(felltop_hourly.get("wind_direction_10m", [])):
            felltop_grouped[date_key]["wind_dir"].append(felltop_hourly["wind_direction_10m"][idx])

    # Extract daily sunrise/sunset
    sunrise_times = daily.get("sunrise", [])
    sunset_times = daily.get("sunset", [])
    daily_dates = [datetime.fromisoformat(d).date() for d in daily.get("time", [])]

    days: list[ForecastDay] = []
    for date_key in sorted(valley_grouped.keys())[:max_days]:
        valley_bucket = valley_grouped[date_key]
        felltop_bucket = felltop_grouped.get(date_key, {"temp_min": [], "temp_max": [], "wind": [], "gust": [], "wind_dir": []})

        # Find sunrise/sunset for this date
        sunrise = None
        sunset = None
        if date_key in daily_dates:
            idx = daily_dates.index(date_key)
            if idx < len(sunrise_times):
                sunrise = datetime.fromisoformat(sunrise_times[idx])
            if idx < len(sunset_times):
                sunset = datetime.fromisoformat(sunset_times[idx])

        days.append(
            ForecastDay(
                date=date_key,
                # Valley conditions
                min_temp_c=min(valley_bucket["temp_min"]) if valley_bucket["temp_min"] else None,
                max_temp_c=max(valley_bucket["temp_max"]) if valley_bucket["temp_max"] else None,
                max_wind_mph=_mps_to_mph(max(valley_bucket["wind"])) if valley_bucket["wind"] else None,
                max_gust_mph=_mps_to_mph(max(valley_bucket["gust"])) if valley_bucket["gust"] else None,
                wind_direction=_dominant_wind_direction(valley_bucket["wind_dir"]) if valley_bucket["wind_dir"] else None,
                # Fell-top conditions
                felltop_min_temp_c=min(felltop_bucket["temp_min"]) if felltop_bucket["temp_min"] else None,
                felltop_max_temp_c=max(felltop_bucket["temp_max"]) if felltop_bucket["temp_max"] else None,
                felltop_max_wind_mph=_mps_to_mph(max(felltop_bucket["wind"])) if felltop_bucket["wind"] else None,
                felltop_max_gust_mph=_mps_to_mph(max(felltop_bucket["gust"])) if felltop_bucket["gust"] else None,
                felltop_wind_direction=_dominant_wind_direction(felltop_bucket["wind_dir"]) if felltop_bucket["wind_dir"] else None,
                # Precipitation and weather (same for both elevations)
                precipitation_mm=round(sum(valley_bucket["precip"]), 1) if valley_bucket["precip"] else None,
                weather_code=_dominant_weather_code(valley_bucket["weather"]),
                # Freezing level
                min_freezing_level_m=min(valley_bucket["freezing"]) if valley_bucket["freezing"] else None,
                # Sunrise/sunset
                sunrise=sunrise,
                sunset=sunset,
            )
        )
    return days


def _add_worst_case_tags(days: list[ForecastDay]) -> None:
    """Add tags to identify worst-case days (Windiest, Wettest, Coldest)."""
    if not days:
        return

    # Find windiest (based on fell-top gusts)
    max_wind_day = max(days, key=lambda d: d.felltop_max_gust_mph or 0)
    if max_wind_day.felltop_max_gust_mph and max_wind_day.felltop_max_gust_mph > 40:
        max_wind_day.tags.append("Windiest")

    # Find wettest
    max_rain_day = max(days, key=lambda d: d.precipitation_mm or 0)
    if max_rain_day.precipitation_mm and max_rain_day.precipitation_mm > 5:
        max_rain_day.tags.append("Wettest")

    # Find coldest (based on fell-top minimum)
    min_temp_day = min(days, key=lambda d: d.felltop_min_temp_c if d.felltop_min_temp_c is not None else 999)
    if min_temp_day.felltop_min_temp_c is not None and min_temp_day.felltop_min_temp_c < 5:
        min_temp_day.tags.append("Coldest")


async def fetch_and_aggregate_historical(config: ServiceConfig, past_days: int = 7) -> ForecastRun:
    """Fetch historical weather data for the past N days."""
    from datetime import timedelta

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=past_days - 1)

    # Use archive API for historical data
    params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "temperature_2m,windspeed_10m,windgusts_10m,wind_direction_10m,precipitation,weathercode",
        "daily": "sunrise,sunset",
        "timezone": config.timezone,
        "elevation": config.valley_elevation_m,
    }

    # Fetch both valley and fell-top historical data
    felltop_params = {**params, "elevation": config.felltop_elevation_m}

    async with httpx.AsyncClient(timeout=30) as client:
        valley_response = await client.get("https://archive-api.open-meteo.com/v1/archive", params=params)
        valley_response.raise_for_status()
        valley_data = valley_response.json()

        felltop_response = await client.get("https://archive-api.open-meteo.com/v1/archive", params=felltop_params)
        felltop_response.raise_for_status()
        felltop_data = felltop_response.json()

    tz = ZoneInfo(config.timezone)

    # Aggregate historical data
    days = _aggregate_dual_elevation(
        valley_data.get("hourly", {}),
        felltop_data.get("hourly", {}),
        valley_data.get("daily", {}),
        tz,
        past_days
    )

    return ForecastRun(
        run_timestamp=datetime.now(timezone.utc),
        source_timezone=config.timezone,
        days=days,
        hourly_today=[],  # No hourly detail for historical view
    )


async def fetch_and_aggregate_forecast(config: ServiceConfig) -> ForecastRun:
    # Fetch both valley and fell-top forecasts
    valley_params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "hourly": "temperature_2m,windspeed_10m,windgusts_10m,wind_direction_10m,precipitation,weathercode,apparent_temperature,freezing_level_height",
        "daily": "sunrise,sunset",
        "timezone": config.timezone,
        "forecast_days": config.max_forecast_days,
        "elevation": config.valley_elevation_m,
    }

    felltop_params = {
        **valley_params,
        "elevation": config.felltop_elevation_m,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        valley_response = await client.get(config.open_meteo_url, params=valley_params)
        valley_response.raise_for_status()
        valley_data = valley_response.json()

        felltop_response = await client.get(config.open_meteo_url, params=felltop_params)
        felltop_response.raise_for_status()
        felltop_data = felltop_response.json()

    tz = ZoneInfo(config.timezone)

    # Aggregate both valley and fell-top data
    days = _aggregate_dual_elevation(
        valley_data.get("hourly", {}),
        felltop_data.get("hourly", {}),
        valley_data.get("daily", {}),
        tz,
        config.max_forecast_days
    )

    # Add worst-case tags
    _add_worst_case_tags(days)

    hourly_today = _extract_today_hourly(valley_data.get("hourly", {}), tz)

    return ForecastRun(
        run_timestamp=datetime.now(timezone.utc),
        source_timezone=config.timezone,
        days=days,
        hourly_today=hourly_today,
    )
