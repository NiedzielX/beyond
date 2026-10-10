# Beyond Weather Telemetry v1 — 2026-10-10

## Purpose

Collect weather **forecasts available before kickoff** so weather can later be tested as a no-leakage attendance feature.

Weather is not used by the production forecast or by frozen Live Signal Study v1.

## Provider

Open-Meteo Weather Forecast API.

The collector uses the hourly forecast endpoint with a 16-day forecast horizon and captures:

- temperature at 2m;
- apparent temperature;
- precipitation probability;
- precipitation amount;
- WMO weather code;
- cloud cover;
- wind speed at 10m;
- wind gusts at 10m.

## Location semantics

Current location quality is `city_centroid` resolved through Open-Meteo geocoding for the home club city.

This is intentionally not labelled as exact stadium weather.

The schema supports a future `stadium_exact` location quality.

## Prospective capture contract

Supabase Edge Function:

`weather_collect_v1`

Cron:

`weather_forecast_capture_6h`

Schedule:

`17 */6 * * *`

For every future ticket event within the 16-day forecast window:

1. resolve or reuse the club weather location;
2. request the forecast in one multi-location Open-Meteo batch;
3. choose the hourly forecast closest to kickoff;
4. store the forecast together with the actual collection timestamp;
5. preserve `hours_to_kickoff` at collection time;
6. do not write another weather snapshot if the previous capture is less than five hours old.

The batch approach was introduced after the first parallel implementation hit Open-Meteo HTTP 429 responses. The corrected v2 collector completed a full batch successfully.

## Database objects

### `club_weather_locations`

Stores resolved location coordinates and location quality.

### `weather_forecast_observations`

Stores immutable prospective weather forecast snapshots:

- `ticket_event_id`
- `captured_at`
- `forecast_for_at`
- `hours_to_kickoff`
- provider/model
- location coordinates/quality
- temperature/apparent temperature
- precipitation probability/amount
- wind speed/gusts
- cloud cover
- weather code

The table is backend-only.

### `get_weather_feature_store_v1()`

Returns at most one strict weather observation per event for:

- T-14
- T-7
- T-3
- T-24h

Selection is one-sided: the weather forecast must have been captured before the target checkpoint. There is no post-checkpoint fallback.

### `multiclub_feature_store_v4`

Extends Multi-Club Feature Store v3 with strict weather candidate features.

Weather columns are prefixed `weather_` and include `weather_feature_available`.

This is a research feature store only.

## Dashboard projections

Browser-safe projections expose only the fields needed by the POC UI:

- `dashboard_ml_readiness_v1`
- `dashboard_event_live_state_v1`
- `dashboard_weather_latest_v1`

Backend research functions remain service-role protected. The browser views use narrow security-definer wrappers rather than opening the underlying research RPCs to anonymous users.

## Dashboard integration

`BeyondTicketingPanel` now shows:

### Forecast Accuracy

`Live Signal Research Readiness` with:

- independent outcomes vs 8-event exploratory cross-club gate;
- clubs with outcomes vs 3-club diversity gate;
- independent outcomes vs 20-event live-correction benchmark gate;
- strict study row count.

### Event Detail

`Demand Signals`:

- inventory index;
- public seat-map availability where verified;
- 6h / 24h velocity;
- acceleration;
- raw snapshot history;
- release activity;
- sector coverage change;
- feature quality.

`Weather at kickoff`:

- temperature / apparent temperature;
- precipitation probability / amount;
- wind / gusts;
- cloud cover / weather code;
- forecast capture timestamp;
- provider/model;
- location quality.

## Current rule

Do not add weather to a fitted attendance or live-correction model merely because telemetry exists.

First evaluate it under the same event-grouped, strict as-of protocol used by the rest of Beyond.
