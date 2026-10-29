# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-29**

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
| P9 prospective v1 | 🟢 2 attempts / 0 predictions / 0 scored | correct fail-closed; protect windows |
| P9 Family Fallback v2 | 🟢 1 attempt / 1 prediction / 0 scored | separate evidence only |
| Form5 prospective | 🟢 COLLECTING | 0/8 completed eligible events; next T-24 event443 |
| Long72 | 🟡 FROZEN | 5 scored; 0.71% point gain |
| P11 odds | 🟡 COLLECTING | continue genuine observations |
| P4a | 🟡 COLLECTING | gate closed |
| Daily trajectory infrastructure | ✅ DONE | PIT dataset + immutable evidence backend |
| Lane A v1 | ❌ REJECTED | MAE 4153.34 vs 2594.54 incumbent |
| Lane B v1 | ❌ DO NOT ADVANCE | MAE 2595.40; near-zero corrections |
| Lane B v2 | ❌ MECHANISM NOT SUPPORTED | MAE 4792.42; harmful over-corrections |
| Supervised tuning on exposed cohort | 🛑 STOPPED | no post-hoc repair |
| SSP trajectory v1 | ✅ REPRESENTATION_SUPPORTED | 0.091722 -> 0.062896 target-free MAE; 5/5 events improved |
| SSP encoder | ✅ FROZEN | immutable v1 artifact |
| Frozen attendance head v1 | ✅ FIT ONCE / FROZEN | Ridge alpha 10, cap +/-10%, no historical selection |
| Frozen encoder prospective shadow | 🟢 ACTIVE / COLLECTING | P-7/P-3/P-1; production off |
| Shadow live evidence | ⚪ 0 attempts / 0 predictions / 0 scores at 2026-10-29 16:09 UTC | first due P-1 at event443 |
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
- Delta: +0.87;
- near-zero corrections;
- decision: `DO_NOT_ADVANCE`.

## Lane B v2

- Lane B v2 MAE: 4792.42;
- Delta: +2197.88;
- harmful over-corrections;
- decision: `MECHANISM_NOT_SUPPORTED`.

Conclusion:

> **Do not keep tuning supervised correction mechanics on the same exposed 10-event cohort.**

---

# 4. SSP v1 result

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Frozen target-free sample:

- 26 usable events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 validation events / 168 pairs.

Result:

- zero-change event-balanced MAE: **0.0917223592**;
- model event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved validation events: **5/5**;
- attendance labels used: false;
- structural prior used: false.

Decision:

`REPRESENTATION_SUPPORTED`

Encoder artifact:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Do not interpret this as attendance accuracy evidence.

---

# 5. Frozen encoder attendance head v1

Candidate ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Protocol:

- frozen 8-d SSP encoder embedding;
- Ridge alpha 10;
- residual-ratio target;
- +/-10% correction cap;
- exact 10-event / 19-row exposed fit cohort;
- no historical candidate selection;
- no historical MAE-based tuning;
- P-7 / P-3 / P-1 prospective only.

The successful fit artifact was persisted exactly to `main` on 2026-10-29. The prospective shadow workflow then passed end-to-end.

---

# 6. Prospective frozen-encoder shadow

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Workflow:

`.github/workflows/trajectory-frozen-encoder-shadow-v1.yml`

Schedule:

`20 * * * *`

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Evidence label before adequate sample:

`true_post_freeze_prospective_small_n`

Do not tune the candidate after early prospective outcomes and keep the same version.

---

# 7. Current live window snapshot

At **2026-10-29 16:09 UTC**:

- event6 Lech–Wisła Kraków P9 T-48 due 16:30 UTC — READY;
- event443 Cracovia–Motor P9/Form5 T-24 due 17:00 UTC — READY;
- event443 frozen-encoder P-1 due 17:00 UTC — first shadow opportunity;
- event444 GKS Katowice–Widzew P9 T-48 due 19:15 UTC — READY.

P9 cadence: `11,26,41,56 * * * *` plus redundant heartbeat bridge.

Frozen-encoder shadow cadence: `20 * * * *`.

---

# 8. Data semantics

Public inventory is a demand/inventory proxy, not confirmed sales or attendance.

P-60 is a collection horizon, not a requirement for fabricated full history.

Never forward-fill or interpolate merely to create model input.

Hidden/unknown inventory is never zero.

---

# 9. Immediate order

1. protect imminent P9/Form5/frozen-encoder cutoffs;
2. verify immutable attempt/prediction rows after due windows;
3. score only after genuine confirmed outcomes;
4. freeze encoder/head parameters while evidence accumulates;
5. report attendance Delta MAE by P-7/P-3/P-1 and event-balanced overall;
6. do not reactively retune against early future scores;
7. continue P11/P4a and trajectory collection;
8. derive business minimum meaningful Delta MAE independently;
9. keep production review-gated and OFF.
