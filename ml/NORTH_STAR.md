# Beyond Ticketing — Product & ML North Star

Last updated: **2026-10-18**

## Single objective

Build the best possible **live demand decision system** for football ticketing.

Beyond must not only forecast final attendance. It must tell the club:

1. where the event is likely to finish;
2. which sector / price area is underperforming or outperforming;
3. what is likely to remain publicly available if the current trajectory continues;
4. which commercial action is worth testing — especially price;
5. eventually, what happened after the club acted.

The forecasting layer remains the analytical foundation. Product value is created when that forecast becomes a useful decision before kickoff.

## Core product question

For every active event and every point in time before kickoff:

> **What is happening, why is it happening, where is the problem/opportunity, what happens if nothing changes, and what should the club test now?**

## Forecasting architecture

### 1. Historical Structural Prior

Estimate expected final demand from historical point-in-time evidence.

### 2. Current-season adjustment

Adapt the long-term baseline to the club's current season reality:

- recent home attendance/demand level;
- current season above/below historical norm;
- recency-weighted evidence.

### 3. Match context

Explain why this particular fixture should differ from the club baseline:

- opponent attractiveness / strength;
- form / league position;
- future fixture attractiveness;
- fixture cannibalization and congestion;
- reliable point-in-time squad context where available.

### 4. Live demand trajectory

Interpret current ticketing evidence:

- public inventory;
- velocity;
- acceleration;
- sector / price-area movement;
- scarcity;
- release / replenishment activity;
- anomalies;
- source quality.

### 5. Live correction

Estimate how reliable current live behaviour should revise the Structural Prior.

Conceptually:

`Live Forecast = Structural Prior + reliable live correction`

The official T-30 / T-14 / T-7 / T-3 / T-1 horizons remain evaluation checkpoints. The internal forecast should ultimately be able to revise after any meaningful new snapshot.

## Sector / price-area decision layer

Current implemented direction:

`sector diagnosis -> no-action projection -> real price-area scenario -> guarded recommendation`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**. Sector projections and event attendance must not be forced into a false 1:1 mapping.

## Dynamic pricing

Dynamic pricing decision support is a first-class product capability.

Current E0 supports assumption-based scenarios and guarded recommendations. It does **not** claim learned elasticity or causal uplift.

Automatic production price changes are not allowed:

`auto_price_change_allowed = false`

Mixed-price sectors must be split into real price areas instead of using a fake weighted executable price.

## Current evidence boundary

Historical Structural Prior is mature and benchmarked.

C1 v8 is still `EXPERIMENTAL_SHADOW`.

As of 2026-10-18:

- prospective prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- there is no confirmed prospective live MAE yet.

Development replay around ~2.0k–2.7k is promising evidence, not production accuracy.

## Validation methodology

- strict point-in-time features;
- no future leakage;
- event is the independent evaluation unit;
- no random snapshot-row split across the same events;
- chronological / rolling-origin evaluation;
- frozen candidate specifications;
- no hidden post-validation tuning;
- historical periods already inspected must not be relabeled pristine untouched holdouts;
- prospective 2026/27 evidence remains the critical fresh validation source.

### Immediate historical unseen-event test

Before more model complexity, run:

1. **Leave-One-Event-Out** with the tested event excluded from fitting/tuning;
2. **chronological walk-forward**;
3. strict reconstruction of only the features available at each historical forecast timestamp;
4. paired comparison of Structural Prior vs Live/C1 vs final selection policy.

Goal: establish whether the current live model is actually closer to ~2k, ~3k or worse on unseen historical events.

## Business horizon priority

1. **T-30** — planning / major intervention;
2. **T-14** — strong pricing / demand intervention window;
3. **T-7** — tactical optimisation;
4. **T-3** — late adjustment;
5. **T-1** — final estimate / calibration.

Early actionability remains first-class even though live reasoning should become continuous between these checkpoints.

## Evaluation dimensions

### Forecast quality

- MAE;
- WAPE;
- median absolute error;
- bias;
- worst-event degradation;
- stability across clubs / seasons / horizons.

### Live trajectory quality

- forecast revision quality;
- incremental uplift over Structural Prior;
- first-detection lead time;
- stability under release / coverage changes.

### Sector decision quality

- correctness of underperformance direction;
- sector no-action projection error;
- false alarm rate;
- time-to-action;
- price-area recommendation consistency.

### Pricing / intervention quality

Before learned pricing:

- scenario consistency;
- guardrail adherence;
- recommendation stability;
- explicit separation of simulated vs observed outcomes.

After real intervention evidence matures:

- incremental tickets;
- incremental revenue / contribution;
- ROI;
- price elasticity calibration;
- uplift uncertainty;
- recommendation expected value.

## Current development order

Canonical roadmap:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

Priority order:

1. **validate current model with LOEO + chronological walk-forward**;
2. strengthen **current-season adjustment**;
3. expand **match context**, especially future-fixture cannibalization and reliable squad context;
4. develop **continuous live demand correction**;
5. tune historical **Structural Prior** last;
6. collect prospective C1 evidence in parallel without retuning frozen v8;
7. keep E0 pricing assumption-based / human-reviewed until real intervention evidence exists;
8. calibrate probabilistic P10/P50/P90 when the evidence supports it.

## Product value statement

**Beyond should combine historical expectation, current-season reality, match context and continuously observed live demand to tell the club where an event is heading — then convert that signal into safe sector and price-area decisions early enough to change the outcome.**
