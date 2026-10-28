# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-28**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan:

`ml/EXECUTION_PLAN_CURRENT.md`

Production:

`live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Readiness/row counts are leading indicators only.

---

# 2. Current status

| Item | Status | Current decision |
|---|---|---|
| Multi-source ticketing coverage | ✅ LIVE | preserve acquisition/PIT evidence; hidden inventory stays fail-closed |
| P7 historical | ✅ FROZEN | 14.44% point gain; no retuning |
| P7 prospective | 🟢 53 rows / 6 events / 0 scored | collect/score only |
| P9 historical v1 | ⚪ NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT | no historical MAE; do not repair retrospectively |
| P9 prospective v1 | 🟢 1 genuine attempt / 0 prediction / 0 scored | protect every T-48/T-24 window |
| P9 Family Fallback v2 | 🟢 PRECOMMITTED / DEPLOYED | run separately; never pool with v1 |
| Form5 prospective | 🟢 READY FOR FIRST T-24 | protect event443 2026-10-29 17:00 UTC |
| Long72 | 🟡 5 scored / 0.71% point gain | frozen / low priority |
| P11 odds | 🟡 6 events / 6 clubs | 5/5/0 at T-24/T-72/T-168; keep collecting |
| P4a | 🟡 4/9 labeled / 3 distinct | gate still closed |
| Ticketing challenger | ❌ REJECTED | current 19-event LOCO challenger ~723.6 MAE worse |
| Hype 48h | ❌ REJECTED | ~69.4 MAE worse |
| Daily trajectory infrastructure | 🆕 START NOW | dataset + immutable daily ledger + horizon-wise MAE |
| Trajectory Lane A | 🆕 PLANNED | simple residual benchmark |
| Trajectory Lane B | 🆕 ACCEPTED R&D | small sequence model research starts early |
| Self-supervised trajectory | 🆕 PLANNED | target-free representation research |
| Business Delta MAE threshold | 🟡 PENDING | derive independently from operational value |

---

# 3. P9 state

## Historical v1

- 9/9 T-168 events / 9 clubs;
- T-24 support-ready 0/11;
- T-48 support-ready 0/9;
- result `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`;
- no valid historical challenger MAE.

## Prospective v1

First real attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- immutable attempt persisted;
- `PIT_SUPPORT_INSUFFICIENT`;
- correct fail-closed.

Do not relax support and do not retro-predict.

## Family Fallback v2

- separately precommitted/deployed;
- exact v1 neighbors;
- unchanged support threshold;
- Structural fallback only under the frozen v2 rule;
- no event443 retro prediction;
- current verified attempts/predictions/scores: 0/0/0.

---

# 4. Near-term protected evidence

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48 — 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48 — 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24 — 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48 — 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48 — 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48 — 2026-10-31 19:30 UTC.

Event448 stays a genuine no/unknown-inventory watch until the source exposes valid data.

---

# 5. New trajectory program

Canonical plan:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Target behaviour:

`P-60 -> P-59 -> ... -> today -> predicted remaining trajectory -> final attendance`

Immediate infrastructure milestones:

- [ ] canonical daily trajectory dataset;
- [ ] PIT lineage/missingness audit;
- [ ] immutable daily attempt ledger;
- [ ] immutable daily prediction ledger;
- [ ] horizon-wise MAE reporting;
- [ ] prospective daily shadow inference path.

## Lane A milestones

- [ ] freeze feature contract;
- [ ] freeze event-grouped folds;
- [ ] precommit simple residual challenger;
- [ ] historical/grouped result;
- [ ] prospective daily shadow predictions;
- [ ] genuine scored prospective result.

## Lane B milestones

- [ ] define sequence representation contract;
- [ ] small GRU/LSTM/TCN first benchmark;
- [ ] identical event-grouped folds as Lane A;
- [ ] compare against Lane A, not only incumbent;
- [ ] self-supervised pretraining experiment where justified;
- [ ] compact Transformer only if sequence representation already shows value;
- [ ] prospective daily shadow predictions;
- [ ] genuine scored prospective result.

---

# 6. Critical validation rule

Daily rows are not independent.

`N events x M prefixes` still gives only `N independent events` for attendance evaluation.

Therefore:

- split by event;
- keep all event prefixes in one fold;
- no random daily-row headline validation;
- event-block uncertainty;
- no future target trajectory leakage;
- persist forecasts before outcomes.

---

# 7. MAE reporting target

Add an accuracy-by-horizon view such as:

| Horizon | Incumbent MAE | Lane A MAE | Lane B MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

This answers not only whether MAE improves, but **how early Beyond becomes accurate enough to be operationally useful**.

---

# 8. Immediate order

1. protect imminent P9/Form5 windows;
2. score frozen P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. start daily trajectory dataset/ledger/reporting work in parallel;
5. keep Long72 frozen;
6. precommit Lane A and Lane B only after the trajectory data contract is audited;
7. run both under identical event-grouped/PIT-safe evaluation;
8. collect prospective daily predictions before outcomes;
9. derive business minimum meaningful Delta MAE;
10. production remains separately review-gated.
