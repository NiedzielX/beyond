# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Read this first — current state in plain language

We have two parallel tracks.

## Track 1 — protect real prospective evidence

Keep P7, P9, Form5, Long72 and current evidence-collection contracts frozen and honest.

## Track 2 — improve MAE with daily trajectory modelling

The infrastructure is done and the first two model experiments are closed.

### Lane A v1 — failed badly

`Structural P50 + engineered trajectory features -> Ridge residual`

- incumbent event-balanced MAE: **2594.54**;
- Lane A MAE: **4153.34**;
- Delta MAE: **+1558.80**;
- **60.1% worse**.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

### Lane B v1 — safe but no gain

`Structural P50 + genuine ordered trajectory -> small GRU -> raw seat residual`

- incumbent MAE: **2594.54**;
- Lane B v1 MAE: **2595.40**;
- Delta vs incumbent: **+0.87**;
- Delta vs Lane A: **-1557.94**;
- median seed spread: **1.50 seats**;
- predicted corrections were only about **-0.06 to +4.33 seats**.

Decision:

`DO_NOT_ADVANCE`

Interpretation:

> Lane B v1 was stable and avoided Lane A's harmful corrections, but it effectively learned `correction ≈ 0`, so it did not beat the structural incumbent.

The active task is now **Lane B v2**, a narrow mechanism diagnostic that changes only target scale:

`raw seat residual -> residual ratio`

Architecture, sequence representation, folds, optimizer, epochs and seeds remain frozen.

Because the 5 outer events are already exposed, **v2 is diagnostic historical research only**. Even a strong result is not unseen validation.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

Rows, snapshots, prefixes, training examples and parameter count are not independent evidence.

---

# 2. Non-negotiable research rules

1. Event/match is the independent unit.
2. All prefixes from one event stay in one fold.
3. No random daily-row/snapshot CV.
4. No future target trajectory at an earlier cutoff.
5. No target attendance in prediction features.
6. No manufactured inventory/history.
7. No support-gate relaxation merely to obtain a result.
8. Frozen experiments are not tuned after their outer/prospective result.
9. Exposed historical results are labeled as exposed research.
10. Genuine prospective evidence outranks historical research when they disagree.
11. No research result activates production automatically.

---

# 3. Protect current prospective evidence first

An imminent genuine window takes priority over trajectory R&D.

## P9 v1

Historical state:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

First genuine attempt:

- event443 Cracovia–Motor T-48;
- 2026-10-28 17:00 UTC;
- `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored.

Correct fail-closed. Do not lower support or retro-predict.

## P9 Family Fallback v2

Separate frozen evidence:

- same exact five v1 neighbors;
- unchanged support gate;
- Structural fallback only under frozen rule;
- never retro-predict event443;
- never pool v1/v2 evidence.

## Form5

First legal prospective T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## P7

Latest recorded:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored;
- no retuning.

## P11 / P4a

Continue genuine evidence accumulation only.

## Long72

Frozen / low priority:

- 5 scored events;
- MAE 6082.40 -> 6039.39;
- 0.71% point gain;
- no retuning.

---

# 4. Near-term windows to protect

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Event448 remains an inventory watch. Unknown inventory is never zero.

---

# 5. Trajectory infrastructure — DONE

Do not create a parallel implementation.

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_shared_dataset_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

Live prospective evidence tables:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Live historical R&D export:

- `public.export_trajectory_development_rows_v1(bigint[])`;
- Edge Function `trajectory_research_export_v1`;
- GitHub OIDC only for `NiedzielX/beyond` on `refs/heads/main`;
- no stored service-role key in GitHub.

Security review found no new trajectory-export issue.

---

# 6. Data reality

Current genuine pre-kickoff inventory sample:

- 32 events;
- 14 clubs;
- median first observation ~**P-9.3**;
- p75 ~**P-14**;
- earliest ~**P-30.3**;
- P-31...P-60 historical coverage = 0.

Representative coverage:

| Horizon | Coverage |
|---|---:|
| P-30 | 3.0% |
| P-14 | 21.9% |
| P-7 | 61.5% |
| P-3 | 75.0% |
| P-1 | 95.0% |

Therefore:

> **P-60 is a collection horizon, not a requirement for a fake complete 60-day vector.**

Use genuine variable-length prefixes. No forward-fill/interpolation merely for model convenience.

---

# 7. Frozen feature and validation contracts

Feature contract:

`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Primary gate:

- PIT-valid structural incumbent;
- >=4 clean snapshots;
- >=24h genuine observation window;
- `signal_readiness=ready`;
- no future target trajectory/outcome.

Validation contract:

`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

- strict expanding temporal event folds;
- only earlier-kickoff events train later events;
- same-kickoff events stay together;
- min 5 earlier train events / 4 train clubs;
- every prefix from an event inherits the event fold.

Frozen development cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events;
- fold SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

This cohort is now exposed. Do not describe later reuse as unseen validation.

---

# 8. Lane A v1 — CLOSED / REJECTED

Docs:

- `ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md`;
- `ml/TRAJECTORY_LANE_A_RESULT_V1.md`;
- `ml/results/trajectory_lane_a_ridge_residual_v1_result.json`.

Result:

| Metric | Value |
|---|---:|
| Incumbent MAE | 2594.54 |
| Lane A MAE | 4153.34 |
| Delta | **+1558.80** |
| Relative change | **+60.1% worse** |
| Event improvement rate | 20% |

Do not retune v1.

---

# 9. Lane B v1 — CLOSED / DO NOT ADVANCE

Docs:

- `ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`;
- `ml/TRAJECTORY_LANE_B_IMPLEMENTATION_NOTE_V1.md`;
- `ml/TRAJECTORY_LANE_B_RESULT_V1.md`;
- `ml/results/trajectory_lane_b_small_gru_residual_v1_result.json`.

Result:

| Metric | Value |
|---|---:|
| Incumbent MAE | 2594.54 |
| Lane B v1 MAE | 2595.40 |
| Delta vs incumbent | **+0.87** |
| Delta vs Lane A | **-1557.94** |
| Event improvement rate | 40% |
| Worst event degradation | +3.42 |
| Median seed spread | 1.50 seats |
| Max seed spread | 2.63 seats |

By horizon:

| Horizon | Incumbent | Lane B v1 | Delta |
|---|---:|---:|---:|
| T-7 | 3399.03 | 3399.83 | +0.81 |
| T-3 | 2667.93 | 2668.20 | +0.27 |
| T-1 | 2314.89 | 2315.89 | +1.00 |

Critical diagnostic:

- true residuals are commonly hundreds/thousands of seats;
- predicted corrections were only about **-0.06...+4.33 seats**;
- seed spread was tiny.

Interpretation:

> **V1 is stable but effectively learned zero correction. It does not demonstrate incremental sequence value.**

Do not change epochs/lr/loss/architecture and still call it v1.

---

# 10. Lane B v2 — ACTIVE MECHANISM DIAGNOSTIC

Precommit:

`ml/TRAJECTORY_LANE_B_V2_PRECOMMIT.md`

Implementation:

`ml/demand_engine/trajectory_lane_b_v2.py`

Runner:

`ml/run_trajectory_lane_b_v2.py`

Workflow:

`.github/workflows/trajectory-lane-b-v2.yml`

## Narrow hypothesis

V1 may have failed because raw seat residuals are badly scaled for the fixed small-GRU + L1 optimization setup.

V2 changes only:

`seat_residual -> residual_ratio`

Training target:

`residual_ratio = (actual - structural_p50) / structural_p50`

Inference:

`seat_residual = predicted_ratio * structural_p50`

Unchanged from v1:

- same 10 events / 19 identities;
- same folds;
- same sequence representation;
- same global context;
- same GRU architecture;
- same AdamW lr/wd;
- same L1 loss;
- same 200 epochs;
- same seeds 17/29/41;
- same event-balanced weighting.

Evidence label:

`historical_exposed_research`

Even a strong v2 result is diagnostic only. Its purpose is to decide whether this scaling mechanism deserves a **future prospective freeze**, not to claim validation.

---

# 11. Immediate execution order

## Evidence protection

1. Protect imminent P9/Form5 windows.
2. Score P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.

## Trajectory R&D

4. Finish Lane B v2 residual-ratio diagnostic.
5. Persist its full result and mechanism decision.
6. Do not tune v2 after seeing the result.
7. If scaling mechanism is supported, freeze a separate prospective candidate **before** new outcomes.
8. If scaling mechanism is not supported, reassess sequence/data formulation before any architecture tournament.
9. Continue genuine forward trajectory collection.
10. Derive business minimum meaningful Delta MAE independently.

Production remains separately review-gated.

---

# 12. Agent decision rules after v2

## If v2 produces meaningful non-zero corrections and improves strongly over v1

`MECHANISM_SUPPORTED`

Then:

- do not call the exposed-cohort result validation;
- freeze the exact ratio-target model as a new prospective candidate;
- start immutable daily shadow inference before future outcomes;
- production stays OFF.

## If v2 still collapses near zero or does not improve v1

`MECHANISM_NOT_SUPPORTED`

Then:

- stop changing optimizer knobs on the same exposed cohort;
- reassess whether trajectory proxy/sequence provides learnable residual signal;
- a new representation/loss/model family requires a separately precommitted hypothesis.

## If future prospective evidence disagrees with historical diagnostics

Prospective evidence wins.

---

# 13. Milestones

### Completed

- [x] trajectory PIT dataset + tests;
- [x] coverage audit;
- [x] immutable daily evidence backend;
- [x] feature contract + strict-forward validation contract;
- [x] frozen 10-event / 19-row cohort;
- [x] Lane A v1 result — rejected;
- [x] Lane B v1 result — do not advance;
- [x] Lane B v1 mechanistic diagnosis;
- [x] Lane B v2 precommit;
- [x] Lane B v2 implementation/runner/workflow.

### Active / next

- [ ] Lane B v2 diagnostic result;
- [ ] v2 mechanism decision;
- [ ] prospective candidate freeze only if mechanism supported;
- [ ] first genuine daily trajectory shadow prediction;
- [ ] first genuine daily trajectory score;
- [ ] enough independent future events for meaningful prospective Delta MAE;
- [ ] business meaningful Delta MAE threshold;
- [ ] production review only after prospective evidence.
