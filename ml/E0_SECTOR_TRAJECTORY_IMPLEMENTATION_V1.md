# Beyond Ticketing — E0 Sector Trajectory Implementation v1

Last updated: **2026-10-16**  
Status: **ACTIVE / implementation plan**

This document is the canonical implementation state for E0 after C1 v8 was frozen and moved to prospective shadow validation.

Product specification remains:

`ml/SECTOR_DECISION_PRICING_V1.md`

C1 prospective shadow remains separate and unchanged:

`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`

## Current implementation decision

The next product-critical capability is:

`sector state -> sector trajectory gap -> no-action sector projection -> pricing scenario -> recommendation`

C1 v8 must continue collecting prospective evidence in parallel, but E0 does **not** wait for C1 promotion or 20 completed matches.

## Important data discovery — sector data already exists

`public.sector_inventory` is already populated for live events.

The first diagnostic query incorrectly returned zero sector rows because it joined through:

`sector_inventory.event_id`

That field is currently nullable / not the canonical event relationship.

The correct relationship is:

`sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id`

Therefore:

> **Do not use `sector_inventory.event_id` as the E0 ownership key.**

Canonical E0 sector ownership must be derived from the snapshot:

`ticket_event_id + snapshot_id + sector`

This rule must be encoded in every E0 SQL/view/materializer so the zero-sector mistake cannot recur.

## Verified live sector coverage

At the implementation checkpoint, active events already expose substantial sector history, including approximately:

- Lech Poznań: **151 sectors**;
- Pogoń Szczecin: **42 sectors**;
- GKS Katowice: **23 sectors**;
- Wisła Płock: **17 sectors**;
- Zagłębie Lubin: **14 sectors**.

The events also have hundreds of snapshots, so E0 can be built from real live trajectories rather than synthetic sector data.

These counts are runtime observations, not a fixed contract. The implementation must remain dynamic because visible sector coverage can change over time.

## Data semantics

A sector row represents **public inventory / public availability observed by the scraper**.

It does **not** represent confirmed paid sales.

Required vocabulary:

- `current_public_availability`;
- `observed_absorption_proxy`;
- `public_sell_through_proxy`;
- `projected_public_availability_at_kickoff`.

Forbidden interpretation:

- public availability movement = confirmed ticket sales;
- sector projection = final paid attendance;
- sum of sector public availability projections = event attendance P50.

Event forecast and sector public-inventory projection remain different quantities.

## E0.1 — Canonical Sector Trajectory Feature Contract — NEXT

Create a versioned sector trajectory contract, initially:

`sector-trajectory-v1`

Implementation should expose one current row per:

`ticket_event_id + sector + as_of_at`

### Required raw identity

- ticket event ID — derived through `snapshots.ticket_event_id`;
- snapshot ID;
- snapshot captured_at;
- sector name / source identifier;
- current available public inventory.

### Required reference values

For every sector derive:

- first reliable observed availability;
- latest availability;
- maximum observed availability;
- reference availability used by the current calculation;
- first observed timestamp;
- latest observed timestamp;
- observation count.

Reference availability must be versioned and auditable. Do not silently reinterpret an inventory increase as ticket demand.

### Required movement features

Where enough evidence exists:

- absolute availability change;
- public absorption proxy;
- public sell-through proxy;
- velocity over 6h;
- velocity over 24h;
- velocity over 72h;
- velocity over 7d;
- acceleration / deceleration;
- hours to kickoff.

All time-window features must be point-in-time safe.

## E0.2 — Release / Coverage Change Detection

This must be implemented before sector statuses are treated as meaningful.

Sector inventory can rise because inventory was released or because scraper coverage changed.

Track at minimum:

- `inventory_increase_flag`;
- `sector_appeared_flag`;
- `sector_disappeared_flag`;
- `sector_coverage_change_flag`;
- `release_activity_flag`;
- `data_gap_flag`;
- last stable observation timestamp.

### Rule

A sudden increase in availability must **not** automatically be interpreted as negative demand.

When a recent release / coverage anomaly is active:

- status may become `INSUFFICIENT_SIGNAL`; or
- gap/projection remains visible but confidence is reduced and the anomaly is shown explicitly.

## E0.3 — Provisional Expected Sector Progress

Do not wait for a learned sector model.

The first E0 baseline should be **relative to the event's stable public-inventory trajectory**, not a fabricated learned expectation.

Initial provisional method:

1. define a stable sector reference set for the current point in time;
2. calculate aggregate event public-inventory progress over that stable set;
3. calculate each sector's own normalized public-inventory progress;
4. compare sector progress with the event progress expected under proportional absorption.

Conceptually:

`expected sector remaining availability = sector reference availability × event remaining ratio`

Then:

`sector gap = observed remaining availability - expected remaining availability`

Also expose the normalized gap as share of sector reference availability.

This is intentionally an MVP baseline and must be labeled:

`PROVISIONAL_RELATIVE_EVENT_BASELINE`

It answers:

> Is this sector moving materially slower or faster than the event around it?

It does **not** yet claim a learned sector-specific demand curve.

## E0.4 — Sector Status

Target statuses:

- `UNDERPERFORMING`;
- `ON_TRACK`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

Status must use:

- normalized trajectory gap;
- current/recent velocity;
- acceleration/deceleration;
- time to kickoff;
- release / coverage flags;
- observation density;
- confidence.

Do not classify from one absolute availability value.

### Threshold governance

Do not tune status thresholds to final outcomes yet.

First materialize the continuous gap metrics across real active events, inspect their distribution and stability, then freeze a small versioned threshold set for E0.

Threshold changes require an explicit version change.

## E0.5 — No-action Sector Projection

Preferred dashboard wording:

**Projected outcome if current trajectory continues**

For each sector estimate:

- projected public availability at kickoff;
- projected public sell-through proxy;
- current availability;
- projected additional absorption proxy;
- confidence / maturity;
- reason codes.

### MVP projection principle

Use a bounded continuation model based on the sector's recent stable absorption velocity.

Candidate hierarchy:

1. stable 24h velocity when enough observations exist;
2. blended 24h/72h velocity when both are available;
3. 72h / 7d fallback for sparse slower-moving sectors;
4. event-relative fallback when the sector history is insufficient;
5. `INSUFFICIENT_SIGNAL` when a release/coverage anomaly makes continuation unreliable.

Projection must be bounded:

`0 <= projected_public_availability_at_kickoff <= current/reference valid range`

Do not extrapolate negative seats.

Do not describe this as a causal no-intervention counterfactual.

## E0.6 — Event-level No-action Context

Event-level and sector-level outputs must be presented together but not forced into one quantity.

Event-level card:

- Structural Prior P50;
- current production live adjustment — currently zero;
- C1 v8 shadow result where available, clearly `EXPERIMENTAL_SHADOW`;
- event trajectory status;
- projected event outcome if current trajectory continues.

Sector-level card/table:

- public availability trajectory;
- relative sector gap;
- sector no-action availability projection;
- status;
- confidence;
- price scenario when available.

Do not sum sector public inventory into a fake attendance forecast.

## E0.7 — Price Data Contract

Dynamic pricing requires a real price source before a sector recommendation can be shown as anything other than `PRICE_DATA_MISSING`.

Next data audit must establish whether current collectors provide, per sector/category:

- current price;
- currency;
- base / face price;
- price effective timestamp;
- price band / category;
- min/max commercial guardrails;
- price history.

If the scraper does not provide live price data, E0 must support an explicit POC/MVP import/configuration source with source and timestamp.

Never infer a price from sector name or seat availability.

## E0.8 — Assumption-based Dynamic Pricing Scenario Engine

After sector gap + no-action projection + price contract are available, implement E0 scenarios.

Initial configurable grid may contain:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

For every scenario persist/display:

- current price;
- proposed price;
- assumed elasticity / demand response;
- projected public availability/sell-through proxy;
- projected revenue proxy;
- delta vs no-action scenario;
- confidence;
- assumption-set version;
- reason codes.

Required label:

`ASSUMPTION_BASED_SCENARIO`

No learned elasticity is claimed at E0.

`auto_price_change_allowed = false`

## E0.9 — Recommendation Persistence

Create the evidence loop from the beginning.

Persist:

- recommendation ID;
- event ID;
- sector;
- generated_at;
- source sector trajectory observation/version;
- no-action projection;
- current price;
- proposed action / price;
- assumption-set version;
- confidence;
- reason codes;
- decision: `ACCEPTED / REJECTED / SNOOZED / NOT_REVIEWED`;
- executed_at;
- actual executed price/action;
- subsequent sector trajectory;
- final outcome where available.

This dataset becomes the basis for future E1 learned elasticity/intervention models.

## E0.10 — Dashboard

Target repository:

`NiedzielX/BeyondTicketingPanel`

Primary target:

`Event Detail -> Sector Performance & Pricing`

Minimum event summary:

- Structural Prior;
- current trajectory/no-action event result;
- C1 shadow state where applicable;
- biggest underperforming sectors;
- biggest outperforming sectors;
- data freshness.

Minimum sector table:

| Sector | Availability | 24h velocity | Expected progress | Actual progress | Gap | Projected at kickoff | Status | Price | Recommendation | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- |

Expanded sector row:

- trajectory chart;
- availability/release history;
- no-action projection;
- price history;
- pricing scenarios;
- rationale/reason codes;
- data-quality flags.

## Exact implementation order

### Step 1 — Sector data contract and feature materialization

Build `sector-trajectory-v1` from `snapshots -> sector_inventory` using `snapshots.ticket_event_id` as canonical ownership.

Acceptance condition:

- one reproducible point-in-time row per event/sector/as-of;
- active events return non-zero sectors where scraper sector data exists;
- sector counts reconcile with source snapshots;
- no dependency on `sector_inventory.event_id`.

### Step 2 — Release-aware continuous trajectory gap

Implement reference availability, sell-through proxy, velocity, acceleration, event-relative expected progress and continuous gap.

Acceptance condition:

- every gap can be traced to source snapshots;
- inventory increases are flagged, not interpreted as sales reversal;
- no status classification yet needs final attendance.

### Step 3 — Versioned status policy

Freeze E0 status thresholds only after inspecting continuous gap distributions/stability across current active events.

Acceptance condition:

- `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL` is deterministic and versioned;
- recent release/coverage anomalies reduce confidence or force insufficient signal.

### Step 4 — Provisional no-action sector projection

Implement bounded continuation projection with velocity hierarchy and explicit confidence/reason codes.

Acceptance condition:

- projection is PIT-safe;
- no negative availability;
- no claim that public availability equals paid sales;
- anomaly cases fail conservative.

### Step 5 — Read-only E0 dashboard data surface

Expose event/sector summary and trajectory history for `BeyondTicketingPanel`.

Acceptance condition:

- dashboard can display real sector underperformance and projected remaining availability;
- source timestamp/version/reason codes are available.

### Step 6 — Price source audit + contract

Determine available price fields/sources and implement `PRICE_DATA_MISSING` semantics.

### Step 7 — Assumption-based pricing scenarios

Implement configurable E0 scenario engine and commercial guardrails.

### Step 8 — Recommendation / decision / execution persistence

Persist club decisions and outcomes before attempting E1 learning.

### Step 9 — Dashboard recommendation UX

Add pricing recommendation card/scenario comparison to Event Detail.

### Step 10 — Evidence collection for E1

Learn elasticity/intervention effects only after real executed price changes and outcomes exist.

## Parallel work rule

While E0 is implemented:

- C1 v8 remains frozen and collects prospective evidence automatically;
- do not retune or retrain v8 because E0 work is progressing;
- production remains `live_adjustment = 0`;
- E0 sector logic must not depend on C1 reaching 20 prospective events;
- T-30 research remains separate from the E0 critical path.

## Immediate next action

> **Implement Step 1: `sector-trajectory-v1` using `snapshots.ticket_event_id -> sector_inventory.snapshot_id`, then materialize release-aware sector movement features on real active events before defining any status threshold or pricing recommendation.**
