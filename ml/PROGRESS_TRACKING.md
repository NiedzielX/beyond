# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-28**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

---

# 2. Current status

| Item | Status | Current decision |
|---|---|---|
| P7 prospective | 🟢 53 rows / 6 events / 0 scored | collect/score only |
| P9 historical v1 | ⚪ NOT_EVALUABLE | PIT support insufficient |
| P9 prospective v1 | 🟢 1 attempt / 0 prediction / 0 scored | protect genuine windows |
| P9 Family Fallback v2 | 🟢 FROZEN / DEPLOYED | separate evidence only |
| Form5 prospective | 🟢 FIRST T-24 PENDING | event443 2026-10-29 17:00 UTC |
| Long72 | 🟡 FROZEN | 5 scored; 0.71% point gain |
| P11 odds | 🟡 COLLECTING | 6 events / 6 clubs; no model fit |
| P4a | 🟡 COLLECTING | gate still closed |
| Daily trajectory infrastructure | ✅ DONE | PIT dataset + immutable evidence backend |
| Lane A v1 | ❌ REJECTED | MAE 4153.34 vs 2594.54 incumbent |
| Lane B v1 | ❌ DO NOT ADVANCE | MAE 2595.40; near-zero corrections |
| Lane B v2 | ❌ MECHANISM NOT SUPPORTED | MAE 4792.42; harmful over-corrections |
| Supervised trajectory tuning on exposed cohort | 🛑 STOPPED | no more post-hoc tuning on 5 exposed outer events |
| Self-supervised trajectory v1 | 🟢 ACTIVE | target-free ~24h delta task |
| SSP frozen export | ✅ LIVE | 26 events, no attendance/P50 |
| SSP usable sample | ✅ FROZEN | 21 train events / 3397 pairs; 5 val events / 168 pairs |
| Prospective attendance trajectory candidate | ⏸️ NOT YET | only after evidence-safe representation freeze |
| Business meaningful Delta MAE | 🟡 PENDING | derive independently |

---

# 3. Closed supervised trajectory evidence

## Lane A v1

- incumbent MAE: 2594.54;
- Lane A MAE: 4153.34;
- Delta: +1558.80;
- decision: `REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`.

## Lane B v1

- Lane B MAE: 2595.40;
- Delta vs incumbent: +0.87;
- predicted seat corrections only about -0.06...+4.33;
- decision: `DO_NOT_ADVANCE`.

## Lane B v2

- residual-ratio target unlocked realistic correction magnitude;
- Lane B v2 MAE: 4792.42;
- Delta vs incumbent: +2197.88;
- median absolute correction ~1550.78 seats;
- decision: `MECHANISM_NOT_SUPPORTED`.

Conclusion:

> **Do not keep tuning supervised correction mechanics on the same exposed 10-event cohort.**

---

# 4. Active self-supervised v1

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Frozen cutoff:

`2026-10-28T22:09:43.958409Z`

Target-free corpus after input gate:

- 26 usable events;
- 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 later validation events / 168 pairs.

Task:

`genuine trajectory prefix -> normalized inventory change ~24h later`

Zero-change baseline:

`predicted delta = 0`

Frozen model:

- GRU input 4 / hidden 8;
- small MLP head;
- AdamW .001 / wd .01;
- weighted L1;
- batch 128;
- 100 epochs;
- seed 17;
- no early stopping;
- no hyperparameter search.

Evidence label:

`target_free_temporal_validation`

No attendance labels and no structural P50 are used.

---

# 5. SSP pipeline

- [x] frozen data cutoff;
- [x] frozen chronological event split;
- [x] usable pair audit;
- [x] split manifest;
- [x] target-free Supabase export RPC;
- [x] service-role-only permissions;
- [x] GitHub OIDC export gateway;
- [x] executable GRU pretraining code;
- [x] protocol tests;
- [x] GitHub Actions workflow;
- [ ] frozen SSP v1 validation result;
- [ ] encoder freeze decision.

---

# 6. Data semantics

Public inventory is a demand/inventory proxy, not confirmed sales or attendance.

P-60 is a collection horizon, not a requirement for a fabricated full sequence.

Never forward-fill or interpolate merely to create model input.

Hidden/unknown inventory is never zero.

---

# 7. Immediate order

1. protect imminent P9/Form5 windows;
2. score P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. finish frozen SSP v1 validation run;
5. persist result and encoder metadata;
6. do not tune SSP v1 after seeing validation;
7. if representation is supported, freeze encoder before any attendance-head work;
8. judge attendance value only on future immutable predictions/outcomes;
9. continue genuine forward trajectory collection;
10. derive business minimum meaningful Delta MAE;
11. production remains review-gated.
