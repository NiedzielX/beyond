# Beyond Ticketing — c) Context meczu — audit v1

Last updated: **2026-10-18**  
Status: **AUDITED / FUTURE-FIXTURE CHALLENGER NOT PROVEN / NO PRODUCTION CHANGE**

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

## Gap tested: future fixtures / cannibalization

Future Fixture Context v1 tested:

### `future_timing`

- days from target match to next home fixture;
- next-home-within-7 flag;
- next-home-within-14 flag;
- count of additional home fixtures in next 7 / 14 / 30 days.

### `future_timing_attractiveness`

Adds the latest available context snapshot for the next home fixture only when that snapshot timestamp is `<= current as_of`:

- next opponent draw ratio mean / recent3;
- next opponent PPG;
- next opponent table position;
- next-vs-current opponent draw gap;
- time-decayed cannibalization proxy.

## Historical-schedule limitation

The committed five-season match dataset contains the **recorded final fixture timestamps**, not a versioned history of what the schedule looked like at each historical forecast timestamp.

Therefore the experiment is labeled:

`SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY`

It is research evidence only and cannot justify production promotion.

## Final result

Canonical evidence:

`ml/results/MATCH_CONTEXT_FUTURE_FIXTURE_V1_2026-10-18.md`

| Horizon | Selected option | Mean incumbent MAE | Mean challenger MAE | Result |
|---|---|---:|---:|---|
| T-30 | `NO_CONTEXT_EXTENSION` | 1,867.8 | 1,867.8 | no extension |
| T-14 | `NO_CONTEXT_EXTENSION` | 1,809.4 | 1,809.4 | no extension |
| T-7 | `future_timing_attractiveness` | **1,790.0** | 1,790.9 | not proven |
| T-3 | `NO_CONTEXT_EXTENSION` | 1,718.4 | 1,718.4 | no extension |
| T-1 | `future_timing_attractiveness` | **1,697.3** | 1,712.4 | not proven |

T-7 is effectively neutral/mixed: +0.13 MAE improvement in 2024/25 and -2.01 degradation in 2025/26.

T-1 is unstable: -37.96 degradation in 2024/25 and +7.65 improvement in 2025/26.

No horizon improves mean holdout MAE and no horizon improves both reference seasons.

## Squad availability

No governed historical point-in-time feed currently exists for:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

Do **not** backfill squad features from present-day or final-season sources. Add them only after a reliable historical PIT source exists.

## Decision

1. Keep the existing opponent / pair / sporting / table / past-congestion context unchanged.
2. Do not add Future Fixture Context v1 to Structural Prior.
3. Do not create historical schedule versioning solely to rescue this weak challenger.
4. Do not add squad context without a real PIT source.
5. Mark workstream **c) Context meczu — rozbudować** as audited/tested for the currently available safe data.
6. Move active development to **d) Live demand — najmocniej rozwinąć**.

## Implementation

Script:

`ml/match_context_future_fixture_v1.py`

Workflow:

`.github/workflows/match-context-future-fixture-v1.yml`
