# Recovered v1.7 T-7 shadow runbook

## Purpose

Run the exactly recovered Lech Historical v1.7 T-7 champion as a separate
Beyond Demand Engine shadow forecast. This path must never overwrite or replace
production `beyond-forecast-v0.3` records.

## Model lineage

- point model: `lech-v17-t7-recovered-exact`
- engine observation version: `beyond-demand-engine-v1-v17-t7-shadow`
- feature set: `v17-t7-recovered-exact-v1`
- interval: `v17-split-conformal-80-v1:T-7`
- conformal radius: `8336.593429081528`
- live features: `live-features-v1`
- live correction: `live-correction-noop-v1`
- persistence RPC: `insert_demand_engine_shadow_forecast_v1`
- persisted status: `shadow`

## Canonical T-7 semantics

For target kickoff `K`:

1. Attendance-history state uses information available before the exact
   timestamp `K - 7 days`.
2. Sporting/table state uses completed Ekstraklasa matches whose **local
   Europe/Warsaw calendar date is strictly earlier** than the local date of
   `K - 7 days`.
3. A league match played on the local T-7 calendar date is excluded even when
   it finishes before the target match's exact T-7 clock time.
4. Cup/European attendance must not enter current-season league home attendance.
5. Table-position features are activated only when both Lech and the opponent
   have at least 10 completed league matches.
6. Gated position value is:
   `((league_team_count + 1) / 2) - raw_position`.
7. Ridge training uses completed prior seasons only; current-season completed
   Lech home matches update target attendance-history features but do not enter
   the Ridge training fold.
8. Live inventory is a demand proxy, not confirmed sales.
9. Live correction remains exactly zero until separately promoted.

## Fail-closed persistence preflight

`run_v17_t7_shadow.py` now calls `validate_t7_evidence()` before any model run.
A persisted shadow forecast is rejected unless all of the following hold:

- event id, home team, away team, competition and optional target kickoff match
  the live Supabase event;
- `league_team_keys` is a unique complete league list and contains both teams;
- every supplied league result belongs to that league and is unique;
- **no supplied league result is on or after the local T-7 calendar date**;
- every supplied Lech home-attendance row belongs to the target season, has a
  positive attendance and occurs strictly before the exact T-7 timestamp;
- duplicate Lech home-attendance rows are rejected;
- `expected_visible_league_results` equals the independently verified number of
  league results visible at the checkpoint;
- `expected_visible_home_attendance_rows` equals the independently verified
  number of eligible Lech home league attendance rows;
- an audit block records source URLs for schedule, league results and home
  attendance plus a timezone-aware `verified_at` timestamp.

Dry runs may omit the independent expected counts/source block to aid debugging,
but **persistence may not**. The persisted path therefore fails closed on
incomplete evidence rather than silently treating missing rows as real zero
history.

## Evidence JSON

Structural example:

```json
{
  "ticket_event_id": 5,
  "season": "2026/2027",
  "home_team": "Lech Poznań",
  "away_team": "Korona Kielce",
  "competition": "Ekstraklasa",
  "target_kickoff_at": "2026-10-18T17:30:00+02:00",
  "home_team_key": "lech",
  "opponent_key": "korona",
  "target_round_no": 11,
  "total_rounds": 34,
  "league_team_keys": ["..."],
  "completed_results": [
    {
      "kickoff_at": "2026-10-10T20:30:00+02:00",
      "home_team_key": "...",
      "away_team_key": "...",
      "home_goals": 0,
      "away_goals": 0
    }
  ],
  "current_season_home_attendance": [
    {
      "season": "2026/2027",
      "match_date": "2026-09-20T20:15:00+02:00",
      "opponent_key": "radomiak",
      "attendance": 19478,
      "capacity_constrained_for_model": false
    }
  ],
  "expected_visible_league_results": 0,
  "expected_visible_home_attendance_rows": 0,
  "stadium_capacity": 43269,
  "sources": {
    "schedule": ["https://..."],
    "league_results": ["https://..."],
    "home_attendance": ["https://..."],
    "verified_at": "2026-10-11T17:31:00+02:00"
  }
}
```

The zero counts and score/attendance values above are structural placeholders,
not values for a real run. Do not copy them into production evidence. Every real
evidence row and every expected count must be independently verified at the
checkpoint.

## Run

Dry run:

```bash
python -m ml.demand_engine.run_v17_t7_shadow \
  --event-id 5 \
  --evidence /path/to/event_5_t7_evidence.json \
  --dry-run
```

Persist shadow observation:

```bash
python -m ml.demand_engine.run_v17_t7_shadow \
  --event-id 5 \
  --evidence /path/to/event_5_t7_evidence.json
```

Required backend environment variables:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Never expose the service-role key to the dashboard/browser.

## Persistence safety

The Supabase RPC:

- accepts `forecast_status='shadow'` only;
- validates event and snapshot lineage;
- allocates `forecast_observations.id` server-side;
- is executable only by `service_role` / database owner;
- is idempotent for identical event + source snapshot + model version +
  forecast timestamp;
- stores model/calibration/live lineage in `payload`.

## First genuine future target

Current planned first real shadow target:

- `ticket_event_id = 5`
- Lech Poznań vs Korona Kielce
- competition: Ekstraklasa
- round: 11
- kickoff: 2026-10-18 17:30 Europe/Warsaw
- canonical T-7: 2026-10-11 17:30 Europe/Warsaw

Operational plan:

1. **2026-10-11 10:00 Europe/Warsaw** — evidence preflight task gathers and
   verifies all results/attendance/source counts after the 10 October fixtures,
   commits the auditable event evidence and performs dry-run only.
2. **2026-10-11 17:35 Europe/Warsaw** — canonical T-7 task re-verifies evidence,
   runs the exact model and persists the shadow observation only if all guards
   pass.

If the complete league results or complete Lech home league attendance history
cannot be verified, do not persist the forecast.
