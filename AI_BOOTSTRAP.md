# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/EXECUTION_PLAN_CURRENT.md`;
2. `ml/NEXT_SESSION_HANDOFF.md`;
3. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
6. `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
7. `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`;
8. `ml/PROGRESS_TRACKING.md`;
9. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Read the exact precommit before touching a frozen experiment. Query live/machine state fresh before acting on scheduled windows or readiness assumptions.

Roadmap v5 is canonical. Do not restart from v3/v4.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger MAE - incumbent MAE`

Desired: `Delta MAE < 0`

Production remains: `live_adjustment = 0`

---

## 3. Current phase

Beyond is in **prospective validation + first trajectory-model development** mode.

### Protect frozen evidence first

- P7 prospective: collect/score only;
- P9 v1: protect T-48/T-24 windows;
- P9 Family Fallback v2: run separately, never pool with v1;
- Form5: protect genuine T-24 captures;
- Long72: frozen / low priority;
- P11/P4a: genuine evidence accumulation only.

### Trajectory infrastructure is already delivered

Do not rebuild another daily dataset/ledger/scoring stack.

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `ml/demand_engine/trajectory_feature_contract_v1.py`;
- `ml/demand_engine/trajectory_validation_folds_v1.py`.

Canonical persistence:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

---

## 4. Frozen trajectory development contracts

### Feature Contract v1

`trajectory-feature-contract-v1`

Shared primary eligibility:

- P-60...P-1;
- PIT-valid structural incumbent;
- >=4 clean genuine snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no target future trajectory/outcome.

Lane A receives engineered trajectory scalar summaries + structural P50.

Lane B receives the genuine ordered variable-length snapshot sequence + structural P50/global quality context.

Lane B uses no interpolation/forward-fill and requires an explicit padding mask/sequence length.

### Validation Fold Contract v1

`trajectory-validation-fold-contract-v1`

Primary method:

- strict expanding temporal event folds;
- all prefixes from one event stay in the same fold;
- same-kickoff events stay together;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- Lane A/B use identical fold registry/manifest.

Random row/snapshot CV is prohibited.

---

## 5. Current data reality

Current genuine pre-kickoff inventory sample:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- p75 ~P-14;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Representative coverage:

- P-30 ~3%;
- P-14 ~22%;
- P-7 ~62%;
- P-3 ~75%;
- P-1 ~95%.

Shared-gate labeled checkpoint support:

- T-30: 0;
- T-14: 0;
- T-7: 4;
- T-3: 5;
- T-1: 10.

Do not pretend this is a large independent sample. More prefixes help training/representation learning, not independent-event evidence.

---

## 6. Next new-model work

The next task is **model-development precommit**, not more generic infrastructure.

### Lane A

Freeze a small benchmark protocol around:

`structural P50 + engineered trajectory residual -> challenger P50`

Keep candidate families small: Ridge/ElasticNet, optionally one restrained tree/boosting residual model, optionally one auditable nearest-trajectory method.

### Lane B

Freeze the first small sequence protocol around:

`structural P50 + genuine variable-length trajectory -> residual`

Accepted architecture order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer only if simpler sequence models establish value.

Lane A/B must use the same event identities, cutoffs, fold registry, incumbent and scoring rules.

---

## 7. Accepted risk decision

> **Test sequence models early despite limited labels.**

Research/model risk is allowed. Evidence shortcuts are not.

Never:

- random-split daily rows;
- treat prefixes as independent events;
- expose future target trajectory;
- expose target attendance during inference;
- fabricate missing history;
- retune frozen challengers on prospective outcomes;
- use complexity as a success metric.

Self-supervised trajectory pretraining is allowed but does not increase independent attendance-event count.

---

## 8. Current protected state

### P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine prospective attempt:

- event443 Cracovia–Motor T-48;
- 2026-10-28 17:00 UTC;
- `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored;
- correct fail-closed.

### P9 v2

Separately precommitted/deployed; same exact five v1 neighbors/support gate; Structural fallback only under frozen rule; never retro-predict event443; never pool v1/v2 evidence.

### Form5

First legal T-24 capture: **event443 — 2026-10-29 17:00 UTC**.

### P7

53 immutable rows / 6 events / 0 scored. No retuning.

### Long72

5 scored; 6082.40 -> 6039.39; 43.01 / 0.71% improvement; frozen/low priority.

### P11

6 events / 6 clubs; T-24/T-72/T-168 = 5/5/0; no model fit yet.

---

## 9. Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains an inventory watch. Unknown inventory is not zero.

---

## 10. Hard rules

- protect genuine prospective windows before lower-priority R&D;
- never lower a gate for coverage;
- never manufacture PIT history;
- never infer attendance from inventory/capacity/model output;
- unknown/hidden inventory is not zero;
- keep all prefixes from one event together;
- persist prospective forecasts before outcomes;
- keep frozen learners separately auditable;
- query machine state fresh;
- no automatic production activation.
