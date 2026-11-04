# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-11-04**

Status: **CURRENT SOURCE OF TRUTH FOR EXECUTION CONTRACTS**

Production: `live_adjustment = 0`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Important: operational counters and cutoff lists below are dated snapshots. Query live machine state before acting.

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Current operational counters, watcher health and deadlines belong in `NEXT_SESSION_HANDOFF.md` and the live runtime status command. Verified milestones:one frozen daily-path model; genuine post-freeze local captures and private backup/restore; hosted panel TypeScript/build; isolated PostgreSQL16persistence and typed panel-feed contract tests(run41810511980). These test milestones do not prove the undeployed SQL/Edge/scheduled workflow in live Supabase. No private partner transactions, production activation or old-model retuning is required.

The attendance history read on2026-11-03 ended at2026-10-25. The six tracked fixtures onOctober30–November2 had no confirmed outcomes in `ticket_event_outcomes`; zero attendance scores are therefore not evidence of zero error. Keep this source-ingestion blocker separate from daily inventory-target scoring.

---

# 0. Current objective

Three priorities run in parallel:

1. **protect genuine prospective evidence** — an imminent immutable P9 / Form5 / trajectory cutoff takes priority when it is actually at risk;
2. **evaluate frozen prospective candidates honestly** without retuning them after seeing outcomes;
3. **actively reduce future MAE in separately versioned research lanes** using the error-driven programme in `ml/MAE_RESEARCH_ROADMAP_V6.md`.

The structural model remains the incumbent for the currently frozen prospective evidence stream.

The exposed 10-event supervised trajectory cohort must not be reused for post-hoc repair of the existing frozen trajectory candidate.

That restriction does **not** stop new MAE R&D. New research is allowed when it is separately versioned and tests genuinely new PIT-safe information, a new structural benchmark, a horizon-specific mechanism, an error-segment hypothesis, or another materially distinct research question.

Default R&D order outside imminent evidence windows:

`MAE-01 error decomposition -> MAE-02 structural benchmark -> MAE-03 context residuals -> MAE-04 trajectory benchmark -> MAE-05 horizon-specific correction -> MAE-06 club/regime heterogeneity -> MAE-07 ablations -> MAE-08 ensemble`

Sequence modelling follows only where simpler evidence justifies the added complexity.

---

# 1. Frozen research state

## Structural incumbent

Frozen supervised trajectory results on the exposed 10-event cohort:

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent for frozen evidence stream |
| Lane A v1 — Ridge | 4153.34 | +1558.80 | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | +0.87 | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | +2197.88 | mechanism not supported |

The cohort is exposed. Do not tune shrinkage, cap, loss, learning rate, epochs, architecture or a new correction rule against those same outer events and then claim the result as fresh evidence.

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

First recorded genuine prospective attendance prediction:

**event446 Wisła Płock–Piast, P-1**

- cutoff `2026-10-30 11:15 UTC`;
- immutable attempt `11:21:26 UTC`;
- structural P50 `6084.5618737955`;
- challenger P50 `6693.01806117505`;
- correction `+608.45618737955` (+10% cap hit);
- target values used false;
- production change false;
- score was pending genuine attendance outcome at the recorded snapshot.

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
11. Historical/grouped R&D and prospective evidence must remain explicitly separated.

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

Latest machine-state values recorded in this document are from **2026-10-30** and must not be assumed current on a later session.

Recorded snapshot around 13:00 UTC on 2026-10-30:

- P9 v1: **4 attempts / 0 predictions / 0 scores**;
- P9 v2: **3 attempts / 2 predictions / 0 scores**;
- Frozen Encoder: **1 attempt / 1 prediction / 0 scores**;
- Form5: **0/8 completed eligible events**, `PROSPECTIVE_COLLECTING`;
- trajectory business labels: P-7/P-3/P-1 = `INSUFFICIENT_PROSPECTIVE_EVIDENCE`;
- P9 v2 business labels: T-48/T-24 = `INSUFFICIENT_PROSPECTIVE_EVIDENCE`;
- production change false;
- `live_adjustment=0`;
- production activation allowed false.

P9 v2 event446 recorded predictions:

- T-48: structural `6084.5618737955` -> challenger `6911.09714798977`;
- T-24: structural `6084.5618737955` -> challenger `8252.87035184191`.

Do not compare those predictions against each other or against trajectory until genuine attendance exists and the precommitted evaluator is used.

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

The operational redundancy is not considered proven solely because YAML exists. When relevant, verify the chain through actual workflow execution and DB persistence.

## Frozen trajectory shadow

Recorded cadence:

`20,50 * * * *`

The second check per hour is operational redundancy only. Frozen artifacts, feature contract, horizons and +90 minute immutable window are unchanged.

---

# 6. Recorded preflight / cutoff snapshot

Trajectory preflight:

`public.trajectory_frozen_encoder_preflight_v1(integer)`

Operational activation boundary:

`2026-10-29 16:11:35 UTC`

Earlier checkpoints are `PRE_ACTIVATION_NOT_EXPECTED`, not operational misses.

The following protected checkpoints were recorded for 2026-10-30/31 and are historical by 2026-11-03:

- event6 Lech Poznań–Wisła Kraków: P9 T-24 + trajectory P-1 at `2026-10-30 16:30 UTC`;
- event445 Zagłębie Lubin–Korona: trajectory P-3 at `2026-10-30 17:00 UTC`;
- event5091 Motor Lublin–Wisła Płock: trajectory P-7 at `2026-10-30 17:00 UTC`;
- event444 GKS Katowice–Widzew: P9 T-24 + trajectory P-1 at `2026-10-30 19:15 UTC`;
- event447 Raków–Pogoń: trajectory P-3 at `2026-10-30 19:30 UTC`;
- event448 Wisła Kraków–Cracovia: trajectory P-7 at `2026-10-30 19:30 UTC`;
- event445 P9 T-48 at `2026-10-31 17:00 UTC`;
- event447 P9 T-48 at `2026-10-31 19:30 UTC`.

Do not use this dated list as today's action list. Query the live RPC before acting.

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

The historical pre-sale zeros stay historical. No history rewrite is allowed.

## Korona Kielce / Stellis

Collector is alive. The source explicitly hides availability with `showAvailableTicketsCount=false` in the recorded diagnostic state.

This is source-side hidden inventory, not a scheduler outage. Do not convert hidden to zero or fabricate continuity.

## Widzew / Stellis

The recorded source state exposed literal zero available places.

Verified 2026/27 stadium capacity `18,018` is in the Structural Prior registry and a genuine PIT-valid prior for event7372 was materialized before its future P-7 cutoff.

The prior blocker is therefore resolved. Any remaining readiness issue is inventory-related, not prior-related.

Do not reinterpret source zero as unknown merely to make the model eligible.

## Wisła Kraków / Roboticket

Event448 is discovered, verified and mapped correctly. The standard Roboticket sector-info contract is empty for this stadium variant.

A separate fail-closed fallback is live:

`supabase/functions/roboticket_vao_collect_v1/index.ts`

Schedule:

`roboticket-wisla-vao-15m` -> `*/15 * * * *`

Source-controlled schedule:

`supabase/sql/roboticket_wisla_vao_schedule_v1.sql`

The fallback mirrors the Roboticket renderer contract:

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

Latest authoritative diagnostic note records:

- geometry coverage from VAO: 100%;
- public empty (`occ=0`) seats observed: **6,870**;
- public selectable seats under Roboticket rights contract: 0;
- therefore no snapshot was written.

Do not promote `occ=0` seats as available unless the rights semantics are genuinely satisfied.

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

The threshold is an accuracy-resolution threshold, not a causal claim that 550 fewer MAE seats produce 550 additional ticket sales.

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

Production activation remains false regardless of evaluator output until a separate explicit review.

---

# 9. Form5

Frozen protocol remains unchanged:

- alpha 30;
- cap +/-25%;
- primary LOCO;
- gate 8 completed events / 5 clubs / 2 distinct Form5 values;
- production off.

Prospective data must remain genuinely prospective; no retrospective repair.

---

# 10. MAE R&D execution programme

When no immutable evidence window is currently at risk, execute the following programme.

## MAE-01 — Error decomposition

2026-11-03 execution: historical diagnostic complete,603events /3,010rows; all10frozen horizon/season metrics reproduced. Result and next hypothesis: `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`. This is exposed-history diagnosis, not fresh validation. Hosted reproducibility checks passed in run41711896063.

Build a reproducible incumbent-error view by club, horizon, attendance/fill regime, weekday/weekend, opponent/context and signed error. Rank the worst absolute-error events and identify which categories contribute most to MAE.

## MAE-02 — Structural baseline benchmark

2026-11-03 bounded audit complete:capacity-weightedmedianT-3/T-1variant rejected on development;Delta+155.01/+104.75, no weighted old-holdout fits. Four fixed simple PIT summaries underperform incumbent. Existing Pre-Live v3 historical research freeze and prior C2 rejection preserved; see `MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md`. Next is new-context coverage audit, not another weighting/context grid.

Audit whether a stronger PIT-safe structural baseline can be built from historical attendance, club/opponent context, verified capacity/utilization, recent attendance form, calendar/competition context and reproducible season state.

This creates a new research baseline version; it does not rewrite the frozen prospective incumbent.

## MAE-03 — Context residual model

Separate new-information preparation for the public-inventory lane: `DAILY_INVENTORY_SOURCE_STATE_CONTRACT_V2.md`. A read-only source receipt/active/visible-state RPC has passed isolated PostgreSQL tests; its fixed feature adapter and actual SQL→feature-row conversion passed hosted run41816696989(20SQL+13adaptertests). It is not wired to frozen v1 and does not authorize a fit. Any benefit needs a separate experimental precommit and genuine future evidence after project deployment.

2026-11-03 audit complete:121stored snapshots,70prospective-window-valid,11distinct events with outcome presence; all37numeric source/baseline/checkpoint groups fail support or grouped-variance screening. No attendance values requested, no model fit. Result:`MAE03_CONTEXT_EVIDENCE_AUDIT_RESULT_V1.md`. Existing Hype gates and P4a9-event gate remain unchanged. Continue forward collection; use independent time to validate prepared daily-path SQL in a disposable database.

Predict `actual - structural forecast` using separately tested PIT-safe context families such as standings/form, opponent strength, future-fixture context and odds. Do not add squad/absence features without a trustworthy timestamped source.

## MAE-04 — Engineered trajectory benchmark

Test inventory/demand level, 1d/3d/7d deltas, velocity, acceleration, slopes, plateau/surge, density/staleness and similarity to prior PIT-safe curves as residual signal.

## MAE-05 — Horizon-specific correction

Test whether early and late horizons require different residual behaviour rather than one global correction mechanism.

## MAE-06 — Demand-regime and club heterogeneity

Test low/normal/near-sellout behaviour and club-specific bias using restrained, partially pooled approaches where sample size is limited.

## MAE-07 — Controlled ablations

Compare structural-only, structural+context, structural+trajectory and combined variants on the same eligible events to identify the source of gain.

## MAE-08 — Ensemble / calibrated blend

Blend only independently useful signals with complementary error profiles. A blend must beat the strongest simpler challenger under identical event-grouped evaluation.

## Sequence modelling

Use small GRU/LSTM/TCN/attention models only when simpler trajectory evidence shows a justified representation gap. Sequence complexity is not automatically the next step.

---

# 11. Mandatory research scoreboard

Every serious MAE experiment must record:

- experiment/version ID;
- hypothesis;
- incumbent/version;
- independent eligible events;
- distinct clubs;
- coverage;
- incumbent event-balanced MAE;
- challenger event-balanced MAE;
- Delta MAE;
- event improvement rate;
- median event Delta AE;
- P90 AE / worst-event degradation;
- signed bias;
- per-horizon MAE where relevant;
- PIT audit status;
- decision.

Do not use narrative memory as the experiment registry.

---

# 12. Immediate execution order

1. Query `public.prospective_decision_summary_v1(10)` fresh before acting on operational state.
2. Protect an imminent legal immutable cutoff if one is currently at risk.
3. Verify due attempts/predictions in live DB; do not assume a scheduled workflow fired.
4. Never backfill a missed prospective row.
5. Keep P9 v1, P9 v2, Form5 and Frozen Encoder evidence streams separate.
6. Keep frozen SSP encoder, frozen trajectory head and frozen P9 policies unchanged while their prospective evidence accumulates.
7. Fix collection only when genuine source semantics are preserved.
8. Score frozen prospective rows only after genuine confirmed attendance outcomes.
9. Outside imminent evidence protection, retain MAE-03 as DATA_BOUND after its completed audit; continue genuine collection; isolated daily-path SQL/feature validation is now complete. Protect new v1/drift evidence and follow the v6 MAE programme.
10. Do not reactively retune frozen candidates against the first future scores.
11. Do not lower or optimize toward the 550-seat business scale after seeing outcomes.
12. Production remains separately review-gated and OFF.

---

# 13. Two different next decisions

## Frozen prospective decision

Question:

> **Does the already-frozen attendance challenger improve genuinely prospective event-balanced MAE over its incumbent by enough to satisfy the precommitted evidence and business guards?**

Only future immutable outcomes can answer this.

## MAE research decision

Question:

> **Which current error segment contributes most to MAE, and what is the smallest new PIT-safe hypothesis that can reduce that error on the same independent events?**

This work starts/continues now in separately versioned research lanes. It does not wait for the frozen prospective candidate to finish collecting.

## Daily-path research refinement —2026-11-04, before first targets

`DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md`shows that the frozen artifact has0nonzero relative-value-history terms despite receiving full prefixes. The issued forecasts reconstruct exactly from latest/scale and negative global/collection-pattern terms. This is an identified capability limitation, not measured forecast error. Keep frozenv1and the existing persistence evaluation.

The next separate daily-path mechanism question may proceed under a new precommit:does a restrained comparator using genuine prefix changes beat persistence on new targets, without treating collection density as demand? Define an explicit anchor/freshness rule, immutable prospective persistence, paired event-balanced/per-lead scoring and future review cohort before fitting/issuing. Do not select an alpha/curve from current pictures or claim the old16training events became fresh evidence. Source-statev2is a separate prepared information contract, still undeployed; no frozen-frame rewiring. Attendance MAE-04queue and frozen550-seat contract remain separate.

Execution update11:06UTC:the authorized separate mechanism question is now implemented as a parameter-free24-hour drift comparator. See`DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md`and frozen`artifacts/daily_inventory_drift_comparator_v1.json`(SHA332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf). Thirteen contract/lifecycle tests passed in hosted run41818376777. Actual no-due cycle and private backup verified; new prospective collection is bounded/host-dependent. No old issue was reconstructed, no learner fitted, noMAEimprovement established. Protect both existing lanes and the new frozen rule while collecting future paired evidence.

## User priority: existing C1 live toward1,200MAE —2026-11-04

Specific plan:`C1_LIVE_MAE_1200_PLAN_V1.md`. The existing11scored C1events have latest policyMAE4121.45; four events contribute83.45%of total error. An outcome-aware ideal selection between current prior/raw predictions would still have4103.05MAE, so gate tuning alone cannot resolve these cases. Next authorized research task:matched-cohort input/label/anchor audit and comparison against the existing frozen D2 residual/P2, before choosing one new-information challenger. Preservev8and all old evidence; the11events are exposed diagnostics. No new model/parameter selection is authorized under an old frozen version. The1,200goal and suggested30event/8clubnew-candidate review are research-plan proposals, not changes to any existing production/business gate or evidence threshold.

## C1 same-time audit completed —2026-11-04 12:20UTC

`C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`: all11events /44exact C1-time representatives retained. C1policyMAE4121.45, D2P2MAE5157.52; do not promote D2from the old later-time event5comparison. C1numerical replay matches,900old training cells verified; frozen D2development and original event5goldens reproduce. Wisła/Górnikactual prior metadata have zero season home history; source queue18history checks+6missing outcomes, no guessed labels. External source revalidation blocked. Separate one-factor9→20training-support experiment is precommitted in `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md` before fitting; oldv8and all prospective gates unchanged. All20become training, never fresh holdout. New future evidence required.
