# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Canonical research strategy:

`ml/MAE_RESEARCH_ROADMAP_V5.md`

Detailed trajectory plan:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction:

`Delta MAE < 0`

Readiness counters, snapshot counts, support counts, odds rows, daily rows and prediction rows are experiment prerequisites only. They are not model success.

Production remains unchanged:

`live_adjustment = 0`

No research lane may activate production automatically.

---

# 2. Research rules

1. Genuine prospective evidence outranks historical reconstruction whenever historical PIT cannot be proven.
2. Never relax a gate merely to obtain a result.
3. Never tune a frozen challenger after opening the outcomes used to judge it.
4. `NOT_EVALUABLE` and fail-closed outcomes are valid research outcomes, not failures to be repaired.
5. Keep differently precommitted learners separately auditable.
6. Event/match is the independent unit; multiple daily prefixes from one event do not create multiple independent events.
7. Promotion requires meaningful prospective MAE gain plus acceptable event-level downside.
8. Rejected hypotheses stay closed on the same outcomes unless a genuinely new mechanism/information source justifies a new version.
9. Never manufacture booking-curve history, forecast history, odds history or outcomes.
10. Hidden/unknown inventory is never zero.
11. Preserve `live_adjustment=0` until an explicit reviewed production decision.

---

# 3. Priority 0 — protect evidence and acquisition

Keep healthy:

- multi-source ticketing acquisition;
- fixture watchdog;
- raw/private buffers;
- verified promotion;
- original `captured_at` timestamps;
- immutable prediction/attempt ledgers;
- PIT lineage;
- production guards.

Do not backfill historical booking curves/forecasts/odds and describe them as prospective.

---

# 4. Priority 1 — P9 v1 genuine prospective validation

Historical P9 v1 is closed:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Historical state:

- T-168: **9/9 events / 9 clubs**;
- T-24 support-ready: **0/11**;
- T-48 support-ready: **0/9**;
- no valid historical challenger MAE.

First genuine prospective attempt:

- event443 Cracovia–Motor;
- T-48 cutoff: **2026-10-28 17:00 UTC**;
- attempt persisted;
- outcome: `PIT_SUPPORT_INSUFFICIENT`;
- genuine attempts: **1**;
- predictions: **0**;
- scored: **0**.

Interpretation: correct fail-closed, not a model loss.

Do not relax the minimum 3-reference support gate and do not retro-predict event443.

Near-term protected windows:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Rule: capture every valid window and record the exact reason whenever no prediction is produced.

---

# 5. Priority 2 — P9 Family Fallback v2, separate evidence

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md`

Purpose:

address v1 source-family support starvation without changing the frozen five neighbors or minimum support gate.

Frozen rule:

1. reproduce the v1 target-family decision and exact five neighbors;
2. if v1 family has >=3 usable refs, v2 emits nothing (`V1_COVERED`);
3. only when v1 selected D2 and D2 support is <3 may Structural be checked on the same five neighbors;
4. fallback requires a valid PIT Structural target incumbent and >=3 Structural residual refs;
5. otherwise fail closed;
6. no target labels, no search, no retroactive event443 prediction.

Current verified state:

- attempts: **0**;
- predictions: **0**;
- scored: **0**;
- production OFF.

Never pool v1 and v2 results into one MAE result.

---

# 6. Priority 3 — Form5 prospective challenger

Precommit:

`ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md`

Frozen design:

- source: `TheSportsDB v1 shadow`;
- immutable prospective T-24 only;
- true immutable baseline comparator;
- LOCO primary / LOEO secondary;
- ridge alpha 30;
- correction cap +/-25%;
- gate: 8 events / 5 clubs / >=2 distinct values;
- production OFF.

First qualifying capture:

**event443 Cracovia–Motor — 2026-10-29 17:00 UTC**.

Do not use older/manual Form5 values for this version.

---

# 7. Priority 4 — P7 prospective scoring

Historical frozen result:

- anchor MAE **7409.79**;
- challenger MAE **6339.99**;
- point gain **1069.80 / 14.44%**;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Current prospective state:

- **53 immutable prediction rows**;
- **6 events**;
- **0 scored**.

Collect/score only. No retuning.

---

# 8. Priority 5 — start Daily Trajectory infrastructure now

This is the new highest-priority **new model direction**, but it must not interrupt protected P9/Form5 windows.

Accepted strategy:

`P-60 -> P-59 -> ... -> today -> forecast remaining trajectory -> final attendance`

At every daily cutoff the system should eventually consume the complete observed prefix genuinely available at that cutoff.

Start now with infrastructure because this does not mutate frozen experiments.

## Immediate deliverables

1. canonical PIT-safe daily trajectory dataset;
2. one event/cutoff row for each supported daily horizon;
3. immutable daily attempt/forecast ledger;
4. horizon-wise MAE reporting;
5. observation-density and missingness audit by event/club/horizon.

Initial daily range:

`P-60 ... P-1`

Missing history remains missing. Never fabricate daily values.

Detailed contract:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

---

# 9. Priority 6 — trajectory model research: two lanes in parallel

Do **not** wait for a conventionally large labeled dataset before starting research.

## Lane A — simple benchmark

Use the structural P50 as anchor and predict a residual using engineered trajectory information:

- level;
- 1d/3d/7d change;
- velocity;
- acceleration;
- slope/slope change;
- volatility;
- trajectory similarity.

Candidate families stay small: Ridge/ElasticNet, restrained tree/boosting residual model, curve-similarity/pickup methods.

## Lane B — controlled high-risk sequence research

Start early in shadow mode.

Architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer/attention encoder only if earlier sequence models justify it.

Recommended formulation:

`observed prefix + structural prior/context -> residual correction / final attendance distribution`

The sequence model must beat Lane A on the same event-grouped/PIT-safe evaluation before more complexity is justified.

Research risk is accepted. Leakage/evidence shortcuts are not.

---

# 10. Priority 7 — self-supervised trajectory research

Because trajectory observations are more abundant than attendance labels, investigate target-free pretraining such as:

- next-observation prediction;
- short-window proxy-change prediction;
- trajectory-shape representation learning;
- chronology-safe masked/reconstruction tasks.

Later attach an attendance/residual head using labeled events.

Important:

> more prefixes may help representation learning, but they do not increase the number of independent events in final evaluation.

---

# 11. Priority 8 — P11 odds and P4a evidence collection

P11 current verified state:

- 6 events / 6 clubs;
- >=3 bookmakers on all 6;
- T-24 coverage: 5;
- T-72 coverage: 5;
- T-168 coverage: 0;
- no model fit yet.

Continue append-only genuine collection. Do not fit/select an attendance model until a genuine horizon audit and precommit exist.

P4a:

- labeled READY: 4/9;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

---

# 12. Priority 9 — Long72 frozen / low priority

Current scored sample: **5 events**.

Overall:

- anchor MAE **6082.40**;
- package MAE **6039.39**;
- improvement **43.01 / 0.71%**;
- event improvement rate **60%**;
- worst degradation ~**3633**.

By band:

- 24–48h: ~105 worse;
- 48–72h: ~191 better.

Do not retune. Monitor operational health only.

---

# 13. Priority 10 — rejected/closed lanes

Keep closed on the same evidence:

- Live Ticketing challenger: ~**723.6 MAE worse** on current 19-event LOCO sample;
- Sporting Match Stakes: worse;
- timing context candidate: worse;
- existing weather point forecast: rejected/no uplift;
- Hype/Attention 48h: **69.4 MAE worse**;
- old estimator sweeps/post-hoc tuning.

The new daily trajectory program is allowed because it is a materially different representation/mechanism, not a rerun of the rejected live-ticketing challenger.

---

# 14. Priority 11 — business minimum meaningful Delta MAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Still unresolved.

Derive the threshold independently from real operational decisions so that a tiny improvement such as ~50 seats is not automatically called meaningful success.

Until then, small positive gains remain research evidence only.

---

# 15. MAE reporting must evolve

For daily trajectory work, show MAE as a function of horizon, not only one aggregate.

Minimum view:

| Horizon | Incumbent MAE | Challenger MAE | Delta MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Primary governance still uses event-balanced MAE under a precommitted aggregation, but horizon-wise reporting tells us **how early the model becomes useful**.

---

# 16. Immediate execution order

1. Protect the upcoming P9 v1/v2 windows.
2. Protect Form5 event443 T-24 on 2026-10-29 17:00 UTC.
3. Watch event448 for genuine inventory; never fabricate zero.
4. Score P7/P9 only after genuine outcomes arrive.
5. In parallel, start the daily trajectory dataset/ledger/reporting infrastructure.
6. Continue P11/P4a evidence accumulation.
7. Keep Long72 frozen.
8. Precommit Lane A and Lane B only after the canonical trajectory dataset contract is implemented/audited.
9. Run simple and sequence trajectory challengers under identical event-grouped/PIT-safe evaluation.
10. Begin daily prospective shadow inference before relevant outcomes are known.
11. Derive the business meaningful Delta MAE threshold.
12. Production promotion remains a separate reviewed decision.

---

# 17. Decision rules

## P9

- if v1 emits predictions: keep it frozen and wait for outcomes;
- if v1 repeatedly support-starves while v2 emits valid predictions: evaluate v2 separately;
- if both repeatedly fail: diagnose support structure before a new P9 design;
- never lower support merely for coverage.

## Daily trajectory program

- if Lane A improves MAE but Lane B does not: prefer the simpler model;
- if Lane B materially beats Lane A: continue sequence research and prospective validation;
- if both fail: diagnose data/proxy/coverage before launching another model tournament;
- if historical/grouped evidence is strong but prospective evidence fails: prospective evidence wins.

---

# 18. Next meaningful milestones

Current evidence milestones:

1. first valid immutable P9 v1 prediction;
2. first valid immutable P9 v2 fallback prediction, if eligible;
3. first Form5 prospective T-24 capture;
4. first genuine P7 prospective scored event;
5. first genuine P9 prospective scored event.

New trajectory milestones:

6. canonical daily trajectory dataset implemented and audited;
7. immutable daily forecast/attempt ledger live;
8. horizon-wise MAE view live;
9. Lane A precommitted and evaluated;
10. first small Lane B sequence challenger evaluated under identical folds;
11. first genuine prospective daily trajectory forecasts scored;
12. enough independent events to compare meaningful prospective Delta MAE;
13. business minimum meaningful Delta MAE agreed;
14. only then any production promotion decision.
