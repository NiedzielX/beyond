# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-19**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED**  
> **d2 Stage 0 Frozen-v2 replay compatibility: DONE / GREEN**  
> **d2 Stage 1 live-residual tournament: DONE / ridge-a10 research lead**  
> **d2 Stage 2 reliability / tail-risk gating: ACTIVE**

Canonical documents:

- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/CURRENT_MODEL.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
- `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`;
- `AI_BOOTSTRAP.md`.

## Critical architecture state

### Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

### Current d2 architecture

After Stage 1:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen Stage-1 expert:

`ridge-a10`

The current problem is not selecting a more complex expert. It is deciding when live evidence is reliable enough to apply the expert's correction.

## Runtime / production boundary

Production remains:

`live_adjustment = 0`

Structural Prior remains production incumbent.

Frozen Pre-Live v2 is not automatically production.

Frozen C1 v8 remains:

`EXPERIMENTAL_SHADOW`

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Do not retune C1 v8 as part of d2.

---

# d2 Stage 0 — COMPLETE

Stage 0 established exact compatibility between the frozen C1 live replay lineage and Frozen Pre-Live v2.

Development lineage:

- 9 events;
- 30 final-24h rows;
- all rows exact Frozen-v2 anchor.

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Diagnostic event MAE on this specific small replay set:

- legacy Structural Prior: `3968.73`;
- Frozen Pre-Live v2: `4128.01`.

This does not reopen historical b2.

---

# d2 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Research lead:

`ridge-a10`

Canonical run:

`39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

## Frozen Stage-1 expert contract

- target: `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- median imputation inside training fold;
- missing indicators;
- standardization;
- event-balanced sample weights;
- event-level LOEO;
- final raw correction capped at +/-10pp occupancy.

Do not retune these during Stage 2.

## Stage-1 results

| Candidate | Latest MAE | Latest uplift | Window MAE | Window uplift | Improvement rate | Worst degradation |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v2 | 4,128.01 | 0.00 | 4,128.01 | 0.00 | 0.0% | 0.00 |
| Inventory extrapolation | 3,869.68 | +258.33 | 3,701.05 | +426.97 | 44.4% | 3,100.60 |
| **Ridge `alpha=10`** | **3,320.39** | **+807.62** | **3,619.19** | **+508.83** | **66.7%** | **4,326.90** |
| Ridge + Chronos-2 | 3,428.25 | +699.76 | 3,645.19 | +482.82 | 66.7% | 4,326.90 |
| Ridge + Bolt-small | 3,428.08 | +699.93 | 3,658.58 | +469.43 | 66.7% | 4,326.90 |

Ridge latest-row relative MAE improvement:

**19.56%**

Ridge event-balanced window improvement:

**12.33%**

Mean absolute Ridge revision:

`1,737.45 seats`

Critical Stage-1 risk:

`worst latest-event degradation = +4,326.90 seats`

Interpretation:

> There is useful live signal, but raw Ridge is not safe enough to promote because it can make very harmful individual revisions.

---

# Chronos / TSFM decision

Stage 1 tested:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both were zero-shot causal inventory-trajectory forecasters using only `available_share_of_capacity` history.

Final attendance never entered TSFM context.

TSFM-ready rows:

`21/30`

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Why:

- plain Ridge latest MAE: `3320.39`;
- Ridge + Chronos-2: `3428.25`;
- Ridge + Bolt-small: `3428.08`.

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same 9-event development lineage.

Reopen this family only with materially more independent trajectory events or a materially new predeclared hypothesis.

---

# d2 Stage 2 — ACTIVE NOW

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

## Objective

> **Preserve a meaningful share of the Stage-1 Ridge MAE uplift while materially reducing worst-event degradation.**

Stage 2 is a policy/reliability layer around the frozen Ridge expert.

Preferred form:

`final_forecast = frozen_v2 + reliability * ridge_delta`

where:

`0 <= reliability <= 1`

## Stage-2 development boundary

Use only the exact frozen development lineage:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rows:

`30`

Independent unit:

`event`

Validation:

`LOEO`

Do not include new completed event 5 in threshold, feature, or policy selection.

## Compact policy tournament

Minimum predeclared comparison:

### P0 — Frozen v2

`reliability = 0`

### P1 — Raw Ridge

`reliability = 1`

### P2 — Observation maturity

Shrink/suppress Ridge based on observation count, observation span and time-to-kickoff.

### P3 — Disagreement / correction magnitude

Large Ridge corrections receive less weight unless evidence quality is strong.

### P4 — Data-quality gate

Shrink/suppress on release, coverage-change, unexplained inventory increase or data-gap conditions.

### P5 — Compact combined reliability

Combine only the strongest predeclared signals from P2-P4.

Do not create a large threshold zoo.

## Reliability inputs

Priority PIT-safe inputs:

- valid observation count;
- observation span;
- hours to kickoff;
- trajectory stability / volatility;
- velocity;
- acceleration;
- Ridge vs Frozen-v2 disagreement;
- proposed correction magnitude;
- release/replenishment flag;
- sector coverage-change flag;
- unexplained inventory increase flag;
- data-gap flag;
- signal-ready / feature-quality state;
- matched sector count / coverage quality where available.

## Stage-2 selection criteria

A policy may advance only if it:

- improves latest-row MAE vs Frozen v2;
- improves event-balanced window MAE vs Frozen v2;
- retains meaningful Ridge uplift;
- materially reduces Ridge's `+4326.90` worst-event degradation;
- avoids unacceptable bias;
- remains stable under event-level LOEO;
- is fully versioned and reproducible;
- is selected before event 5 is opened.

If no policy improves the risk-return tradeoff enough, retain raw Ridge as research lead but do not promote it.

---

# Reserved chronological holdout — event 5

Append-only exporter now has a new completed event that was not used in Stage 1:

- event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

Mandatory rule:

> **Do not use event 5 to tune Stage 2. Freeze the Stage-2 policy first, then open event 5 exactly once.**

After Stage-2 freeze compare:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

Score:

- whole trajectory/window;
- latest row;
- revision magnitudes;
- whether reliability correctly suppressed or allowed corrections.

No retuning after the result is known.

---

# After event 5

- persist the holdout result regardless of outcome;
- continue append-only collection of independent completed events;
- score the frozen d2 candidate prospectively;
- do not silently fold new outcomes into training;
- open a separately versioned retraining cycle only when enough new independent events exist;
- keep production promotion evidence-gated.

---

# Continuous-time behavior

The live engine remains continuous over time-to-kickoff.

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints, not separate live-model boundaries.

New meaningful snapshots may produce revised shadow forecasts while preserving:

- as-of timestamp;
- input snapshot IDs;
- Frozen-v2 lineage;
- Ridge model ID;
- reliability-policy ID;
- previous forecast;
- proposed raw correction;
- applied governed correction;
- audit reason / reliability score.

---

# Inventory interpretation

Public availability is a proxy, not confirmed paid sales.

The live engine must distinguish as far as possible:

- demand movement;
- ticket releases;
- sector openings/closures;
- coverage changes;
- scrape/data anomalies.

These signals are especially important for Stage-2 reliability.

---

# Accuracy evaluation

Mandatory metrics for Stage 2 and future prospective scoring:

- latest-row MAE;
- event-balanced window MAE;
- median AE;
- bias;
- event improvement rate;
- worst-event degradation;
- tail metric / p90 where meaningful;
- revision activation rate;
- mean/max revision magnitude;
- retained share of raw Ridge uplift;
- performance by observation count and time-to-kickoff.

A lower average MAE alone is insufficient if tail risk remains unacceptable.

---

# CI/CD requirements

All Stage-2 work follows `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`.

Persist:

- exact Ridge model ID and immutable contract;
- policy ID;
- thresholds / shrinkage weights;
- input feature definitions;
- frozen development event IDs;
- holdout exclusion;
- PIT assertions;
- LOEO evidence;
- run/artifact IDs and hashes;
- committed result doc;
- explicit decision;
- canonical docs update.

CI green does not mean production activation.

---

# Promotion boundary

Production live correction remains evidence-gated.

Promotion requires:

- materially more genuinely prospective independent events;
- positive uplift against the correct frozen baseline;
- acceptable degradation/tail risk;
- frozen reproducible model + reliability package;
- full CI evidence;
- explicit reviewed promotion.

No automatic promotion exists.

## Immediate live-engine instruction

> **Freeze `ridge-a10` exactly as selected. Build Stage-2 reliability/tail-risk gating only on the original 9-event/30-row development lineage. Do not tune on Lech–Korona event 5. Freeze the policy first; then score event 5 once as the first chronological holdout. Keep C1 v8, Pre-Live v2 and production unchanged.**
