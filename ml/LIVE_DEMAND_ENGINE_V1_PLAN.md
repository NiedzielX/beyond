# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-16**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1 — Learned Live Correction: EVIDENCE-GATED**  
> **Phase E0 — Sector Decision & Dynamic Pricing MVP: START NOW**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Bounded / versioned continuation logic, not promoted ML | **START NOW** |
| C1 — Learned Live Correction | Train / evaluate live residual correction | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector Decision & Dynamic Pricing | Sector diagnosis, no-action projection, pricing scenarios, dashboard | **START NOW** |
| E1 — Learned Pricing / Intervention | Learned elasticity and intervention uplift | **EVIDENCE-GATED** |

Canonical product direction:

`ml/SECTOR_DECISION_PRICING_V1.md`

## Product purpose

Beyond must continuously answer:

1. **Where is the event likely to finish?**
2. **Which sector is underperforming or outperforming?**
3. **What happens if the current trajectory continues and the club does nothing new?**
4. **What pricing action should the club consider for that sector?**
5. **What happened after the club acted?**

Generic marketing recommendations are secondary. The primary decision unit is:

`event -> sector -> trajectory -> no-action projection -> pricing scenario -> recommendation`

## Current forecasting stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> shadow revision -> first-detection/revision audit`

Current production still has:

`live_adjustment = 0`

for the promoted learned layer.

This does **not** prevent an explicitly labeled provisional decision-support layer from showing continuation scenarios and pricing recommendations.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong pricing / demand intervention;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final forecast / calibration.

## Phase A — DONE

Canonical feature contract:

`live-trajectory-v1.1`

Already includes the building blocks needed for sector decisions:

- point-in-time public inventory;
- multi-window velocity;
- acceleration;
- sector absorption / release / coverage changes;
- inventory normalization;
- quality and gap telemetry;
- anomaly semantics;
- exact checkpoint readiness.

Canonical evidence store:

`private.live_trajectory_feature_snapshots_v1`

## Phase B — DONE

All five Structural Prior checkpoints are executable:

- T-30: `structural-prior-runtime-v1-t30-extra-full`;
- T-14: `structural-prior-runtime-v1-t14-hist-base`;
- T-7: `structural-prior-runtime-v1-t7-gbr-base`;
- T-3: `structural-prior-runtime-v1-t3-hist-full`;
- T-1: `structural-prior-runtime-v1-t1-hist-full`.

Trajectory gap statuses:

- `UNDERPERFORMING`;
- `ON_TRACK`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

Confidence:

- `NONE`;
- `LOW`;
- `MEDIUM`;
- `HIGH`.

Public inventory remains a **demand proxy, not confirmed paid sales**.

## Phase C — split into C0 and C1

### C0 — Provisional live decision layer — START NOW

Purpose: make the product operational before the learned-correction evidence gate is met.

Allowed:

- continuation / no-action event projection;
- explicitly bounded and versioned provisional live adjustment if needed;
- sector trajectory diagnosis;
- reason codes;
- dashboard display.

Required labels:

- `PROVISIONAL`;
- `SCENARIO`;
- `CURRENT TRAJECTORY CONTINUES`.

C0 must not claim that a learned live model has proven uplift.

### C1 — Learned Live Correction — EVIDENCE-GATED

Target:

`live_target_residual = actual_attendance - structural_prior_p50`

The existing 20-independent-completed-match rule remains a **promotion gate** for C1.

It is no longer a blocker for operating C0 or E0.

Promotion still requires:

- sufficient independent completed matches;
- challenger MAE below incumbent;
- positive uplift;
- frozen evidence package;
- mandatory human review;
- no automatic activation.

## Phase D — Probabilistic

Later:

- P10/P50/P90;
- pinball loss;
- empirical coverage;
- horizon-specific calibration.

Do not fabricate confidence intervals before calibration.

## Phase E — split into E0 and E1

### E0 — Sector Decision & Dynamic Pricing MVP — START NOW

This is now part of the near-term product, not a distant downstream layer.

#### E0.1 Sector-level trajectory

For every observable sector:

- current availability;
- absorption / sell-through proxy;
- velocity / acceleration;
- expected progress;
- observed progress;
- trajectory gap;
- status / confidence;
- release / coverage / data-quality flags.

#### E0.2 Sector no-action projection

Estimate:

- projected final public sell-through proxy;
- projected public seats remaining at kickoff;
- confidence / assumptions.

Preferred product wording:

**Projected outcome if current trajectory continues**

Do not call this a causal counterfactual.

#### E0.3 Event no-action projection

Display:

- Structural Prior P50;
- current live/provisional P50;
- delta vs Structural Prior;
- projected final event demand / attendance if current trajectory continues;
- latest evidence timestamp.

Sector public-inventory projection and event attendance P50 are different quantities and must not be forced to sum 1:1.

#### E0.4 Dynamic pricing scenario engine

Pricing is a first-class recommendation.

Per sector / price band, where price data exists, evaluate configurable scenarios such as:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

For each scenario show:

- proposed price;
- elasticity / demand-response assumption;
- projected sell-through / remaining inventory proxy;
- projected revenue proxy;
- delta vs no-action;
- confidence / maturity;
- assumption-set version.

Before learned elasticity exists, label the result:

**Scenario estimate based on current demand signal and provisional elasticity assumptions**

No automatic production price changes:

`auto_price_change_allowed = false`

#### E0.5 Recommendation tracking

Persist from day one:

- event / sector;
- recommendation time;
- no-action projection;
- current price;
- recommended action / price;
- reason codes;
- assumption/model version;
- club decision;
- execution time;
- actual executed price/action;
- later sector trajectory;
- final outcome;
- revenue outcome where available.

This creates the training evidence for E1.

### E1 — Learned Pricing / Intervention Engine — EVIDENCE-GATED

Later, learn:

- price elasticity;
- context-specific intervention response;
- expected incremental sell-through;
- incremental revenue / contribution;
- uncertainty;
- ranking of actions by expected value.

Where possible, use randomized holdouts. Otherwise explicitly label quasi-experimental / non-causal designs.

## Relationship to Growth

Existing Growth measurement remains valid:

`Demand signal -> recommendation -> experiment -> treatment/holdout -> outcome -> incremental tickets/revenue -> ROI`

Pricing becomes a measurable intervention family.

Growth does not replace sector diagnosis or dynamic-pricing decision support. It measures what happened after an intervention.

Relevant docs:

- `growth/GROWTH_MEASUREMENT_V1.md`;
- `growth/GROWTH_EXECUTION_DATA_V2.md`.

## Dashboard target

Primary surface:

`NiedzielX/BeyondTicketingPanel -> EventDetailPage`

Add a **Sector Performance & Pricing** block.

Minimum sector table:

| Sector | Current price | Availability | Velocity | Expected progress | Actual progress | Gap | No-action final | Status | Price recommendation | Scenario impact | Confidence |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|

Expandable sector detail:

- trajectory chart;
- price history;
- release history;
- no-action projection;
- price scenarios;
- rationale;
- data quality.

## Immediate implementation sequence

1. verify first naturally due T-1 and keep five-horizon production healthy;
2. implement sector-level trajectory-gap/status contract;
3. implement sector no-action projection;
4. define price data contract / ingest and `PRICE_DATA_MISSING` semantics;
5. implement assumption-based dynamic-pricing E0 scenarios;
6. persist recommendation / club decision / execution history;
7. expose Sector Performance & Pricing in Event Detail dashboard;
8. continue prospective evidence collection for learned C1/E1;
9. continue T-30 R&D in parallel — not as the product critical path;
10. calibrate probabilistic outputs when enough evidence exists.

## Validation rule after 2026-10-16

2024/25 and 2025/26 have been inspected in T-30 R&D and must not be described as pristine untouched holdouts for future T-30 challenger cycles.

Use:

- rolling-origin pre-validation for structural R&D;
- exposed historical seasons only as fixed regression evidence where appropriate;
- prospective 2026/27 as critical fresh OOS evidence for new learned live / pricing decisions.

Governance:

`ml/T30_RND_GOVERNANCE_V2.md`

## Product target

> **Beyond should tell the club which sector is falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — while learning from every real decision and outcome.**
