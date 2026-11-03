# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-30**

Status: **OPERATIONAL HANDOFF — READ AFTER MAE STRATEGY AND PLANS**

## Added 2026-11-03: daily inventory-path implementation

**Later operational update, 19:46UTC:** six local attempts /21daily future points /0scores. Verified private Storage backup and latest-manifest restore now work. A single bounded model watcher (not a coding agent) runs every15minutes through2026-11-04T17:15Z, dependent on this host/session. Status/PID: `/workspace/ops-runtime/2026-11-03-daily-path/latest-cycle.json` and `watcher.pid`. Do not launch duplicate watchers. See [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md) for recovery and prepared-but-not-applied SQL/gateway/disabled GitHub workflow. Admin token is absent; npm registry blocked. Missing network destinations and secure token requirement were saved to environment draft, not applied. The old "no watcher" statement below records the earlier17:00handoff and is superseded by this note. Model artifacts/thresholds remain unchanged.

Read [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md) after the canonical strategy/plans for the new research lane. Frozen artifact `ml/artifacts/daily_inventory_path_v1.json` was fit once on16completed events /1,239rows, cutoff2026-11-03T00:00Z, frozen16:37:09UTC. At17:00:13UTC its first two local prospective attempts (events5091/10500) persisted18future-day points in `/workspace/ops-runtime/2026-11-03-daily-path/shadow-v1.sqlite`; retry was idempotent. First targets mature2026-11-04T17:00UTC. No future-target scores yet. Do not refit v1 or backfill old daily issues.

Separate panel checkout `/workspace/BeyondTicketingPanel` reads the generated `/public/research/daily-inventory-path-v1.json`. Real payload validated by parser/geometry. Full React typecheck/build is blocked by missing dependencies/npm403. New lane is not deployed to Supabase and has no daily GitHub scheduler yet; the local ledger depends on workspace persistence. No always-on coding daemon is running. Existing frozen attendance lanes/production flags remain unchanged. Historical counters/windows below are still the dated October snapshot, not current state.

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Read before this operational handoff, in order: `ml/MAE_RESEARCH_ROADMAP_V5.md`, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`. Only then inspect code, workflows, SQL, Actions and live DB. This handoff describes current operational state and is not the MAE strategy.

---

# 1. First live operational command, after reading the strategy and plans

For current operational facts, query live DB after completing the document read order:

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

Latest verified state at 15:09 UTC on 2026-10-30, from live `prospective_decision_summary_v1(10)`:

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

The next decision about the existing frozen attendance candidate uses future **prospective attendance Delta MAE**, evaluated against its frozen evidence protocol and precommitted business threshold. Do not retune that candidate on its exposed evidence.

This does not stop R&D. New, separately versioned/precommitted MAE experiments proceed in parallel through `baseline -> new information -> simple challenger -> event-grouped/PIT-safe MAE -> freeze -> prospective shadow -> genuine outcomes`. Their strategy comes from roadmap v5, not this operational handoff.

---

# 10. Supplementary cloud watchdog — 2026-10-30 only

An additional operational watchdog is running in the current Codex cloud execution session, started at 15:08 UTC:

- helper: `/workspace/ops-runtime/2026-10-30/monitor.py`;
- status: `/workspace/ops-runtime/2026-10-30/state.json`;
- audit: `/workspace/ops-runtime/2026-10-30/audit.jsonl`;
- original model/inference hashes: `/workspace/ops-runtime/2026-10-30/frozen-manifest.json`;
- live RPC snapshot: `/workspace/ops-runtime/2026-10-30/latest-decision.json`.

It reads the decision RPC every 30 seconds, verifies production OFF and frozen files on main, and dispatches existing heartbeat/trajectory workflows only inside still-missing legal windows. At most three dispatch attempts per lane/cutoff, separated by 20 minutes. It never predicts locally, edits models, repairs source history, or changes eligibility. Six tests verified before-cutoff refusal, exact boundaries, after-window refusal, captured-attempt preservation and fail-closed coverage behavior.

This watchdog depends on the current cloud machine/session staying alive. Do not assume it survives a restart or publication. Read the local status and live DB first; do not launch a duplicate process. It is scoped to 2026-10-30 and stops at 21:02 UTC / 22:02 Europe/Warsaw. Existing GitHub schedules remain the primary independent mechanisms.

At 15:09 UTC the watcher was alive, no window was open, and no due-window prediction had been requested. A manual heartbeat smoke run was dispatched without modifying workflow definitions; heartbeat `41078080759` succeeded and downstream P9 `41078098602` succeeded at 15:10 UTC. A subsequent live DB snapshot at 15:11 UTC showed unchanged counters, consistent with no legal target during this control run. Run metadata and state evidence are saved in `smoke-evidence.json` in the watchdog directory.

Full heartbeat → P9 → successful execution → expected DB record remains **PENDING_FULL_CHAIN_VERIFICATION** until the genuine cutoff chain is correlated. A no-target run must not close that task. Downloading this new run's raw logs encountered proxy denial at `results-receiver.actions.githubusercontent.com`; the required hostname was added to the environment configuration draft, preserving existing domains. Runtime access to that log host still needs validation after settings are applied. Metadata from api.github.com and the live DB read both work.
