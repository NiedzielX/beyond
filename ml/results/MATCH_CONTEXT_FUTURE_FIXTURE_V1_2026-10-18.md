# Match Context Future Fixture v1 — 2026-10-18

Status: **COMPLETED / NOT PROVEN / RESEARCH-ONLY / NO PRODUCTION CHANGE**

## Evidence

GitHub Actions run: `39148803742`  
Main commit: `bfceeb9b48a5610f21008ea057981ff3d76307d5`  
Artifact: `match-context-future-fixture-v1-39148803742`  
Artifact id: `12144506059`  
Artifact SHA256: `75c5389ac35f8fcf1ae31a2e03c83e88b03cac557a012ac7d7a0d6f6ce744d11`  
Result JSON SHA256: `2198b44a943572f1ebb8f40ede8467f8b5206ecd1087854d5d298748282c3bad`

Evidence class:

`SCHEDULE_AS_RECORDED_RETROSPECTIVE_PROXY`

The historical dataset contains the final recorded fixture timestamps, not a versioned history of what the schedule looked like at each historical forecast timestamp. Therefore this experiment is research evidence only and cannot justify production promotion even if a challenger improves historical MAE.

## Audit result before the challenger

The canonical Structural Prior already contains substantial PIT-safe context:

- opponent demand history and recent draw;
- home-vs-opponent pair history;
- home/away PPG and GD/game;
- last-5 form for both teams;
- table positions and gaps;
- top/bottom-table interactions;
- past rest and previous-14-day congestion.

The clearest remaining safe-to-test gap was future home-fixture timing / cannibalization. Squad injuries/suspensions were not tested because no reliable historical PIT feed exists.

## Candidate variants

- `NO_CONTEXT_EXTENSION`;
- `future_timing`;
- `future_timing_attractiveness`.

The richer challenger includes next-home-fixture timing plus the latest available context snapshot for that future fixture only when `future_fixture_snapshot.as_of_at <= current_as_of`.

## Protocol

- development train: 2021/22–2022/23;
- variant selection: 2023/24 only;
- frozen reference holdouts: 2024/25 and 2025/26;
- incumbent Structural Prior fitted/scored before challenger-only columns are added;
- exact frozen incumbent holdout MAE hard-asserted;
- no automatic promotion;
- production unchanged.

## Result by horizon

| Horizon | Selected on development | Signal | Mean incumbent MAE | Mean challenger MAE | Delta vs incumbent |
|---|---|---|---:|---:|---:|
| T-30 | `NO_CONTEXT_EXTENSION` | `NO_CONTEXT_EXTENSION_SELECTED` | 1,867.8 | 1,867.8 | 0.0 |
| T-14 | `NO_CONTEXT_EXTENSION` | `NO_CONTEXT_EXTENSION_SELECTED` | 1,809.4 | 1,809.4 | 0.0 |
| T-7 | `future_timing_attractiveness` | `NOT_PROVEN` | **1,790.0** | 1,790.9 | -0.9 |
| T-3 | `NO_CONTEXT_EXTENSION` | `NO_CONTEXT_EXTENSION_SELECTED` | 1,718.4 | 1,718.4 | 0.0 |
| T-1 | `future_timing_attractiveness` | `NOT_PROVEN` | **1,697.3** | 1,712.4 | -15.2 |

No horizon has positive mean holdout improvement. No horizon improves both reference seasons.

## Holdout detail

### T-7

Development chooses `future_timing_attractiveness`, but the holdout effect is effectively neutral/mixed:

- 2024/25: 1,777.69 -> 1,777.57 MAE, improvement **+0.13**;
- 2025/26: 1,802.28 -> 1,804.28 MAE, degradation **-2.01**.

Mean effect: **-0.94 MAE**.

### T-1

Development also chooses `future_timing_attractiveness`, but the reference seasons disagree materially:

- 2024/25: 1,651.73 -> 1,689.69 MAE, degradation **-37.96**;
- 2025/26: 1,742.84 -> 1,735.18 MAE, improvement **+7.65**.

Mean effect: **-15.15 MAE**.

### Coverage of the future-fixture signal

On the T-7/T-1 holdouts:

- next recorded home fixture known for ~**94%** of rows;
- next home fixture within 14 days for ~**38%** of rows;
- next-fixture context snapshot available for roughly **80–86%** of rows, depending on horizon/season.

The lack of improvement is therefore not explained simply by near-zero feature coverage.

## Decision

1. **Do not add Future Fixture Context v1 to Structural Prior.**
2. Do not create a schedule-history collection project solely to rescue this challenger; the current retrospective signal is not strong enough to justify that work.
3. Keep existing opponent/form/table/past-congestion context unchanged.
4. Do not backfill squad context without a reliable historical PIT source.
5. Mark workstream **c) Context meczu — rozbudować** as audited and tested for the currently available safe data; no new context extension is proven.
6. Move active development to **d) Live demand — najmocniej rozwinąć**.
7. Frozen C1 v8 and production `live_adjustment = 0` remain unchanged.
