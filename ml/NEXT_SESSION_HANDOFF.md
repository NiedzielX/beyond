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

`20,50 * * * *`

The cadence was hardened on 2026-10-30 from one to two checks per hour because the immutable write window is only +90 minutes and scheduled GitHub runs can be delayed or dropped. This is operational redundancy only; the frozen model, head, cutoffs and persistence contract are unchanged.

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

Event443 Cracovia–Motor P-1 at `2026-10-29 17:00 UTC` has no immutable shadow attempt and its +90 minute window is closed. It must remain missing; never create a retrospective row.

---

# 6. Current protected prospective state

Fresh machine snapshot on **2026-10-30 around 12:22 UTC**:

- P9 v1: **4 attempts / 0 predictions / 0 scored**; every attempt is `PIT_SUPPORT_INSUFFICIENT` and therefore correct fail-closed evidence;
- P9 v2: **3 attempts / 2 immutable predictions / 0 scored**;
- Form5: `PROSPECTIVE_COLLECTING`, **0/8** completed eligible events, gate closed;
- Frozen Encoder Shadow: **1 attempt / 1 immutable prediction / 0 scores**;
- production change false;
- `live_adjustment = 0`.

P9 detail:

- event443 T-48: v1 `PIT_SUPPORT_INSUFFICIENT`;
- event443 T-24: `MISSED_WINDOW` — do not backfill;
- event446 T-48: v1 `PIT_SUPPORT_INSUFFICIENT`, v2 `FALLBACK_PREDICTION_READY`;
- event444 T-48: v1 `PIT_SUPPORT_INSUFFICIENT`, v2 `FALLBACK_SUPPORT_INSUFFICIENT`;
- event446 T-24: v1 `PIT_SUPPORT_INSUFFICIENT`, v2 `FALLBACK_PREDICTION_READY` captured at `12:19:45 UTC`, still inside the legal +90 minute window.

Event446 frozen P9 v2 predictions remain separately auditable:

- T-48 challenger: `6911.09714798977` vs structural `6084.5618737955`;
- T-24 challenger: `8252.87035184191` vs structural `6084.5618737955`.

Do not compare which challenger is better until genuine attendance exists.

Operational P9 protection:

- frozen P9 workflow: `11,26,41,56 * * * *`;
- Structural Prior -> P9 workflow-run bridge remains active;
- independent P9 heartbeat added on 2026-10-30: `16,46 * * * *`;
- persistence remains immutable/idempotent per event+cutoff.

---

# 7. Immediate future cutoffs

At the latest machine check:

- event6 Lech Poznań–Wisła Kraków P9 T-48 is already `MISSED_WINDOW` — do not backfill;
- event6 P9 T-24 and Frozen Encoder P-1 cutoff: **2026-10-30 16:30 UTC**;
- event444 GKS Katowice–Widzew P9 T-24 and Frozen Encoder P-1 cutoff: **2026-10-30 19:15 UTC**;
- both event6 and event444 currently have genuine pre-cutoff snapshots and PIT-valid structural priors available for their P-1 shadow checkpoints;
- event445 KGHM Zagłębie Lubin–Korona Kielce P9 T-48: **2026-10-31 17:00 UTC**;
- event447 Raków Częstochowa–Pogoń Szczecin P9 T-48: **2026-10-31 19:30 UTC**.

Watch items from P9 preflight:

- event448 Wisła Kraków–Cracovia currently `WATCH_NO_SNAPSHOT`;
- event7372 Widzew Łódź–Pogoń Szczecin currently `WATCH_NO_INCUMBENT`.

These are future readiness issues, not reasons to fabricate inputs.

---

# 8. Next agent action

1. Query current machine state first.
2. Protect every due cutoff before doing research work.
3. Verify event6 T-24/P-1 and event444 T-24/P-1 immediately after their legal windows begin; do not assume the scheduler fired.
4. Never backfill event443 P9 T-24, event443 trajectory P-1, event6 P9 T-48 or any other missed prospective window with later information.
5. Score only after genuine confirmed attendance outcomes.
6. Compare actual attendance against each frozen incumbent/challenger pair; record AE and Delta AE without tuning.
7. Keep P9 v1, P9 v2, Form5 and Frozen Encoder evidence separate.
8. Accumulate a cohort before interpreting Delta MAE; do not react to the first 1–2 outcomes.
9. Do not change SSP encoder, attendance-head alpha/cap or P9 fallback policy under the current candidate versions.
10. Do not interpret SSP validation as attendance accuracy.
11. Keep `live_adjustment = 0` and production OFF.

The next meaningful model decision comes from **future prospective attendance Delta MAE**, not another historical tuning pass.
