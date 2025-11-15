from datetime import date
from zoneinfo import ZoneInfo

from backend.app.services.open_meteo import aggregate_hourly_to_daily


def test_aggregate_hourly_to_daily():
    hourly = {
        "time": [
            "2025-11-15T00:00",
            "2025-11-15T01:00",
            "2025-11-16T00:00",
            "2025-11-16T01:00",
        ],
        "temperature_2m": [5.0, 6.0, 3.0, 8.0],
        "windspeed_10m": [5.0, 7.0, 3.5, 4.0],
        "windgusts_10m": [10.0, 9.0, 8.0, 12.0],
        "precipitation": [1.0, 0.0, 2.5, 0.5],
        "weathercode": [0, 0, 61, 61],
    }
    tz = ZoneInfo("Europe/London")

    days = aggregate_hourly_to_daily(hourly, tz, max_days=2)

    assert len(days) == 2
    assert days[0].date == date(2025, 11, 15)
    assert days[0].min_temp_c == 5.0
    assert days[0].max_temp_c == 6.0
    assert days[0].max_wind_mph == round(max(5.0, 7.0) * 2.23693629, 1)
    assert days[0].precipitation_mm == 1.0
    assert days[0].weather_code == 0

    assert days[1].date == date(2025, 11, 16)
    assert days[1].min_temp_c == 3.0
    assert days[1].max_temp_c == 8.0
    assert days[1].max_gust_mph == round(max(8.0, 12.0) * 2.23693629, 1)
    assert days[1].precipitation_mm == 3.0
    assert days[1].weather_code == 61
