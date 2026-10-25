# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start rules and current state;
2. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md) — **latest operational handoff: main vs active branch vs live Supabase**;
3. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md) — **exact next work order**;
4. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md) — canonical status snapshot;
5. [`ml/MAE_RESEARCH_ROADMAP_V4.md`](ml/MAE_RESEARCH_ROADMAP_V4.md) — literature-grounded MAE-first strategy;
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — detailed forecasting state;
7. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — experiment / CI rules;
8. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) and [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) when touching live/promotion logic.

Do **not** start from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with point-in-time-safe, reproducible evidence.**

Complexity is not the objective. Lower future MAE is.

Current mode: **representation-first, not tuning-first**.

## Current operational warning

Active development branch:

`ml/p9-p11-execution-2026-10-24`

It contains **two active implementation slices** that must not be recreated from scratch:

- **P9a target-free T-24/T-48 booking-curve freeze/export harness**;
- **P11a v2 genuine PIT odds capture**.

Branch reconciliation warning:

- branch vs `main`: **diverged**;
- branch is currently **31 commits ahead** and **13 commits behind** `main`;
- do **not** blindly merge, force-push, or recreate the implementation;
- reconcile/rebase carefully and preserve newer `main` work before opening/merging a PR.

The live Supabase project is temporarily **ahead of `main` for both P9a/P11a source code**:

- P9a input/label RPCs are live;
- Edge Function `p9a_booking_curve_export_v1` is ACTIVE v1;
- P11 v2 DB contract is live;
- Edge Function `p11_odds_capture_v2` is ACTIVE v2;
- genuine P11 v2 odds rows remain `0`;
- no automatic P11 odds schedule is enabled.

P9a target-free export currently exposes:

- T-24: `18` target events / `19` reference events;
- T-48: `15` target events / `19` reference events;
- `target_values_used=false`;
- no post-cutoff target snapshots.

This is freeze infrastructure only — it does **not** mean a P9 learner is trained or labels may be opened.

P11 expects external secret `THE_ODDS_API_KEY`; its presence must be configured/verified before the first genuine capture.

Read `ml/NEXT_SESSION_HANDOFF.md` before touching either area.

## Current MAE workstreams

### P9 — Booking Curve / Trajectory Shape

Highest-priority live representation gap:

`normalized PIT trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual`

Current full-168h reference coverage: **4/9**. Do not fit the first learnable full-window P9 model before the gate and a separate learner precommit.

P9a already provides target-free T-24/T-48 freeze tooling. After branch reconciliation, verify the main freeze audit/manifests; keep `target_values_opened=false` and `model_training_performed=false` until a separate learner/comparator precommit.

### P10 / P10b — pooled horizon

Closed for the fixed pooled-HGB architecture.

- P10 beat the same weaker local HGB by `63.47` MAE seats;
- P10b lost to frozen Pre-Live v3 by `147.51` MAE seats;
- do not retune this architecture after observing the result.

### P11 — Match Attractiveness / Commercial Context

Priority:

1. genuine PIT market odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / attention later.

P11a v2 captures raw bookmaker-level 1X2 quotes append-only and derives an as-known de-vigged market consensus. No closing-odds backfill is allowed.

### Governance v2

A small positive point gain is not automatically a robust advance.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

`ROBUST_RESEARCH_ADVANCE` requires a predeclared **business-derived minimum meaningful MAE improvement**. Do not infer that threshold from the experiment being judged.

## Current frozen/data-bound gates

Always query fresh:

`public.ml_research_readiness_v1()`

Latest recorded checkpoint: **2026-10-25 10:18 UTC**.

- Long72: `90` reproducible rows, `0` genuine scored events;
- P7 Long168: **8/9**, still closed;
- P4a: `5` READY events, `0` genuine labels, gate `>=9 labeled + >=3 distinct labeled spacing values`;
- P9 full-168h: **4/9**;
- P11a v2: `0` genuine odds events.

Important: event 6 was expected to enter the P7 Long168 window, but canonical readiness is still 8/9. The next session must **diagnose event 6 readiness before running any P7 experiment**.

## Explicit next-session handoff — current status and open questions

The next chat should **continue from this state, not restart research design**.

### 1. P7 Long168 — unexpected 8/9 is the first diagnostic

Expected behaviour was that event `6` (Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30 UTC`) would become the ninth Long168 event after entering the `<=168h` window.

Canonical readiness is nevertheless still **8/9**.

Before executing P7, determine exactly why event 6 is absent. Check, in this order:

1. whether a genuine snapshot exists inside the required `72 < h <= 168` window;
2. whether the Long168 exporter selects that snapshot/event;
3. whether bucket/identity/deduplication logic excludes it;
4. whether `public.ml_research_readiness_v1()` is using the same eligibility semantics as the frozen P7 harness.

Do **not** lower the `9`-event gate and do **not** run P7 from the expected clock time alone.

### 2. Long72 / P4a labels — possible upstream outcome-data delay

Despite weekend matches approaching/being played, the latest recorded state still shows:

- Long72 genuine scored events: `0`;
- P4a genuine labels: `0`.

This may simply reflect timing of upstream actual-attendance ingestion, but it needs verification before assuming the scoring pipeline is broken.

Next session should inspect:

- `ticket_event_outcomes` / home-history actual attendance availability for completed events;
- outcome sync cron health;
- prospective score attachment after actual attendance appears.

Do not retune frozen Long72/P4a from early labels.

### 3. P9/P9a — infrastructure exists; learner is still intentionally blocked

Do not rebuild trajectory infrastructure.

Current facts:

- full-window P9 reference coverage remains `4/9` at 168h;
- target-free T-24/T-48 P9a freeze/export infrastructure is already live;
- T-24 currently has `18` target / `19` reference events;
- T-48 currently has `15` target / `19` reference events;
- labels have not been opened for learner selection;
- no P9 learnable residual model is precommitted yet.

Open question is **not** “which model should we tune now?”. It is whether/when the data supports a separately precommitted booking-curve learner without compromising PIT evidence.

### 4. P11a odds — capture infrastructure is ready, evidence is not

Current implementation already provides:

- raw bookmaker-level append-only 1X2 storage;
- provider-event / capture-batch lineage;
- verified alias + kickoff-tolerance mapping;
- fail-closed ambiguous mapping;
- bookmaker-level de-vigging;
- deterministic as-known consensus;
- target-free readiness;
- no in-play capture;
- no automatic schedule.

Current evidence remains `0` genuine P11 v2 observations.

Before first capture:

1. verify whether `THE_ODDS_API_KEY` is actually configured in Supabase Edge Function secrets;
2. run one manual capture first;
3. inspect provider team naming and add only **verified** aliases if mapping fails;
4. verify bookmaker count / market completeness / kickoff alignment;
5. only after genuine PIT coverage exists define a separate model precommit.

Do **not** use closing odds or historical provider backfill as if they had been known at an earlier forecast cutoff.

### 5. Branch/live/main reconciliation is a real engineering risk

There are currently three states:

- `main` — canonical repository state;
- `ml/p9-p11-execution-2026-10-24` — active development branch, diverged from main;
- live Supabase — already contains P9a/P11a components that are not fully represented by current `main` source.

The next chat must reconcile these deliberately. Do not assume “live == main” and do not overwrite live contracts with older source during deployment.

### 6. Governance v2 still has one intentional unresolved business input

The minimum practically meaningful `ΔMAE` is **not defined yet**.

This is intentional. Do not invent `100 seats`, `3%`, or derive a threshold from challenger results.

Until the threshold is derived from downstream operational/business decisions, a positive result may at most be interpreted as:

`POINT_GAIN_UNCERTAINTY_LIMITED`

and not `ROBUST_RESEARCH_ADVANCE`.

### 7. Closed loops stay closed

Do not spend the next session reopening:

- P10/P10b pooled-HGB tuning;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- post-hoc calibration on already inspected evidence.

New work should add genuinely new information/representation or process new prospective evidence.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until an explicit reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
