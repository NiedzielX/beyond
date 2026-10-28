# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
6. [`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`](ml/TRAJECTORY_FEATURE_CONTRACT_V1.md)
7. [`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`](ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md)
8. [`ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`](ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md)
9. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
10. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md)

Read the exact precommit before touching a frozen experiment. Roadmap v5 is canonical; do not restart from v3/v4.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

Desired: `Delta MAE < 0`

Production remains: `live_adjustment = 0`

---

## Current phase

Beyond is doing two things in parallel:

1. protect genuine prospective P7/P9/Form5 evidence;
2. develop the first trajectory-first Lane A vs Lane B comparison.

The daily trajectory infrastructure phase is already delivered.

### Implemented

- canonical PIT-safe P-N dataset builder;
- future-snapshot / structural-prior leakage tests;
- immutable daily attempt/prediction/score ledgers in Supabase;
- post-outcome scoring + MAE-by-horizon backend;
- Trajectory Feature Contract v1, documented and executable;
- strict-forward Validation Fold Contract v1, documented and executable;
- Demand Engine tests green.

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

Canonical SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

---

## Trajectory direction

Target product/model behaviour:

`P-60 -> P-59 -> ... -> genuine observed prefix -> today -> predicted remaining path -> final attendance`

This is **daily inference, not daily retuning**.

Current data are genuinely sparse early:

- 32 events / 14 clubs with any pre-kickoff inventory observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- current P-31...P-60 historical coverage = 0.

So P-60 is a **collection horizon**, not a requirement for a fabricated 60-day vector.

Lane B uses genuine variable-length sequences and explicit padding masks. No forward-fill. Missing inventory is not zero.

---

## Frozen first comparison

### Lane A

`structural P50 + engineered trajectory features -> residual correction`

### Lane B

`structural P50 + genuine ordered variable-length snapshot sequence -> residual correction`

Both lanes use the same information boundary and exclude unrelated odds/weather/hype/match-stakes/context in v1.

Shared primary input gate:

- PIT-valid structural incumbent;
- >=4 clean snapshots;
- >=24h observation window;
- canonical `signal_readiness=ready`;
- no future target trajectory/outcome.

Primary validation:

- strict expanding temporal event folds;
- all prefixes from one event stay together;
- same-kickoff events stay together;
- minimum 5 prior train events / 4 train clubs;
- Lane A and Lane B use the exact same fold registry.

Random daily-row CV is prohibited.

---

## Current execution priorities

1. Protect imminent P9 v1/v2 and Form5 windows.
2. Score P7/P9 only after genuine outcomes.
3. Keep P11/P4a collection healthy.
4. **Precommit Lane A development protocol.**
5. **Precommit first small Lane B sequence protocol.**
6. Materialize one shared eligible event/cutoff export + fold-registry manifest.
7. Run Lane A/B on identical strict-forward folds.
8. Report MAE together with independent event/club support.
9. Freeze a candidate only if evidence justifies it.
10. Start prospective daily shadow inference only after candidate freeze and before future outcomes.
11. Derive business minimum meaningful Delta MAE independently.

Operational source of truth: [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)

---

## Important semantics

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales and not confirmed attendance.

Never infer attendance labels from inventory, capacity, model output or hidden/unknown inventory.

---

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> event-safe evaluation -> immutable artifacts/hashes -> result -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause separately versioned model development.**
