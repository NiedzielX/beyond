# Beyond Ticketing — Agent Start Here

Last updated: **2026-11-03**

## Mission

The primary objective is:

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Do not optimize for number of workflows, snapshots, experiments, model complexity or prediction coverage. Those are enabling metrics only.

Operational protection of prospective cutoffs is mandatory, but it is **not the research objective**. The research objective is lower future MAE.

Production remains OFF unless separately reviewed:

- `live_adjustment = 0`
- `production_change = false`

---

## Read in this order

### 1. `ml/MAE_RESEARCH_ROADMAP_V6.md`

Read this first. It is the canonical MAE research strategy.

V6 defines the current error-driven programme:

- MAE-01 incumbent error decomposition;
- MAE-02 structural baseline benchmark;
- MAE-03 residual context modelling;
- MAE-04 trajectory benchmark;
- MAE-05 horizon-specific correction;
- MAE-06 demand-regime and club heterogeneity;
- MAE-07 controlled ablations;
- MAE-08 ensemble/calibrated blend;
- sequence modelling only when simpler evidence justifies the added complexity.

### 2. `ml/EXECUTION_PLAN_CURRENT.md`

Read this second for frozen contracts, prospective evidence rules and the latest recorded operational state.

If a research idea conflicts with a frozen evidence contract, create a **new version / research lane**. Never mutate the frozen lane.

### 3. `ml/PROGRESS_TRACKING.md`

Use this to understand what has already been tried, rejected, frozen or left collecting.

Do not restart a rejected mechanism on the same exposed cohort through cosmetic tuning.

### 4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Read before changing trajectory features, daily cutoffs, sequence representations or trajectory evaluation.

### 5. `ml/NEXT_SESSION_HANDOFF.md`

Use for live operational context and immediate due windows.

Always query live machine state first because dated operational snapshots in markdown can become stale.

### 6. Actual implementation

Then inspect as needed:

- `.github/workflows/`
- `ml/`
- `supabase/sql/`
- `supabase/functions/`
- recent GitHub Actions runs
- live DB state / decision RPCs

The implementation and live DB are the authority for what actually ran. Markdown defines the intended research/evidence contract unless implementation proves the documentation stale.

---

# Working model

Two workstreams run in parallel.

## Workstream A — protect evidence integrity

Before optional research, check whether an immutable P9 / trajectory / Form5 / other precommitted cutoff is due or at risk.

Rules:

1. protect genuine legal cutoffs;
2. never backfill missed prospective windows;
3. fail closed when source semantics are unknown;
4. never loosen frozen eligibility to create a prediction;
5. distinguish `configured`, `workflow succeeded`, and `proven end-to-end in DB`.

This workstream protects truth. It does not replace MAE research.

## Workstream B — actively reduce MAE

Outside imminent evidence windows, follow `ml/MAE_RESEARCH_ROADMAP_V6.md`.

Default research order:

1. **MAE-01 — Error decomposition**: identify where the incumbent loses the most seats of error.
2. **MAE-02 — Structural baseline**: verify the research anchor is genuinely strong.
3. **MAE-03 — Context residuals**: form, standings, opponent, fixture context, odds; squad only after a trustworthy PIT-safe source exists.
4. **MAE-04 — Trajectory**: level, deltas, velocity, acceleration, plateau/surge, density/staleness, curve similarity.
5. **MAE-05 — Horizon-specific corrections**: test whether early and late horizons need different residual logic.
6. **MAE-06 — Club/regime heterogeneity**: investigate club bias and low/normal/near-sellout behaviour without brittle small-sample overfitting.
7. **MAE-07 — Ablations**: structural vs context vs trajectory vs combined, so the source of gain is known.
8. **MAE-08 — Ensemble**: blend only independently useful signals with complementary errors.
9. Test sequence models only when engineered trajectory evidence leaves a justified representation gap.

---

# Mandatory evaluation

Every serious challenger must be compared on the same eligible independent events and report at least:

- event-balanced incumbent MAE;
- event-balanced challenger MAE;
- Delta MAE;
- independent events;
- distinct clubs;
- coverage;
- event improvement rate;
- median event Delta AE;
- P90/worst-event degradation;
- signed bias;
- per-horizon MAE when applicable;
- PIT audit status.

Daily rows from one event are not independent observations.

The experiment scoreboard is research memory; narrative impressions are not.

---

# Promotion path

`event-grouped PIT-safe research -> review -> precommit -> freeze -> prospective shadow -> genuine outcomes -> event-balanced Delta MAE -> risk/business guards -> explicit promotion review`

For the active frozen prospective comparison, the current precommitted business-resolution scale remains:

> **Delta MAE <= -550 seats**

Do not tune toward this number and do not change it after seeing the relevant outcomes.

---

# What not to do

- Do not retune frozen candidates after early future outcomes.
- Do not rewrite missed prospective windows.
- Do not convert unknown/hidden inventory to zero.
- Do not use future standings/results/squad/odds/ticket observations at an earlier cutoff.
- Do not count multiple horizons from one event as multiple independent events.
- Do not add features without a falsifiable error hypothesis.
- Do not add squad/injury data without a trustworthy timestamped source.
- Do not select a model because it is more sophisticated.
- Do not change production automatically from research results.

---

# First question for every next task

Ask:

> **What is the highest-value next action that can honestly reduce future prospective MAE while preserving the validity of already-running evidence streams?**

If an immutable evidence window is at risk, protect it first.

Otherwise continue the highest-value MAE work package — starting with error decomposition rather than another arbitrary feature/model search.
