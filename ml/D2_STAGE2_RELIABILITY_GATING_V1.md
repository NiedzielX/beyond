# Beyond Ticketing — d2 Stage 2 Reliability / Tail-Risk Gating v1

Last updated: **2026-10-19**

Status: **NEXT ACTIVE D2 STAGE / DESIGN CONTRACT / NO PRODUCTION CHANGE**

Parent result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Frozen Stage-1 research lead:

`ridge-a10`

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

## Frozen prediction expert

Base learned expert:

`ridge-a10`

Do not retune Ridge `alpha`, feature contract, preprocessing, or correction cap during Stage 2.

The purpose of Stage 2 is to govern the existing Stage-1 expert.

If Ridge itself is changed, that is a new model challenger and must receive a new version outside this Stage-2 policy comparison.

## Primary architecture

Preferred form:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

where:

`0 <= reliability(t) <= 1`

Allowed policy families:

1. hard gate: use Ridge or Frozen v2;
2. continuous shrinkage: multiply Ridge correction by a reliability weight;
3. bounded piecewise shrinkage based on predeclared reliability states.

No policy may use actual attendance or future snapshots at decision time.

## Candidate reliability inputs

Use only signals already available PIT-safe at the exact forecast timestamp.

Priority inputs:

- valid observation count;
- observation span;
- hours to kickoff;
- current inventory / available share;
- trajectory velocity;
- trajectory acceleration;
- trajectory stability / volatility;
- disagreement magnitude between Ridge and Frozen v2;
- absolute proposed Ridge correction size;
- release/replenishment flag;
- sector coverage-change flag;
- unexplained inventory increase flag;
- data-gap flag;
- signal-ready / feature-quality state;
- matched sector count / coverage quality where present.

Potential secondary inputs, only if already PIT-valid in the existing feature contract:

- sector consistency;
- price-area consistency;
- price coverage quality.

Do not add new external context simply to rescue Stage 2.

## Stage-2 policy tournament

Keep the policy family deliberately small and predeclared.

Minimum comparison:

### P0 — Frozen Pre-Live v2

`reliability = 0`

### P1 — Raw Ridge

`reliability = 1`

### P2 — Observation-maturity gate

Reliability depends only on observation count / span / time-to-kickoff.

### P3 — Disagreement / correction-magnitude shrinkage

Large Ridge revisions receive lower weight unless live evidence quality is strong.

### P4 — Data-quality gate

Suppress or shrink Ridge when release/coverage/data-gap diagnostics indicate an unstable inventory interpretation.

### P5 — Compact combined reliability policy

Combine only the strongest predeclared reliability factors from P2-P4.

Do not create a large threshold zoo.

## Selection objective

Stage 2 is not allowed to optimize mean MAE alone.

Primary objective:

1. retain a meaningful portion of Stage-1 MAE uplift;
2. materially reduce worst-event degradation;
3. avoid creating systematic bias;
4. remain simple enough to reproduce and explain.

Mandatory metrics:

- latest-row MAE;
- event-balanced window MAE;
- improvement vs Frozen v2;
- retained share of raw Ridge uplift;
- event improvement rate;
- worst latest-event degradation;
- p90 event degradation / tail metric where meaningful;
- mean and max revision magnitude;
- revision activation rate;
- bias;
- behavior by observation count and time-to-kickoff.

## Advancement rule

A Stage-2 policy may become the frozen d2 research candidate only if it:

- improves both latest-row and event-balanced window MAE versus Frozen v2;
- reduces raw Ridge worst-event degradation materially;
- does not depend on future/outcome information;
- is stable under event-level LOEO;
- has a fully versioned feature/policy contract;
- is selected before event 5 is opened.

If no policy improves the risk/return trade-off sufficiently:

> retain raw Ridge as research lead, but do not promote it to prospective shadow deployment beyond controlled comparison.

## Event 5 holdout rule

Reserved holdout:

- ticket event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

The outcome is already known operationally, but for model-governance purposes it was not used in Stage-1 selection and must not be used in Stage-2 policy design.

After Stage 2 is frozen, score in one pass:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 comparator where contract-compatible.

Score the whole trajectory and the latest row.

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

## Production boundary

Always during Stage 2:

- `production_change = false`;
- `promotion_allowed = false`;
- production `live_adjustment = 0`;
- Frozen Pre-Live v2 unchanged;
- frozen C1 v8 unchanged.

## One-line instruction

> **Freeze Stage-1 `ridge-a10`; use only the original 9-event/30-row development lineage to design a compact reliability/shrinkage policy that preserves MAE uplift while reducing the +4.3k-seat tail failure. Do not inspect event 5 for policy selection. Freeze Stage 2 first, then score Lech–Korona once as an untouched chronological holdout.**
