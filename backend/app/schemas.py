from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class HourlyForecast(BaseModel):
    time: datetime
    temperature_c: float | None = Field(None, description="Temperature in Celsius")
    wind_mph: float | None = Field(None, description="Wind speed in mph")
    wind_direction: int | None = Field(None, description="Wind direction in degrees (0-360)")
    gust_mph: float | None = Field(None, description="Wind gust in mph")
    precipitation_mm: float | None = Field(None, description="Precipitation in mm")
    weather_code: int | None = Field(None, description="Weather code")
    apparent_temperature_c: float | None = Field(None, description="Apparent/feels-like temperature in Celsius")
    freezing_level_m: float | None = Field(None, description="Freezing level height in meters")


class ForecastDay(BaseModel):
    date: date
    # Valley conditions
    min_temp_c: float | None = Field(None, description="Daily minimum temperature at valley level")
    max_temp_c: float | None = Field(None, description="Daily maximum temperature at valley level")
    # Fell-top conditions (800m)
    felltop_min_temp_c: float | None = Field(None, description="Daily minimum temperature at fell-top (800m)")
    felltop_max_temp_c: float | None = Field(None, description="Daily maximum temperature at fell-top (800m)")
    felltop_max_wind_mph: float | None = Field(None, description="Maximum wind speed at fell-top (800m)")
    felltop_max_gust_mph: float | None = Field(None, description="Maximum wind gust at fell-top (800m)")
    felltop_wind_direction: int | None = Field(None, description="Dominant wind direction at fell-top in degrees (0-360)")
    # Wind (valley level)
    max_wind_mph: float | None = Field(None, description="Maximum sustained wind speed in mph")
    max_gust_mph: float | None = Field(None, description="Maximum wind gust in mph")
    wind_direction: int | None = Field(None, description="Dominant wind direction in degrees (0-360)")
    # Precipitation and weather
    precipitation_mm: float | None = Field(None, description="Total precipitation for the day (rain + snow equivalent)")
    weather_code: int | None = Field(None, description="Dominant weather code for the day")
    # Additional mountain-specific data
    min_freezing_level_m: float | None = Field(None, description="Minimum freezing level height in meters")
    sunrise: datetime | None = Field(None, description="Sunrise time")
    sunset: datetime | None = Field(None, description="Sunset time")
    # Tags for worst-case identification
    tags: list[str] = Field(default_factory=list, description="Tags like 'Windiest', 'Wettest', 'Coldest'")


class ForecastRun(BaseModel):
    run_timestamp: datetime = Field(..., description="UTC timestamp when the forecast was retrieved")
    source_timezone: str = Field(..., description="Timezone used for local aggregation")
    days: list[ForecastDay] = Field(..., description="Aggregated stats for the forecast horizon")
    hourly_today: list[HourlyForecast] = Field(default_factory=list, description="Hourly forecast for today")
