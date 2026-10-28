# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md)
7. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
8. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md)

When working on a frozen experiment, also read its exact precommit before changing anything.

Do **not** restart from Roadmap v3/v4. Roadmap v5 is canonical.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction:

`Delta MAE < 0`

Production remains unchanged:

`live_adjustment = 0`

No research result activates production automatically.

---

## Current research mode

Beyond is now doing two things in parallel:

### 1. Protect genuine prospective evidence

Do not mutate the active/frozen lanes:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72 frozen package;
- P11/P4a genuine evidence collection.

### 2. Build the next trajectory-first forecasting capability

New accepted direction:

`P-60 -> P-59 -> ... -> today -> forecast remaining trajectory -> final attendance`

The system should eventually create a new immutable forecast at every daily cutoff using the **complete genuine trajectory prefix visible at that moment**.

This is **daily inference, not daily retuning**.

The next model program has two parallel lanes:

- **Lane A:** simple/regularized trajectory residual models;
- **Lane B:** intentionally higher-risk small sequence models (GRU/LSTM/TCN first, compact Transformer later only if justified).

We accept early sequence-model research even with limited labels, but we do **not** relax PIT safety, event-grouped validation or prospective evidence requirements.

Detailed plan:

[`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)

---

## Current execution priorities

1. Protect every genuine P9 v1/v2 T-48/T-24 window.
2. Protect Form5 prospective T-24 captures.
3. Score P7/P9 only after genuine outcomes arrive.
4. Keep P11/P4a genuine evidence accumulation healthy.
5. Keep Long72 frozen and operationally healthy.
6. In parallel, build the canonical daily trajectory dataset.
7. Add immutable daily forecast/attempt persistence.
8. Add horizon-wise MAE reporting.
9. Then precommit and compare Lane A vs Lane B under identical PIT-safe/event-grouped evaluation.
10. Derive the business minimum meaningful Delta MAE independently of model results.

Operational source of truth:

[`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)

---

## Important modelling distinction

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales and not confirmed attendance.

Never infer attendance labels from:

- inventory;
- capacity;
- model output;
- hidden/unknown inventory.

Hidden or unknown inventory is never converted to zero.

---

## Validation rule for daily trajectories

Daily rows are correlated.

For example:

`50 events x 40 prefixes = 2,000 rows`

still means only:

`50 independent events`

Therefore:

- split/evaluate by event;
- keep every prefix from one event in the same fold;
- never use random daily-row splits as headline evidence;
- never let future target snapshots enter an earlier cutoff;
- persist prospective forecasts before target outcomes are known.

---

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> event-safe evaluation -> immutable artifacts/hashes -> result -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause separately versioned model development.**
