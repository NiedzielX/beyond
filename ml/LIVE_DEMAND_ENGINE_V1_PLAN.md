# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-15**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting / Step 6: ACTIVE**  
> **Step 6a StructuralPrior adapter: DONE**  
> **Step 6b executable Structural Prior runtime + materialization: ACTIVE**

| Phase | Step | Scope | Status |
|---|---:|---|---|
| A — Foundation | 1 | Canonical LiveTrajectoryFeatureStore | **DONE** |
| A — Foundation | 2 | Exact-cutoff checkpoint/readiness integration | **DONE** |
| A — Foundation | 3 | Robust release / anomaly semantics | **DONE** |
| A — Foundation | 4 | Append-only PIT live feature evidence store | **DONE** |
| A — Foundation | 5 | Versioned live contract registry | **DONE** |
| B — Shadow Forecasting | 6a | StructuralPrior adapter + model-domain guard | **DONE** |
| B — Shadow Forecasting | 6b | Executable Structural Prior runtime + genuine P50 materialization | **ACTIVE** |
| B — Shadow Forecasting | 7 | Expected trajectory / trajectory gap | TODO |
| B — Shadow Forecasting | 8 | Persist shadow live forecasts | TODO |
| B — Shadow Forecasting | 9 | Persist first detection + forecast revisions | TODO |
| B — Shadow Forecasting | 10 | Keep live correction shadow-only until evidence is sufficient | TODO |
| C — Learned Correction | 11–14 | Train / evaluate residual live correction | BLOCKED ON EVIDENCE |
| D — Probabilistic | 15–17 | Calibrated P10/P50/P90 live trajectories | TODO |
| E — Recommendations | 18–20 | Recommendation / intervention layer | LATER |

## Purpose

Build a leakage-safe live forecasting system that continuously answers:

1. **Where is this match expected to finish?**
2. **Is current demand evolving better or worse than it should?**
3. **Did we detect the divergence early enough for the club to act?**

The product equation remains:

`Live Forecast(t) = Structural Prior(t) + Live Trajectory Correction(t)`

and

`Trajectory Gap(t) = Observed Live Trajectory(t) - Expected Trajectory(t)`

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong intervention / correction;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration.

T-1/T-3 accuracy remains important, but early actionable horizons are the product priority.

# Phase A — Foundation — DONE

## 1. Canonical live trajectory features

Current semantics: `live-trajectory-v1.1`.

Includes:

- point-in-time inventory level;
- 6h / 24h / 72h / 7d velocity;
- acceleration / deceleration;
- public-seat-map and capacity normalization where valid;
- sector absorption, re-availability and coverage changes;
- snapshot quality / stale data / gap telemetry;
- release/anomaly semantics.

Material matched-sector release threshold:

`max(50 seats, 0.5% of first observed inventory)`

Public ticket inventory is treated as a **demand proxy, not confirmed paid sales**.

## 2. Exact-cutoff readiness

Current contract:

`private.ticketing_horizon_readiness_v2_1`

The old nearest-snapshot readiness v1 is lineage only and must not be used for new modelling because it could select evidence after the intended checkpoint.

## 3. Append-only live evidence

Current evidence store:

`private.live_trajectory_feature_snapshots_v1`

Initial exact-checkpoint materialization:

- 31 rows;
- 0 leakage violations;
- 0 time violations;
- 0 PIT validation failures;
- 0 feature-version mismatches;
- idempotent replay.

Training-eligible evidence currently remains small:

| Horizon | Training-eligible |
|---|---:|
| T-30 | 0 |
| T-14 | 3 |
| T-7 | 3 |
| T-3 | 2 |
| T-1 | 5 |

Therefore learned live correction remains shadow-only / not ready.

# Phase B — Shadow Forecasting

## Step 6a — StructuralPrior adapter — DONE

Implemented:

- current model spec per horizon;
- exact PIT/model/feature lineage validation;
- carry-forward only from an already-due checkpoint;
- no lookahead to a future horizon;
- no silent fallback to old Lech models;
- append-only `private.structural_prior_forecasts_v1`;
- resolver `public.get_structural_prior_v1`;
- explicit states: `not_due`, `out_of_domain`, `missing_prior`, `invalid_prior`, `ready`;
- current validated model domain = **Ekstraklasa**.

UEFA fixtures are therefore `out_of_domain` for the current historical champion even if live ticket collection exists for them.

## Step 6b — Executable Structural Prior runtime — ACTIVE

### Historical runtime feature contract

Implementation:

`ml/features/structural_prior_feature_store_v1.py`

Rules:

- five seasons, 1,530 matches;
- 7,650 PIT snapshots;
- attendance history may carry across seasons;
- sporting/form/table state resets per season;
- match state enters only after `kickoff + 3h`;
- target never enters its own state;
- exact home/opponent pair history is PIT-only;
- opponent draw is PIT-only;
- verified season/venue-specific stadium capacity;
- known closed-door zero-attendance event excluded from normal demand training.

Exact historical input hashes are pinned in:

`ml/data/STRUCTURAL_PRIOR_RUNTIME_V1_INPUT_MANIFEST.md`

### Early-horizon champion candidates recovered as executable runtime

Benchmark:

`ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md`

Selection rule remains frozen:

- train candidates on 2021/22–2022/23;
- choose on 2023/24 only;
- evaluate untouched 2024/25;
- refit through 2024/25 and evaluate untouched 2025/26.

Current results:

| Horizon | Runtime spec | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| **T-30** | ExtraTrees + full PIT + verified-capacity occupancy residual | **1,889.4** | **1,846.3** |
| **T-14** | HistGBR + base PIT + verified-capacity occupancy residual | **1,748.5** | **1,870.4** |

Previous verified-capacity champion:

- T-30: `1,998.7 / 1,994.6`;
- T-14: `1,869.8 / 1,960.3`.

Decision:

- T-14 becomes the preferred current historical candidate;
- T-30 becomes the preferred current historical candidate but R&D continues toward the strategic **<1,700 MAE** target;
- historical prior improvements do **not** count as live uplift.

### Remaining Step 6b work

Step 6 is not closed until all of the following are true:

1. build the current-event PIT Structural Prior feature row from information available at the requested checkpoint;
2. fit the approved horizon runtime on the approved historical seasons;
3. generate a genuine current P50 for an eligible future **Ekstraklasa** event;
4. persist it into `private.structural_prior_forecasts_v1`;
5. persist exact model spec, feature contract, dataset hashes, training seasons, capacity and target checkpoint lineage;
6. update DB current T-30/T-14 specs to the new runtime IDs;
7. finish the missing 2021/22–2024/25 Supabase historical backfill so DB-native rebuilds do not depend on external local files.

**Do not start Step 7 by inventing or proxying a Structural Prior row.**

## Step 7 — Expected trajectory / trajectory gap — TODO

Only after a genuine current Structural Prior exists.

Initial implementation may use descriptive / rule-based expected trajectory references where live sample size is too small for credible ML.

Core outputs:

- expected demand progress;
- observed demand progress;
- level gap;
- velocity gap;
- acceleration gap;
- `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- confidence / data-quality state.

## Step 8 — Shadow forecasts — TODO

Persist every eligible revision with:

- Structural Prior P50;
- current live evidence version;
- live correction;
- resulting shadow P50;
- later P10/P90;
- reason codes and signal quality.

## Step 9 — First detection / revisions — TODO

First detection is a product KPI, not telemetry noise.

Persist:

- first divergence timestamp;
- first horizon / lead time;
- direction and magnitude;
- every subsequent forecast revision;
- whether additional evidence improved or destabilised the forecast.

## Step 10 — Promotion gate — TODO

No live correction auto-promotion from tiny evidence.

For identical completed events/checkpoints compare:

1. Structural Prior error;
2. Structural Prior + live correction error.

Evaluate by horizon and club using MAE, WAPE, bias, event-improvement rate and early-warning lead time.

# Phase C — Learned live correction

When sufficient completed events exist:

`live_target_residual = actual_attendance - structural_prior_p50`

Candidate predictors include:

- trajectory gap;
- normalized inventory position;
- multi-window velocity;
- acceleration;
- scarcity;
- sector movement;
- material release / coverage flags;
- data quality;
- days to kickoff;
- selected Structural Prior × live-signal interactions.

Promote only if unseen-event error improves under the same point-in-time protocol.

# Phase D — Probabilistic live forecast

Add calibrated:

- P10;
- P50;
- P90.

Evaluate pinball loss and interval coverage separately by horizon. Do not fabricate intervals from legacy models.

# Phase E — Recommendations

Only after forecasting and early-warning reliability are proven:

- translate a reliable trajectory state into club actions;
- keep recommendations separate from the truth/forecast layer;
- eventually learn intervention effectiveness from observed action → post-action trajectory changes.

# Immediate coding backlog

1. **NOW — current-event Structural Prior PIT feature builder / scorer.**
2. Materialize first genuine T-30/T-14 P50 for an in-domain future fixture.
3. Update DB current runtime model IDs and lineage.
4. Continue T-30 historical R&D toward **<1,700 MAE** in parallel.
5. Finish historical Supabase backfill.
6. Start Step 7 only after Step 6b closes.

# Definition of v1 success

Live Demand Engine v1 succeeds when it can, on unseen completed events:

1. reproduce a versioned Structural Prior;
2. build a leakage-safe live ticket trajectory;
3. identify whether the event is ahead / on track / behind expected behaviour;
4. update the final forecast without future information;
5. demonstrate incremental live uplift over the same Structural Prior;
6. record when divergence first became reliably detectable;
7. provide calibrated uncertainty once sufficient evidence exists.

**Beyond should predict where demand is heading and detect meaningful divergence early enough for the club to act.**
