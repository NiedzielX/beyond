# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-30**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Where we are now

There are two parallel tracks.

## Track 1 — protect genuine prospective evidence

Keep P7, P9, Form5, Long72 and the frozen trajectory shadow honest. An imminent immutable cutoff always has priority over new R&D.

## Track 2 — improve attendance MAE with trajectory information

The supervised trajectory cohort is exhausted for model selection. Lane A v1, Lane B v1 and Lane B v2 are closed.

Target-free self-supervised trajectory pretraining v1 is complete and produced a **supported representation**:

| Target-free SSP v1 metric | Result |
|---|---:|
| zero-change event-balanced MAE | 0.091722 |
| GRU event-balanced MAE | **0.062896** |
| Delta MAE | **-0.028826** |
| validation events improved | **5 / 5** |

Decision: `REPRESENTATION_SUPPORTED`.

This is evidence that the encoder learned reusable inventory-trajectory dynamics. It is **not attendance-forecast evidence**.

The encoder is frozen. A single conservative attendance head was fitted once on the already-exposed historical cohort without historical model selection:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Current active attendance experiment:

> **Frozen encoder + frozen Ridge residual-ratio head -> immutable P-7 / P-3 / P-1 prospective shadow -> future event-balanced attendance Delta MAE.**

No tuning is allowed against early prospective outcomes under the same candidate version.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary attendance metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired: `Delta MAE < 0`.

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
13. A missed prospective window stays missing; never backfill it with later information.
14. Operational scheduler hardening may add redundant execution paths only if model/data/evidence semantics remain unchanged.

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

Precommit: `ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result: `ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Frozen encoder: `ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Frozen data cutoff: `2026-10-28T22:09:43.958409Z`

Evidence class: `target_free_temporal_validation`

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

The encoder is immutable for candidate v1. SSP v1 must not be retuned against the same validation events.

---

# 5. Active trajectory attendance candidate — prospective shadow v1

Precommit: `ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Candidate: `trajectory-frozen-encoder-ridge-ratio-head-v1`

Components:

- frozen SSP v1 GRU encoder;
- 8-dimensional embedding;
- one fixed Ridge residual-ratio head;
- Ridge alpha **10**;
- correction cap **+/-10%**;
- fit cohort: exact exposed 10-event / 19-row historical cohort;
- historical candidate selection performed: **false**;
- horizons: **P-7 / P-3 / P-1**.

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

The exact frozen head is persisted to `main`. Do not refit it.

Current prospective state at the 2026-10-30 machine check:

- attempts: **1**;
- immutable predictions: **1**;
- scores: **0**;
- production change: **false**.

First genuine prediction — event446 Wisła Płock–Piast, P-1:

- cutoff: `2026-10-30 11:15:00 UTC`;
- attempt: `2026-10-30 11:21:26 UTC`;
- status: `PREDICTION_READY`;
- structural P50: `6084.5618737955`;
- challenger P50: `6693.01806117505`;
- residual: `+608.45618737955`;
- +10% cap hit;
- target values used: false;
- production change: false;
- score pending genuine confirmed attendance.

Do not interpret a single prospective prediction as model proof.

---

# 6. Frozen shadow evidence contract

Exact cutoff:

`target_as_of_at = kickoff_at - N days`, where `N in {7,3,1}`.

Eligibility requires:

- future event and no known attendance outcome;
- execution inside the exact cutoff through +90 minute immutable window;
- genuine observations only;
- context limited to the 168h before the cutoff;
- hourly-bucket deduplication;
- >=4 eligible observations;
- >=24h observed prefix span;
- positive first genuine inventory observation;
- PIT-valid structural prior genuinely available by the cutoff;
- no previous immutable attempt for the same event/horizon/candidate.

Prediction:

`challenger_p50 = structural_p50 * (1 + clipped_head_ratio)`

with ratio clipped to `[-0.10,+0.10]`.

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Never insert synthetic or retrospective prospective evidence.

Operational activation boundary used by preflight:

`2026-10-29 16:11:35 UTC`

Earlier checkpoints are reported as `PRE_ACTIVATION_NOT_EXPECTED`, not false misses.

---

# 7. Live prospective evidence snapshot — 2026-10-30 ~12:30 UTC

## P9 v1

- **4 attempts / 0 predictions / 0 scored**;
- all captured attempts are `PIT_SUPPORT_INSUFFICIENT`;
- correct fail-closed;
- production change false.

Known missed windows:

- event443 Cracovia–Motor T-24;
- event6 Lech Poznań–Wisła Kraków T-48.

Never backfill them.

## P9 Family Fallback v2

- **3 attempts / 2 immutable predictions / 0 scored**;
- event446 T-48: structural `6084.5618737955` -> challenger `6911.09714798977`;
- event446 T-24: structural `6084.5618737955` -> challenger `8252.87035184191`;
- event444 T-48: `FALLBACK_SUPPORT_INSUFFICIENT`;
- separate evidence only;
- production change false.

Never pool v1 and v2 evidence.

## Form5

- `PROSPECTIVE_COLLECTING`;
- **0/8** completed eligible events;
- gate closed;
- future stream: **14 events / 13 clubs / 9 distinct values**;
- Ridge alpha 30;
- cap +/-25%;
- production change false.

The prospective dataset remains empty until genuine outcomes exist by design.

## Frozen Encoder Shadow

- **1 attempt / 1 prediction / 0 scored**;
- event446 P-1 captured;
- event443 Cracovia–Motor P-1 at `2026-10-29 17:00 UTC` is a genuine `MISSED_WINDOW` for the current operational version and remains missing.

## P7

Latest canonical state:

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

# 8. Prospective protection / scheduler state

## P9

Primary frozen cadence:

`11,26,41,56 * * * *`

Redundancy:

- successful Structural Prior Materializer -> P9 workflow-run bridge;
- independent heartbeat: `16,46 * * * *`.

The independent heartbeat was added after event446 T-24 had no attempt despite the normal scheduler path. The T-24 window was rescued prospectively while still legal; no model semantics changed.

## Frozen trajectory shadow

Cadence:

`20,50 * * * *`

This was hardened from one to two checks per hour because the immutable write window is only +90 minutes. Model, artifacts, cutoffs and prediction logic remain unchanged.

---

# 9. Trajectory prospective preflight

Live read-only RPC:

`public.trajectory_frozen_encoder_preflight_v1(integer)`

Purpose:

- identify future P-7/P-3/P-1 readiness before windows open;
- mirror the frozen encoder input gates;
- distinguish pre-activation checkpoints from genuine misses;
- surface collection/prior problems without creating predictions.

Security:

- `anon`: no execute;
- `authenticated`: no execute;
- `service_role`: execute;
- target values used: false;
- production change: false.

Machine snapshot at `2026-10-30 12:30 UTC`:

- READY: **10** checkpoints;
- CAPTURED: **1**;
- PRE_ACTIVATION_NOT_EXPECTED: **10**;
- WATCH: **13**;
- CRITICAL / genuine missed: **5**.

Current actionable items:

1. event443 Cracovia–Motor P-1 — `MISSED_WINDOW`; preserve as missing.
2. event5091 Motor Lublin–Wisła Płock P-7 (`2026-10-30 17:00 UTC`) — `CRITICAL_FIRST_INVENTORY_INVALID`; source series contains early zero inventory followed by positive values. Frozen v1 must fail closed rather than redefine the gate.
3. event448 Wisła Kraków–Cracovia P-7 (`2026-10-30 19:30 UTC`) — `CRITICAL_TOO_FEW_OBSERVATIONS`; currently no snapshots.
4. event603 Korona Kielce–Radomiak P-7 (`2026-10-31 11:15 UTC`) — `CRITICAL_PREFIX_SPAN_INSUFFICIENT`; latest stored snapshot is still from 2026-10-26, so collection health requires investigation.
5. event7372 Widzew Łódź–Pogoń P-7 (`2026-10-31 19:15 UTC`) — `CRITICAL_NO_INCUMBENT`; current snapshot stream is also all-zero inventory and therefore not trajectory-ready.

Do not solve these alerts by loosening frozen v1 input gates.

---

# 10. Immediate immutable windows

Today / next protected checkpoints:

- event6 Lech Poznań–Wisła Kraków P9 T-24 + Frozen Encoder P-1: **2026-10-30 16:30 UTC** — trajectory preflight `READY`;
- event445 KGHM Zagłębie Lubin–Korona P-3: **2026-10-30 17:00 UTC** — trajectory `READY`;
- event5091 Motor Lublin–Wisła Płock P-7: **2026-10-30 17:00 UTC** — trajectory input invalid under frozen v1;
- event444 GKS Katowice–Widzew P9 T-24 + Frozen Encoder P-1: **2026-10-30 19:15 UTC** — trajectory preflight `READY`;
- event447 Raków–Pogoń P-3: **2026-10-30 19:30 UTC** — trajectory `READY`;
- event448 Wisła Kraków–Cracovia P-7: **2026-10-30 19:30 UTC** — no trajectory observations yet;
- event445 P9 T-48: **2026-10-31 17:00 UTC**;
- event447 P9 T-48: **2026-10-31 19:30 UTC**.

The runner reconstructs inputs strictly at the exact cutoff even if execution happens later inside the immutable +90 minute window.

---

# 11. Data reality

Current genuine pre-kickoff inventory history remains sparse and heterogeneous by club/provider.

Rules:

- use genuine variable-length prefixes;
- no interpolation or forward-fill merely for model convenience;
- hidden/unknown inventory is never converted into a usable positive observation;
- public inventory is a demand/inventory proxy, not confirmed sales or attendance;
- P-60 is a collection horizon, not a requirement for a fabricated complete 60-day sequence.

Current collection cases requiring operational diagnosis include:

- Korona: no new stored snapshot since 2026-10-26;
- Wisła Kraków event448: mapped event but no snapshots;
- Widzew event7372: snapshots exist but all currently carry `available_total=0`;
- Motor event5091: early zero rows followed by positive inventory; frozen v1 treats the first zero as invalid and must fail closed.

---

# 12. Immediate execution order

1. Protect every imminent P9 / Form5 / frozen-encoder cutoff before research work.
2. Use P9 and trajectory preflight to find readiness failures before windows open.
3. Fix collection/materialization operations only when doing so preserves genuine source semantics; never fabricate or rewrite prospective evidence to make a candidate eligible.
4. Confirm immutable attempts/predictions after each due window; never backfill missed windows.
5. Score P7/P9/trajectory only after genuine confirmed attendance outcomes.
6. Keep P9 v1, P9 v2, Form5 and Frozen Encoder evidence separate.
7. Keep the SSP encoder, attendance-head alpha/cap and P9 fallback policy unchanged while evidence accumulates.
8. Report trajectory attendance evidence separately by P-7 / P-3 / P-1 and event-balanced overall.
9. Do not react to the first one or two prospective outcomes by changing model parameters or features.
10. Continue genuine trajectory, P11 and P4a collection.
11. Derive a business minimum meaningful attendance Delta MAE independently of observed candidate results.
12. Production remains separately review-gated and OFF.

---

# 13. Next model decision

No new model search is justified now.

SSP v1 answered the representation question. The current question is:

> **Does the frozen representation add genuinely prospective attendance accuracy over the structural incumbent?**

Only future immutable attendance outcomes can answer that.
