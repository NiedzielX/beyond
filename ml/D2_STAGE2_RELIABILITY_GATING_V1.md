# Beyond Ticketing — d2 Stage 2 Reliability / Tail-Risk Gating v1

Last updated: **2026-10-19**

Status: **IMPLEMENTED CANDIDATE CONTRACT / AWAITING CANONICAL CI EVIDENCE / NO PRODUCTION CHANGE**

Parent result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Frozen Stage-1 research lead:

`ridge-a10`

Implementation:

`ml/d2_stage2_reliability_gating_v1.py`

Tests:

`ml/test_d2_stage2_reliability_gating_v1.py`

Workflow:

`.github/workflows/d2-stage2-reliability-gating-v1.yml`

## Objective

Stage 1 established that a simple learned live residual model can materially improve average MAE versus Frozen Pre-Live v2 on the 9-event development set.

However, raw Ridge still has unacceptable tail risk:

- latest-row MAE improves from `4128.01` to `3320.39`;
- latest-row improvement = `+807.62 seats` / `19.56%`;
- event-balanced window improvement = `+508.83 seats` / `12.33%`;
- latest-event improvement rate = `66.7%`;
- worst latest-event degradation = **`+4326.90 seats`**.

Therefore Stage 2 asks:

> **When should the model trust the Ridge live correction, shrink it, or ignore it and stay with Frozen Pre-Live v2?**

Stage 2 is a reliability/governance problem, not a new open-ended model-family tournament.

## Immutable development boundary

Development events remain exactly:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Development rows:

`30`

Independent unit:

`event`

Validation:

`LOEO`

Stage 2 must not use event `5` Lech Poznań–Korona Kielce outcome or trajectory when selecting reliability thresholds, weights, features, or policies.

Event `5` is reserved as a chronological/prospective holdout after Stage 2 is frozen.

The workflow reconstructs the exact development rows by `(ticket_event_id, as_of_at)` identity from the committed C1 training contract and hard-fails if event `5` appears in the Stage-2 development set.

## Frozen prediction expert

Base learned expert:

`ridge-a10`

Stage 2 reproduces the exact Stage-1 Ridge through the existing LOEO implementation and hard-checks its canonical metrics before evaluating any reliability policy.

Do not retune:

- Ridge `alpha=10.0`;
- target `target_live_delta_occupancy`;
- feature contract;
- median-imputation behavior;
- missing indicators;
- standardization;
- event-balanced weights;
- +/-10pp occupancy raw correction cap.

If any of these changes, that is a new model challenger and not Stage-2 policy tuning.

## Primary architecture

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

where:

`0 <= reliability(t) <= 1`

No policy may use actual attendance or future snapshots at decision time.

## Causal Stage-2 state

Stage 2 derives only PIT-safe state available at the exact row as-of:

- `stage2_observation_index`: 1, 2, 3, ... within the event trajectory;
- `stage2_observation_span_hours`: elapsed hours since the event's first Stage-2 observation;
- `hours_to_kickoff`;
- Stage-0 quality/release/coverage diagnostics;
- the out-of-fold Ridge proposed correction itself.

Attendance outcome is used only for evaluation after reliability has been calculated.

## Frozen Stage-2 policy tournament

No threshold search is performed. The policies and thresholds below are fixed before canonical evidence scoring.

### P0 — Frozen Pre-Live v2

`reliability = 0.00`

Purpose: incumbent anchor baseline.

### P1 — Raw frozen Ridge

`reliability = 1.00`

Purpose: Stage-1 research-lead baseline.

### P2 — Observation maturity

Observation-index reliability:

- first Stage-2 observation: `0.25`;
- second observation: `0.60`;
- third or later observation: `1.00`.

Time-to-kickoff cap:

- `hours_to_kickoff > 18`: maximum reliability `0.75`;
- `12 < hours_to_kickoff <= 18`: maximum reliability `0.90`;
- `hours_to_kickoff <= 12`: maximum reliability `1.00`.

Final P2 weight:

`min(observation_index_weight, time_weight)`

This policy uses no outcome information and no fitted thresholds.

### P3 — Correction magnitude

Use the already Stage-1-governed Ridge correction magnitude in occupancy points:

- `abs(delta) <= 0.025`: reliability `1.00`;
- `0.025 < abs(delta) <= 0.050`: reliability `0.80`;
- `0.050 < abs(delta) <= 0.075`: reliability `0.55`;
- `abs(delta) > 0.075`: reliability `0.35`.

Rationale: large live revisions are the main known tail-risk mechanism and require stronger shrinkage.

### P4 — Data quality

Start from:

`reliability = 1.00`

Soft warning cap to `0.50` when any is true:

- `release_activity_flag > 0.5`;
- `sector_coverage_change_flag > 0.5`;
- `max_visible_gap_hours > 12`.

Hard warning cap to `0.25` when any is true:

- `signal_ready < 0.5`;
- `feature_quality_good < 0.5`;
- `data_gap_detected > 0.5`;
- `unexplained_inventory_increase_flag > 0.5`.

Missing diagnostics use conservative contract defaults defined in code; no outcome-driven imputation is allowed.

### P5 — Compact combined reliability

`reliability = min(P2, P3, P4)`

This deliberately conservative composition prevents a strong score from one dimension from overriding a known weakness in another.

No additional policy variants or threshold grid are allowed in v1.

## Selection objective

Stage 2 is not allowed to optimize mean MAE alone.

Mandatory metrics:

- latest-row MAE;
- event-balanced window MAE;
- improvement vs Frozen v2;
- retained share of raw Ridge uplift;
- event improvement rate;
- worst latest-event degradation;
- p90 latest-event degradation;
- mean/max revision magnitude;
- mean reliability;
- full/zero reliability share;
- row bias.

## Frozen advancement gates

A Stage-2 policy P2-P5 is eligible only if all are true:

1. latest-row MAE is better than Frozen v2;
2. event-balanced window MAE is better than Frozen v2;
3. retained latest-row uplift is at least **50%** of raw Ridge uplift;
4. retained event-balanced window uplift is at least **50%** of raw Ridge uplift;
5. worst latest-event degradation is reduced by at least **25%** relative to raw Ridge.

Constants:

- `MIN_RETAINED_LATEST_UPLIFT = 0.50`;
- `MIN_RETAINED_WINDOW_UPLIFT = 0.50`;
- `MIN_WORST_DEGRADATION_REDUCTION = 0.25`.

Among eligible policies, selection is deterministic:

1. lowest latest-row MAE;
2. lowest event-balanced window MAE;
3. lowest worst latest-event degradation;
4. policy ID.

If no P2-P5 policy passes every gate:

`RAW_RIDGE_RETAINED_NO_STAGE2_POLICY_PASSED`

and `P1-raw-ridge` remains research lead without Stage-2 advancement.

## Canonical Stage-1 reproduction gates

Before policy scoring, Stage 2 must reproduce within `0.10 seat` tolerance:

- Frozen-v2 latest MAE: `4128.01`;
- raw Ridge latest MAE: `3320.39`;
- raw Ridge event-balanced window MAE: `3619.19`;
- raw Ridge worst latest-event degradation: `4326.90`.

A failure means lineage/model drift and invalidates Stage-2 evidence.

## Event 5 holdout rule

Reserved holdout:

- ticket event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

The outcome is already known operationally, but for model-governance purposes it was not used in Stage-1 selection and must not be used in Stage-2 policy design or selection.

After canonical Stage 2 evidence is persisted and the decision is frozen, score in one pass:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen Stage-2 governed Ridge if a policy advances;
4. frozen C1 v8 comparator where contract-compatible.

Score the whole trajectory and latest row.

No retuning after opening the holdout.

## Post-holdout roadmap

After event 5:

1. persist the holdout result regardless of outcome;
2. keep collecting append-only completed live events;
3. score the frozen d2 candidate prospectively on every new eligible event;
4. do not fold new outcomes into training until a separately versioned retraining cycle is declared;
5. require a materially larger independent event sample before production promotion.

## Chronos / TSFM boundary

Stage-1 decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet during Stage 2.

Reopen TSFM research only when:

- materially more independent trajectory events exist; or
- a materially different TSFM hypothesis is predeclared before evaluation.

## CI/CD evidence contract

Canonical Stage-2 evidence requires:

- committed implementation;
- committed tests;
- executable main-only workflow;
- pinned numpy/pandas/scikit-learn/joblib runtime;
- exact 9/30 split reconstruction;
- explicit event-5 exclusion gate;
- exact Stage-0 Frozen-v2 reconstruction;
- exact Stage-1 Ridge metric reproduction;
- machine-readable Stage-2 JSON;
- row-level policy prediction CSV;
- SHA256 evidence hashes;
- uploaded workflow artifact;
- committed human-readable result document;
- canonical state docs updated in the same evidence cycle.

No local-only result is canonical.

## Production boundary

Always during Stage 2:

- `production_change = false`;
- `promotion_allowed = false`;
- production `live_adjustment = 0`;
- Frozen Pre-Live v2 unchanged;
- frozen C1 v8 unchanged.

## One-line instruction

> **Freeze Stage-1 `ridge-a10` exactly. Evaluate only P0-P5 above on the original 9-event/30-row development lineage, with the 50%/50% uplift-retention and 25% tail-reduction gates fixed in advance. Do not inspect event 5 for selection. Persist canonical CI evidence first; only then open Lech-Korona once as the chronological holdout.**
