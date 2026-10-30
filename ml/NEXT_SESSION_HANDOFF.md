# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-30**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

---

# 1. What matters most

Two jobs remain:

1. protect genuine prospective P7/P9/Form5 evidence and every imminent immutable cutoff;
2. collect genuinely prospective attendance evidence for the frozen trajectory encoder candidate.

Do not restart supervised trajectory tuning on the exposed 10-event cohort.

The first genuine frozen-encoder attendance prediction now exists. Do not change the candidate after seeing early outcomes.

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

# 5. Prospective shadow plumbing and first live evidence

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

The workflow is verified end-to-end:

- frozen encoder/head artifacts present;
- compile success;
- OIDC success;
- immutable shadow check success;
- database guards reject future snapshots and restrict writes to the cutoff +90 minute immutable window.

First genuine prospective attendance prediction was created on **2026-10-30** for event446 (Wisła Płock–Piast Gliwice), P-1:

- target cutoff: `2026-10-30 11:15:00 UTC`;
- attempt: `PREDICTION_READY` at `11:21:26 UTC`;
- source snapshot: `11:05:02 UTC`;
- structural incumbent P50: `6084.5618737955`;
- frozen-encoder challenger P50: `6693.01806117505`;
- trajectory residual: `+608.45618737955` (+10% cap hit);
- target values used: false;
- production change: false;
- score: pending genuine confirmed attendance outcome.

The protected run completed successfully with `due_target_count=1`, `attempt_count=1`, `prediction_count=1`, `inserted_scores=0`.

Operational note: the protected run was re-triggered after the legal cutoff because GitHub scheduled execution had not started exactly at the due time. This did not change the evidence contract: the database selected only observations with `captured_at <= target_as_of_at`, and the write occurred inside the frozen +90 minute window.

---

# 6. Current protected prospective state

Fresh snapshot after the first frozen-encoder prediction on **2026-10-30**:

- P9 v1: 3 attempts / 0 predictions / 0 scored; all fail-closed support-insufficient;
- P9 v2: 2 attempts / 1 immutable prediction / 0 scored;
- Form5: collecting, 0 completed eligible events in the prospective dataset until genuine attendance outcomes arrive;
- Frozen Encoder Shadow: 1 attempt / 1 immutable prediction / 0 scores;
- production change false;
- `live_adjustment = 0`.

P9 detail:

- event446 T-48: v1 `PIT_SUPPORT_INSUFFICIENT`, v2 `FALLBACK_PREDICTION_READY`;
- event444 T-48: v1 `PIT_SUPPORT_INSUFFICIENT`, v2 `FALLBACK_SUPPORT_INSUFFICIENT`.

Frozen Encoder next state:

- event446 P-1 is now protected and immutable;
- no other P-7/P-3/P-1 target was due in the next 48h at the 2026-10-30 checkpoint query.

P9 schedule: `11,26,41,56 * * * *` plus redundant heartbeat bridge.

---

# 7. Next agent action

1. Query current machine state first.
2. Protect every due cutoff before doing research work.
3. If a protected cutoff has passed, verify its immutable attempt/prediction rather than assuming the scheduler fired.
4. Never backfill a missed prospective window with later information.
5. Score event446 only after a genuine confirmed attendance outcome is available after kickoff.
6. Compare actual attendance against the frozen structural incumbent and frozen challenger; record AE and Delta AE without tuning.
7. Accumulate a cohort before interpreting Delta MAE; do not react to the first 1–2 outcomes.
8. Do not change SSP encoder or attendance-head parameters under candidate v1.
9. Do not interpret SSP validation as attendance accuracy.
10. Do not pool P9 v1/v2 evidence.
11. Keep `live_adjustment = 0` and production OFF.

The next meaningful model decision comes from **future prospective attendance Delta MAE**, not another historical tuning pass.
