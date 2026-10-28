# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Detailed trajectory plan: `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Current trajectory coverage audit: `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction:

`Delta MAE < 0`

Readiness counters, snapshot counts, support counts, odds rows, daily rows and prediction rows are prerequisites only. They are not model success.

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
- result: `PIT_SUPPORT_INSUFFICIENT`;
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

Rule: capture every valid window and persist the exact reason whenever no prediction is emitted.

---

# 5. Priority 2 — P9 Family Fallback v2, separate evidence

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md`

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

- source `TheSportsDB v1 shadow`;
- immutable prospective T-24 only;
- true immutable baseline comparator;
- LOCO primary / LOEO secondary;
- ridge alpha 30;
- correction cap +/-25%;
- gate 8 events / 5 clubs / >=2 distinct values;
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

# 8. Priority 5 — Daily Trajectory infrastructure: backend delivered

Accepted direction:

`P-60 -> P-59 -> ... -> genuine observed prefix -> today -> predicted remaining trajectory -> final attendance`

Important data reality from the 2026-10-28 audit:

- 32 events / 14 clubs currently have any genuine pre-kickoff inventory observation;
- median first observation is only around **P-9.3**;
- earliest observed event begins around **P-30.3**;
- coverage: P-30 3.0%, P-14 21.9%, P-7 61.5%, P-3 75.0%, P-1 95.0%;
- P-31...P-60 historical coverage is currently zero.

Therefore P-60 is a **collection horizon**, not a requirement for a complete 60-day vector.

Models must support genuine variable-length prefixes and explicit missingness. Do not fabricate early history.

Completed infrastructure:

- [x] canonical daily P-N dataset builder: `ml/demand_engine/daily_trajectory_dataset.py`;
- [x] PIT/leakage tests: `ml/demand_engine/test_daily_trajectory_dataset.py`;
- [x] Demand Engine smoke CI green;
- [x] live data coverage/missingness audit;
- [x] immutable attempt ledger live;
- [x] immutable prediction ledger live;
- [x] immutable post-outcome score ledger live;
- [x] horizon-wise MAE backend live;
- [x] service-role permissions locked to read tables + controlled RPC writes;
- [x] Supabase security/performance review; new FK-index finding fixed.

Live evidence tables:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Canonical SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

No synthetic daily prediction was inserted to claim progress.

---

# 9. Priority 6 — freeze the shared Trajectory Feature Contract v1

This is the next new-model engineering task.

The shared contract must define exactly what Lane A and Lane B may see at each cutoff.

## Lane A representation

Structural P50 anchor plus PIT-safe engineered trajectory state, drawn from the canonical trajectory feature store/dataset rather than a new duplicate implementation.

Candidate families remain small:

- Ridge / ElasticNet;
- restrained tree/boosting residual learner;
- auditable nearest-trajectory/pickup residual method.

## Lane B representation

Use the ordered **genuine snapshot sequence** available by the cutoff rather than inventing one value for every missing day.

Preferred conceptual sequence element:

`(hours_to_kickoff, normalized_proxy, time_since_previous, quality/missingness context)`

plus structural prior/context and explicit sequence length/padding mask.

Padding zero must never mean genuine zero inventory.

---

# 10. Priority 7 — trajectory model development: two lanes in parallel

Do **not** wait for a conventionally large labeled dataset before starting research.

## Lane A — simple benchmark

Target default:

`actual attendance - structural incumbent P50`

Purpose: establish whether trajectory information itself adds value with low-capacity, auditable models.

## Lane B — controlled high-risk sequence research

Accepted architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer/attention encoder only if earlier sequence models justify it.

Recommended formulation:

`genuine observed sequence + structural prior/context -> residual correction / final attendance distribution`

The sequence model must beat Lane A on the same events, cutoffs and folds before more complexity is justified.

Research risk is accepted. Leakage/evidence shortcuts are not.

---

# 11. Priority 8 — self-supervised trajectory research

Because trajectory observations are more abundant than attendance labels, investigate target-free pretraining such as:

- next genuine observation prediction;
- short-window proxy-change prediction;
- trajectory-shape representation learning;
- chronology-safe masked/reconstruction tasks.

Later attach an attendance/residual head using labeled events.

More prefixes may improve representation learning, but they do not increase independent-event count for attendance evaluation.

---

# 12. Priority 9 — P11 odds and P4a evidence collection

P11 current verified state:

- 6 events / 6 clubs;
- >=3 bookmakers on all 6;
- T-24 coverage 5;
- T-72 coverage 5;
- T-168 coverage 0;
- no model fit yet.

Continue append-only genuine collection. Do not fit/select an attendance model until a genuine horizon audit and precommit exist.

P4a:

- labeled READY 4/9;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

---

# 13. Priority 10 — Long72 frozen / low priority

Current scored sample: **5 events**.

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

# 14. Priority 11 — rejected/closed lanes

Keep closed on the same evidence:

- previous Live Ticketing challenger: ~723.6 MAE worse on current 19-event LOCO sample;
- Sporting Match Stakes;
- timing context;
- existing weather point forecast;
- Hype/Attention 48h: 69.4 MAE worse;
- old estimator sweeps/post-hoc tuning.

The new daily trajectory program is allowed because it is a materially different representation/mechanism.

---

# 15. Priority 12 — business minimum meaningful Delta MAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Still unresolved.

Derive independently from real operational decisions so a tiny improvement is not automatically called meaningful success.

---

# 16. Daily MAE reporting rule

The live backend now supports MAE by daily horizon once genuine predictions are scored.

Minimum analytical view:

| Horizon | Incumbent MAE | Lane A MAE | Lane B MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Always show independent-event/club support next to MAE.

Primary governance remains precommitted event-balanced MAE, with downside/uncertainty guardrails.

---

# 17. Immediate execution order

1. Protect the upcoming P9 v1/v2 windows.
2. Protect Form5 event443 T-24 on 2026-10-29 17:00 UTC.
3. Watch event448 for genuine inventory; never fabricate zero.
4. Score P7/P9 only after genuine outcomes arrive.
5. Keep P11/P4a collection healthy.
6. Freeze `Trajectory Feature Contract v1` shared by Lane A/B.
7. Freeze one event-grouped fold/export registry shared by both lanes.
8. Precommit Lane A development protocol and first small Lane B sequence protocol.
9. Run Lane A/B on identical events/cutoffs/PIT rules.
10. Report support + horizon-wise MAE; do not overclaim sparse early horizons.
11. Start prospective daily shadow inference only after candidate contracts are frozen and before relevant outcomes are known.
12. Keep collecting longer genuine prefixes forward rather than waiting for complete P-60 history.
13. Derive business meaningful Delta MAE threshold.
14. Production promotion remains a separate reviewed decision.

---

# 18. Decision rules

## P9

- if v1 emits predictions: keep frozen and wait for outcomes;
- if v1 repeatedly support-starves while v2 emits valid predictions: evaluate v2 separately;
- if both repeatedly fail: diagnose support structure before a new P9 design;
- never lower support merely for coverage.

## Daily trajectory program

- if Lane A improves MAE but Lane B does not: prefer the simpler model;
- if Lane B materially beats Lane A: continue sequence research and require prospective confirmation;
- if both fail: diagnose proxy quality, coverage, independent-event count and structural-incumbent strength before another tournament;
- if historical/grouped evidence is strong but prospective evidence fails: prospective evidence wins.

---

# 19. Next meaningful milestones

Current evidence milestones:

1. first valid immutable P9 v1 prediction;
2. first valid immutable P9 v2 fallback prediction, if eligible;
3. first Form5 prospective T-24 capture;
4. first genuine P7 prospective scored event;
5. first genuine P9 prospective scored event.

Trajectory milestones:

6. **DONE** — canonical daily dataset builder/PIT tests;
7. **DONE** — live coverage audit;
8. **DONE** — immutable daily attempt/prediction/score ledger;
9. **DONE** — horizon-wise MAE backend;
10. freeze Trajectory Feature Contract v1 + fold registry;
11. first Lane A grouped result;
12. first small Lane B sequence result on identical folds;
13. first genuine prospective daily trajectory predictions;
14. first genuine prospective daily trajectory scores;
15. enough independent events for meaningful Delta MAE comparison;
16. business minimum meaningful Delta MAE agreed;
17. only then any production promotion decision.
