# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Trajectory plan: `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Feature contract: `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Validation contract: `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

Coverage audit: `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons, with PIT-safe, reproducible evidence.**

Primary decision metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `Delta MAE < 0`

Counts of rows, snapshots, attempts, model parameters or training examples are not success metrics.

Production remains:

`live_adjustment = 0`

---

# 2. Non-negotiable research rules

1. Genuine prospective evidence outranks favorable historical reconstruction.
2. Event/match is the independent evaluation unit.
3. All prefixes from one event stay together.
4. Never random-split daily rows/snapshots as headline evidence.
5. Never use future target trajectory at an earlier cutoff.
6. Never use target attendance during prediction construction.
7. Never manufacture booking/inventory/forecast history.
8. Never lower a gate merely to obtain coverage.
9. Frozen learners remain separately auditable.
10. No research lane activates production automatically.

---

# 3. Priority A — protect current prospective evidence

This remains higher priority than trajectory R&D whenever a genuine window is imminent.

## P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine prospective attempt:

- event443 Cracovia–Motor T-48;
- 2026-10-28 17:00 UTC;
- immutable attempt persisted;
- result `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored.

Correct fail-closed. Do not lower the minimum support and do not retro-predict.

## P9 Family Fallback v2

Separately precommitted/deployed:

- same exact five v1 neighbors;
- unchanged support threshold;
- Structural fallback only under frozen rule;
- never retro-predict event443;
- never pool v1/v2 evidence.

Latest verified: 0 attempts / 0 predictions / 0 scored.

## Form5

First legal prospective T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## P7

Latest verified:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored;
- no retuning.

## P11 / P4a

Continue genuine accumulation only.

P11 latest verified:

- 6 events / 6 clubs;
- >=3 bookmakers on all 6;
- T-24/T-72/T-168 = 5/5/0;
- no model fit yet.

P4a remains below event-count gate.

## Long72

Frozen / low priority:

- 5 scored events;
- 6082.40 -> 6039.39 MAE;
- 43.01 / 0.71% point improvement;
- do not retune.

---

# 4. Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Event448 remains a genuine inventory watch. Unknown inventory is not zero.

---

# 5. Daily Trajectory infrastructure — DONE

The core trajectory evidence infrastructure is now implemented.

Repo:

- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/test_daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/test_trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`;
- `ml/demand_engine/test_trajectory_validation_folds_v1.py`.

Live Supabase:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`;
- controlled service-role attempt/prediction RPCs;
- post-outcome scoring RPC;
- MAE-by-horizon RPC.

Canonical SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

Demand Engine test suite is green after the feature/fold-contract implementation.

No synthetic daily prediction has been inserted to claim progress.

---

# 6. Data reality — do not design for an imaginary complete P-60 dataset

Current genuine pre-kickoff inventory coverage:

- 32 events / 14 clubs with any genuine observation;
- median first observation ~P-9.3;
- p75 ~P-14;
- earliest ~P-30.3;
- current P-31...P-60 historical coverage = 0.

Representative coverage:

- P-30: 3.0%;
- P-14: 21.9%;
- P-7: 61.5%;
- P-3: 75.0%;
- P-1: 95.0%.

Decision:

> **P-60 remains the collection horizon, not a requirement for a fabricated 60-day sequence.**

Use genuine variable-length prefixes and explicit missingness/masks.

---

# 7. Trajectory Feature Contract v1 — FROZEN

Contract ID:

`trajectory-feature-contract-v1`

Shared primary eligibility:

- P-60...P-1;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no future target snapshot/outcome.

## Lane A

Receives fixed engineered trajectory summaries + the structural P50 anchor.

## Lane B

Receives the genuine ordered variable-length snapshot sequence + the same structural anchor/global quality context.

Sequence v1:

- only genuine observations;
- exact timestamp dedupe;
- at most one real observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- explicit sequence length/padding mask;
- padded zero is never genuine zero inventory.

Both lanes exclude unrelated P11 odds, weather, hype, match-stakes, Form5 and P4 context in v1. The first test isolates **trajectory representation**.

---

# 8. Validation Fold Contract v1 — FROZEN

Contract ID:

`trajectory-validation-fold-contract-v1`

Primary development validation:

- strict expanding temporal event folds;
- all prefixes from one event inherit the same fold;
- same-kickoff events are held out together;
- training contains only events with earlier kickoff;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- Lane A and Lane B use the exact same registry/manifest.

LOEO/LOCO may be secondary diagnostics only.

Random row-level CV is prohibited.

Current checkpoint evidence under the shared input gate is genuinely small:

| Horizon | Input-ready events | Labeled ready events |
|---|---:|---:|
| T-30 | 0 | 0 |
| T-14 | 1 | 0 |
| T-7 | 7 | 4 |
| T-3 | 9 | 5 |
| T-1 | 10 | 10 |

Do not overclaim sparse early-horizon results.

---

# 9. Priority B — NEXT: precommit Lane A

The next new-model task is a small, auditable benchmark protocol.

Default formulation:

`structural P50 + engineered trajectory residual -> challenger P50`

Candidate family set must be small and frozen before outer-fold comparison.

Preferred first candidates:

- Ridge / ElasticNet;
- one restrained tree/boosting residual model if justified;
- optional auditable nearest-trajectory correction.

No broad feature/model tournament.

Preprocessing is fit inside train folds only.

---

# 10. Priority C — NEXT: precommit first Lane B sequence model

Accepted research risk:

> **Start sequence-model research now despite limited labels.**

First sequence protocol should stay deliberately small.

Architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer only if earlier sequence models establish value.

Recommended target:

`actual attendance - structural P50`

Lane B must use the exact same eligible events/folds/cutoffs as Lane A.

The first question is not “which neural net wins?” but:

> **Does reading the ordered trajectory reduce MAE beyond engineered trajectory summaries?**

---

# 11. Self-supervised trajectory research

Allowed separately as target-free representation research:

- next genuine observation prediction;
- short-window proxy-change prediction;
- chronology-safe trajectory representation learning;
- masked/reconstruction tasks with no target-future leakage.

This may help representation learning but does not increase independent attendance-event count.

---

# 12. Daily MAE reporting

Once genuine prospective daily predictions exist and are scored, report at minimum:

| Horizon | Incumbent MAE | Lane A MAE | Lane B MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Always show support next to MAE.

Also report bias, median/P90 AE, improvement rate, worst degradation and event-block uncertainty.

---

# 13. Rejected lanes remain closed

Do not reopen on the same exposed evidence:

- previous Live Ticketing challenger;
- Sporting Match Stakes;
- timing context;
- existing weather point forecast;
- Hype/Attention 48h;
- old broad estimator/post-hoc sweeps.

The daily trajectory program is allowed because it is a materially new representation/model contract.

---

# 14. Business meaningful Delta MAE

Still unresolved.

Derive independently from real operational decisions. A tiny negative Delta MAE is not automatically a meaningful success.

---

# 15. Immediate execution order

1. Protect imminent P9/Form5 windows.
2. Score P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.
4. **Precommit Lane A development protocol.**
5. **Precommit first small Lane B development protocol.**
6. Materialize one shared eligible event/cutoff export + fold registry manifest.
7. Run Lane A and Lane B on identical strict-forward folds.
8. Report support + horizon-wise MAE; no sparse-horizon overclaiming.
9. Freeze a candidate only if evidence justifies it.
10. Start prospective daily shadow inference only after candidate freeze and before relevant outcomes.
11. Continue collecting longer genuine prefixes forward.
12. Derive business minimum meaningful Delta MAE.
13. Production promotion remains a separate reviewed decision.

---

# 16. Next milestones

Evidence lanes:

1. first valid P9 v1 prediction;
2. first valid P9 v2 fallback prediction, if eligible;
3. first Form5 prospective capture;
4. first P7 prospective score;
5. first P9 prospective score.

Trajectory program:

6. **DONE** — daily dataset + PIT tests;
7. **DONE** — coverage audit;
8. **DONE** — immutable attempt/prediction/score backend;
9. **DONE** — MAE-by-horizon backend;
10. **DONE** — Trajectory Feature Contract v1 + executable implementation/tests;
11. **DONE** — strict-forward Validation Fold Contract v1 + executable implementation/tests;
12. Lane A precommit + first grouped result;
13. first small Lane B sequence precommit + grouped result;
14. first genuine prospective daily trajectory predictions;
15. first genuine prospective daily trajectory scores;
16. enough independent events for meaningful Delta MAE comparison;
17. business meaningful Delta MAE agreed;
18. only then production-promotion consideration.
