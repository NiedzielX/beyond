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

## Evidence JSON

The end-to-end runner expects:

```json
{
  "ticket_event_id": 5,
  "season": "2026/2027",
  "home_team_key": "lech",
  "opponent_key": "korona",
  "target_round_no": 0,
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
      "opponent_key": "...",
      "attendance": 0,
      "capacity_constrained_for_model": false
    }
  ],
  "stadium_capacity": 43269
}
```

Values above are structural examples only. Do not copy example opponent/result/
attendance values into a real run. Every real evidence row must be verified from
a point-in-time source.

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
- kickoff: 2026-10-18 17:30 Europe/Warsaw
- canonical T-7: 2026-10-11 17:30 Europe/Warsaw

The run should occur only after point-in-time evidence is verified. If the
complete league results or complete Lech home league attendance history cannot
be verified, do not persist the forecast.
