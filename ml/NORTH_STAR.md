# Beyond Ticketing — Product & ML North Star

Last updated: **2026-10-16**

## Single objective

Build the best possible **live demand decision system** for football ticketing.

Beyond must not only forecast final attendance. It must tell the club:

1. where the event is likely to finish;
2. which sector is underperforming or outperforming;
3. what is likely to remain unsold if the current trajectory continues;
4. which commercial action is worth testing — especially price;
5. what happened after the club acted.

The forecasting layer remains the analytical foundation. The product value is created when that forecast becomes a sector-level decision before kickoff.

## Core product question

For every active event and every point in time before kickoff:

> **What is happening, where is the problem/opportunity, what happens if nothing changes, and what should the club test now?**

## What Beyond must estimate

### Event level

1. final demand / attendance;
2. Structural Prior;
3. current live / provisional P50;
4. expected demand trajectory;
5. observed live trajectory;
6. trajectory gap;
7. projected outcome if the current trajectory continues;
8. calibrated uncertainty when available;
9. reason codes / drivers.

### Sector level

For every observable sector:

1. current public availability;
2. sell-through / absorption proxy;
3. short- and medium-window velocity;
4. acceleration / deceleration;
5. expected progress at this point before kickoff;
6. observed progress;
7. trajectory gap;
8. underperforming / on-track / outperforming status;
9. projected final public sell-through / remaining availability if the trajectory continues;
10. confidence and data-quality flags.

Public seat-map inventory is a **demand proxy, not confirmed paid sales**. Sector projections and event attendance must not be forced into a false 1:1 mapping.

## Dynamic pricing is a first-class product capability

The primary intervention Beyond should support is **sector-level dynamic pricing decision support**.

For a sector, Beyond should eventually answer:

> Should the club HOLD, INCREASE or DECREASE the price, what price scenario should it test, and what could that imply for sell-through and revenue?

Before learned elasticity exists, Beyond may use explicitly versioned, assumption-based pricing scenarios. They must be labeled as provisional scenarios, not causal uplift.

Automatic production price changes are not allowed in the MVP:

`auto_price_change_allowed = false`

Canonical product specification:

`ml/SECTOR_DECISION_PRICING_V1.md`

## Model architecture

### 1. Structural Prior

Estimate expected final demand from historical and contextual point-in-time evidence.

### 2. Live Trajectory

Interpret current ticketing evidence:

- public inventory;
- velocity;
- acceleration;
- sector movement;
- scarcity;
- release / replenishment activity;
- anomalies;
- source quality.

### 3. Live Correction

Estimate how current live behaviour should revise the Structural Prior.

Conceptually:

`Live Forecast = Structural Prior + Live Correction`

### 4. Sector Decision Layer

Turn live evidence into:

`sector diagnosis -> no-action projection -> pricing scenario -> recommendation`

### 5. Intervention Measurement

Persist:

`recommendation -> club decision -> execution -> subsequent trajectory -> final outcome -> revenue outcome`

This evidence becomes the training set for learned pricing and intervention models.

## Phase C governance: 20 matches are not a product blocker

The existing 20-independent-completed-match rule remains a **promotion gate for learned live correction**.

It does **not** block:

- sector-level diagnosis;
- provisional / bounded live correction where explicitly labeled;
- no-action continuation projections;
- assumption-based pricing scenarios;
- recommendation display;
- recommendation / execution logging.

It does block claims that a learned correction or learned pricing model is proven better until enough prospective evidence exists.

## Phase E split

### E0 — Decision Support MVP — START NOW

- sector underperformance detection;
- sector no-action projection;
- event no-action projection;
- dynamic-pricing scenario engine;
- dashboard recommendation cards;
- club decision / execution capture;
- no automatic execution.

### E1 — Learned Pricing / Intervention Engine — EVIDENCE-DRIVEN

- learned elasticity;
- intervention uplift estimation;
- expected-value ranking;
- calibrated uncertainty;
- human/commercial guardrails.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong pricing / demand intervention window;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final estimate / calibration.

Early actionability remains first-class.

## Evaluation dimensions

### Forecast quality

- MAE;
- WAPE;
- median absolute error;
- bias;
- stability across clubs / seasons / horizons.

### Live trajectory quality

- trajectory-gap accuracy;
- forecast revision quality;
- incremental uplift over Structural Prior;
- first-detection lead time.

### Sector decision quality

- correctness of sector underperformance direction;
- sector no-action projection error;
- false alarm rate;
- time-to-action;
- stability under release / coverage changes.

### Pricing / intervention quality

Before learned pricing:

- scenario calibration;
- recommendation consistency;
- commercial guardrail adherence;
- club acceptance / rejection;
- outcome tracking completeness.

After evidence matures:

- incremental tickets;
- incremental revenue / contribution;
- ROI;
- price elasticity calibration;
- uplift uncertainty;
- recommendation expected value.

## Validation methodology

- strict point-in-time features;
- no future leakage;
- chronological / rolling-origin evaluation;
- frozen candidate specifications;
- cross-club evaluation;
- reproducible model / assumption versions;
- no hidden post-validation tuning;
- historical validation seasons that have already been inspected must not be relabeled as pristine untouched holdouts;
- prospective 2026/27 evidence is the critical fresh validation source for new learned live / pricing decisions.

T-30 R&D governance:

`ml/T30_RND_GOVERNANCE_V2.md`

## Priority order now

1. keep the five-horizon Structural Prior and live pipeline healthy;
2. build sector-level trajectory diagnosis;
3. build no-action sector/event projections;
4. add price data contract and dynamic-pricing E0 scenarios;
5. show sector/pricing decisions in Event Detail dashboard;
6. log recommendations and real club actions from day one;
7. collect prospective evidence for learned C1 / E1;
8. improve T-30 historical prior in parallel, not as the product critical path;
9. calibrate P10/P50/P90 as evidence supports it.

## Product value statement

**Beyond should tell the club which sector is falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — early enough to change the outcome.**
