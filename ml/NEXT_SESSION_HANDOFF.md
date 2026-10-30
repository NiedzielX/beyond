# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-30**

Status: **QUERY LIVE MACHINE STATE FIRST — PROSPECTIVE EVIDENCE IS PRIMARY**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

---

# 1. First command / first principle

Start from live DB, not markdown:

`public.prospective_decision_summary_v1(10)`

This single read-only call composes:

- protected-lane operational state;
- prospective attendance evaluation;
- the precommitted business-meaningful trajectory gain gate.

For lower-level operational detail use:

`public.prospective_ops_summary_v1(10)`

Then protect any imminent immutable cutoff before doing R&D.

Never backfill a missed prospective window.

Production remains OFF:

- `live_adjustment=0`;
- `production_change=false`;
- `production_activation_allowed=false`.

---

# 2. Frozen model state

Structural model remains the attendance incumbent.

SSP v1 is closed as `REPRESENTATION_SUPPORTED`:

- zero-change validation MAE `0.0917223592`;
- GRU MAE `0.0628961688`;
- Delta `-0.0288261905`;
- improved events 5/5;
- no attendance labels or structural P50 used.

This is representation evidence only.

Active attendance candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen contract:

- SSP encoder frozen;
- Ridge residual-ratio head alpha 10;
- cap +/-10%;
- P-7 / P-3 / P-1;
- no refit or retuning under v1.

First genuine prospective prediction exists for event446 Wisła Płock–Piast P-1:

- structural `6084.5618737955`;
- challenger `6693.01806117505`;
- score pending outcome.

---

# 3. Current evidence counters

Latest verified state before 13:00 UTC on 2026-10-30:

- P9 v1: **4 attempts / 0 predictions / 0 scores**;
- P9 v2: **3 attempts / 2 predictions / 0 scores**;
- Frozen Encoder: **1 attempt / 1 prediction / 0 scores**;
- Form5: **0/8 completed events**, gate closed;
- all attendance MAE metrics still null.

P9 v2 event446:

- T-48 challenger `6911.09714798977` vs structural `6084.5618737955`;
- T-24 challenger `8252.87035184191` vs structural `6084.5618737955`.

Do not infer winner before genuine attendance.

Known missed windows:

- event443 P9 T-24;
- event443 trajectory P-1;
- event6 P9 T-48.

Leave them missing forever.

---

# 4. Scheduler protection

P9 primary:

`11,26,41,56 * * * *`

P9 redundancy:

- Structural Prior success -> `p9-prospective-heartbeat-bridge.yml` -> one P9 dispatch;
- independent heartbeat `16,46 * * * *`.

The independent heartbeat no longer duplicates the Structural Prior `workflow_run` path.

Frozen trajectory:

`20,50 * * * *`

Both systems remain immutable/idempotent at the evidence layer.

---

# 5. Immediate protected cutoffs

- event6 Lech–Wisła: P9 T-24 + trajectory P-1 at **2026-10-30 16:30 UTC** — READY;
- event445 Zagłębie–Korona: trajectory P-3 at **17:00 UTC** — READY;
- event5091 Motor–Wisła Płock: trajectory P-7 at **17:00 UTC** — expected fail-closed due first inventory zero;
- event444 GKS–Widzew: P9 T-24 + trajectory P-1 at **19:15 UTC** — READY;
- event447 Raków–Pogoń: trajectory P-3 at **19:30 UTC** — READY;
- event448 Wisła Kraków–Cracovia: trajectory P-7 at **19:30 UTC** — no legal prefix, expected fail-closed;
- event445 P9 T-48: **2026-10-31 17:00 UTC**;
- event447 P9 T-48: **2026-10-31 19:30 UTC**.

Verify persistence after each cutoff; do not assume GitHub cron fired.

---

# 6. Data collection fixes / current source reality

## Motor / Stellis

Root cause of early zero inventory identified:

- six `available_total=0` raw rows had `has_active_stage=false`;
- first positive count appeared exactly when `has_active_stage=true`.

Prospective promotion guard v2.2 is live:

`supabase/sql/stellis_visible_promotion_active_stage_guard_v1.sql`

New inactive-stage rows stay raw and are not promoted.

Historical six zeros remain untouched, so current P-7/P-3 eligibility is not repaired retrospectively. Later P-1 may become legal naturally when those rows fall outside the 168h window.

## Korona / Stellis

Collector is healthy. Current source explicitly has `showAvailableTicketsCount=false`.

Treat as hidden inventory, not zero and not an outage.

## Widzew / Stellis

Source currently exposes literal zero availability. Do not reinterpret it.

Verified Widzew stadium capacity `18,018` was added from the official City of Łódź source and a genuine Structural Prior for event7372 was successfully materialized before its future P-7 cutoff.

Remaining readiness problem is inventory/prefix semantics, not missing prior.

## Wisła Kraków / Roboticket

Event448 is discovered, verified and mapped.

Standard `GetWGLSectorsInfo` is empty for this stadium variant, but full seat geometry and VAO occupancy are available.

Fail-closed fallback is live:

`supabase/functions/roboticket_vao_collect_v1/index.ts`

Cron:

`roboticket-wisla-vao-15m` -> every 15 minutes.

Validated contract:

- 33,499 stadium geometry seats;
- 100% of geometry IDs matched to VAO occupancy;
- 158 extra technical IDs discarded;
- `spatialHashShift` read from page;
- Roboticket enum: Empty=0, My=1, Other=2, NotAvailable=3;
- frontend contract sets `seat.ava = anyRight && hasSgRight && hasResRight`;
- selectable = all three rights true AND occ in {0,1}.

Latest validation found 6,890 `occ=Empty` seats but **0 public-selectable seats** under Roboticket's own rights contract, so no snapshot was inserted.

The collector never writes `available_total=0`. It starts writing only after a positive, fully covered public selectable count exists.

Temporary diagnostic probe was retired and now requires JWT / returns 410.

---

# 7. Preflight / machine-state tools

Trajectory readiness:

`public.trajectory_frozen_encoder_preflight_v1(integer)`

Unified protected-lane state:

`public.prospective_ops_summary_v1(integer)`

Unified operational + evidence + business decision state:

`public.prospective_decision_summary_v1(integer)`

All are service_role-only.

Trajectory operational activation boundary:

`2026-10-29 16:11:35 UTC`

Earlier checkpoints are `PRE_ACTIVATION_NOT_EXPECTED`.

Current key trajectory alerts:

- event443 P-1 true `MISSED_WINDOW`;
- event5091 P-7 first inventory invalid because historical pre-sale zero remains;
- event448 P-7 no legal observations;
- event603 P-7 insufficient historical prefix because source now hides availability;
- event7372 P-7 has a genuine prior, but its inventory prefix is still unsuitable.

Do not loosen the frozen v1 eligibility gate to make these rows pass.

---

# 8. Evaluation and business threshold are precommitted

## Evidence protocol

Protocol:

`ml/PROSPECTIVE_ATTENDANCE_EVALUATION_V1.md`

Evaluator:

`public.prospective_attendance_eval_v1()`

Created before the first Frozen Encoder / P9-v2 attendance score.

Primary method:

- row AE first;
- if multiple horizons exist, average within event;
- then average equally across events;
- primary metric = event-balanced Delta MAE.

Supporting metrics:

- coverage;
- per-horizon MAE;
- improvement rate;
- median event Delta AE;
- worst-event degradation;
- best-event improvement.

Evidence review gate:

- 8 independent scored events;
- 5 distinct clubs.

Before gate: `PROSPECTIVE_COLLECTING`.
After gate: `EVIDENCE_REVIEW_READY`.

This gate is not automatic production promotion.

## Business-meaningful forecast gain

Independent precommit:

`ml/BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md`

Trajectory business evaluator:

`public.trajectory_business_meaningful_gain_v1()`

Frozen absolute threshold:

> **at least 550 seats of prospective event-balanced MAE improvement**

Equivalent:

`Delta MAE <= -550 seats`

The threshold was defined before any frozen-trajectory attendance score and was derived from the project's commercial 7% fill-rate action scale using the current 70/30 top-end / medium-club reference mix. It is an accuracy-resolution threshold, not a claim that 550 fewer forecast-error seats cause 550 incremental sales.

Additional risk guards:

- event improvement rate > 50%;
- median event Delta AE < 0;
- challenger P90 AE not worse;
- absolute signed bias not worse;
- no retrospective/backfilled rows;
- equal event weighting.

Current business labels at P-7/P-3/P-1:

`INSUFFICIENT_PROSPECTIVE_EVIDENCE`

because no trajectory attendance outcomes have been scored yet.

Unified decision RPC:

`public.prospective_decision_summary_v1(10)`

Current state remains:

- trajectory: 1 prediction / 0 scores / `PROSPECTIVE_COLLECTING`;
- P9 v2: 2 predictions / 0 scores / `PROSPECTIVE_COLLECTING`;
- business threshold: 550 seats;
- production activation allowed: false.

---

# 9. Next actions

1. Query `prospective_decision_summary_v1(10)` fresh.
2. Protect due windows first.
3. Verify event6 T-24/P-1 after 16:30 UTC.
4. Verify event445 P-3 and expected Motor P-7 fail-closed after 17:00 UTC.
5. Verify event444 T-24/P-1 after 19:15 UTC.
6. Verify event447 P-3 and event448 P-7 fail-closed after 19:30 UTC.
7. Confirm the Wisła VAO cron remains fail-closed until genuinely selectable seats appear.
8. Score only after confirmed attendance outcomes.
9. Use the precommitted evaluators, not ad-hoc analysis.
10. Do not change model parameters after the first 1–2 outcomes.
11. Keep P9 v1, P9 v2, Form5 and Frozen Encoder evidence separate.
12. Production remains OFF.

The next meaningful model decision is future **prospective attendance Delta MAE**, evaluated against both the frozen evidence protocol and the independently precommitted business threshold — not another historical search.
