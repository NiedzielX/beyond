# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-28**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Where we are now

There are two parallel tracks.

## Track 1 — protect real prospective evidence

Keep P7, P9, Form5, Long72 and current evidence-collection contracts frozen and honest. An imminent genuine window always takes priority over trajectory R&D.

## Track 2 — improve MAE with trajectory modelling

The trajectory infrastructure is complete. The first three supervised experiments on the frozen 10-event development cohort are also complete.

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | **+1558.80** | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | **+0.87** | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | **+2197.88** | mechanism not supported |

The supervised 10-event cohort is now **fully exposed**. We stop tuning correction magnitude, caps, loss functions or sequence architectures against those same five outer test events.

The active research direction is now:

> **Target-free self-supervised trajectory representation learning using genuine inventory sequences, followed later by prospective attendance validation on future independent events.**

Active precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary attendance metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

Self-supervised trajectory metrics are representation-learning evidence only. They are **not** attendance-forecast evidence.

---

# 2. Non-negotiable rules

1. Event/match is the independent attendance-evaluation unit.
2. All prefixes from one event stay together.
3. No random daily-row/snapshot CV for attendance claims.
4. No future target trajectory at an earlier cutoff.
5. No target attendance in inference features.
6. No manufactured inventory/history.
7. Frozen experiments are not tuned after their result.
8. The exposed 10-event supervised cohort is not reused as unseen confirmation.
9. Genuine prospective attendance evidence outranks historical research.
10. No research workflow activates production automatically.

---

# 3. Protect current prospective evidence

## P9 v1

First genuine event443 T-48 attempt:

`PIT_SUPPORT_INSUFFICIENT`

- 1 attempt;
- 0 predictions;
- 0 scored.

Correct fail-closed. Do not lower support or retro-predict.

## P9 Family Fallback v2

Separate frozen evidence only. Never pool with v1.

## Form5

First legal prospective T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## P7

Latest recorded:

- 53 immutable rows;
- 6 events;
- 0 scored;
- no retuning.

## P11 / P4a

Continue genuine evidence accumulation only.

## Long72

Frozen / low priority:

- 5 scored events;
- 6082.40 -> 6039.39 MAE;
- 0.71% point gain.

---

# 4. Near-term windows to protect

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: **2026-10-29 11:15 UTC**;
- event6 Lech–Wisła Kraków T-48: **2026-10-29 16:30 UTC**;
- event443 Cracovia–Motor T-24: **2026-10-29 17:00 UTC**;
- event444 GKS Katowice–Widzew T-48: **2026-10-29 19:15 UTC**;
- event445 Zagłębie–Korona T-48: **2026-10-31 17:00 UTC**;
- event447 Raków–Pogoń T-48: **2026-10-31 19:30 UTC**.

Unknown inventory is never converted to zero.

---

# 5. Trajectory infrastructure — DONE

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_shared_dataset_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

Live prospective evidence backend:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`;
- post-outcome scoring;
- MAE-by-horizon reporting.

No synthetic prospective prediction has been inserted.

---

# 6. Data reality

Current genuine pre-kickoff inventory history:

- 32 events;
- 14 clubs;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Therefore:

> **P-60 is a collection horizon, not a requirement for a fabricated complete 60-day sequence.**

Use genuine variable-length prefixes. No interpolation/forward-fill merely for model convenience.

---

# 7. Supervised trajectory evidence — CLOSED

Frozen development cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events;
- fold SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

This cohort is now exposed.

## Lane A v1

Result:

- MAE 4153.34 vs 2594.54 incumbent;
- +60.1% worse.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

## Lane B v1

Result:

- MAE 2595.40;
- +0.87 worse than incumbent;
- predictions collapsed near zero correction.

Decision:

`DO_NOT_ADVANCE`

## Lane B v2

Target scaling changed raw seat residual into residual ratio while keeping architecture/folds/optimizer/seeds fixed.

Result:

- MAE 4792.42;
- +2197.88 worse than incumbent;
- median absolute correction ~1551 seats;
- worst event degradation +4647.90.

Decision:

`MECHANISM_NOT_SUPPORTED`

Conclusion:

> **Target scaling solved the zero-output problem mechanically, but produced harmful over-corrections. Stop supervised tuning on this exposed cohort.**

Do not now try post-hoc shrinkage factors, caps, different LR/epochs, Huber, LSTM, TCN or Transformer against the same five exposed events.

---

# 8. Active research — target-free trajectory pretraining v1

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Split manifest:

`ml/artifacts/trajectory_self_supervised_v1_split.json`

Frozen data cutoff:

`2026-10-28T22:09:43.958409Z`

This experiment uses **no attendance labels and no structural P50**.

## Frozen usable sample

- 26 usable events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 train pairs;
- 5 temporally later validation events / 168 validation pairs.

Validation events:

`[447, 449, 450, 451, 452]`

## Target-free task

Input:

- genuine trajectory prefix up to source observation;
- max 168h context;
- >=4 observations;
- >=24h observed prefix span.

Target:

`future_available_index_~24h - source_available_index`

Zero-change baseline:

`predicted delta = 0`

## Frozen model

- one-layer GRU;
- input 4;
- hidden 8;
- 8-unit MLP head;
- dropout .20;
- AdamW .001 / wd .01;
- weighted L1;
- batch 128;
- 100 epochs;
- grad clip 1;
- seed 17;
- no early stopping;
- no hyperparameter search.

Evidence label:

`target_free_temporal_validation`

A win means only that the encoder learns trajectory dynamics better than a zero-change baseline. It does **not** mean attendance MAE improves.

---

# 9. Self-supervised data/export path

Frozen target-free export:

`public.export_trajectory_self_supervised_v1()`

OIDC gateway:

`trajectory_self_supervised_export_v1`

GitHub workflow:

`.github/workflows/trajectory-self-supervised-v1.yml`

Guards:

- exact frozen cutoff;
- exactly 26 exported events;
- exactly 3397 train + 168 validation usable pairs after reconstruction;
- `attendance_labels_used=false`;
- `structural_prior_used=false`;
- `production_change=false`.

---

# 10. Immediate execution order

## Evidence protection

1. Protect imminent P9/Form5 windows.
2. Score P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.

## Trajectory R&D

4. Finish frozen self-supervised v1 run.
5. Persist result and encoder artifact.
6. Do not tune SSP v1 after validation result.
7. If it beats zero-change on multiple validation events, freeze the encoder before any attendance-head experiment.
8. If it fails, do not tune against those same five validation events; any material change becomes SSP v2.
9. Continue collecting genuine trajectories and independent future attendance labels.
10. Derive business minimum meaningful attendance Delta MAE independently.

Production remains separately review-gated.

---

# 11. Decision rules after SSP v1

## `REPRESENTATION_SUPPORTED`

Require:

- validation event-balanced MAE < zero-change baseline;
- improvement on at least two of five validation events;
- non-collapsed predictions;
- all data guards pass.

Then:

- freeze encoder artifact;
- do not call it attendance validation;
- define a separately precommitted small attendance head;
- judge attendance value only on future immutable predictions/outcomes.

## `REPRESENTATION_NOT_SUPPORTED`

Then:

- do not tune architecture/hyperparameters on the same five validation events;
- reassess trajectory representation/task;
- any material change becomes SSP v2.

Prospective attendance evidence remains the final authority.
