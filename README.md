# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

Read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
6. [`ml/TRAJECTORY_LANE_A_RESULT_V1.md`](ml/TRAJECTORY_LANE_A_RESULT_V1.md)
7. [`ml/TRAJECTORY_LANE_B_RESULT_V1.md`](ml/TRAJECTORY_LANE_B_RESULT_V1.md)
8. [`ml/TRAJECTORY_LANE_B_V2_RESULT.md`](ml/TRAJECTORY_LANE_B_V2_RESULT.md)
9. [`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`](ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md)
10. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)

Roadmap v5 is canonical. Read the exact precommit before touching a frozen experiment.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

---

## Current state in one minute

The structural model remains the incumbent.

The first supervised trajectory experiments are closed:

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | **+1558.80** | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | **+0.87** | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | **+2197.88** | mechanism not supported |

What we learned:

- Lane A made harmful corrections;
- Lane B v1 was stable but learned almost `correction = 0`;
- Lane B v2 fixed the output-scale problem but over-corrected badly;
- the 10-event supervised development cohort is now fully exposed.

Therefore:

> **Stop supervised trajectory tuning on those same five outer test events.**

No post-hoc shrinkage, caps, learning-rate sweeps, loss swaps, LSTM/TCN/Transformer tournament, or manual horizon multipliers on the same exposed cohort.

---

## Active experiment — target-free trajectory pretraining v1

Precommit:

[`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`](ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md)

Goal:

> **Learn trajectory dynamics without attendance labels, then freeze the encoder before future attendance evaluation.**

Frozen data cutoff:

`2026-10-28T22:09:43.958409Z`

Usable target-free sample:

- 26 events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 train pairs;
- 5 later validation events / 168 validation pairs.

Task:

`genuine trajectory prefix -> predict normalized inventory change ~24h later`

Baseline:

`predict no change`

Model:

- GRU input 4 / hidden 8;
- small 8-unit head;
- AdamW .001 / wd .01;
- weighted L1;
- batch 128;
- 100 epochs;
- seed 17;
- no early stopping;
- no architecture or hyperparameter search.

No attendance labels. No structural P50. No club/event identity as a model feature.

A win means only that the encoder learned useful **trajectory dynamics**. It does not mean attendance MAE improved.

---

## Evidence-safe next step

If self-supervised v1 beats the zero-change baseline on multiple validation events:

1. freeze the encoder artifact;
2. do not tune it against attendance yet;
3. define a separately precommitted small attendance head;
4. create immutable future daily forecasts before outcomes;
5. judge attendance value on genuinely future independent events.

If it fails, any material change becomes self-supervised v2. Do not tune against the same five validation events and still call it v1.

---

## Prospective evidence remains protected

P7 / P9 / Form5 and current collection contracts remain separate from trajectory R&D.

Near-term genuine windows take priority over research work.

---

## Important semantics

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales or attendance.

Missing/hidden inventory is never zero.

P-60 is a collection horizon, not a requirement for a fabricated complete sequence.

---

## Engineering rule

`hypothesis -> precommit -> PIT contract -> code -> strict evidence -> result -> decision -> canonical docs`

> **A failed frozen experiment is evidence. Do not repair it after seeing the answer.**
