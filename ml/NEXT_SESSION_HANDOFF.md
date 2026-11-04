# Beyond Ticketing — Next Session Handoff

Last updated: **2026-11-04**

Status: **DAILY-PATH MVP + LIVE EVIDENCE PROTECTION; MAE-01 FOR ATTENDANCE R&D**

Canonical MAE strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Canonical execution contracts: `ml/EXECUTION_PLAN_CURRENT.md`

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Recorded2026-11-04T09:44:27Z:the detached host-dependent worker completed a new export/capture/score cycle and byte-verified private backup. The ledger retains7attempts /4predicted events /57future-day points /0scores. First targets maturetoday17:00UTC(18:00Europe/Warsaw). The prior foreground worker stopped after2026-11-03T20:54; missed issue windows are not reconstructed. Current detached worker is bounded until2026-11-05T09:30Z. Inspect `python -m ml.start_daily_inventory_path_watcher_v1 --runtime /workspace/ops-runtime/2026-11-03-daily-path --status`; HEALTHY requires both a live PID and a recent successful, model-matched, backup-verified cycle. Runtime state is host-dependent, not an autonomous coding service. Isolated PostgreSQL16tests and DB→pinned panel parser passed in Actions run41810511980; this is synthetic test evidence, not live Supabase deployment. SQL/Edge/GitHub scheduling remain undeployed/disabled. Deno types, policy/key transport and isolated real HTTP denial checks passed in run41811081476. Panel real TypeScript/build already passed; local npm remains blocked. Saved cloud setup draft is not applied and admin deployment binding is still absent.

The attendance history read on2026-11-03 ended at2026-10-25. The six tracked fixtures onOctober30–November2 had no confirmed outcomes in `ticket_event_outcomes`; zero attendance scores are therefore not evidence of zero error. Keep this source-ingestion blocker separate from daily inventory-target scoring.

---

# 1. First read / first command

Complete the canonical document order first: roadmap v6 → execution plan → progress tracker → trajectory plan → this handoff. Then inspect implementation and live DB. The handoff supplies operational context; it does not replace the strategy.

Then query live state before trusting any dated operational snapshot in markdown:

`public.prospective_decision_summary_v1(10)`

For lower-level operational detail:

`public.prospective_ops_summary_v1(10)`

If an immutable legal cutoff is currently due or at risk, protect it first.

Otherwise the default next research task is:

> **MAE-03 audit is complete and DATA_BOUND; validate prepared daily-path SQL in an isolated DB while genuine collection continues.**

Do not spend the session maintaining infrastructure when no evidence window is actually at risk.

Never backfill a missed prospective window.

Production remains OFF:

- `live_adjustment=0`;
- `production_change=false`;
- `production_activation_allowed=false` unless explicitly reviewed later.

---

# 2. Research mission

The next agent is not tasked with finding a more complicated model.

The task is:

> **Find where the incumbent loses the most event-balanced MAE, state a falsifiable PIT-safe hypothesis for that residual error, and test the smallest useful challenger on the same independent events.**

Current ordered programme:

1. MAE-01 — error decomposition;
2. MAE-02 — structural baseline benchmark;
3. MAE-03 — context residual model;
4. MAE-04 — engineered trajectory benchmark;
5. MAE-05 — horizon-specific correction;
6. MAE-06 — demand-regime / club heterogeneity;
7. MAE-07 — controlled ablations;
8. MAE-08 — ensemble/calibrated blend;
9. sequence models only if simpler trajectory evidence justifies added complexity.

Every experiment must be event-grouped, PIT-safe and registered in the experiment scoreboard.

---

# 3. MAE-01 — completed historical diagnostic and next hypothesis

Completed2026-11-03:603events /3,010rows, all10frozen horizon/season MAEs reproduced, source/artifact hashes unchanged. See `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md` and `artifacts/mae01_incumbent_error_audit_v1/`. This is already-exposed historical evidence, not fresh validation. MAE-02 weighting audit subsequently rejected that mechanism:developmentDelta+155.01/+104.75. No old-holdout weighted fitting or variant search followed. See `MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md`. Preserve the archived Pre-Live v3 research anchor and prior C2 rejection; proceed to new-context coverage. Hosted reproducibility passed in run41711896063.

Original decomposition requirements, retained for future genuine outcomes:

At minimum calculate event-level error and grouped MAE / signed error by:

- club;
- horizon;
- attendance bucket;
- stadium utilization/fill bucket where verified capacity exists;
- weekday/weekend;
- competition/season context where available;
- opponent strength/attractiveness proxy where already PIT-safe;
- demand regime: low / normal / near-sellout / sellout-prone.

Rank the largest absolute-error events.

For the worst events classify plausible failure type:

- structural level error;
- club bias;
- opponent/context mismatch;
- trajectory/demand-momentum mismatch;
- source/data-quality limitation;
- horizon-specific error;
- unexplained/event-specific shock.

Output must answer:

> **Which event types currently contribute most to total MAE and therefore deserve the next experiment?**

Do not choose the next feature before this analysis unless an already-supported hypothesis clearly requires it.

---

# 4. Frozen model/evidence rules

Structural model remains the incumbent for the existing frozen prospective stream.

SSP v1 remains `REPRESENTATION_SUPPORTED`, but this is representation evidence only.

Active frozen attendance candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen contract:

- SSP encoder frozen;
- Ridge residual-ratio head alpha 10;
- cap +/-10%;
- P-7 / P-3 / P-1;
- no refit or retuning under v1.

The previously exposed 10-event supervised trajectory cohort must not be reused for post-hoc tuning and then presented as new evidence.

This does **not** stop separately versioned MAE research.

---

# 5. Prospective evidence rules

1. Event/match is the independent evaluation unit.
2. Multiple horizons from one event are dependent observations.
3. No future feature state at an earlier cutoff.
4. No target attendance in prediction construction.
5. Missed prospective windows remain missing forever.
6. Fail-closed attempts are valid coverage evidence.
7. Hidden/unknown inventory is never converted to zero.
8. Operational reliability fixes must not mutate frozen prediction semantics.
9. Historical/grouped research is not prospective evidence.
10. No research result activates production automatically.

---

# 6. Mandatory experiment scoreboard

For every serious challenger record at least:

- experiment/version ID;
- hypothesis;
- incumbent/version;
- independent events;
- distinct clubs;
- coverage;
- incumbent MAE;
- challenger MAE;
- Delta MAE;
- event improvement rate;
- median event Delta AE;
- P90/worst-event degradation;
- signed bias;
- per-horizon MAE when relevant;
- PIT audit status;
- decision.

Use `ml/MAE_EXPERIMENT_SCOREBOARD.md` as the human-readable registry once created/updated.

---

# 7. Current source/data semantics to preserve

## Motor / Stellis

Historical pre-sale zero observations caused by inactive sales stage remain untouched. The prospective active-stage promotion guard prevents new inactive-stage zeroes from being promoted.

Do not rewrite history to improve eligibility.

## Korona / Stellis

Recorded source behaviour hides availability (`showAvailableTicketsCount=false`). Treat hidden as unknown, not zero.

## Widzew / Stellis

The structural-prior blocker was resolved. Any remaining issue is inventory/source semantics, not missing capacity prior.

Do not reinterpret literal source zero merely to make a model eligible.

## Wisła Kraków / Roboticket

VAO collection is fail-closed.

Latest authoritative diagnostic note:

- VAO geometry coverage: 100%;
- `occ=0` public-empty seats observed: **6,870**;
- public-selectable seats under the rights contract: **0**.

Do not promote `occ=0` to available seats without satisfying Roboticket rights semantics.

---

# 8. Dated operational snapshot warning

Older documents contain detailed cutoff/counter snapshots from **2026-10-30/31**. By 2026-11-03 these are historical observations, not today's task list.

Always query live DB and recent workflow runs before concluding that a window is READY, MISSED, scored or pending.

Known historical missed windows remain non-backfillable:

- event443 P9 T-24;
- event443 trajectory P-1;
- event6 P9 T-48.

---

# 9. Evaluation / promotion contract

Primary point metric:

**event-balanced MAE**

Headline comparison:

`Delta MAE = challenger MAE - incumbent MAE`

For the active frozen prospective comparison, current business-resolution threshold remains:

`Delta MAE <= -550 seats`

Supporting guards include:

- event improvement rate > 50% for the frozen business gate;
- median event Delta AE < 0;
- P90 AE not worse;
- absolute signed bias not worse;
- genuine/non-backfilled evidence;
- equal event weighting.

Do not tune research candidates toward exactly 550 seats.

---

# 10. Session decision rule

Use this order:

1. Query live state.
2. Protect a genuine immutable cutoff only if one is currently at risk.
3. MAE-03 audit found no currently testable numeric context group. Continue genuine collection and isolated SQL validation; do not force a context fit or repeat closed mechanisms.
4. Use MAE-01 findings to select the next falsifiable hypothesis.
5. Run the smallest useful PIT-safe/event-grouped experiment.
6. Update the scoreboard and progress tracker.
7. Freeze/reject before moving on; do not narratively keep every challenger alive.

The next research question is not "what model should we try?"

It is:

> **What currently causes the largest honest forecast error, and what new information can explain it without leaking the future?**

## Latest operational check —2026-11-03T20:16UTC

Fresh decision RPC: frozen encoder8attempts /5predictions /0scores; P9v1 6/0/0; P9v2 5/3/0. Wisła448P-3 recorded MODEL_INPUT_INSUFFICIENT at19:47:17UTC after successful existing workflow run41706363428; open_count=0. Next encoder cutoff: Korona603onNov4 11:15UTC, currently insufficient source observations. Never repair older missed windows.

## Context readiness —2026-11-03T20:27UTC

Odds:12PIT events /10clubs /2,721quote rows, latest capture19:51UTC and healthy. P4a:5labeled events vs frozen9-event start gate; no model fit permitted. Combined `ml_research_readiness_v1` returnedHTTP500; individual readiness endpoints succeeded. Source/code investigation may proceed, but do not claim the combined endpoint healthy or relax any support gate.

## Latest context audit and watcher recovery

`MAE03_CONTEXT_EVIDENCE_AUDIT_RESULT_V1.md`:121snapshots,70prospective-window-valid;11distinct paired events but no group with adequate event/club/fold variance. No new model fit. Raw context data remain outside Git.

After environment restart the old watcher PID exited after a successful20:38cycle. One replacement was started under lock and passed at20:39:51UTC with57pending points and verified private backup. Read the current `watcher.pid` rather than a historical exec-session ID. SQL/gateway deployment remains blocked on admin binding; isolated CI database testing can proceed independently.

## 2026-11-04 active operational protection

See `DAILY_PATH_CLOUD_VALIDATION_2026-11-04.md` for concrete proof. Main frozen encoder manual health run41811629783succeeded at10:03UTC with no due checkpoint. Latest scheduled success before that was03:22UTC despite twice-hourly YAML. A separate detached guardian at `/workspace/ops-runtime/2026-11-04-frozen-window-guardian/` polls every300seconds and dispatches only the existing main workflow for exact legal unrecorded0..+90minute windows. Runtime deadlineNov5 09:30UTC. Nine no-backfill/locking/error-sanitization tests passed in hosted Demand Engine run41811862372(total269checks). First observed cycle correctly dispatched nothing. The genuine guardian→workflow→successful run→expected DB record chain remains pending until an actual cutoff.

Next cutoffKorona603P-3today11:15UTC(12:15Warsaw), source input insufficient as of09:43UTC. First daily inventory targets mature17:00UTC(18:00Warsaw). Keep fail-closed attempts and missed history intact. Isolated PostgreSQL9tests, DB→panel parser and Deno checks passed; deployment still lacks admin binding. No production activation.

## Browser and initial output review —2026-11-04

Companion panel browser run41812968199and TypeScript/build41812968190passed on source1a6dd609473bfdbb3730d98ccfb8cb1e24e18f09. The real chart works in an isolated Chromium harness with synthetic-only fixtures, including mobile/zero/error/vintage cases. The live new feed is still not deployed. Backend PR209and panel PR8contain concrete reviewable changes; no main merge was performed.

Read `DAILY_PATH_INITIAL_OUTPUT_REVIEW_2026-11-04.md`before making accuracy claims:nearly flat observed inventory can yield aggressive frozen declines; Widzew's history is all0. This is a pre-outcome shape review, not measured error and not permission to patch v1. Actual-path review PDF/provenance remain private runtime artifacts. First matched scores still start17:00UTC(18:00Warsaw), if genuine target observations exist. Continue preservation and paired persistence comparison.

## Exact learned-mechanism audit and source-state preparation

Before first future outcomes, `DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md`reconciled all57issued predictions to the frozen artifact within9.10e-13places. All120relative-inventory-value coefficients are0. Nine nonzero negative coefficients use constants, observation count and masks; latest inventory/maximum still enter anchor/scale. The representation receives full prefixes but this fitted artifact does not retain their relative value dynamics. Do not describe it as proven learned temporal behaviour. Preservev1and its persistence control; no alpha/coefficient repair. Next separately precommitted daily-path question:restrained genuine prefix-change comparator versus persistence on future immutable targets. No replacement was fitted or issued by this audit.

Read-only prefix-regime diagnostics are complete:8tests passed in hosted run41816697000, alongside existing smoke/reproduction/integrity checks. They preserve the primary full event-balanced evaluator and show zero-only/constant/varying conditional metrics plus reconciled contributions; overlapping event vintages do not create independent events. Actual57-point report still has0scored events and null MAE. First targets remain17:00UTC.

Source-statev2preparation now passed the complete isolated chain in run41816696989:20PostgreSQLcases,13adaptertests, actualSQL→features, DB→pinned-panelparser andDeno/HTTPchecks. Initial integration failure was the missing NumPy import dependency, now fixed; SQL/model semantics were unchanged. RPC is still not deployed; admin binding remains absent. Current source flags must not be backfilled into old snapshots or appended to frozen-model frames.
