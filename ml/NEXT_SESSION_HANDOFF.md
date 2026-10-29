# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-29**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

---

# 1. What matters most

Two jobs remain:

1. protect genuine prospective P7/P9/Form5 evidence and every imminent immutable cutoff;
2. collect genuinely prospective attendance evidence for the frozen trajectory encoder candidate.

Do not restart supervised trajectory tuning on the exposed 10-event cohort.

---

# 2. Closed supervised trajectory experiments

- Lane A v1: 4153.34 MAE vs 2594.54 incumbent, rejected;
- Lane B v1: 2595.40, +0.87 worse, do not advance;
- Lane B v2: 4792.42, +2197.88 worse, mechanism not supported.

No post-hoc shrinkage/caps/loss/LR/epoch/architecture tournament on the same exposed outer events.

---

# 3. SSP v1 is complete

Precommit:

`trajectory-self-supervised-24h-delta-v1`

Frozen target-free validation result:

- zero-change event-balanced MAE: 0.0917223592;
- GRU event-balanced MAE: 0.0628961688;
- Delta: -0.0288261905;
- improved validation events: 5/5;
- attendance labels used: false;
- structural P50 used: false.

Decision:

`REPRESENTATION_SUPPORTED`

Frozen encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

This is representation-learning evidence only, not attendance evidence.

---

# 4. Active attendance candidate

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Frozen head:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Protocol:

- frozen SSP encoder;
- one Ridge head;
- alpha 10;
- +/-10% residual-ratio cap;
- exact 10-event / 19-row exposed historical fit cohort;
- no historical candidate selection;
- P-7 / P-3 / P-1 only;
- immutable predictions before outcomes;
- production off.

The exact successful fit artifact was persisted to `main` on 2026-10-29. Do not refit it.

---

# 5. Prospective shadow plumbing

Target RPC:

`public.get_trajectory_frozen_encoder_shadow_due_v1()`

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Workflow:

`.github/workflows/trajectory-frozen-encoder-shadow-v1.yml`

Schedule:

`20 * * * *`

The workflow was verified end-to-end after the head artifact was persisted:

- artifact present;
- compile success;
- OIDC success;
- immutable shadow check success.

As of 2026-10-29 16:09 UTC there were 0 shadow attempts/predictions/scores because the first due P-1 cutoff had not occurred yet.

---

# 6. Current protected prospective state

Fresh snapshot at **2026-10-29 16:09 UTC**:

- P9 v1: 2 attempts / 0 predictions / 0 scored; both support-insufficient;
- P9 v2: 1 attempt / 1 prediction / 0 scored;
- Form5: collecting, 0/8 completed eligible events;
- production change false.

Near-term windows:

- event6 Lech–Wisła Kraków P9 T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor P9/Form5 T-24: 2026-10-29 17:00 UTC;
- event443 Cracovia–Motor frozen-encoder P-1: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew P9 T-48: 2026-10-29 19:15 UTC;
- event446 Wisła Płock–Piast P9 T-24: 2026-10-30 11:15 UTC.

P9 schedule: `11,26,41,56 * * * *` plus redundant heartbeat bridge.

---

# 7. Next agent action

1. Query current machine state first.
2. If a protected cutoff has passed, verify its immutable attempt/prediction rather than assuming the scheduler fired.
3. Never backfill a missed prospective window with later information.
4. Score only after genuine confirmed attendance outcomes.
5. Do not change SSP encoder or attendance-head parameters under candidate v1.
6. Do not interpret SSP validation as attendance accuracy.
7. Do not pool P9 v1/v2 evidence.
8. Keep `live_adjustment = 0`.

The next meaningful model decision comes from **future prospective attendance Delta MAE**, not another historical tuning pass.
