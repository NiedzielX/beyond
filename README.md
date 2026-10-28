# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
6. [`ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`](ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md)
7. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md)
8. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
9. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md)

When working on a frozen experiment, also read its exact precommit before changing anything.

Do **not** restart from Roadmap v3/v4. Roadmap v5 is canonical.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `Delta MAE < 0`

Production remains unchanged: `live_adjustment = 0`

No research result activates production automatically.

---

## Current research mode

Beyond is doing two things in parallel.

### 1. Protect genuine prospective evidence

Do not mutate the active/frozen lanes:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72 frozen package;
- P11/P4a genuine evidence collection.

### 2. Build trajectory-first forecasting

Accepted direction:

`P-60 -> P-59 -> ... -> genuine observed prefix -> today -> predicted remaining path -> final attendance`

Daily forecasts use everything genuinely known at that cutoff. This is **daily inference, not daily retuning**.

Two model lanes will be compared on the same event-safe evidence:

- **Lane A:** simple/regularized trajectory residual model;
- **Lane B:** intentionally higher-risk small sequence model (GRU/LSTM/TCN first; compact Transformer later only if justified).

We accept early sequence-model research with limited labels. We do **not** relax PIT safety, event independence or prospective evidence requirements.

---

## Daily trajectory infrastructure status

Already implemented/live:

- canonical PIT-safe P-N dataset builder;
- future-snapshot / structural-prior leakage tests;
- green Demand Engine CI;
- live coverage/missingness audit;
- immutable daily attempt ledger;
- immutable daily prediction ledger;
- immutable post-outcome scoring ledger;
- MAE-by-horizon backend;
- controlled service-role RPC permissions.

Key data reality:

- 32 current Ekstraklasa events have any genuine pre-kickoff inventory observation;
- median first observation is only around P-9.3;
- earliest observed event is around P-30.3;
- current snapshot coverage is about 3% at P-30, 22% at P-14, 62% at P-7, 75% at P-3 and 95% at P-1;
- P-31...P-60 historical coverage is currently zero.

Therefore P-60 is a **collection horizon**, not a requirement for a fabricated 60-day input vector. Sequence models must support genuine variable-length prefixes and explicit missingness/masks.

Canonical SQL contract:

[`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`](supabase/sql/daily_trajectory_prospective_evidence_v1.sql)

---

## Current execution priorities

1. Protect every genuine P9 v1/v2 T-48/T-24 window.
2. Protect Form5 prospective T-24 captures.
3. Score P7/P9 only after genuine outcomes arrive.
4. Keep P11/P4a genuine evidence accumulation healthy.
5. Keep Long72 frozen and operationally healthy.
6. Freeze `Trajectory Feature Contract v1` shared by Lane A/B.
7. Freeze one event-grouped fold/export registry shared by both lanes.
8. Precommit Lane A and first small Lane B development protocols.
9. Compare both lanes on identical events/cutoffs/PIT rules.
10. Start prospective daily shadow inference only after candidate contracts are frozen and before outcomes are known.
11. Derive the business minimum meaningful Delta MAE independently of model results.

Operational source of truth:

[`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)

---

## Important modelling distinction

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales and not confirmed attendance.

Never infer attendance labels from inventory, capacity, model output or hidden/unknown inventory.

Hidden or unknown inventory is never converted to zero.

---

## Validation rule for daily trajectories

Daily rows are correlated.

`50 events x 40 prefixes = 2,000 rows`

still means only:

`50 independent events`.

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
