# Beyond Ticketing — Sector Decision & Dynamic Pricing v1

Status: **canonical product direction / MVP specification**  
Effective: **2026-10-16**

## Why this document exists

Beyond must not stop at an event-level forecast or generic recommendation such as "run CRM" or "increase paid media".

The product must answer, for a live event:

1. **Which sector is underperforming or outperforming?**
2. **By how much is it off the expected trajectory?**
3. **What is the projected final outcome if the club does nothing and the current trajectory continues?**
4. **What pricing action should the club consider for that sector?**
5. **What is the expected scenario impact on tickets / sell-through / revenue, with explicit confidence and assumptions?**

Generic marketing actions may exist as secondary recommendations, but they are not the primary product outcome.

## Product principle

The primary decision unit is:

`event -> sector -> trajectory -> no-action projection -> pricing scenario -> recommendation`

Event-level forecasting remains the anchor, but the dashboard must explain **where** the problem sits and **what commercial lever** can be used.

## Current data semantics

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

Therefore the product must distinguish:

- `public inventory / availability` — what the scraper sees;
- `observed sell-through proxy` — movement inferred from public inventory;
- `actual attendance / paid ticket outcome` — final outcome where a verified source exists.

The system must never present scraped public inventory as confirmed paid ticket sales.

## MVP output per event

### 1. Event-level no-action forecast

Display the best current estimate of the final event outcome if no new intervention is observed and the current demand trajectory continues.

Preferred label:

**Projected outcome if current trajectory continues**

Do not label this as a causal counterfactual. At MVP stage it is a continuation scenario, not proof of what would happen in a world where the club literally does nothing.

Required values:

- Structural Prior P50;
- current provisional / live P50 when available;
- delta vs Structural Prior;
- current trajectory status;
- confidence;
- projected final attendance / demand at event level;
- latest evidence timestamp.

### 2. Sector-level diagnosis

For each visible sector, show:

- sector identifier / name;
- current public availability;
- initial / reference availability where available;
- observed absorption / sell-through proxy;
- 6h / 24h / 72h / 7d velocity where sufficient history exists;
- acceleration / deceleration;
- expected progress for this point before kickoff;
- observed progress;
- trajectory gap;
- status: `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- signal confidence;
- data-quality flags;
- release / sector-coverage-change flags.

Sector underperformance must not be inferred from one absolute inventory number alone. It must be trajectory-aware and release-aware.

## Sector no-action projection

For each sector, Beyond should estimate:

- projected final public sell-through proxy;
- projected final public availability / unsold proxy;
- expected range where possible;
- confidence;
- main drivers.

Example dashboard statement:

> Sector B4 is 18% behind its expected trajectory. If the current trajectory continues, approximately 620 public seats are projected to remain available at kickoff.

This output is allowed before a learned sector model exists, provided it is clearly labeled as a provisional / scenario projection and its assumptions are persisted.

### Event-level reconciliation

Sector-level public-inventory projections and event attendance P50 are different quantities and must not be forced to sum 1:1.

Until a verified mapping between public inventory and paid/final attendance exists:

- sector projection = public sell-through / availability proxy;
- event projection = final attendance / demand P50;
- dashboard explains the difference.

## Dynamic Pricing — MVP objective

Pricing is a first-class intervention in Beyond.

The MVP should answer:

> **Given the current sector trajectory, should the club HOLD, INCREASE or DECREASE the price, and what price scenario should it test?**

Dynamic pricing is initially a **decision-support recommendation**, not an automatic production price change.

`auto_price_change_allowed = false`

## Required pricing input

Per sector / price band, where available:

- current price;
- currency;
- face/base price if different;
- price history with effective timestamps;
- sector / category mapping;
- inventory / availability at the price-change timestamp;
- subsequent trajectory observations;
- any known restrictions / min / max price.

If live price data is unavailable, the dashboard must show `PRICE_DATA_MISSING` rather than fabricate a recommendation.

A manually configured or imported current price may be used in POC/MVP if its source and timestamp are stored.

## Dynamic Pricing E0 — assumption-based scenario engine

We do **not** need to wait for 20 completed matches before showing pricing recommendations.

Before learned elasticity is available, use a versioned assumption-based scenario engine.

The engine may simulate a small pre-approved price grid, for example:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

The exact scenario grid must be configurable by club / competition and subject to commercial guardrails.

For every scenario show:

- proposed price;
- assumed demand response / elasticity assumption;
- projected sector sell-through / remaining availability;
- projected ticket revenue proxy;
- delta vs no-action scenario;
- confidence / maturity label;
- assumption-set version.

The system must not describe these early scenario deltas as causal or learned uplift.

Preferred label:

**Scenario estimate based on current demand signal and provisional elasticity assumptions**

## Initial pricing logic

Pricing recommendations should be driven primarily by sector demand state.

### Underperforming sector

Candidate actions:

- `HOLD` when the gap is small / confidence low;
- `DECREASE` when the sector is materially behind expected trajectory and there is enough time to react;
- consider demand activation as a secondary lever when price should not change.

### Outperforming sector

Candidate actions:

- `HOLD` when sell-through is healthy but not supply-constrained;
- `INCREASE` when the sector is materially ahead of trajectory and scarcity is emerging;
- protect yield rather than discounting.

### On-track sector

Default action:

- `HOLD` unless revenue/yield optimization indicates a safe price increase.

### Insufficient signal

Default action:

- no automated recommendation;
- show `MONITOR / INSUFFICIENT SIGNAL`.

## Recommendation ranking

A pricing recommendation should consider at least:

1. sector trajectory gap;
2. velocity and acceleration;
3. time to kickoff;
4. current availability / scarcity;
5. release / coverage-change flags;
6. signal confidence and data quality;
7. current price and price history;
8. configured commercial price limits;
9. event-level Structural Prior / live forecast context.

Generic CRM / paid media / partner-channel recommendations are secondary and should not replace this sector/pricing analysis.

## Dashboard — Event Detail target

The Event Detail page should contain a prominent **Sector Performance & Pricing** block.

### Event summary

Show:

- Structural Prior;
- Live / provisional P50;
- **Projected outcome if current trajectory continues**;
- event trajectory status;
- confidence;
- biggest sector risks / opportunities;
- projected no-action attendance / demand result.

### Sector table

Recommended columns:

| Sector | Current price | Availability | Velocity | Expected progress | Actual progress | Gap | No-action final | Status | Price recommendation | Scenario impact | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |

A sector row should be expandable to show:

- trajectory chart;
- price history;
- inventory/release history;
- no-action projection;
- price scenarios;
- rationale / reason codes;
- data quality / limitations.

## Decision card example

The primary recommendation card should look conceptually like:

**Sector:** B4  
**Status:** UNDERPERFORMING  
**Gap:** -18% vs expected trajectory  
**Current price:** 90 PLN  
**Projected no-action result:** ~620 public seats remaining at kickoff  
**Recommendation:** Test 85 PLN / -5.6%  
**Scenario:** projected improvement in sell-through and revenue vs no-action  
**Confidence:** Medium  
**Why:** weak 24h velocity + persistent negative trajectory gap + no release anomaly

The exact numbers must come from runtime data/scenario calculations; this is only the product shape.

## Intervention tracking — start immediately

Every recommendation must be persistable even before learned recommendation models exist.

Store:

- recommendation id;
- event id;
- sector id;
- generated_at;
- source signal / trajectory observation id;
- no-action projection at recommendation time;
- current price;
- recommended price / action;
- assumption-set / model version;
- confidence;
- reason codes;
- club decision: `ACCEPTED / REJECTED / SNOOZED / NOT_REVIEWED`;
- executed_at;
- actual executed price/action;
- subsequent sector trajectory;
- final event outcome;
- revenue outcome where available.

This is how Beyond creates the evidence required for a future learned pricing / intervention model.

## Phase C and the 20-match gate

The existing 20-independent-completed-match rule remains useful, but its meaning changes:

**It is a promotion gate for a learned live-correction model, not a blocker for product operation.**

Before that gate is met, Beyond may operate:

- Structural Prior;
- trajectory diagnostics;
- sector underperformance detection;
- no-action continuation projections;
- provisional / bounded live correction where explicitly versioned;
- assumption-based pricing scenarios;
- recommendations and intervention logging.

What must remain gated:

- claiming learned live correction is proven better than Structural Prior;
- automatic promotion of a correction model;
- claiming learned price elasticity / causal uplift without evidence;
- automatic price execution.

## Phase E redefinition

Phase E is no longer "something later after Phase D".

Split it into:

### E0 — Decision Support MVP — START NOW

- sector-level performance diagnosis;
- no-action sector/event projection;
- dynamic-pricing scenario engine with explicit assumptions;
- recommendation display in dashboard;
- decision/execution logging;
- no automatic execution.

### E1 — Learned Pricing / Intervention Engine — LATER, EVIDENCE-DRIVEN

- learn sector-specific / context-specific elasticity;
- learn which interventions improve sell-through, revenue and contribution;
- estimate intervention uplift with uncertainty;
- rank actions by expected value;
- still require commercial guardrails and human review before auto-execution.

## Relationship to Growth

Existing Growth flow remains valuable:

`Demand signal -> recommendation -> experiment -> treatment/holdout -> outcome -> incremental tickets/revenue -> ROI`

Pricing becomes another measurable intervention family.

Where operationally possible, price interventions should use controlled experimentation / holdouts. Where randomization is not feasible, the design must be labeled quasi-experimental or non-causal.

Do not collapse dynamic pricing into generic campaign Growth reporting. Sector trajectory and pricing decision support are first-class product capabilities; Growth provides the measurement framework for intervention outcomes.

## Implementation priority

1. sector-level trajectory gap and status;
2. no-action sector projection;
3. price data contract / ingest;
4. E0 scenario-based pricing recommendation;
5. Event Detail dashboard surface;
6. recommendation / execution persistence;
7. outcome measurement;
8. prospective evidence collection for learned C1 / E1.

## Non-negotiable labels / guardrails

Until learned and validated:

- use `PROVISIONAL`, `SCENARIO`, or `ASSUMPTION-BASED` labels;
- never call scenario uplift causal;
- never claim public inventory equals paid sales;
- never change a club's production price automatically;
- persist the source, timestamp, assumption set and reason codes behind every recommendation.

## One-line product target

> **Beyond should tell the club which sector is falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — while learning from every decision and outcome.**
