# Beyond Ticketing — Frozen Encoder Prospective Shadow v1

Precommit date: **2026-10-28**

Status: **PRECOMMITTED PROSPECTIVE SHADOW / PRODUCTION OFF**

Candidate ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Head precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_ATTENDANCE_HEAD_V1.md`

Production:

`live_adjustment = 0`

---

# 1. Purpose

The supported target-free encoder has now been frozen. A single fixed Ridge attendance head is fitted on the already-exposed historical labels without historical model selection.

The purpose of this shadow is to create the **first genuinely prospective attendance evidence** for this representation.

The question is:

> **Does the frozen encoder + frozen conservative attendance head reduce future event-balanced attendance MAE relative to the structural incumbent?**

No prediction from this shadow may affect production behaviour.

---

# 2. Frozen candidate

Candidate components are immutable before prospective scoring:

1. self-supervised GRU encoder v1;
2. frozen encoder artifact/hash;
3. Ridge residual-ratio head v1;
4. head scaler/coefficient/intercept artifact/hash;
5. Ridge alpha 10;
6. correction ratio cap +/-10%;
7. trajectory input semantics;
8. prospective horizon policy;
9. immutable persistence/scoring contract.

Any change to these after future outcomes are exposed requires a new candidate version.

---

# 3. Prospective horizons v1

Only:

- P-7;
- P-3;
- P-1.

Exact cutoff:

`target_as_of_at = kickoff_at - N * 24h`

The shadow runner may execute within the existing immutable evidence window around the exact cutoff, but the feature state is always rebuilt strictly at `target_as_of_at`.

Do not use snapshots captured after the target cutoff even if the workflow runs later.

---

# 4. Target eligibility

A target event/checkpoint may emit a prediction only when all are true:

1. event kickoff is in the future at prediction time;
2. no attendance outcome is already present;
3. exact P-7/P-3/P-1 cutoff is due within the immutable execution window;
4. at least 4 genuine eligible hourly-bucket observations exist by the cutoff;
5. observed prefix span within the final 168h context is at least 24h;
6. first genuine event inventory observation is positive so `available_index` is defined;
7. a PIT-valid structural prior genuinely existed by the cutoff;
8. structural P50 > 0;
9. no existing immutable attempt exists for the same event/horizon/candidate.

Otherwise persist a fail-closed attempt with the explicit reason whenever the persistence contract permits it.

---

# 5. Input semantics

Use exactly the frozen encoder semantics:

- genuine pre-cutoff snapshots only;
- non-negative available_total;
- exact timestamp duplicate -> highest snapshot ID;
- max one genuine observation per integer hour-to-kickoff bucket;
- final 168h context before the target cutoff;
- no interpolation;
- no forward-fill;
- hidden/unknown inventory is not zero.

Per timestep channels:

1. `hours_to_kickoff / 1440`;
2. `available_index` relative to the event's first genuine available inventory observation;
3. `delta_hours_since_previous / 24`;
4. `delta_available_index`.

No attendance target is visible.

---

# 6. Prediction

1. compute the frozen 8-d encoder embedding;
2. standardize with frozen head scaler;
3. apply frozen Ridge head;
4. clip residual ratio to `[-0.10,+0.10]`;
5. `challenger_p50 = structural_p50 * (1 + clipped_ratio)`;
6. lower bound 0;
7. upper bound verified stadium capacity when available.

Persist:

- raw head ratio;
- clipped ratio;
- structural P50;
- challenger P50;
- head/encoder hashes;
- target cutoff;
- source snapshot lineage;
- prefix range/count;
- manifest/identity hashes;
- `target_values_used=false`;
- `production_change=false`.

---

# 7. Persistence

Reuse the existing immutable daily trajectory evidence backend:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- existing controlled attempt/prediction RPCs;
- existing post-outcome score ledger.

Model version:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Precommit ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Dataset version:

`trajectory-frozen-encoder-shadow-input-v1`

No parallel mutable prediction table.

---

# 8. Scheduling

The shadow workflow may check due targets hourly.

It is acceptable for execution to happen after the exact cutoff only inside the existing immutable write window, because all input is reconstructed with `captured_at <= target_as_of_at`.

The scheduler is evidence plumbing, not a model trigger based on live outcome information.

---

# 9. Scoring

After genuine attendance is confirmed, reuse immutable post-outcome scoring.

Primary:

`event-balanced Delta MAE = candidate MAE - structural incumbent MAE`

Report separately by P-7 / P-3 / P-1 and combined under a precommitted event-balanced aggregation.

Also report:

- independent events;
- clubs;
- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation;
- raw/clipped ratio distributions;
- cap-hit rate.

---

# 10. Evidence interpretation

Early prospective rows are not a promotion decision.

Until enough independent future events exist, label evidence as:

`true_post_freeze_prospective_small_n`

Do not tune the candidate against early prospective outcomes and continue under the same version.

Any material change after seeing prospective scores requires a new precommit/version.

---

# 11. Production boundary

This is shadow research only.

- no live ticketing intervention;
- no operational correction;
- no production overwrite;
- no automatic promotion;
- `live_adjustment = 0`.
