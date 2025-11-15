import { useEffect, useMemo, useState } from "react";

interface HourlyForecast {
  time: string;
  temperature_c: number | null;
  wind_mph: number | null;
  wind_direction: number | null;
  gust_mph: number | null;
  precipitation_mm: number | null;
  weather_code: number | null;
  apparent_temperature_c: number | null;
  freezing_level_m: number | null;
}

interface ForecastDay {
  date: string;
  // Valley conditions
  min_temp_c: number | null;
  max_temp_c: number | null;
  // Fell-top conditions (800m)
  felltop_min_temp_c: number | null;
  felltop_max_temp_c: number | null;
  felltop_max_wind_mph: number | null;
  felltop_max_gust_mph: number | null;
  felltop_wind_direction: number | null;
  // Wind (valley level)
  max_wind_mph: number | null;
  max_gust_mph: number | null;
  wind_direction: number | null;
  // Precipitation and weather
  precipitation_mm: number | null;
  weather_code: number | null;
  // Additional mountain-specific data
  min_freezing_level_m: number | null;
  sunrise: string | null;
  sunset: string | null;
  // Tags for worst-case identification
  tags: string[];
}

interface ForecastRun {
  run_timestamp: string;
  source_timezone: string;
  days: ForecastDay[];
  hourly_today: HourlyForecast[];
}

const windAlertThreshold = 40;
const rainAlertThreshold = 20;

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getWeatherIcon(weatherCode: number | null): string {
  if (weatherCode === null) return "❓";

  // WMO Weather interpretation codes
  // https://open-meteo.com/en/docs
  if (weatherCode === 0) return "☀️"; // Clear sky
  if (weatherCode === 1) return "🌤️"; // Mainly clear
  if (weatherCode === 2) return "⛅"; // Partly cloudy
  if (weatherCode === 3) return "☁️"; // Overcast
  if (weatherCode === 45 || weatherCode === 48) return "🌫️"; // Fog
  if (weatherCode >= 51 && weatherCode <= 55) return "🌦️"; // Drizzle
  if (weatherCode >= 56 && weatherCode <= 57) return "🌧️"; // Freezing drizzle
  if (weatherCode >= 61 && weatherCode <= 65) return "🌧️"; // Rain
  if (weatherCode >= 66 && weatherCode <= 67) return "🌧️"; // Freezing rain
  if (weatherCode >= 71 && weatherCode <= 75) return "❄️"; // Snow
  if (weatherCode === 77) return "❄️"; // Snow grains
  if (weatherCode >= 80 && weatherCode <= 82) return "🌧️"; // Rain showers
  if (weatherCode >= 85 && weatherCode <= 86) return "🌨️"; // Snow showers
  if (weatherCode >= 95 && weatherCode <= 99) return "⛈️"; // Thunderstorm

  return "☁️"; // Default
}

function severityClass(day: ForecastDay) {
  // Use fell-top wind for severity assessment
  if ((day.felltop_max_gust_mph ?? 0) > windAlertThreshold) {
    return "danger-wind";
  }
  if ((day.precipitation_mm ?? 0) > rainAlertThreshold) {
    return "danger-rain";
  }
  return "normal";
}

function calculateRemainingDaylight(sunrise: string | null, sunset: string | null): string {
  if (!sunrise || !sunset) return "N/A";

  const now = new Date().getTime();
  const sunriseTime = new Date(sunrise).getTime();
  const sunsetTime = new Date(sunset).getTime();

  // If before sunrise or after sunset, no daylight remaining
  if (now < sunriseTime) {
    return "Not yet sunrise";
  }

  if (now > sunsetTime) {
    return "After sunset";
  }

  // Calculate remaining daylight
  const remainingMs = sunsetTime - now;
  const hours = Math.floor(remainingMs / (1000 * 60 * 60));
  const minutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) {
    return `${hours}h ${minutes}m left`;
  } else {
    return `${minutes}m left`;
  }
}

function degreesToCompass(degrees: number | null): string {
  if (degrees === null) return "";

  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(((degrees % 360) / 45)) % 8;
  return directions[index];
}

const App = () => {
  const [forecast, setForecast] = useState<ForecastRun | null>(null);
  const [historicalData7, setHistoricalData7] = useState<ForecastRun | null>(null);
  const [historicalData14, setHistoricalData14] = useState<ForecastRun | null>(null);
  const [historicalData21, setHistoricalData21] = useState<ForecastRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0); // For clickable day cards
  const [viewMode, setViewMode] = useState<"forecast" | "historical7" | "historical14" | "historical21">("forecast");

  useEffect(() => {
    fetch("/api/forecast/latest")
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch forecast");
        }
        return res.json();
      })
      .then((data) => {
        setForecast(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const loadHistoricalData7 = () => {
    setLoading(true);
    setError(null);
    fetch("/api/forecast/historical?days=7")
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch historical data");
        }
        return res.json();
      })
      .then((data) => {
        setHistoricalData7(data);
        setViewMode("historical7");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const loadHistoricalData14 = () => {
    setLoading(true);
    setError(null);
    fetch("/api/forecast/historical?days=14")
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch historical data");
        }
        return res.json();
      })
      .then((data) => {
        setHistoricalData14(data);
        setViewMode("historical14");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const loadHistoricalData21 = () => {
    setLoading(true);
    setError(null);
    fetch("/api/forecast/historical?days=21")
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch historical data");
        }
        return res.json();
      })
      .then((data) => {
        setHistoricalData21(data);
        setViewMode("historical21");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const switchToForecast = () => {
    setViewMode("forecast");
    setSelectedDayIndex(0);
  };

  const currentData = viewMode === "forecast" ? forecast :
                      viewMode === "historical7" ? historicalData7 :
                      viewMode === "historical14" ? historicalData14 : historicalData21;
  const sortedDays = useMemo(() => currentData?.days ?? [], [currentData]);
  const hourlyToday = useMemo(() => currentData?.hourly_today ?? [], [currentData]);
  const selectedDay = sortedDays[selectedDayIndex] || null;

  const timeOfDaySplit = useMemo(() => {
    if (hourlyToday.length === 0) return { daytime: [], evening: [], overnight: [] };

    return {
      daytime: hourlyToday.filter((h) => {
        const hour = new Date(h.time).getHours();
        return hour >= 6 && hour < 18;
      }),
      evening: hourlyToday.filter((h) => {
        const hour = new Date(h.time).getHours();
        return hour >= 18 && hour < 22;
      }),
      overnight: hourlyToday.filter((h) => {
        const hour = new Date(h.time).getHours();
        return hour >= 22 || hour < 6;
      }),
    };
  }, [hourlyToday]);

  const overviewStats = useMemo(() => {
    if (!forecast || sortedDays.length === 0) return null;

    const highWindDays = sortedDays.filter(d => (d.felltop_max_gust_mph ?? 0) > windAlertThreshold).length;
    const highRainDays = sortedDays.filter(d => (d.precipitation_mm ?? 0) > rainAlertThreshold).length;
    const maxWind = Math.max(...sortedDays.map(d => d.felltop_max_gust_mph ?? 0));
    const totalRain = sortedDays.reduce((sum, d) => sum + (d.precipitation_mm ?? 0), 0);
    // Fell-top temperatures
    const maxFelltopTemp = Math.max(...sortedDays.map(d => d.felltop_max_temp_c ?? -999));
    const minFelltopTemp = Math.min(...sortedDays.map(d => d.felltop_min_temp_c ?? 999));
    // Valley temperatures
    const maxValleyTemp = Math.max(...sortedDays.map(d => d.max_temp_c ?? -999));
    const minValleyTemp = Math.min(...sortedDays.map(d => d.min_temp_c ?? 999));

    return { highWindDays, highRainDays, maxWind, totalRain, maxFelltopTemp, minFelltopTemp, maxValleyTemp, minValleyTemp };
  }, [sortedDays, forecast]);

  const riskSummary = useMemo(() => {
    if (!forecast || sortedDays.length === 0) return { precipitation: "Low", wind: "Low", visibility: "Good" };

    const maxPrecip = Math.max(...sortedDays.map(d => d.precipitation_mm ?? 0));
    const maxWind = Math.max(...sortedDays.map(d => d.max_wind_mph ?? 0));

    return {
      precipitation: maxPrecip > rainAlertThreshold ? "High" : maxPrecip > 10 ? "Medium" : "Low",
      wind: maxWind > windAlertThreshold ? "High" : maxWind > 25 ? "Medium" : "Low",
      visibility: "Good", // Placeholder - not available in current data
    };
  }, [sortedDays, forecast]);

  return (
    <div className="app-shell">
      <header className="main-header">
        <div className="header-left">
          <h1>Duddon & Furness MRT - Weather</h1>
          <p className="subtitle">
            {viewMode === "forecast" ? "7-day forecast" :
             viewMode === "historical7" ? "Previous 7 days" :
             viewMode === "historical14" ? "Previous 14 days" : "Previous 21 days"} for mountain rescue operations
          </p>
          {currentData && sortedDays.length > 0 && (
            <p className="meta-issued">
              {viewMode === "forecast" ? "Issued" : "Historical data"} {formatTime(currentData.run_timestamp)} ·
              {viewMode === "forecast" ? "Valid for" : "Covering"} {formatDate(sortedDays[0].date)} – {formatDate(sortedDays[sortedDays.length - 1].date)}
            </p>
          )}
          <div className="view-mode-toggle">
            <button
              className={`toggle-btn ${viewMode === "forecast" ? "active" : ""}`}
              onClick={switchToForecast}
            >
              📅 Forecast
            </button>
            <button
              className={`toggle-btn ${viewMode === "historical7" ? "active" : ""}`}
              onClick={loadHistoricalData7}
            >
              📊 Previous 7 Days
            </button>
            <button
              className={`toggle-btn ${viewMode === "historical14" ? "active" : ""}`}
              onClick={loadHistoricalData14}
            >
              📊 Previous 14 Days
            </button>
            <button
              className={`toggle-btn ${viewMode === "historical21" ? "active" : ""}`}
              onClick={loadHistoricalData21}
            >
              📊 Previous 21 Days
            </button>
          </div>
        </div>
        <div className="header-right">
          {sortedDays.length > 0 && sortedDays[0].sunrise && sortedDays[0].sunset && (
            <div className="daylight-info">
              <div className="sun-times">
                <div className="sun-time">
                  <span className="sun-label">Sunrise</span>
                  <span className="sun-value">{formatTime(sortedDays[0].sunrise)}</span>
                </div>
                <span className="sun-separator">•</span>
                <div className="sun-time">
                  <span className="sun-label">Sunset</span>
                  <span className="sun-value">{formatTime(sortedDays[0].sunset)}</span>
                </div>
              </div>
              <div className="daylight-duration">
                {calculateRemainingDaylight(sortedDays[0].sunrise, sortedDays[0].sunset)}
              </div>
            </div>
          )}
          <div className="meta-item">
            <span className="meta-label">Last updated:</span>
            <span className="meta-value">{forecast ? formatDateTime(forecast.run_timestamp) : "..."}</span>
          </div>
        </div>
      </header>

      <main>
        {loading && <p className="notice">Loading latest forecast…</p>}
        {error && <p className="notice notice-error">{error}</p>}
        {!loading && !forecast && <p className="notice">No forecast data yet.</p>}

        <section className="forecast-grid">
          {sortedDays.map((day, idx) => (
            <article
              key={day.date}
              className={`day-card ${severityClass(day)} ${selectedDayIndex === idx ? 'selected' : ''}`}
              onClick={() => setSelectedDayIndex(idx)}
              style={{ cursor: 'pointer' }}
            >
              <div className="day-tags">
                {day.tags.map(tag => (
                  <span key={tag} className={`tag tag-${tag.toLowerCase()}`}>{tag}</span>
                ))}
              </div>
              <div className="risk-indicator" data-risk={severityClass(day)}></div>
              <p className="day-label">{formatDate(day.date)}</p>
              <div className="weather-icon">{getWeatherIcon(day.weather_code)}</div>
              <div className="temp-range">
                <div className="temp-line">
                  <span className="temp-label">Valley:</span>
                  <span>{day.min_temp_c?.toFixed(0) ?? "?"} / {day.max_temp_c?.toFixed(0) ?? "?"} °C</span>
                </div>
                <div className="temp-line">
                  <span className="temp-label">Fell-tops:</span>
                  <span>{day.felltop_min_temp_c?.toFixed(0) ?? "?"} / {day.felltop_max_temp_c?.toFixed(0) ?? "?"} °C</span>
                </div>
              </div>
              <div className="day-stats">
                <div>
                  Wind: {day.felltop_max_wind_mph?.toFixed(0) ?? "N/A"} mph{" "}
                  {day.felltop_wind_direction !== null && (
                    <span className="wind-dir">{degreesToCompass(day.felltop_wind_direction)}</span>
                  )}
                </div>
                <div>Gust: {day.felltop_max_gust_mph?.toFixed(0) ?? "N/A"} mph</div>
                <div>Rain: {day.precipitation_mm?.toFixed(1) ?? "N/A"} mm</div>
                {day.min_freezing_level_m !== null && (
                  <div className="freezing-level">Freezing: {day.min_freezing_level_m.toFixed(0)} m</div>
                )}
              </div>
            </article>
          ))}
        </section>

        <section className="details-grid">
          <div className="detail-card">
            <h2>{selectedDay ? `${formatDate(selectedDay.date)} - Detail` : 'Today - Detail'}</h2>
            <div className="hourly-table-container">
              {selectedDayIndex > 0 && selectedDay ? (
                <div className="time-of-day-summary">
                  <div className="time-period">
                    <h3>Valley Conditions</h3>
                    <p>
                      Temperature: {selectedDay.min_temp_c?.toFixed(1) ?? "N/A"}°C to {selectedDay.max_temp_c?.toFixed(1) ?? "N/A"}°C
                      {selectedDay.wind_direction !== null && (
                        <> · Wind direction: {degreesToCompass(selectedDay.wind_direction)}</>
                      )}
                      <br />
                      Max wind: {selectedDay.max_wind_mph?.toFixed(0) ?? "N/A"} mph · Max gust: {selectedDay.max_gust_mph?.toFixed(0) ?? "N/A"} mph
                    </p>
                  </div>
                  <div className="time-period">
                    <h3>Fell-top Conditions (800m)</h3>
                    <p>
                      Temperature: {selectedDay.felltop_min_temp_c?.toFixed(1) ?? "N/A"}°C to {selectedDay.felltop_max_temp_c?.toFixed(1) ?? "N/A"}°C
                      {selectedDay.felltop_wind_direction !== null && (
                        <> · Wind direction: {degreesToCompass(selectedDay.felltop_wind_direction)}</>
                      )}
                      <br />
                      Max wind: {selectedDay.felltop_max_wind_mph?.toFixed(0) ?? "N/A"} mph · Max gust: {selectedDay.felltop_max_gust_mph?.toFixed(0) ?? "N/A"} mph
                    </p>
                  </div>
                  <div className="time-period">
                    <h3>Precipitation & Conditions</h3>
                    <p>
                      Precipitation: {selectedDay.precipitation_mm?.toFixed(1) ?? "N/A"} mm
                      {selectedDay.min_freezing_level_m !== null && (
                        <> · Freezing level: {selectedDay.min_freezing_level_m.toFixed(0)} m</>
                      )}
                      <br />
                      {selectedDay.sunrise && selectedDay.sunset && (
                        <>Sunrise: {formatTime(selectedDay.sunrise)} · Sunset: {formatTime(selectedDay.sunset)}</>
                      )}
                    </p>
                  </div>
                  <p className="info-message" style={{ marginTop: '1rem' }}>
                    Hourly breakdown only available for today. For extended forecasts, use MWIS/Met Office links below.
                  </p>
                </div>
              ) : selectedDayIndex === 0 && hourlyToday.length === 0 ? (
                <div className="no-data">
                  <p>Hourly breakdown not available for this source.</p>
                  <p className="suggestion">Use the forecast links below for more detailed hourly information.</p>
                </div>
              ) : (
                <>
                  <div className="time-of-day-summary">
                    {timeOfDaySplit.daytime.length > 0 && (
                      <div className="time-period">
                        <h3>Daytime (06:00-18:00)</h3>
                        <p>
                          Temp: {Math.min(...timeOfDaySplit.daytime.map(h => h.temperature_c ?? 999)).toFixed(0)}° –
                          {Math.max(...timeOfDaySplit.daytime.map(h => h.temperature_c ?? -999)).toFixed(0)}°C ·
                          Wind: up to {Math.max(...timeOfDaySplit.daytime.map(h => h.wind_mph ?? 0)).toFixed(0)} mph
                          {timeOfDaySplit.daytime[0]?.wind_direction !== null && (
                            <> {degreesToCompass(timeOfDaySplit.daytime[0].wind_direction)}</>
                          )}
                          {timeOfDaySplit.daytime[0]?.apparent_temperature_c !== null && (
                            <> · Feels like: {timeOfDaySplit.daytime[0]?.apparent_temperature_c.toFixed(0)}°C</>
                          )}
                        </p>
                      </div>
                    )}
                    {timeOfDaySplit.evening.length > 0 && (
                      <div className="time-period">
                        <h3>Evening (18:00-22:00)</h3>
                        <p>
                          Temp: {Math.min(...timeOfDaySplit.evening.map(h => h.temperature_c ?? 999)).toFixed(0)}° –
                          {Math.max(...timeOfDaySplit.evening.map(h => h.temperature_c ?? -999)).toFixed(0)}°C ·
                          Wind: up to {Math.max(...timeOfDaySplit.evening.map(h => h.wind_mph ?? 0)).toFixed(0)} mph
                          {timeOfDaySplit.evening[0]?.wind_direction !== null && (
                            <> {degreesToCompass(timeOfDaySplit.evening[0].wind_direction)}</>
                          )}
                        </p>
                      </div>
                    )}
                    {timeOfDaySplit.overnight.length > 0 && (
                      <div className="time-period">
                        <h3>Overnight (22:00-06:00)</h3>
                        <p>
                          Temp: {Math.min(...timeOfDaySplit.overnight.map(h => h.temperature_c ?? 999)).toFixed(0)}° –
                          {Math.max(...timeOfDaySplit.overnight.map(h => h.temperature_c ?? -999)).toFixed(0)}°C ·
                          Wind: up to {Math.max(...timeOfDaySplit.overnight.map(h => h.wind_mph ?? 0)).toFixed(0)} mph
                          {timeOfDaySplit.overnight[0]?.wind_direction !== null && (
                            <> {degreesToCompass(timeOfDaySplit.overnight[0].wind_direction)}</>
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="detail-card">
            <h2>🔺 Alerts for next 7 days</h2>
            {overviewStats && (
              <>
                {(overviewStats.highWindDays > 0 || overviewStats.highRainDays > 0) ? (
                  <p className="overview-summary">
                    {overviewStats.highWindDays > 0 && `High winds on ${overviewStats.highWindDays} of next 7 days. `}
                    {overviewStats.highRainDays > 0 && `Heavy rain on ${overviewStats.highRainDays} of next 7 days.`}
                  </p>
                ) : (
                  <p className="overview-summary">Conditions are generally favorable for the next 7 days.</p>
                )}
                <ul className="overview-bullets">
                  <li>Max wind: {overviewStats.maxWind.toFixed(0)} mph (fell-tops)</li>
                  <li>Total rain: {overviewStats.totalRain.toFixed(1)} mm</li>
                  <li>Fell-top temps: {overviewStats.minFelltopTemp.toFixed(0)}°C to {overviewStats.maxFelltopTemp.toFixed(0)}°C</li>
                  <li>Valley temps: {overviewStats.minValleyTemp.toFixed(0)}°C to {overviewStats.maxValleyTemp.toFixed(0)}°C</li>
                </ul>
              </>
            )}
          </div>

          <div className="detail-card">
            <h2>Risk summary</h2>
            <div className="risk-list">
              <div className="risk-item">
                <span className="risk-label">Precipitation:</span>
                <span className={`risk-badge risk-${riskSummary.precipitation.toLowerCase()}`}>
                  {riskSummary.precipitation}
                </span>
              </div>
              <div className="risk-item">
                <span className="risk-label">Wind:</span>
                <span className={`risk-badge risk-${riskSummary.wind.toLowerCase()}`}>
                  {riskSummary.wind}
                </span>
              </div>
              <div className="risk-item">
                <span className="risk-label">Visibility:</span>
                <span className={`risk-badge risk-${riskSummary.visibility.toLowerCase()}`}>
                  {riskSummary.visibility}
                </span>
              </div>
            </div>
          </div>

          <div className="detail-card">
            <h2>External mountain forecasts</h2>
            <p className="forecast-links-intro">Cross-check with trusted mountain forecast services:</p>
            <div className="forecast-links">
              <a
                href="https://www.mwis.org.uk/english-welsh-forecast/LD"
                target="_blank"
                rel="noopener noreferrer"
                className="forecast-link"
              >
                Open MWIS (Lake District)
              </a>
              <a
                href="https://www.metoffice.gov.uk/weather/specialist-forecasts/mountain"
                target="_blank"
                rel="noopener noreferrer"
                className="forecast-link"
              >
                Open Met Office Mountain Forecast
              </a>
            </div>
          </div>
        </section>

        <section className="notes-section">
          <h2>Notes for mountain rescue</h2>
          <p>
            Weather conditions can change rapidly at altitude. Always check current conditions before deployment.
            Wind speeds may be significantly higher on exposed ridges and summits. Fell-top temperatures shown are for 800m elevation.
          </p>
        </section>
      </main>
    </div>
  );
};

export default App;
