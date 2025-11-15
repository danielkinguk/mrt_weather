# MRT Weather Summary Service – Functional Specification

File: `function.md`
Version: 0.1
Date: 2025-11-15
Owner: Duddon & Furness MRT (Weather Tool)

---

## 1. Purpose

Provide a simple, reliable way for the team to:

1. Store the last **7 days of issued weather forecasts** for the MRT area.
2. Extract a small set of **key weather statistics** per day.
3. Present these stats in a **simple “box table” view** that is easily
   accessible on:
   - Personal phones (Android/iOS)
   - Base computer(s)

This is intended as an operational planning aid for early winter
conditions (snow, ice, strong wind, heavy rain).

---

## 2. Scope

### In scope (MVP)

- Automatic retrieval of a **7-day weather forecast** for a configurable
  location (e.g. base grid ref / lat-long).
- Storage of **up to 7 days of forecast runs** (rolling window).
- Extraction of key forecast metrics for each forecast day.
- A simple tabular view (“box table”) of stats covering:
  - 7-day forecast horizon
  - Key metrics per day
- Read-only access for all team members via:
  - Mobile browser, and/or
  - Shared online document (e.g. Google Sheet, web page)

### Out of scope (for MVP)

- Multiple locations / microclimates.
- Fancy charts, maps or GIS integration.
- Alerting (SMS, push notifications, email).
- Integration with callout board (can be added later).
- Offline mode / caching on devices.

---

## 3. Users and Usage

### Users

- MRT Team Members
  - Need a quick daily sense check of conditions.
- Duty Leader / Controller
  - Uses it for incident planning and team safety briefings.
- Training Leads
  - Uses it when selecting venues and activities.

### Usage patterns

- Checked ad-hoc during the day (mobile).
- Checked at base before training / planned activities.
- Checked during incidents for short-term planning.

---

## 4. Data Source

The system shall use a **single forecast API** (implementation to choose
one, e.g. Open-Meteo or Met Office API) providing:

- 7-day (or longer) forecast horizon.
- Time-series or daily summary data including at least:
  - Air temperature
  - Wind speed and gusts
  - Precipitation (rain/snow)
  - Weather type / code

Requirements:

- No or minimal cost for expected request volume.
- Stable, documented API using HTTPS and JSON (preferred).
- Configurable latitude/longitude for MRT area.

---

## 5. Key Concepts

### 5.1 Forecast Run

A **forecast run** is one complete set of forecast data retrieved from
the weather API at a specific time (e.g. 06:00 or 18:00).

- Each run has:
  - A **run timestamp** (UTC + local time).
  - A set of **per-day forecast entries** (up to 7+ days).

The system stores the **last 7 forecast runs** only (rolling window).

### 5.2 Forecast Day Entry

For each day in a forecast run, the system derives a **Forecast Day
Entry**, including:

- Forecast date (local).
- Derived daily stats, e.g.:
  - Minimum temperature.
  - Maximum temperature.
  - Maximum sustained wind speed.
  - Maximum gust speed.
  - Total precipitation (rain + snow equivalent).
  - Dominant weather type (e.g. clear, showers, heavy rain, snow).
  - Optional: minimum freezing level or “feels like” temperature
    (if available from API).

The “box table” will show one row (or column) per **Forecast Day Entry**.

---

## 6. Functional Requirements

### FR1 – Location configuration

- FR1.1: The system must allow configuration of a **primary location**
  (latitude/longitude or similar).
- FR1.2: Location configuration must be editable by an administrator
  (not by general team members).

### FR2 – Scheduled forecast retrieval

- FR2.1: The system shall automatically retrieve a new forecast run
  **at least once per day**.
- FR2.2: The retrieval schedule (e.g. daily at 06:00, or twice daily at
  06:00 and 18:00 local time) must be configurable.
- FR2.3: If a scheduled retrieval fails (e.g. network error), the
  system must:
  - Log the failure.
  - Keep the last successful forecast available to users.

### FR3 – Forecast storage and retention

- FR3.1: The system shall store each **successful forecast run** with:
  - Run timestamp
  - Raw API response (or a parsed equivalent)
  - Derived per-day stats
- FR3.2: The system shall keep only the **last 7 forecast runs** and
  delete older runs automatically.
- FR3.3: Timezone shall be handled consistently (store UTC with
  clear conversion to local time display).

### FR4 – Data processing (stats extraction)

- FR4.1: For each forecast run, the system shall derive, for each
  forecast day (up to at least 7 days ahead):
  - Date (local).
  - Minimum and maximum temperature.
  - Maximum sustained wind speed.
  - Maximum gust speed.
  - Total precipitation (mm).
  - Primary weather type / code.
- FR4.2: If the API provides only hourly data, the system shall compute:
  - Min/Max over hourly values.
  - Total precipitation as sum over the day.
  - Max wind/gust as max over the day.
- FR4.3: Any unavailable metric must be clearly indicated (e.g. `N/A`)
  rather than left blank.

### FR5 – Box table view (UI)

- FR5.1: The system shall provide a **7-day box table** for the **latest
  forecast run**.
- FR5.2: The table must show a compact overview suitable for a small
  screen, including at minimum per day:
  - Date (day of week + date)
  - Min/Max temperature
  - Max wind speed (and ideally gust)
  - Total precipitation
  - Simple weather description or icon/text
- FR5.3: The layout shall be **mobile-friendly** and readable on a
  phone in portrait orientation.
- FR5.4: The system should support simple visual emphasis, e.g.:
  - Highlighting “high wind” days above a configurable threshold.
  - Highlighting heavy precipitation days above a threshold.

### FR6 – Access and sharing

- FR6.1: All team members shall be able to access the box table via:
  - URL opened in a mobile browser, or
  - Shared online document (e.g. Google Sheet) link.
- FR6.2: No login should be required for basic read-only access for the
  MVP (unless the chosen platform enforces it).
- FR6.3: The solution must allow easy bookmarking and/or QR-code linking
  from base.

### FR7 – Admin functions

- FR7.1: Basic admin tasks:
  - Configure location.
  - Configure API key (if required).
  - Configure retrieval schedule.
  - Configure thresholds (e.g. high wind, heavy rain).
- FR7.2: Admin operations may be performed by a small set of designated
  users (e.g. via platform permissions – Google Drive, web app login).

---

## 7. Non-functional Requirements

### NFR1 – Reliability

- The system should be resilient to occasional API or network issues.
- If a scheduled retrieval fails, the last successful forecast should
  remain visible.

### NFR2 – Performance

- Box table view should load in **< 2 seconds** on a typical 4G/5G
  connection.
- Scheduled jobs should finish within a few seconds; long-running tasks
  are not expected.

### NFR3 – Usability

- Must be understandable at a glance by non-technical team members.
- Minimal interaction: open the page / sheet and immediately see the
  latest 7-day summary.

### NFR4 – Security and privacy

- Only publicly available weather data is used.
- No personal data is processed.
- If API keys are required, they must be stored securely and not
  visible to general team members.

---

## 8. Implementation Notes (non-binding)

These are suggestions, not hard requirements, for the implementer:

- **MVP option (fastest):**
  - Google Sheet as storage + presentation.
  - Google Apps Script to:
    - Fetch forecast JSON from API on schedule.
    - Parse and populate daily stats rows.
    - Maintain only last 7 forecast runs.
  - “Dashboard” tab with the 7-day box table.

- **Future extension:**
  - Replace/augment Google Sheet with:
    - Small web service (Python/Node) + database.
    - Responsive web front-end.
    - Potential integration with callout board / resource manager.

---

## 9. Acceptance Criteria

The feature is considered “done” when:

1. A scheduled job is running and demonstrably:
   - Fetches **at least one** forecast run per day.
   - Stores up to **7 recent forecast runs**.
2. The box table view:
   - Shows **7 days of forecast** derived from the latest run.
   - Displays min/max temperature, wind, and precipitation per day.
   - Is readable on a typical smartphone.
3. Team members can:
   - Access the view from their phones and base computer via a URL or
     shared document link.
4. A short **one-page user guide** exists for:
   - How to open the table.
   - What each column/metric means.
   - Who to contact if it appears broken.

---