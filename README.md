# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

Read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
6. [`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`](ml/TRAJECTORY_FEATURE_CONTRACT_V1.md)
7. [`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`](ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md)
8. [`ml/TRAJECTORY_LANE_A_RESULT_V1.md`](ml/TRAJECTORY_LANE_A_RESULT_V1.md)
9. [`ml/TRAJECTORY_LANE_B_RESULT_V1.md`](ml/TRAJECTORY_LANE_B_RESULT_V1.md)
10. [`ml/TRAJECTORY_LANE_B_V2_PRECOMMIT.md`](ml/TRAJECTORY_LANE_B_V2_PRECOMMIT.md)
11. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)

Roadmap v5 is canonical. Read the exact precommit before touching a frozen experiment.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

Production remains:

`live_adjustment = 0`

---

## Current state in one minute

### Prospective evidence

Protect P7 / P9 / Form5 and current evidence-collection contracts. Do not retune frozen learners after outcomes.

### Trajectory research

The infrastructure is complete and two first model experiments are closed.

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | **+1558.80** | rejected |
| Lane B v1 — small GRU / raw seat residual | 2595.40 | **+0.87** | do not advance |

Lane A made harmful corrections.

Lane B v1 was very different: it was stable and effectively learned **almost zero correction**. Its predicted residuals were only about `-0.06...+4.33` seats, so its result almost exactly reproduced the structural incumbent.

That means the active question is now narrower:

> **Did Lane B v1 fail because the raw seat residual target was badly scaled for the frozen small-GRU/L1 setup?**

---

## Active experiment — Lane B v2

Precommit:

[`ml/TRAJECTORY_LANE_B_V2_PRECOMMIT.md`](ml/TRAJECTORY_LANE_B_V2_PRECOMMIT.md)

V2 changes only the target/output scale:

`residual_ratio = (actual - structural_p50) / structural_p50`

Then:

`predicted_seat_residual = predicted_ratio * structural_p50`

Unchanged from v1:

- same 10 events / 19 frozen checkpoint rows;
- same strict-forward folds;
- same sequence representation;
- same GRU architecture;
- same optimizer / learning rate / weight decay;
- same L1 loss;
- same 200 epochs;
- same seeds 17 / 29 / 41;
- same event-balanced weighting.

Important:

> **The v2 cohort is already exposed. V2 is a mechanism diagnostic, not unseen validation.**

A good v2 result can justify freezing a future prospective candidate. It cannot by itself prove promotion readiness.

---

## Frozen development evidence

Cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events;
- fold SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Rules:

- only earlier-kickoff events train later events;
- same-kickoff events stay together;
- every prefix from an event stays in the same fold;
- random daily-row CV is prohibited.

---

## Trajectory data reality

Current genuine history remains short:

- 32 events / 14 clubs with any pre-kickoff observation;
- median first observation around P-9.3;
- earliest around P-30.3;
- P-31...P-60 historical coverage currently zero.

P-60 is a **collection horizon**, not a requirement for a fabricated 60-day vector.

Use genuine variable-length sequences. Missing/hidden inventory is never zero.

---

## Implemented stack

- PIT trajectory feature store;
- exact daily P-N builder;
- shared Lane A/B materializer;
- frozen feature contract;
- frozen strict-forward fold contract;
- immutable prospective attempt/prediction/score ledgers;
- MAE-by-horizon scoring;
- OIDC-protected historical development export;
- Lane A v1 learner/result;
- Lane B v1 learner/result;
- Lane B v2 ratio-target learner/runner/workflow.

No production activation is connected to any of these research workflows.

---

## Current priorities

1. Protect imminent P9/Form5 prospective windows.
2. Score frozen P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.
4. Finish and record **Lane B v2** diagnostic.
5. Do not tune v2 after seeing its result.
6. If target scaling is supported, freeze the exact mechanism for **future prospective daily shadow evidence**.
7. If scaling is not supported, reassess the sequence/data hypothesis before trying more architectures.
8. Keep collecting longer genuine trajectories.
9. Derive business minimum meaningful Delta MAE independently.

Operational source of truth:

[`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)

---

## Important semantics

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales or attendance.

Never infer attendance labels from inventory, capacity, model output or hidden/unknown inventory.

---

## Engineering rule

`hypothesis -> precommit -> PIT contract -> code -> strict evidence -> result -> decision -> canonical docs`

> **A failed frozen experiment is evidence. Do not repair it after seeing the answer.**
