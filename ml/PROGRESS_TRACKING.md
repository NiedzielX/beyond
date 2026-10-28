# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-28**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

---

# 2. Current status

| Item | Status | Current decision |
|---|---|---|
| P7 prospective | 🟢 53 rows / 6 events / 0 scored | collect/score only |
| P9 historical v1 | ⚪ NOT_EVALUABLE | PIT support insufficient |
| P9 prospective v1 | 🟢 1 attempt / 0 prediction / 0 scored | protect genuine windows |
| P9 Family Fallback v2 | 🟢 PRECOMMITTED / DEPLOYED | separate evidence only |
| Form5 prospective | 🟢 FIRST T-24 PENDING | event443 2026-10-29 17:00 UTC |
| Long72 | 🟡 FROZEN | 5 scored; 0.71% point gain |
| P11 odds | 🟡 COLLECTING | 6 events / 6 clubs; 5/5/0 T-24/T-72/T-168 |
| P4a | 🟡 COLLECTING | gate still closed |
| Daily trajectory infrastructure | ✅ DONE | PIT dataset + immutable evidence backend |
| Trajectory Feature Contract v1 | ✅ FROZEN + CODED | shared A/B information boundary |
| Validation Fold Contract v1 | ✅ FROZEN + CODED | strict expanding temporal folds |
| Frozen development cohort | ✅ 10 events / 19 rows | 5 strict-forward outer test events |
| Lane A v1 | ❌ REJECTED AS CANDIDATE | 4153.3 vs 2594.5 incumbent MAE |
| Lane B v1 | 🟢 ACTIVE | frozen small GRU; run via OIDC workflow |
| Frozen development export | ✅ LIVE | service-role RPC + GitHub OIDC gateway |
| Prospective daily trajectory candidate | ⏸️ NOT YET | only after a justified development win |
| Business meaningful Delta MAE | 🟡 PENDING | derive independently |

---

# 3. Lane A result — closed

Precommit:

`trajectory-lane-a-ridge-residual-v1`

Strict-forward result:

| Metric | Value |
|---|---:|
| Independent test events | 5 |
| Test prefix rows | 14 |
| Incumbent event-balanced MAE | 2594.5 |
| Lane A event-balanced MAE | 4153.3 |
| Delta MAE | **+1558.8** |
| Relative change | **+60.1% worse** |
| Event improvement rate | 20% |
| Worst event degradation | +4166.4 |

By horizon:

| Horizon | Incumbent | Lane A | Delta |
|---|---:|---:|---:|
| T-7 | 3399.0 | 4490.9 | +1091.9 |
| T-3 | 2667.9 | 4224.7 | +1556.8 |
| T-1 | 2314.9 | 3727.8 | +1412.9 |

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Do not tune v1 after the result.

---

# 4. Lane B v1 — active

Precommit:

`trajectory-lane-b-small-gru-residual-v1`

Fixed model:

- GRU 1 layer / hidden 8;
- five genuine sequence channels;
- MLP head 8;
- dropout .20;
- AdamW 0.001 / wd 0.01;
- event-balanced weighted L1;
- 200 fixed epochs;
- gradient clip 1.0;
- seeds 17 / 29 / 41;
- median seed prediction;
- no architecture search;
- no self-supervised pretraining in v1.

Advance requirement:

- Lane B beats incumbent;
- Lane B beats frozen Lane A;
- downside/seed stability acceptable;
- no evidence guard fails.

---

# 5. Frozen cohort and data path

Cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 independent labeled events;
- 19 exact persisted checkpoint identities;
- 5 strict-forward test events.

Fold SHA256:

`fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`

Export RPC:

`public.export_trajectory_development_rows_v1(bigint[])`

OIDC gateway:

`trajectory_research_export_v1`

Workflow:

`.github/workflows/trajectory-lane-b-v1.yml`

Runner fails closed unless the export matches the frozen cohort exactly.

---

# 6. Completed trajectory engineering

- [x] daily PIT dataset builder;
- [x] future-snapshot / prior leakage tests;
- [x] coverage audit;
- [x] immutable daily attempt/prediction/score backend;
- [x] MAE-by-horizon scoring;
- [x] feature contract v1;
- [x] strict-forward fold contract v1;
- [x] frozen 10-event cohort;
- [x] shared dataset materializer;
- [x] Lane A precommit + executable benchmark;
- [x] Lane A strict-forward result + decision;
- [x] Lane B precommit + executable GRU;
- [x] service-role historical research bundle;
- [x] frozen model-ready development export;
- [x] GitHub OIDC export gateway;
- [x] Lane B GitHub Actions workflow.

---

# 7. Data reality

Current genuine pre-kickoff inventory:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

P-60 remains collection horizon only. Use genuine variable-length sequences; never manufacture missing history.

---

# 8. Immediate order

1. protect imminent P9/Form5 windows;
2. score P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. inspect/finish the frozen Lane B v1 workflow;
5. persist Lane B result and decision;
6. do not tune Lane B v1 after outer result;
7. if Lane B wins, create a separately frozen prospective daily-shadow candidate;
8. if Lane B fails, diagnose before any versioned v2;
9. continue genuine trajectory collection;
10. derive business minimum meaningful Delta MAE;
11. production remains review-gated.
