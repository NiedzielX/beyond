# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-28**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

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
| Daily trajectory dataset contract | ✅ IMPLEMENTED / CI GREEN | exact P-N rows, missing preserved, PIT guards |
| Daily trajectory coverage audit | ✅ DONE | data is variable-length; median first observation ~P-9.3 |
| Daily attempt/prediction ledger | ✅ LIVE | private immutable tables + controlled service-role RPCs |
| Daily scoring / MAE by horizon | ✅ LIVE BACKEND | score only post-outcome; no rows yet |
| Prospective daily inference workflow | 🟡 NEXT | requires frozen Lane A/B model contract first |
| Trajectory Lane A | 🟡 NEXT DESIGN | simple residual benchmark |
| Trajectory Lane B | 🟡 ACCEPTED R&D | small sequence model research starts early |
| Self-supervised trajectory | 🟡 PLANNED | target-free representation research |
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

# 5. Daily trajectory infrastructure — completed 2026-10-28

Canonical plan:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Coverage audit:

`ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`

Implemented:

- [x] canonical daily trajectory dataset builder/contract;
- [x] PIT/future-snapshot/structural-prior leakage tests;
- [x] Demand Engine CI integration and green run;
- [x] live observation-density/missingness audit;
- [x] immutable daily attempt ledger;
- [x] immutable daily prediction ledger;
- [x] immutable post-outcome score ledger;
- [x] horizon-wise MAE backend;
- [x] controlled service-role RPC permissions;
- [x] Supabase advisor review; new FK index warning fixed;
- [ ] prospective daily shadow inference path — intentionally blocked until a model contract is frozen.

No synthetic daily prediction was inserted to manufacture progress.

---

# 6. Data reality discovered by the audit

Current genuine Ekstraklasa inventory sample:

- 32 events with at least one pre-kickoff snapshot;
- 14 clubs;
- median first observation ~P-9.3;
- p25 ~P-5.6;
- p75 ~P-14.0;
- earliest ~P-30.3.

Representative snapshot coverage:

| Horizon | Events with snapshot / eligible | Coverage |
|---|---:|---:|
| P-30 | 1 / 33 | 3.0% |
| P-21 | 2 / 32 | 6.3% |
| P-14 | 7 / 32 | 21.9% |
| P-7 | 16 / 26 | 61.5% |
| P-3 | 18 / 24 | 75.0% |
| P-1 | 19 / 20 | 95.0% |

P-31...P-60 currently has no genuine historical snapshot coverage by those cutoffs.

Decision:

- keep P-60...P-1 as the collection/cutoff frame;
- models must accept variable-length genuine prefixes;
- do not fabricate complete 60-day vectors;
- Lane B must use sequence lengths/masks or equivalent missingness-aware representation.

---

# 7. Next trajectory milestones

## Shared feature/data contract

- [ ] freeze `Trajectory Feature Contract v1` shared by Lane A/B;
- [ ] define genuine variable-length sequence representation;
- [ ] create event-grouped fold registry shared by both lanes;
- [ ] create reproducible development export/manifest.

## Lane A

- [ ] precommit simple residual development protocol;
- [ ] run grouped historical/development result;
- [ ] freeze candidate for prospective daily shadow inference if justified.

## Lane B

- [ ] precommit first small sequence development protocol;
- [ ] GRU/LSTM/TCN benchmark under the exact same events/folds as Lane A;
- [ ] investigate self-supervised pretraining separately;
- [ ] compact Transformer only if simpler sequence representation adds signal;
- [ ] freeze candidate for prospective daily shadow inference if justified.

---

# 8. Critical validation rule

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

# 9. MAE reporting target

The live backend now supports MAE by daily horizon once genuine predictions are scored.

Minimum analytical view:

| Horizon | Incumbent MAE | Lane A MAE | Lane B MAE | Events | Clubs |
|---|---:|---:|---:|---:|---:|
| P-30 | | | | | |
| P-21 | | | | | |
| P-14 | | | | | |
| P-7 | | | | | |
| P-3 | | | | | |
| P-1 | | | | | |

Always show support next to MAE.

---

# 10. Immediate order

1. protect imminent P9/Form5 windows;
2. score frozen P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. freeze the shared Trajectory Feature Contract v1;
5. freeze the event-grouped fold/export contract;
6. precommit Lane A and first small Lane B development protocols;
7. run both under identical events/folds/PIT rules;
8. start prospective daily shadow inference only for frozen candidates;
9. keep collecting longer genuine prefixes forward;
10. derive business minimum meaningful Delta MAE;
11. production remains separately review-gated.
