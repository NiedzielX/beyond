# Beyond Agent Instructions

Last updated: **2026-10-28**

## Read first

For any Beyond forecasting / ML / Demand Engine task:

1. `AI_BOOTSTRAP.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/NEXT_SESSION_HANDOFF.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
5. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
6. `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
7. `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
8. `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`;
9. `ml/PROGRESS_TRACKING.md`;
10. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Read the exact precommit before touching any frozen experiment. Query live/machine state fresh before acting on scheduled windows or readiness assumptions.

Roadmap v5 is canonical. Do not restart from v3/v4.

---

## Core objective

> **Lower true prospective event-balanced attendance MAE, not model complexity.**

Primary metric:

`Delta MAE = challenger MAE - incumbent MAE`

Desired: `Delta MAE < 0`

Production remains:

`live_adjustment = 0`

---

## Current phase

### Protect frozen evidence

Do not mutate:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72 frozen package;
- P11/P4a evidence rules.

### Develop Lane A vs Lane B

Daily trajectory infrastructure is already implemented. Do not create a parallel dataset/ledger/scoring stack.

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

Canonical persistence SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

Next work is to precommit and execute the first Lane A and Lane B development protocols on the shared contracts.

---

## Feature contract v1

Shared primary eligibility:

- P-60...P-1 cutoff;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no target future trajectory;
- no target outcome.

Lane A:

`structural P50 + engineered trajectory scalar features -> residual`

Lane B:

`structural P50 + genuine ordered variable-length snapshot sequence -> residual`

Lane B v1 sequence rules:

- exact timestamp dedupe keeps highest snapshot ID;
- max one genuine observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- explicit padding mask/sequence length;
- padded zero never means genuine zero inventory.

Exclude odds/weather/hype/match-stakes/Form5/P4 context from both v1 lanes so the comparison isolates trajectory representation.

---

## Validation fold contract v1

Primary validation:

- strict expanding temporal event folds;
- event/match is the independent unit;
- same-kickoff events are held out together;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- all prefixes from one event stay in the same fold;
- Lane A and Lane B use the exact same fold registry.

LOEO/LOCO may be secondary diagnostics. Random daily-row/snapshot CV is prohibited.

Preprocessing must be fitted inside train folds only.

---

## Current data reality

Current genuine pre-kickoff trajectory sample:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Representative coverage:

- P-30 ~3%;
- P-14 ~22%;
- P-7 ~62%;
- P-3 ~75%;
- P-1 ~95%.

Shared-gate labeled checkpoint counts:

- T-30: 0;
- T-14: 0;
- T-7: 4;
- T-3: 5;
- T-1: 10.

Do not pretend this is a large dataset. The accepted response is variable-length sequence research + strict evidence discipline, not fabricated history or random CV.

---

## Lane A / Lane B model rule

Lane A candidate set must stay small and precommitted.

Lane B accepted architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer only if simpler sequence models establish value.

Self-supervised trajectory pretraining is allowed, but it does not create additional independent attendance outcomes.

Research/model risk is accepted. Evidence/leakage shortcuts are not.

---

## Hard rules

- protect imminent genuine P9/Form5 windows first;
- never lower a gate just to get coverage;
- never manufacture PIT history;
- never infer attendance from inventory/capacity/model output;
- unknown/hidden inventory is not zero;
- all prefixes from one event stay together;
- no target future trajectory;
- no target attendance during inference;
- persist prospective forecasts before outcomes;
- keep differently frozen learners separately auditable;
- no automatic production activation.

The old ChatGPT Beyond readiness automations remain disabled. Do not enable them implicitly.
