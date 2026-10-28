# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/EXECUTION_PLAN_CURRENT.md`;
2. `ml/NEXT_SESSION_HANDOFF.md`;
3. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/TRAJECTORY_LANE_A_RESULT_V1.md`;
6. `ml/TRAJECTORY_LANE_B_RESULT_V1.md`;
7. `ml/TRAJECTORY_LANE_B_V2_RESULT.md`;
8. `ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`;
9. `ml/PROGRESS_TRACKING.md`;
10. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Read the exact precommit before touching a frozen experiment. Query live machine state before acting on scheduled prospective windows.

Roadmap v5 is canonical.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

---

## 3. Current model state

Structural forecast remains the incumbent.

Supervised trajectory experiments on the frozen 10-event cohort are closed:

| Model | MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 | 4153.34 | +1558.80 | rejected |
| Lane B v1 | 2595.40 | +0.87 | do not advance |
| Lane B v2 | 4792.42 | +2197.88 | mechanism not supported |

Do not tune A/B v1/v2 further on the same exposed five outer events.

In particular, do not run post-hoc:

- shrinkage/correction caps;
- LR/epoch/loss sweeps;
- LSTM/TCN/Transformer tournament;
- manual horizon multipliers.

Any such work would be increasingly optimized against known answers.

---

## 4. Active trajectory task

Active experiment:

`trajectory-self-supervised-24h-delta-v1`

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Purpose:

> **Learn trajectory dynamics without attendance labels, then freeze the encoder before future attendance evaluation.**

Frozen cutoff:

`2026-10-28T22:09:43.958409Z`

Usable sample:

- 26 events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 later validation events / 168 pairs.

No attendance labels. No structural P50. No club/event identity as a model feature.

---

## 5. Frozen SSP v1 protocol

Task:

`trajectory prefix -> normalized inventory delta ~24h later`

Baseline:

`predict delta = 0`

Input prefix:

- genuine observations only;
- max 168h context;
- >=4 observations;
- >=24h observed span;
- no interpolation/forward-fill.

Model:

- GRU input 4;
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

A win means useful representation learning only, not attendance-model validation.

---

## 6. SSP data/export path

Split manifest:

`ml/artifacts/trajectory_self_supervised_v1_split.json`

Export RPC:

`public.export_trajectory_self_supervised_v1()`

OIDC gateway:

`trajectory_self_supervised_export_v1`

Workflow:

`.github/workflows/trajectory-self-supervised-v1.yml`

Runner:

`ml/run_trajectory_self_supervised_v1.py`

Hard guards require:

- exact frozen cutoff;
- 26 exported events;
- reconstructed 3397 train + 168 validation pairs;
- `attendance_labels_used=false`;
- `structural_prior_used=false`;
- `production_change=false`.

---

## 7. Decision after SSP v1

If validation event-balanced MAE beats zero-change on at least two validation events and predictions are non-collapsed:

`REPRESENTATION_SUPPORTED`

Then freeze the encoder before any attendance-head experiment.

If not:

`REPRESENTATION_NOT_SUPPORTED`

Do not tune v1 against the same five validation events. Any material change becomes SSP v2.

Attendance value must ultimately be judged on genuinely future immutable predictions/outcomes.

---

## 8. Prospective evidence remains protected

P7 / P9 / Form5 and current collection contracts remain separate from trajectory R&D.

An imminent genuine prospective window takes priority over research work.

---

## 9. Hard rules

- no future target trajectory;
- no target attendance in self-supervised research;
- no structural P50 in SSP v1;
- no fabricated history;
- no random event leakage;
- no post-result tuning and still call it v1;
- missing/hidden inventory is never zero;
- no automatic production activation.
