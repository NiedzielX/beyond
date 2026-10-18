# Beyond Ticketing — c) Context meczu — audit v1

Last updated: **2026-10-18**  
Status: **ACTIVE DEVELOPMENT / AUDIT COMPLETE / FUTURE-FIXTURE CHALLENGER NEXT**

## Purpose

Before adding more context, audit what the canonical point-in-time Structural Prior already contains and isolate the real gaps.

## Context already present and PIT-safe

The canonical feature store already contains substantial match context.

### Opponent demand / attractiveness

- `opponent_draw_n`;
- `opponent_draw_ratio_mean`;
- `opponent_draw_ratio_recent3`;
- `opponent_raw_attendance_mean`;
- home-vs-away pair history:
  - `pair_n`;
  - `pair_ratio_mean`;
  - `pair_ratio_recent2`;
  - `pair_attendance_mean`.

These are updated only after completed historical matches.

### Sporting strength and form

For both home and away teams:

- matches played;
- points;
- PPG;
- goal-difference per game;
- last-5 points;
- last-5 goal difference;
- days since last match;
- matches in previous 14 days.

### Table context

- home / away position;
- position gap;
- PPG gap;
- form gap;
- GD/game gap;
- combined PPG;
- combined table strength;
- top-4 / bottom-4 flags;
- late-season table interactions.

### Schedule context already present

Past schedule state is already represented through:

- home / away days since last match;
- `rest_gap`;
- previous-14-day match counts;
- `congestion_sum`.

## Real gaps

### 1. Future fixtures / cannibalization

The current store does **not** model:

- how soon the club's next home fixture occurs after the target match;
- how many additional home fixtures occur in the next 7 / 14 / 30 days;
- whether the next home opponent appears more attractive than the current opponent;
- a bounded proxy for potential demand cannibalization by that next home fixture.

This is the clearest first gap for workstream c).

### 2. Squad availability

No governed historical point-in-time feed currently exists for:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

Do **not** backfill squad features from present-day or final-season sources. Add them only after a reliable historical PIT source exists.

## Important historical-schedule limitation

The committed five-season match dataset contains the **recorded final fixture timestamps**, not a versioned history of what the schedule looked like at every historical forecast timestamp.

Therefore future-fixture features derived from it are labeled:

`SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY`

They can answer:

> Is future-home-fixture context promising enough to justify collecting/versioning schedule history?

They cannot by themselves justify production promotion, because historical reschedules may not be reconstructible exactly as known at T-30/T-14/etc.

## Future Fixture Context v1 challenger

The first challenger adds only future-home-fixture context on top of the untouched Structural Prior feature store.

Candidate groups:

### `future_timing`

- days from target match to next home fixture;
- next-home-within-7 flag;
- next-home-within-14 flag;
- count of additional home fixtures in next 7 / 14 / 30 days.

### `future_timing_attractiveness`

Adds the latest safely available context snapshot for the next home fixture where that snapshot timestamp is `<= current as_of`:

- next opponent draw ratio mean / recent3;
- next opponent PPG;
- next opponent table position;
- next-vs-current opponent draw gap;
- time-decayed cannibalization proxy.

If no prior snapshot of the next fixture exists yet, attractiveness fields remain missing and the model receives the missingness signal rather than future information.

## Evaluation protocol

For every T-30/T-14/T-7/T-3/T-1 horizon:

1. fit/predict the incumbent on the untouched canonical store;
2. hard-assert frozen incumbent holdout MAE;
3. choose between `NO_CONTEXT_EXTENSION`, `future_timing`, and `future_timing_attractiveness` on 2023/24 development only;
4. freeze that choice;
5. evaluate unchanged on 2024/25 and 2025/26;
6. never alter production automatically.

Even if a future-fixture variant improves both historical holdouts, the result remains **research evidence only** until historical schedule versioning is available.

## Implementation

Script:

`ml/match_context_future_fixture_v1.py`

Workflow:

`.github/workflows/match-context-future-fixture-v1.yml`
