# MRT Weather Summary Service - AI Agent Instructions

## Project Overview

This is a Mountain Rescue Team (MRT) weather planning tool for Duddon & Furness MRT. The goal is to provide a simple, mobile-friendly 7-day weather forecast summary to help team members assess conditions for operational planning (snow, ice, strong wind, heavy rain).

**Key constraint**: This is an MVP focused on simplicity, reliability, and mobile accessibility. Avoid over-engineering.

## Architecture & Implementation Strategy

### Priorities & preferred stack

The user is targeting a **Python or Node.js backend coupled with a React or Svelte front-end** so the UI can look polished on mobile and desktop.
- Keep the backend focused on aggregating hourly API data into daily stats, caching the last seven runs, and exposing a compact API for the UI.
- Deliver a responsive box-table page (React or Svelte) with configurable alerts and stylistic cues for severe conditions.
- Host on a modern platform (Vercel, Netlify, Cloud Run, small VPS) that can run scheduled jobs without relying on Google Workspace.

If you need to prototype quickly, the original **Google Apps Script + Google Sheets** path is acceptable as long as you document how to move to the preferred stack later.

### Data Source Selection & location

Use a free/low-cost weather API (see `spec.md` section 4):
- **Open-Meteo** (recommended): Free, no API key, provides hourly data for 7+ days
- **Met Office API**: UK-specific, requires API key
- Must provide: temperature, wind speed/gusts, precipitation, weather codes

**API endpoint pattern**: `/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,windspeed_10m,windgusts_10m,precipitation,weathercode`

**Primary coordinates**: `54.2586° N, 3.2145° W` (Duddon & Furness area).

### Key Domain Concepts

1. **Forecast Run**: One complete API fetch at a specific timestamp (e.g., 06:00 daily)
   - Store: run timestamp (UTC), raw/parsed API response, derived daily stats
   - Retention: Keep only last 7 runs, auto-delete older

2. **Forecast Day Entry**: Aggregated daily statistics from hourly data
   - Derive: min/max temp, max wind/gust, total precipitation (sum), dominant weather type
   - Display: 7 days ahead from latest run

3. **Rolling Window**: Always maintain exactly 7 most recent forecast runs to track forecast changes over time

## Critical Functional Requirements

### Data Processing (FR4)

When API provides **hourly data**, aggregate to daily stats:
- Temperature: `MIN()` and `MAX()` across all hours in day
- Wind/Gust: `MAX()` across all hours in day  
- Precipitation: `SUM()` across all hours in day (convert to mm)
- Weather type: Most frequent code or worst condition in day

**Important**: Show `N/A` for missing data, never leave blank (FR4.3).

### Timezone Handling (FR3.3)

- Store all timestamps in **UTC** internally
- Convert to **local time** (UK time) for display
- Forecast day boundaries: Use local midnight (00:00) not UTC

### Scheduled Retrieval (FR2)

- Default schedule: run twice daily (06:00 and 18:00 UK time) but make this configurable in case weather cadence changes.
- On failure: log the error, keep the previous run visible, and surface the failure in the admin log or notification channel.
- Prefer platform-native schedulers (Cloud Scheduler, GitHub Actions, cron) when using the Python/Node.js stack; Apps Script time-driven triggers remain an acceptable fallback for quick prototypes.

### Box Table View (FR5)

Mobile-first design requirements:
- Columns per day: Date (day of week + date), Min/Max Temp, Max Wind (+ gust), Precipitation, Weather icon/text
- Visual emphasis: Highlight high wind (e.g., **> 40 mph**) or heavy rain (e.g., **> 20 mm**) via color/typography contrasts; expose these thresholds in config so they can be tuned.
- Readable in portrait mode on phone screens

## Configuration & Admin

- Configuration values (store in Sheet "Config" tab, script properties, or backend config service):
  - Primary location: Latitude/Longitude (default to `54.2586° N, 3.2145° W`, editable by admins)
  - API endpoint/key (if needed)
  - Retrieval schedule (cron-like or time of day)
  - Alert thresholds: Use `> 40 mph` for wind warnings and `> 20 mm` for heavy rain, but keep these values configurable.

**Access control**: Admin functions (location, schedule, thresholds) editable by designated users only. General team members: read-only access.

## Testing & Validation

### Acceptance Criteria (from spec.md section 9)

MVP is "done" when:
1. Scheduled job runs daily and stores up to 7 forecast runs
2. Box table shows 7-day forecast with min/max temp, wind, precipitation
3. View is readable on smartphone
4. Team can access via URL/link from any device
5. One-page user guide exists (how to access, interpret metrics, report issues)

### Edge Cases to Handle

- API timeout or error: Preserve last successful forecast, log failure
- Missing hourly data points: Mark individual metrics as `N/A`
- Leap days, DST transitions: Use robust date library
- First run (no history): Display only current forecast, note "historical runs pending"

## Code Organization (for future non-Google-Sheets implementation)

If migrating from Google Sheets to standalone service:
```
/src
  /api          - Weather API client, fetch & parse logic
  /models       - ForecastRun, ForecastDayEntry data structures
  /aggregation  - Hourly → daily stats computation
  /storage      - Database layer (rolling window management)
  /ui           - Box table rendering (HTML/CSS)
/config         - Location, API keys, thresholds
/scripts        - Scheduled job trigger
```

### Current code layout

- `backend/`: FastAPI service that aggregates Open-Meteo data, caches the last seven runs in `backend/data/`, and exposes `/api/forecast/*` endpoints for the UI and scheduler.
  - `backend/app/`: Config, schema, storage, and service modules.
  - `backend/scripts/run_fetch.py`: CLI entrypoint used by cron or GitHub Actions to capture the latest forecast.
  - `backend/tests/`: Pytest modules that exercise the aggregation helpers.
- `frontend/`: Vite + React UI that polls `/api/forecast/latest` and renders the seven-day box table.
  - `frontend/src`: Main presentation layer.
  - `frontend/vite.config.ts`: Sets up proxy to `/api` during development.

## Non-Goals (Out of Scope for MVP)

Per `spec.md` section 2:
- ❌ Multiple locations/microclimates
- ❌ Charts, maps, GIS integration
- ❌ Alerting (SMS, push, email)
- ❌ Callout board integration
- ❌ Offline mode/device caching

Focus on the core: reliable 7-day summary table accessible from mobile browsers.

## User Personas & Use Cases

- **Team Member**: Quick daily condition check on phone while commuting
- **Duty Leader**: Incident planning & safety briefings at base
- **Training Lead**: Venue/activity selection based on forecast

**Usage pattern**: Ad-hoc mobile checks throughout the day, not continuous monitoring.

## Further Reading

- Full specification: `spec.md` (contains all FRs, NFRs, and rationale)
- Weather API docs: [Open-Meteo](https://open-meteo.com/en/docs) or [Met Office DataPoint](https://www.metoffice.gov.uk/services/data/datapoint)
- Google Apps Script: [Time-driven triggers](https://developers.google.com/apps-script/guides/triggers/installable#time-driven_triggers)
