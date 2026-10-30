# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-30**

Status: **CURRENT SOURCE OF TRUTH**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 0. Current objective

Two priorities run in parallel:

1. **protect genuine prospective evidence** — every imminent immutable P9 / Form5 / trajectory cutoff takes priority over new R&D;
2. **evaluate the frozen trajectory representation on future attendance outcomes** without retuning after seeing early results.

The structural model remains the attendance incumbent.

No new supervised trajectory tournament is justified on the exposed historical cohort.

---

# 1. Frozen research state

## Structural incumbent

Frozen supervised trajectory results on the exposed 10-event cohort:

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | +1558.80 | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | +0.87 | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | +2197.88 | mechanism not supported |

The cohort is exposed. Do not tune shrinkage, cap, loss, learning rate, epochs, architecture or a new correction rule against those same outer events.

## Target-free SSP v1

Precommit: `ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Frozen encoder: `ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Result:

- zero-change event-balanced MAE: **0.0917223592**;
- GRU event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved validation events: **5/5**;
- attendance labels used: false;
- structural P50 used: false.

Decision: `REPRESENTATION_SUPPORTED`.

This is representation-learning evidence only, not attendance-forecast proof.

---

# 2. Active frozen attendance candidate

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Frozen head:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Contract:

- frozen SSP encoder;
- 8-dimensional embedding;
- one Ridge residual-ratio head;
- alpha **10**;
- correction cap **+/-10%**;
- exact exposed 10-event / 19-row fit cohort;
- no historical candidate selection;
- prospective P-7 / P-3 / P-1 only;
- production off.

The head was fitted once and must not be refitted under candidate v1.

First genuine prospective attendance prediction:

**event446 Wisła Płock–Piast, P-1**

- cutoff `2026-10-30 11:15 UTC`;
- immutable attempt `11:21:26 UTC`;
- structural P50 `6084.5618737955`;
- challenger P50 `6693.01806117505`;
- correction `+608.45618737955` (+10% cap hit);
- target values used false;
- production change false;
- score pending genuine attendance outcome.

Event443 Cracovia–Motor P-1 was missed after current shadow activation and must remain missing forever under this evidence stream.

---

# 3. Non-negotiable prospective rules

1. Event/match is the independent attendance-evaluation unit.
2. No future target trajectory at an earlier cutoff.
3. No target attendance in prediction features.
4. No manufactured, interpolated or retrospectively repaired inventory merely to make a candidate eligible.
5. A missed prospective window stays missing.
6. Fail-closed attempts are valid coverage evidence, not forecast errors.
7. A material model/feature/cap/alpha/horizon change after outcomes creates a new version and new prospective stream.
8. SSP validation is never presented as attendance evidence.
9. Operational scheduler/data-collection hardening may change execution reliability only; it must not change frozen prediction semantics.
10. No research workflow changes production automatically.

Trajectory v1 eligibility at exact cutoff:

- execution cutoff through +90 minutes;
- genuine observations only;
- 168h maximum prefix;
- hourly-bucket deduplication;
- >=4 observations;
- >=24h prefix span;
- first genuine inventory observation >0;
- PIT-valid structural prior available by cutoff.

---

# 4. Current machine state

Canonical one-call decision-state RPC:

`public.prospective_decision_summary_v1(integer)`

It composes:

- operational state / preflights;
- frozen prospective attendance evaluation;
- trajectory business-meaningful gain evaluation;
- P9 v2 business-meaningful gain evaluation.

Lower-level operational RPC:

`public.prospective_ops_summary_v1(integer)`

Security for decision summary:

- anon execute: false;
- authenticated execute: false;
- service_role execute: true.

Latest verified state on 2026-10-30 around 13:00 UTC:

- P9 v1: **4 attempts / 0 predictions / 0 scores**;
- P9 v2: **3 attempts / 2 predictions / 0 scores**;
- Frozen Encoder: **1 attempt / 1 prediction / 0 scores**;
- Form5: **0/8 completed eligible events**, `PROSPECTIVE_COLLECTING`;
- trajectory business labels: P-7/P-3/P-1 = `INSUFFICIENT_PROSPECTIVE_EVIDENCE`;
- P9 v2 business labels: T-48/T-24 = `INSUFFICIENT_PROSPECTIVE_EVIDENCE`;
- production change false;
- `live_adjustment=0`;
- production activation allowed false.

P9 v2 event446:

- T-48: structural `6084.5618737955` -> challenger `6911.09714798977`;
- T-24: structural `6084.5618737955` -> challenger `8252.87035184191`.

Do not compare those predictions against each other or against trajectory until genuine attendance exists.

Known missed windows that must never be backfilled:

- event443 P9 T-24;
- event443 trajectory P-1;
- event6 P9 T-48.

---

# 5. Scheduler protection

## P9

Primary cadence:

`11,26,41,56 * * * *`

Redundancy:

- `p9-prospective-heartbeat-bridge.yml`: one dispatch after successful Structural Prior Materializer on main;
- independent heartbeat `p9-prospective-heartbeat-v1.yml`: `16,46 * * * *`.

The duplicate Structural Prior `workflow_run` path was removed from the independent heartbeat. The bridge owns that path; the independent heartbeat owns its separate cron.

## Frozen trajectory shadow

Cadence:

`20,50 * * * *`

The second check per hour is operational redundancy only. Frozen artifacts, feature contract, horizons and +90 minute immutable window are unchanged.

---

# 6. Preflight and immediate windows

Trajectory preflight:

`public.trajectory_frozen_encoder_preflight_v1(integer)`

Operational activation boundary:

`2026-10-29 16:11:35 UTC`

Earlier checkpoints are `PRE_ACTIVATION_NOT_EXPECTED`, not operational misses.

Current protected checkpoints:

- event6 Lech Poznań–Wisła Kraków: P9 T-24 + trajectory P-1 at **2026-10-30 16:30 UTC** — READY;
- event445 Zagłębie Lubin–Korona: trajectory P-3 at **17:00 UTC** — READY;
- event5091 Motor Lublin–Wisła Płock: trajectory P-7 at **17:00 UTC** — expected fail-closed because first inventory in frozen window is 0;
- event444 GKS Katowice–Widzew: P9 T-24 + trajectory P-1 at **19:15 UTC** — READY;
- event447 Raków–Pogoń: trajectory P-3 at **19:30 UTC** — READY;
- event448 Wisła Kraków–Cracovia: trajectory P-7 at **19:30 UTC** — no legal 24h prefix; expected fail-closed;
- event445 P9 T-48: **2026-10-31 17:00 UTC**;
- event447 P9 T-48: **2026-10-31 19:30 UTC**.

At or shortly after each cutoff, verify persistence in live DB. If a legal window is open and scheduler has not written an attempt, protect the window before any research work.

---

# 7. Collection/data-contract findings

## Motor Lublin / Stellis

Root cause found for early zero inventory on event5091:

- six raw observations had `available_total=0` while `has_active_stage=false`;
- first positive inventory appeared exactly when `has_active_stage=true`.

Prospective fix is live in:

`supabase/sql/stellis_visible_promotion_active_stage_guard_v1.sql`

Promotion contract v2.2:

- explicit `has_active_stage=false` remains in raw data and is not promoted to `public.snapshots`;
- active-stage observations continue normally;
- legacy parsers without this field retain existing behavior;
- historical snapshots are untouched.

The six historical pre-sale zeros stay in event5091. Therefore its current P-7/P-3 windows remain legitimately affected; no history rewrite is allowed. Its later P-1 window may naturally become legal when those zeros fall outside the 168h prefix.

## Korona Kielce / Stellis

Collector is alive. The current source explicitly hides availability with `showAvailableTicketsCount=false`.

This is source-side hidden inventory, not a scheduler outage. Do not convert hidden to zero or fabricate continuity.

## Widzew / Stellis

The source currently exposes literal zero available places.

Verified 2026/27 stadium capacity `18,018` is now in the Structural Prior registry and a genuine PIT-valid prior for event7372 was materialized on 2026-10-30 before its future P-7 cutoff.

Remaining trajectory readiness is inventory-related, not prior-related.

Do not reinterpret source zero as unknown merely to make the model eligible.

## Wisła Kraków / Roboticket

Event448 is discovered, verified and mapped correctly. The standard Roboticket sector-info contract is empty for this stadium variant.

A separate fail-closed fallback is live:

`supabase/functions/roboticket_vao_collect_v1/index.ts`

Schedule:

`roboticket-wisla-vao-15m` -> `*/15 * * * *`

Source-controlled schedule:

`supabase/sql/roboticket_wisla_vao_schedule_v1.sql`

The fallback mirrors the current Roboticket renderer contract:

- parse `spatialHashShift` from the page;
- build VAO keys from geometry;
- batch occupancy requests;
- require 100% match of stadium geometry seat IDs;
- discard extra technical IDs;
- Roboticket occupancy enum: Empty=0, My=1, Other=2, NotAvailable=3;
- frontend sets `seat.ava = anyRight && hasSgRight && hasResRight`;
- selectable seat = all rights true AND `occ in {0,1}`;
- never write a snapshot when selectable count is 0;
- write only a positive, fully covered, source-observed count with source `roboticket_vao_selectable_v1`.

Validated current Wisła state:

- geometry seats: 33,499;
- geometry coverage from VAO: 100%;
- public empty (`occ=0`) seats observed: 6,890;
- public selectable seats under Roboticket rights contract: 0;
- therefore no snapshot was written.

Zero selectable seats is **not** represented as `available_total=0`; collection remains fail-closed until the source exposes genuinely selectable public inventory.

---

# 8. Frozen prospective evaluation and business decision contract

## Evidence protocol

Precommit:

`ml/PROSPECTIVE_ATTENDANCE_EVALUATION_V1.md`

Live evaluator:

`public.prospective_attendance_eval_v1()`

Created before the first scored Frozen Encoder / P9-v2 outcome.

Primary evaluation:

1. score immutable prediction rows only after genuine confirmed attendance;
2. calculate incumbent/challenger AE per row;
3. average multiple horizons within an event first;
4. average event values across events -> **event-balanced MAE**;
5. report `Delta_MAE = challenger - incumbent`.

Mandatory supporting metrics:

- prediction coverage;
- scored independent events;
- distinct clubs;
- per-horizon MAE;
- event improvement rate;
- median event Delta AE;
- worst-event degradation;
- best-event improvement.

Minimum evidence review gate:

- 8 independent scored events;
- 5 distinct clubs.

Before both are met: `PROSPECTIVE_COLLECTING`.

After both are met: `EVIDENCE_REVIEW_READY`.

This is a review gate only, **not** an automatic promotion criterion.

## Business-meaningful effect

Independent precommit:

`ml/BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md`

Frozen v1 threshold:

> **business gain >= 550 seats of event-balanced MAE improvement**

Equivalent:

`Delta MAE <= -550 seats`

The threshold was frozen before any trajectory/P9-v2 attendance score and is derived from the project's own commercial 7% fill-rate action scale using the current 70/30 reference mix. It is a forecast-accuracy resolution threshold, not a causal claim that 550 fewer MAE seats produce 550 additional ticket sales.

Risk guards at the evaluated horizon/cutoff:

- event improvement rate > 50%;
- median Delta AE < 0;
- challenger P90 AE not worse;
- absolute signed bias not worse;
- no retrospective/backfilled evidence;
- equal event weighting.

Trajectory evaluator:

`public.trajectory_business_meaningful_gain_v1()`

P9 v2 evaluator:

`public.p9_v2_business_meaningful_gain_v1()`

Current labels are `INSUFFICIENT_PROSPECTIVE_EVIDENCE` at every trajectory horizon and P9-v2 cutoff because there are no scored target outcomes yet.

Production activation remains false regardless of evaluator output until a separate explicit review.

---

# 9. Form5

Frozen protocol remains unchanged:

- alpha 30;
- cap +/-25%;
- primary LOCO;
- gate 8 completed events / 5 clubs / 2 distinct Form5 values;
- current completed events 0;
- future stream 14 events / 13 clubs / 9 values;
- production off.

The prospective dataset stays empty before genuine outcomes by design.

---

# 10. Immediate execution order

1. Query `public.prospective_decision_summary_v1(10)` before acting.
2. Protect imminent legal cutoffs first.
3. Verify immutable attempts/predictions after each due window.
4. Never backfill a missed prospective row.
5. Keep P9 v1, P9 v2, Form5 and Frozen Encoder evidence separate.
6. Keep SSP encoder, trajectory head alpha/cap and P9 fallback policy unchanged while evidence accumulates.
7. Fix collection only when genuine source semantics are preserved.
8. Score only after genuine confirmed attendance outcomes.
9. Use the precommitted evidence and business evaluators, not ad-hoc calculations.
10. Do not interpret the first 1–2 scored events as a model decision.
11. Do not lower the 550-seat threshold after seeing early outcomes; any future replacement requires a stronger business-derived v2 precommit.
12. Production remains separately review-gated and OFF.

---

# 11. Next model decision

No new model search is justified now.

The current question is:

> **Does a frozen attendance challenger improve genuinely prospective event-balanced MAE over its incumbent by enough to be both statistically/research-positive and commercially meaningful under the precommitted 550-seat decision scale?**

Only future immutable outcomes can answer it.
