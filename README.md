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
8. [`ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md`](ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md)
9. [`ml/TRAJECTORY_LANE_A_RESULT_V1.md`](ml/TRAJECTORY_LANE_A_RESULT_V1.md)
10. [`ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`](ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md)
11. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)

Read the exact precommit before touching a frozen experiment.

Roadmap v5 is canonical. Do not restart from v3/v4.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

Desired: `Delta MAE < 0`

Production remains:

`live_adjustment = 0`

---

## Current state in one minute

### Prospective evidence track

Protect P7 / P9 / Form5 and current evidence-collection contracts. Do not retune frozen learners after outcomes.

### Trajectory R&D track

Infrastructure is complete.

The first simple trajectory benchmark has already been tested:

**Lane A v1 — Ridge residual model**

- incumbent event-balanced MAE: **2594.5**;
- Lane A MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- about **60.1% worse**;
- 5 independent strict-forward test events.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Do not tune Lane A v1 after this result.

The active experiment is now:

**Lane B v1 — small GRU over the genuine ordered trajectory**.

Its job is to test whether sequence representation contains signal that engineered velocity/acceleration summaries missed.

---

## Frozen development comparison

### Lane A — frozen failed benchmark

`structural P50 + engineered trajectory features -> residual`

Precommit:

`ml/TRAJECTORY_LANE_A_PRECOMMIT_V1.md`

Result:

`ml/TRAJECTORY_LANE_A_RESULT_V1.md`

### Lane B — active

`structural P50 + genuine variable-length trajectory -> small GRU -> residual`

Precommit:

`ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`

Executable learner:

`ml/demand_engine/trajectory_lane_b_v1.py`

Lane B must beat:

1. the structural incumbent;
2. the frozen Lane A benchmark.

No architecture search in v1.

---

## Validation is intentionally strict

Frozen cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 5 strict-forward outer test events;
- only earlier-kickoff events train a later event;
- same-kickoff events stay together;
- every prefix from an event stays in the same fold;
- minimum 5 previous events / 4 clubs before a fold becomes evaluable.

Random daily-row CV is prohibited.

More prefixes do **not** mean more independent events.

---

## Trajectory data reality

Current genuine history is short:

- 32 events / 14 clubs with any pre-kickoff observation;
- median first observation around P-9.3;
- earliest around P-30.3;
- P-31...P-60 historical coverage currently zero.

So P-60 is a **collection horizon**, not a requirement for a fake complete sequence.

Lane B uses variable-length genuine sequences with explicit lengths/masks.

No interpolation/forward-fill merely to create model input.

---

## Implemented trajectory stack

- PIT live trajectory feature store;
- daily P-N dataset builder;
- shared Lane A/B dataset materializer;
- frozen feature contract;
- frozen strict-forward fold contract;
- frozen development cohort manifest;
- Lane A learner + result;
- Lane B GRU learner;
- immutable daily attempt/prediction/score ledgers;
- MAE-by-horizon scoring;
- service-role research event bundle RPC.

Canonical research bundle SQL:

`supabase/sql/trajectory_research_event_bundle_v1.sql`

---

## Current execution priorities

1. Protect imminent P9/Form5 prospective windows.
2. Score frozen P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.
4. Validate CI after the new Lane A/B code.
5. Run **Lane B v1** on the frozen strict-forward cohort.
6. Persist Lane B result without post-result tuning.
7. If Lane B wins, freeze a separate prospective daily-shadow candidate before future outcomes.
8. If Lane B fails, diagnose first; any changed experiment becomes v2.
9. Keep collecting longer genuine trajectories.
10. Derive business minimum meaningful Delta MAE independently.

Operational source of truth:

[`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)

---

## Important semantics

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales or attendance.

Never infer attendance labels from inventory, capacity, model output or hidden/unknown inventory.

Hidden/unknown inventory is never zero.

---

## Engineering rule

`hypothesis -> precommit -> PIT contract -> code -> tests -> strict evidence -> result -> decision -> canonical docs`

> **A failed frozen experiment is evidence. Do not repair it after seeing the answer.**
