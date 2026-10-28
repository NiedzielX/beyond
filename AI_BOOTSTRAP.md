# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/EXECUTION_PLAN_CURRENT.md`;
2. `ml/NEXT_SESSION_HANDOFF.md`;
3. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`;
6. `ml/CURRENT_MODEL.md`;
7. `ml/PROGRESS_TRACKING.md`;
8. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Then read the exact precommit for any frozen experiment you are about to touch.

Do not restart from Roadmap v3/v4. Query live/machine state fresh before changing operational assumptions.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `Delta MAE < 0`

Production remains: `live_adjustment = 0`

Readiness, snapshot counts, trajectory rows, support counts and prediction counts are prerequisites, not model success.

---

## 3. Current execution mode

Beyond is in **prospective validation + trajectory model development** mode.

### Protect frozen evidence first

- P7 prospective: collect/score only;
- P9 v1: protect every T-48/T-24 window;
- P9 Family Fallback v2: run separately, never pool with v1;
- Form5: protect genuine T-24 captures;
- Long72: frozen / low priority;
- P11/P4a: genuine evidence accumulation only.

### Daily trajectory infrastructure is already delivered

Implemented/live:

- canonical P-N dataset builder + PIT tests;
- immutable daily attempt/prediction/score ledgers;
- post-outcome scoring;
- MAE-by-horizon backend;
- coverage/missingness audit;
- controlled service-role write RPCs.

Do not rebuild these as a parallel implementation.

Canonical code:

- `ml/demand_engine/live_trajectory_feature_store.py`;
- `ml/demand_engine/daily_trajectory_dataset.py`;
- `supabase/sql/daily_trajectory_prospective_evidence_v1.sql`.

---

## 4. Data reality that changes model design

Current genuine Ekstraklasa inventory data:

- 32 events / 14 clubs with any pre-kickoff inventory observation;
- median first observation ~P-9.3;
- p75 ~P-14;
- earliest ~P-30.3;
- coverage ~3% P-30, 22% P-14, 62% P-7, 75% P-3, 95% P-1;
- P-31...P-60 historical coverage currently zero.

Therefore:

- P-60 is a collection horizon, not a mandatory complete input;
- use genuine variable-length prefixes;
- missing does not become zero;
- Lane B must use lengths/masks or equivalent missingness-aware handling;
- preferred sequence input is the ordered genuine snapshot sequence with time-to-kickoff/time-gap information, not fabricated daily forward-fill.

---

## 5. Next new-model task

The next task is **not** another broad feature tournament.

Freeze a shared `Trajectory Feature Contract v1` and an event-grouped fold/export registry.

Then compare on identical evidence:

### Lane A

`structural P50 + simple engineered-trajectory residual model`

Candidate families remain restrained: Ridge/ElasticNet, small tree/boosting residual model, nearest-trajectory correction.

### Lane B

`structural P50 + genuine variable-length sequence encoder residual model`

Accepted research order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact Transformer only if simpler sequence models establish value.

Sequence research starts early despite limited labels, but remains research/shadow-only.

---

## 6. Accepted model-risk decision

Research risk is allowed. Evidence shortcuts are not.

Never:

- random-split daily rows;
- treat prefixes as independent events;
- expose future target trajectory;
- expose target attendance during prediction;
- fabricate missing history;
- retune frozen challengers on prospective outcomes;
- call model complexity a success metric.

Self-supervised trajectory pretraining is allowed, but it does not increase independent attendance-event count.

---

## 7. Current key state

### P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine prospective attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- `PIT_SUPPORT_INSUFFICIENT`;
- 1 genuine attempt / 0 predictions / 0 scored;
- correct fail-closed.

### P9 v2

Separately precommitted/deployed. Same five v1 neighbors, unchanged support gate, Structural fallback only under frozen rule. No retro event443. Never pool with v1.

### Form5

First legal T-24 capture: **event443 — 2026-10-29 17:00 UTC**.

### P7

53 immutable rows / 6 events / 0 scored. No retuning.

### Long72

5 scored; 6082.40 -> 6039.39; 43.01 / 0.71% improvement; frozen/low priority.

### P11

6 events / 6 clubs; T-24/T-72/T-168 = 5/5/0; no model fit yet.

---

## 8. Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains a genuine inventory watch. Unknown inventory is not zero.

---

## 9. Hard rules

- protect genuine prospective windows before lower-priority R&D;
- never lower a gate just to get coverage;
- never manufacture PIT history;
- never infer attendance from inventory/capacity/model output;
- keep all prefixes from one event in one fold;
- persist forecasts before outcomes;
- keep frozen learners separately auditable;
- query machine state fresh;
- keep `live_adjustment=0` until explicit reviewed promotion.
