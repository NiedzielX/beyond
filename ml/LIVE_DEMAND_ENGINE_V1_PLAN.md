# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-21**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED / TRACK A**  
> **d2 Stage 0: DONE**  
> **d2 Stage 1: DONE / ridge-a10 FROZEN**  
> **d2 Stage 2: DONE / P2-observation-maturity FROZEN**  
> **d2 prospective validation: ACTIVE IN TRACK A**  
> **Pre-Live v3 historical research candidate: FROZEN + SEALED / TRACK B**  
> **d2-v3 Stage 0 anchor equivalence/replay: ACTIVE NEXT**

Canonical documents:

- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
- `ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`;
- `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
- `AI_BOOTSTRAP.md`.

## Two-track rule

### Track A — frozen live validation

Keep the current v2/Ridge/P2 package unchanged and score new outcomes append-only.

### Track B — active model R&D

Pre-Live v3 is now a sealed research anchor:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Active next work is to determine whether the final-24h live anchor actually changes under v3 before any unnecessary d2 retraining.

> **Production promotion waits for prospective evidence. R&D does not.**

## Production boundary

Production remains:

`live_adjustment = 0`

Structural Prior remains production incumbent.

Neither frozen v2 nor frozen research v3 is production activation.

---

# Track A — frozen v2 live stack

Pre-Live v2:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Stage-1 expert:

`ridge-a10`

Stage-2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Stage-2 policy:

`P2-observation-maturity`

Frozen architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + P2_reliability(t) * ridge_delta(t)`

This stack remains the Track-A prospective benchmark.

---

# Track B — frozen Pre-Live v3 research anchor

Freeze ID:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Manifest:

`ml/artifacts/pre_live_v3_historical_candidate_v1/manifest.json`

Manifest SHA256:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Changed horizons only:

### T-30

Historical:

`0.75 current a2 + 0.25 XGBoost depth3`

Regime:

`NO_ADJUSTMENT`

### T-7

Historical:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Regime:

`ewma50-resid-k4-cap05-min2`

### T-14 / T-3 / T-1

Exact Frozen-v2 horizon package.

This detail matters for live modeling: **v3 T-1 is intentionally identical to v2 T-1**.

---

# d2 Stage 0 / Stage 1 / Stage 2 — current v2 lineage

## Stage 0

Exact Frozen-v2 compatibility established on:

- 9 independent events;
- 30 final-24h rows;
- exact frozen anchor lineage.

## Stage 1

Expert:

`ridge-a10`

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- Ridge window MAE `3619.19`;
- worst degradation `4326.90`.

Chronos-2 / Bolt-small did not beat plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

## Stage 2

Policy:

`P2-observation-maturity`

Development:

- latest MAE `3240.99`;
- latest uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`.

---

# d2-v3 Stage 0 — ACTIVE NEXT

Before creating any new live-model tournament, prove whether the frozen v3 anchor changes the existing final-24h d2 development rows.

## Exact input set

Reuse the exact frozen Stage-1 development identities:

- 9 events;
- 30 final-24h rows;
- exact event + `as_of_at` identity;
- no newly completed event enters selection.

## Required comparison

For every row reconstruct:

1. Frozen Pre-Live v2 anchor;
2. Frozen Pre-Live v3 research anchor;
3. difference in seats;
4. difference in occupancy share;
5. resulting v2 live residual target;
6. resulting v3 live residual target.

Hard assertions:

- same event set;
- same row set;
- same capacities;
- same actual-attendance labels;
- no future outcome enters anchor construction;
- no production write.

## Key equivalence hypothesis

The existing d2 replay is final-24h and historically anchored on the T-1 Pre-Live package.

Because v3 T-1 is exactly v2 T-1, the predeclared hypothesis is:

`H0: v3_anchor == v2_anchor for all frozen final-24h d2 rows`

This must be tested, not assumed.

Possible decisions:

### `V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

If every row is identical within a hard numerical tolerance:

- do **not** rerun a nominal d2 tournament merely because the Pre-Live version number changed;
- retain current d2 target lineage for final-24h rows;
- open the next live R&D cycle only for a materially different hypothesis, such as longer-than-24h live updating, new target formulation, learned reliability or richer PIT-safe signals.

### `V3_FINAL24_ANCHOR_DIFFERS_FROM_V2`

If any row differs:

- create a new d2-v3 residual target;
- rerun Stage-1 expert selection under event-level LOEO;
- revalidate reliability/tail governance under new IDs;
- retain v2/Ridge/P2 as benchmark.

---

# If d2-v3 target differs — Stage 1

Primary benchmark:

`v3-zero-correction`

External benchmark:

frozen v2/Ridge/P2 package.

Candidate set must remain compact and materially differentiated, e.g.:

- Ridge;
- Huber;
- HGB / LightGBM / CatBoost where justified by sample size;
- transparent inventory extrapolation;
- predeclared ensemble only if it adds a distinct hypothesis.

No random snapshot split.

Independent unit:

`event`

Evaluation:

`LOEO / event-balanced`

---

# Reliability / tail governance

If a new Stage-1 expert is warranted, reliability must be revalidated under a new policy ID.

Candidate PIT-safe signals may include:

- observation count;
- observation span;
- time to kickoff;
- correction magnitude;
- velocity / acceleration;
- stability / quality flags;
- disagreement magnitude.

Existing P2 remains a benchmark, not an inherited policy.

---

# Prospective validation continues in Track A

For each new completed event, persist:

1. Structural T-1 base;
2. Frozen Pre-Live v2;
3. raw frozen Ridge;
4. frozen P2;
5. genuine persisted comparator where available.

Evidence classes remain separate:

- `DELAYED_LABEL_HOLDOUT`;
- `TRUE_POST_FREEZE_PROSPECTIVE`.

Do not use Track-A outcomes to mutate the frozen v2/Ridge/P2 package.

---

# Continuous-time behavior

The live engine remains continuous over time-to-kickoff.

Named T-30/T-14/T-7/T-3/T-1 are evaluation checkpoints, not separate product modes.

A future live engine extending beyond final-24h must explicitly define how the pre-live anchor transitions across horizons; that is a materially different hypothesis from the existing final-24h d2 contract.

---

# Inventory interpretation

Public availability is a proxy, not confirmed paid sales.

Distinguish where possible:

- genuine demand movement;
- ticket releases;
- sector openings/closures;
- coverage changes;
- scrape/data anomalies.

---

# Promotion boundary

Historical/LOEO success is not production promotion.

Promotion requires materially more genuine prospective evidence, positive aggregate uplift, acceptable tail risk/bias, reproducible frozen lineage and explicit reviewed activation.

Until then:

`live_adjustment = 0`

## Immediate live-engine instruction

> **Keep v2/Ridge/P2 frozen in Track A. Pre-Live v3 is sealed in Track B. Run d2-v3 Stage 0 exact final-24h anchor equivalence before retraining anything; if v3 and v2 anchors are identical on the 9-event/30-row replay, do not create a cosmetic new live model version.**
