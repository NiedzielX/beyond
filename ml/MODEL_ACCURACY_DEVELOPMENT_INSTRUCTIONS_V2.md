# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-21**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

## Objective

> **Reduce forecasting error as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Primary development KPI:

`MAE`

Mandatory constraints:

- tail risk;
- bias;
- event independence;
- point-in-time safety;
- reproducibility;
- honest treatment of exposed evidence;
- no silent production activation.

A failed challenger closes the challenger, not the workstream.

---

# 1. Parallel-track rule

## Track A — frozen validation / promotion evidence

Use the current frozen model/policy unchanged on new events.

Purpose:

- measure real forward behavior;
- preserve independent evidence;
- support eventual production promotion;
- diagnose component failures without post-hoc tuning.

Track A may wait for future outcomes because they genuinely do not exist yet.

## Track B — active accuracy R&D

Continue research now whenever an honest evaluation boundary can be declared.

Track B does **not** wait for a fixed prospective event count.

A new versioned challenger may begin when at least one is true:

- a bounded part of the original investigation remains incomplete;
- a materially new model/target/ensemble hypothesis exists;
- materially new independent historical data exists;
- a new PIT-safe feature/source becomes available;
- repeated prospective evidence suggests a failure mode.

The current frozen package remains the benchmark.

> **Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Canonical frozen architecture — Track A

## Frozen Pre-Live v2

Freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Concept:

`historical demand + frozen current-season regime -> Frozen Pre-Live v2`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Frozen b2 policies:

- T-30 `NO_ADJUSTMENT`;
- T-14 `NO_ADJUSTMENT`;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

## Frozen d2

Stage-1 expert:

`ridge-a10`

Stage-2 policy:

`P2-observation-maturity`

Frozen package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen P2:

- observation 1 `0.25`;
- observation 2 `0.60`;
- observation 3+ `1.00`;
- >18h cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`;
- final reliability = minimum of observation and time weights.

These frozen IDs are evidence objects. Track-B experiments never mutate them.

---

# 3. Current evidence state

Frozen Pre-Live v2 reference mean MAE:

- T-30 `1867.82`;
- T-14 `1809.45`;
- T-7 `1691.40`;
- T-3 `1682.63`;
- T-1 `1661.52`.

d2 Stage-1 development:

- Frozen latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- uplift `807.62 / 19.56%`;
- Ridge window MAE `3619.19`;
- worst latest-event degradation `4326.90`.

d2 Stage-2 development:

- P2 latest MAE `3240.99`;
- uplift vs Frozen `887.02 / 21.49%`;
- P2 window MAE `3657.65`;
- worst degradation `1081.72`;
- 75% reduction in raw-Ridge worst degradation.

Event 5 is exposed and can never be reused as unseen validation.

---

# 4. Evidence classes

Frozen Stage-2 cutoff:

`2026-10-19T19:11:01Z`

## `DELAYED_LABEL_HOLDOUT`

Kickoff at or before the cutoff, but truth became available later.

Use for diagnostics, component-failure analysis and future hypothesis generation. Do not count it as true post-freeze promotion evidence.

## `TRUE_POST_FREEZE_PROSPECTIVE`

Kickoff after the cutoff.

This class may contribute to genuine forward promotion evidence.

Never combine both classes into one headline prospective N.

---

# 5. Historical model R&D rules

Historical R&D uses strict chronological boundaries.

Required:

- no random split as headline evidence;
- training only on earlier seasons/events;
- development selection boundary declared before tuning;
- exposed reference seasons never used to choose variants or ensemble weights;
- all features reconstructable point-in-time;
- horizon-specific metrics;
- MAE plus median AE, bias, p90/worst event and stability;
- deterministic/pinned dependencies.

Historical data already available must be used now rather than waiting for prospective data.

## a2 external-family / ensemble closure — COMPLETE

Canonical results:

- `ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`;
- `ml/results/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1_2026-10-21.md`.

The bounded external-family gap is closed.

Exact robust historical challengers passed positive MAE improvement in all four rolling folds:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`;
- T-1: `0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`.

T-14 and T-3 retained current a2 after mixed exposed-reference evidence.

Passing robustness does **not** mutate current a2 or Frozen Pre-Live v2.

## Active historical R&D — Pre-Live v3

The next versioned challenger must use the robust historical bases at T-30/T-7/T-1 and current a2 at T-14/T-3, then revalidate the current-season regime before any new freeze.

---

# 6. Current-season regime rules

Frozen b2 must remain unchanged in Track A.

Component diagnostics must preserve:

`Structural/historical base -> b2 -> Pre-Live`

so wrong-direction current-season corrections remain visible.

## Pre-Live v3 requirement

The old b2 policy may **not** be silently copied onto the new v3 historical anchors.

Reason:

> b2 is a residual-regime layer and its residuals were defined relative to the old historical bases.

The v3 experiment must compare:

1. new historical anchor only;
2. old frozen b2 formulation applied unchanged on the new anchor as a fixed comparator;
3. newly selected current-season-regime challenger under a declared historical temporal boundary;
4. Frozen Pre-Live v2 as unchanged benchmark.

No event-5 or later delayed-label/prospective d2 outcomes may be used for b2 selection.

If the current-season layer does not add stable incremental value on a new historical anchor, `NO_ADJUSTMENT` is a valid v3 decision for that horizon.

---

# 7. c2/context rules

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

Forward context R&D is allowed now when sources are genuinely PIT-safe.

Examples:

- verified rivalry/derby;
- verified injuries/suspensions;
- expected XI/key-player availability;
- sporting context;
- media attention;
- search/social/hype.

Rules:

- collect point-in-time;
- never reconstruct historical values from later/final-state knowledge;
- version source semantics;
- test incremental value separately;
- no integration unless out-of-sample MAE evidence supports it.

---

# 8. Frozen d2 Stage-1 expert contract

Expert:

`ridge-a10`

Frozen Track-A contract:

- target `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- numeric PIT-safe live features;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw correction clipped to +/-10pp occupancy.

Do not change this package during Track-A prospective accumulation.

A changed target, estimator, feature contract, preprocessing or correction rule creates a new Track-B challenger.

---

# 9. d2 after a new pre-live anchor

The current Ridge/P2 package is tied to Frozen Pre-Live v2.

If Pre-Live v3 earns a freeze, do **not** silently attach the old live model to the new anchor.

Create a new d2 version and rebuild/revalidate the live residual layer relative to v3.

Possible new d2 hypotheses include:

- remaining-demand target;
- alternative capacity-normalized residual target;
- anchor-error direction/sign plus correction magnitude;
- learned reliability;
- compact heterogeneous live-model ensemble;
- materially different trajectory representation.

Requirements:

1. new experiment/model ID;
2. declared development set before fitting;
3. frozen v2/Ridge/P2 retained as benchmark;
4. exposed event labels recorded honestly;
5. no claim that exposed events are unseen;
6. no production write.

Do not simply tune old Ridge/P2 thresholds event by event.

---

# 10. TSFM / Chronos boundary

Stage-1 tested:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both improved Frozen v2 when added to Ridge but lost to plain Ridge.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Therefore:

- no same-data fine-tuning to rescue that challenger;
- no automatic Lag-Llama / NeuralProphet model zoo on the same formulation.

TSFM may be reopened only when materially more independent trajectory data exists or a materially different predeclared use/target exists.

---

# 11. Prospective scoring rules

For every new Track-A event:

1. score once under the frozen package;
2. persist the result regardless of direction;
3. do not train on that event in the same evidence cycle;
4. preserve component diagnostics;
5. register it as exposed after reviewed persistence.

Mandatory layers:

1. Structural T-1 base;
2. Frozen Pre-Live v2 / b2;
3. raw frozen Ridge;
4. frozen P2;
5. genuine persisted C1 comparator where available.

Mandatory metrics:

- latest AE;
- trajectory/window MAE;
- component incremental error;
- bias;
- max revision;
- correction direction/magnitude;
- reliability trajectory;
- data-quality warnings;
- evidence class.

---

# 12. Data-quality blockers

Missing attendance, capacity, fixture or source coverage is a data-contract problem.

Rules:

- fix trusted source coverage;
- record provenance;
- never infer attendance from inventory;
- do not use data blockers as a reason to pause unrelated Track-B R&D.

---

# 13. Non-negotiable experiment/CI contract

Every material experiment must have:

1. source code;
2. executable CI workflow;
3. pinned runtime/dependencies;
4. syntax/import checks;
5. deterministic seeds where applicable;
6. exact input/data lineage;
7. explicit train/development/reference or forward split;
8. PIT assertions;
9. frozen incumbent benchmark;
10. machine-readable JSON/CSV evidence;
11. artifact name, run ID and hashes;
12. human-readable result under `ml/results/`;
13. explicit decision: advance / retain / reject / insufficient;
14. canonical docs synchronized in the same evidence cycle;
15. no production activation unless explicitly reviewed.

A material change to target, feature set, source semantics, preprocessing, model family, hyperparameters, weighting, correction cap, split, exclusions or ensemble composition creates a new challenger/version.

---

# 14. Promotion boundary

Historical improvement alone is not production promotion.

Production requires:

- materially more genuine `TRUE_POST_FREEZE_PROSPECTIVE` events;
- positive aggregate latest/window uplift;
- acceptable tail risk;
- acceptable bias;
- no unresolved systematic component failure;
- frozen reproducible package;
- explicit reviewed promotion.

Until then:

`live_adjustment = 0`

---

# 15. Immediate instruction

> **Keep Pre-Live v2 / Ridge / P2 frozen for Track-A evidence. The a2 external/ensemble gap is closed with robust T-30/T-7/T-1 challengers. Active Track-B work is now a separately versioned Pre-Live v3 historical-anchor + current-season-regime revalidation. Do not silently inherit b2 onto the new anchors, do not use prospective sample-count gates to pause this R&D, and do not rebuild d2 until a v3 anchor actually earns a freeze. Production remains unchanged.**
