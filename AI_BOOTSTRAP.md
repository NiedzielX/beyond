# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-16**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing any Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation roadmap;
3. `ml/SECTOR_DECISION_PRICING_V1.md` — canonical sector + no-action + dynamic-pricing product contract;
4. `ml/NORTH_STAR.md` — product/ML objective;
5. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md` — orchestration state;
6. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md` — frozen Structural Prior runtime;
7. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md` — learned-model promotion gates;
8. `ml/T30_RND_GOVERNANCE_V2.md` — T-30 R&D validation rules;
9. `growth/GROWTH_EXECUTION_DATA_V2.md` — intervention execution/outcome measurement.

## Critical product direction — DO NOT LOSE THIS

Beyond is **not** primarily a generic campaign recommendation tool.

The primary product output is:

`event -> sector -> trajectory -> no-action projection -> pricing scenario -> recommendation`

For an active event the product should tell the club:

1. **which sector is underperforming or outperforming;**
2. **how far it is from expected trajectory;**
3. **what is projected to remain unsold / where the event is likely to finish if the current trajectory continues;**
4. **what price action is worth testing for that sector;**
5. **what happened after the club acted.**

Generic CRM / paid-media / partner activation can be secondary suggestions. They must not replace sector diagnosis or dynamic-pricing decision support.

Canonical spec:

`ml/SECTOR_DECISION_PRICING_V1.md`

## Dynamic pricing — product rule

Pricing is a first-class intervention.

MVP recommendation per sector:

- `HOLD`;
- `INCREASE`;
- `DECREASE`;
- proposed price / scenario;
- projected sell-through / availability impact;
- projected revenue proxy;
- confidence;
- reason codes;
- assumption/model version.

Before learned elasticity exists, pricing is **assumption-based scenario analysis** and must be labeled as such.

Never change a club's production price automatically:

`auto_price_change_allowed = false`

## No-action forecast semantics

Preferred label:

**Projected outcome if current trajectory continues**

This is a continuation scenario, not a causal proof of what would happen in a literal no-intervention world.

At sector level show public sell-through / remaining availability proxy.

At event level show attendance/demand P50.

Do not force sector public inventory to sum 1:1 to final attendance.

## Public inventory semantics

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

Never write or display scraped availability as if it were paid ticket sales.

Release / replenishment / sector-coverage changes must be accounted for before labeling a sector underperforming.

## Phase C — 20 matches are NOT a product blocker

The existing 20-independent-completed-match rule is a **promotion gate for C1 learned live correction**.

It does not block:

- C0 provisional/scenario decision support;
- sector underperformance detection;
- no-action continuation projections;
- E0 pricing scenarios;
- recommendation display;
- recommendation / execution logging.

Do not tell the user the product must wait for 20 matches before it can work.

## Phase E — starts now

### E0 — Decision Support MVP — START NOW

- sector-level trajectory gap/status;
- sector no-action projection;
- event no-action projection;
- dynamic-pricing scenario engine;
- dashboard sector/pricing recommendation;
- club decision / execution logging;
- no automatic execution.

### E1 — Learned Pricing / Intervention — EVIDENCE-DRIVEN

Later learn:

- price elasticity;
- intervention uplift;
- incremental tickets / revenue / contribution;
- expected value of actions;
- uncertainty.

## Dashboard target

Repository:

`NiedzielX/BeyondTicketingPanel`

Primary page:

`src/pages/EventDetailPage.tsx`

Target block:

**Sector Performance & Pricing**

Minimum table:

`Sector | Current price | Availability | Velocity | Expected progress | Actual progress | Gap | No-action final | Status | Price recommendation | Scenario impact | Confidence`

## Structural Prior state

All canonical horizons have executable frozen current-event runtimes:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled Structural Prior inference is load + predict only; never fit on scheduler runs.

## Historical dataset / validation state

Canonical history:

- Ekstraklasa;
- seasons 2021/22–2025/26;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified historical capacity coverage 100%.

Important governance update:

**2024/25 and 2025/26 are no longer pristine untouched T-30 holdouts.**

They were exposed during controlled T-30 challenger verification on 2026-10-16. Do not relabel them as untouched or repeatedly tune against them.

Use rolling-origin pre-validation and prospective 2026/27 as the critical fresh evidence source.

## T-30 R&D state

Production remains:

`structural-prior-runtime-v1-t30-extra-full`

Controlled v2-v6 challenger work did not justify promotion. T-30 R&D continues in parallel, but it is **not the product critical path**.

Merged diagnostic evidence:

`ml/results/T30_PREVALIDATION_ERROR_AUDIT_V1_2026-10-16.md`

## Growth relationship

Growth measures intervention outcomes:

`Demand signal -> recommendation -> experiment -> execution -> outcome -> incremental tickets/revenue -> ROI`

Dynamic pricing is another intervention family.

Do not collapse sector/pricing decision support into generic Growth campaign reporting.

## Critical rule: do not re-run just to recover context

Do not retrain models, rebuild the five-season feature store, replay imports, or rerun historical benchmarks merely to understand current state.

Re-run only when:

- model code / hyperparameters change;
- feature contract changes;
- historical input/hash changes;
- source-data correction affects benchmark data;
- benchmark protocol changes;
- a new challenger is intentionally evaluated;
- governance explicitly requires a fresh run;
- the user explicitly requests reproduction.

Otherwise read persisted state and query only dynamic rows.

## Immediate work order

When a new session starts, continue here:

1. keep Structural Prior / orchestrator healthy;
2. implement sector-level trajectory gap/status;
3. implement sector no-action projection;
4. define price data contract / ingest;
5. implement E0 assumption-based dynamic-pricing scenarios;
6. persist recommendation / club decision / execution history;
7. show Sector Performance & Pricing in Event Detail;
8. collect prospective 2026/27 evidence for learned C1/E1;
9. continue T-30 R&D in parallel;
10. probabilistic calibration later when evidence supports it.

## One-line cold-start instruction

> **Do not wait for 20 matches to make Beyond useful: show sector underperformance, project the no-action outcome, recommend a pricing scenario with explicit assumptions, log what the club does, and use prospective outcomes to learn the next generation.**
