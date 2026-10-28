# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-28**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

---

# 2. Current status

| Item | Status | Current decision |
|---|---|---|
| Multi-source ticketing acquisition | ✅ LIVE | preserve PIT evidence; hidden inventory remains unknown, not zero |
| P7 historical | ✅ FROZEN | historical point gain only; no retuning |
| P7 prospective | 🟢 53 rows / 6 events / 0 scored | collect/score only |
| P9 historical v1 | ⚪ NOT_EVALUABLE | PIT support insufficient; no historical MAE |
| P9 prospective v1 | 🟢 1 genuine attempt / 0 prediction / 0 scored | protect every T-48/T-24 window |
| P9 Family Fallback v2 | 🟢 PRECOMMITTED / DEPLOYED | separate evidence; never pool with v1 |
| Form5 prospective | 🟢 FIRST T-24 PENDING | event443 2026-10-29 17:00 UTC |
| Long72 | 🟡 FROZEN | 5 scored; 0.71% point gain; low priority |
| P11 odds | 🟡 COLLECTING | 6 events / 6 clubs; 5/5/0 T-24/T-72/T-168 |
| P4a | 🟡 COLLECTING | gate still closed |
| Daily trajectory dataset | ✅ DONE | exact P-N + PIT tests |
| Daily trajectory coverage audit | ✅ DONE | variable-length data reality confirmed |
| Immutable daily evidence backend | ✅ LIVE | attempts/predictions/scores + controlled RPCs |
| MAE-by-horizon backend | ✅ LIVE | post-outcome only |
| Trajectory Feature Contract v1 | ✅ FROZEN + CODED | shared Lane A/B information boundary |
| Validation Fold Contract v1 | ✅ FROZEN + CODED | strict expanding temporal event folds |
| Demand Engine tests | ✅ GREEN | feature/fold contract tests pass |
| Lane A | 🟡 NEXT | precommit small residual benchmark |
| Lane B | 🟡 NEXT | precommit first small sequence model |
| Prospective daily trajectory inference | ⏸️ BLOCKED BY MODEL FREEZE | do not emit challenger forecasts before candidate precommit |
| Business meaningful Delta MAE | 🟡 PENDING | derive independently from model results |

---

# 3. Current data reality

Genuine pre-kickoff inventory:

- 32 events;
- 14 clubs;
- median first observation ~P-9.3;
- p75 ~P-14;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Representative coverage:

| Horizon | Snapshot coverage |
|---|---:|
| P-30 | 3.0% |
| P-14 | 21.9% |
| P-7 | 61.5% |
| P-3 | 75.0% |
| P-1 | 95.0% |

Shared input-gate checkpoint support:

| Horizon | Input-ready events | Labeled ready events |
|---|---:|---:|
| T-30 | 0 | 0 |
| T-14 | 1 | 0 |
| T-7 | 7 | 4 |
| T-3 | 9 | 5 |
| T-1 | 10 | 10 |

Decision:

- keep P-60...P-1 as collection/cutoff frame;
- do not require a complete P-60 vector;
- use genuine variable-length prefixes;
- never fabricate missing observations;
- show independent-event support with every MAE result.

---

# 4. Frozen trajectory contracts

## Feature Contract v1

`ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Shared primary eligibility:

- PIT-valid structural incumbent;
- >=4 clean snapshots;
- >=24h observation window;
- `signal_readiness=ready`;
- no future target trajectory/outcome.

Lane A = engineered scalar trajectory summary + structural P50.

Lane B = genuine ordered variable-length snapshot sequence + structural P50/global context.

No odds/weather/hype/match-stakes/Form5/P4 context in v1.

## Validation Fold Contract v1

`ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

Primary method:

- strict expanding temporal event folds;
- same-kickoff events stay together;
- min 5 earlier train events;
- min 4 earlier train clubs;
- all prefixes from one event inherit the same fold;
- Lane A/B use identical registry/manifest.

---

# 5. Completed trajectory infrastructure

- [x] canonical daily dataset builder;
- [x] PIT/future-snapshot/structural-prior tests;
- [x] coverage/missingness audit;
- [x] immutable attempt ledger;
- [x] immutable prediction ledger;
- [x] immutable score ledger;
- [x] post-outcome scoring RPC;
- [x] MAE-by-horizon RPC;
- [x] service-role-only controlled writes;
- [x] security/performance review for new backend;
- [x] Trajectory Feature Contract v1 implementation/tests;
- [x] strict-forward fold-registry implementation/tests;
- [x] Demand Engine tests green.

No synthetic daily prediction was inserted.

---

# 6. Next trajectory milestones

## Lane A

- [ ] precommit exact candidate set;
- [ ] freeze fold-local preprocessing;
- [ ] materialize shared eligible export/fold manifest;
- [ ] run strict-forward result;
- [ ] report horizon-wise support + MAE;
- [ ] freeze candidate for prospective daily shadow only if justified.

## Lane B

- [ ] precommit first small sequence architecture/protocol;
- [ ] use exact same eligible export/folds as Lane A;
- [ ] run small GRU/LSTM/TCN comparison under controlled model-selection rules;
- [ ] compare directly against Lane A, not only incumbent;
- [ ] optionally investigate self-supervised pretraining separately;
- [ ] compact Transformer only if simpler sequence representation adds signal;
- [ ] freeze candidate for prospective daily shadow only if justified.

---

# 7. Protected evidence windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48 — 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48 — 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24 — 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48 — 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48 — 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48 — 2026-10-31 19:30 UTC.

---

# 8. Immediate order

1. protect imminent P9/Form5 windows;
2. score frozen P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. precommit Lane A;
5. precommit first Lane B sequence protocol;
6. build one shared eligible export + strict-forward fold manifest;
7. run both lanes on identical evidence;
8. report support + horizon-wise and event-balanced MAE;
9. freeze a prospective candidate only if evidence justifies it;
10. continue forward data collection;
11. derive business minimum meaningful Delta MAE;
12. keep production separately review-gated.
