# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-29**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Where we are now

There are two parallel tracks.

## Track 1 — protect genuine prospective evidence

Keep P7, P9, Form5, Long72 and the frozen trajectory shadow honest. An imminent immutable cutoff always has priority over new R&D.

## Track 2 — improve attendance MAE with trajectory information

The first supervised trajectory cohort is exhausted for model selection. Lane A v1, Lane B v1 and Lane B v2 are closed.

Target-free self-supervised trajectory pretraining v1 is also complete and produced a **supported representation**:

| Target-free SSP v1 metric | Result |
|---|---:|
| zero-change event-balanced MAE | 0.091722 |
| GRU event-balanced MAE | **0.062896** |
| Delta MAE | **-0.028826** |
| validation events improved | **5 / 5** |

Decision: `REPRESENTATION_SUPPORTED`.

This is evidence that the encoder learned reusable inventory-trajectory dynamics. It is **not attendance-forecast evidence**.

The encoder is frozen. A single conservative attendance head has been fitted once on the already-exposed historical cohort without historical model selection:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

The current active attendance experiment is therefore:

> **Frozen encoder + frozen Ridge residual-ratio head -> immutable P-7 / P-3 / P-1 prospective shadow -> future event-balanced attendance Delta MAE.**

No tuning is allowed against early prospective outcomes under the same candidate version.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary attendance metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

---

# 2. Non-negotiable rules

1. Event/match is the independent attendance-evaluation unit.
2. All prefixes from one event stay together.
3. No random daily-row/snapshot CV for attendance claims.
4. No future target trajectory at an earlier cutoff.
5. No target attendance in inference features.
6. No manufactured inventory/history.
7. Frozen experiments are not tuned after their result.
8. The exposed 10-event supervised cohort is not reused as unseen confirmation.
9. SSP v1 validation events are representation-learning validation only, never attendance confirmation.
10. Genuine prospective attendance evidence outranks historical research.
11. Any material candidate change after prospective outcomes requires a new precommit/version.
12. No research workflow activates production automatically.

---

# 3. Structural incumbent

The structural model remains the attendance incumbent.

Frozen supervised trajectory results on the exposed 10-event cohort:

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | +1558.80 | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | +0.87 | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | +2197.88 | mechanism not supported |

Do not perform post-hoc shrinkage, cap, learning-rate, epoch, loss or architecture tuning on those same exposed outer events.

---

# 4. SSP v1 — CLOSED / REPRESENTATION SUPPORTED

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Frozen encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Frozen data cutoff:

`2026-10-28T22:09:43.958409Z`

Evidence class:

`target_free_temporal_validation`

Sample:

- 26 usable events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 temporally later validation events / 168 pairs.

Result:

- baseline event-balanced MAE: **0.0917223592**;
- model event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved events: **5/5**;
- attendance labels used: **false**;
- structural P50 used: **false**.

The encoder is now immutable for candidate v1. SSP v1 must not be retuned against the same validation events.

---

# 5. Active trajectory attendance candidate — prospective shadow v1

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Components:

- frozen SSP v1 GRU encoder;
- 8-dimensional embedding;
- one fixed Ridge residual-ratio head;
- Ridge alpha: **10**;
- correction cap: **+/-10%**;
- fit cohort: exact exposed 10-event / 19-row historical cohort;
- historical candidate selection performed: **false**;
- horizons: **P-7 / P-3 / P-1**.

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

The original successful fit workflow generated the head as an Actions artifact. On 2026-10-29 the exact frozen artifact was persisted to `main` so the prospective shadow runner can execute without refitting.

Operational verification after persistence:

- checkout: success;
- pinned inference runtime: success;
- compile: success;
- main-only OIDC: success;
- immutable shadow check: **success**;
- production change: **false**.

As of **2026-10-29 16:09 UTC**, before the first due P-1 cutoff:

- shadow attempts: **0**;
- shadow predictions: **0**;
- shadow scores: **0**.

This is expected. Do not create retrospective rows.

---

# 6. Frozen shadow evidence contract

Exact cutoff:

`target_as_of_at = kickoff_at - N days`, where `N in {7,3,1}`.

Eligibility requires:

- future event and no known attendance outcome;
- execution inside the immutable cutoff window;
- genuine observations only;
- >=4 eligible hourly-bucket observations;
- >=24h observed prefix span;
- positive first genuine inventory observation;
- PIT-valid structural prior genuinely available by the cutoff;
- no previous immutable attempt for the same event/horizon/candidate.

Prediction:

`challenger_p50 = structural_p50 * (1 + clipped_head_ratio)`

with ratio clipped to `[-0.10,+0.10]`.

Persist to the existing immutable trajectory backend:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Never insert synthetic or retrospective prospective evidence.

---

# 7. Live prospective evidence snapshot — 2026-10-29 16:09 UTC

## P9 v1

- 2 genuine attempts / 2 events;
- 0 predictions;
- 0 scored;
- both attempts support-insufficient;
- correct fail-closed;
- production change false.

Do not lower support or retro-predict.

## P9 Family Fallback v2

- 1 genuine attempt;
- 1 immutable prediction;
- 0 scored;
- separate evidence only;
- production change false.

Never pool v1 and v2 evidence.

## Form5

- `PROSPECTIVE_COLLECTING`;
- 0/8 completed eligible events;
- 0/5 clubs;
- 0/2 distinct values;
- future stream: 13 events / 12 clubs / 9 distinct values;
- Ridge alpha 30;
- cap +/-25%;
- production change false.

## P7

Latest recorded canonical state:

- 53 immutable rows;
- 6 events;
- 0 scored;
- no retuning.

## Long72

Frozen / low priority:

- 5 scored events;
- 6082.40 -> 6039.39 MAE;
- 0.71% point gain.

## P11 / P4a

Continue genuine evidence accumulation only. No forced model fit below gates.

---

# 8. Imminent immutable windows

Fresh machine state at **2026-10-29 16:09 UTC**:

- event6 Lech Poznań–Wisła Kraków P9 T-48: **2026-10-29 16:30 UTC** — READY;
- event443 Cracovia–Motor P9/Form5 T-24: **2026-10-29 17:00 UTC** — READY;
- event443 Cracovia–Motor frozen-encoder P-1: **2026-10-29 17:00 UTC** — first shadow opportunity;
- event444 GKS Katowice–Widzew P9 T-48: **2026-10-29 19:15 UTC** — READY;
- event446 Wisła Płock–Piast P9 T-24: **2026-10-30 11:15 UTC** — READY.

P9 cadence:

`11,26,41,56 * * * *`

plus the redundant Structural Prior Materializer -> P9 heartbeat bridge.

Frozen-encoder shadow cadence:

`20 * * * *`

The runner reconstructs inputs strictly at the exact cutoff even if execution happens later inside the immutable window.

Unknown inventory is never converted to zero.

---

# 9. Data reality

Current genuine pre-kickoff inventory history:

- 32 events;
- 14 clubs;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Therefore:

> **P-60 is a collection horizon, not a requirement for a fabricated complete 60-day sequence.**

Use genuine variable-length prefixes. No interpolation or forward-fill merely for model convenience.

---

# 10. Immediate execution order

1. Protect imminent P9 / Form5 / frozen-encoder shadow cutoffs.
2. Confirm immutable rows after each due window; never backfill a missed window with later information.
3. Score P7/P9/trajectory shadow only after genuine confirmed outcomes.
4. Keep the frozen encoder and attendance head unchanged while prospective evidence accumulates.
5. Report trajectory attendance evidence separately by P-7 / P-3 / P-1 and event-balanced overall.
6. Do not react to the first one or two prospective outcomes by changing alpha, cap, encoder or features.
7. Continue genuine trajectory, P11 and P4a collection.
8. Derive a business minimum meaningful attendance Delta MAE independently of observed candidate results.
9. Production remains separately review-gated and OFF.

---

# 11. Next model decision

No new model search is justified now.

The next meaningful question is no longer whether trajectory dynamics can be represented — SSP v1 says they can.

The next question is:

> **Does the frozen representation add genuinely prospective attendance accuracy over the structural incumbent?**

Only future immutable attendance outcomes can answer that.
