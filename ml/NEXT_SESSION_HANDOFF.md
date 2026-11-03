# Beyond Ticketing — Next Session Handoff

Last updated: **2026-11-03**

Status: **DAILY-PATH MVP + LIVE EVIDENCE PROTECTION; MAE-01 FOR ATTENDANCE R&D**

Canonical MAE strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Canonical execution contracts: `ml/EXECUTION_PLAN_CURRENT.md`

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Recorded at 20:01 UTC: 7 local immutable attempts / 57 future-day points / 0 scores, plus verified private Supabase Storage backup and full restore. A bounded host-dependent watcher runs through2026-11-04T17:15Z; its status is `/workspace/ops-runtime/2026-11-03-daily-path/latest-cycle.json`. Inspect it and `watcher.pid` before starting another process. First targets mature2026-11-04T17:00Z. Local/cloud inference is verified; new SQL/gateway/GitHub schedule remain prepared but not deployed/enabled. Panel parser/geometry are verified; full TypeScript check and production build passed in GitHub Actions on the companion panel PR. Local npm access remains blocked. Missing network/management-token requirements are saved as an environment draft, not applied. No private transaction access, production activation or old-model retuning is required.

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

> **MAE-01 — incumbent error decomposition.**

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

# 3. MAE-01 — exact next research deliverable

Build a reproducible incumbent-error decomposition.

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
3. Otherwise execute/continue MAE-01.
4. Use MAE-01 findings to select the next falsifiable hypothesis.
5. Run the smallest useful PIT-safe/event-grouped experiment.
6. Update the scoreboard and progress tracker.
7. Freeze/reject before moving on; do not narratively keep every challenger alive.

The next research question is not "what model should we try?"

It is:

> **What currently causes the largest honest forecast error, and what new information can explain it without leaking the future?**
