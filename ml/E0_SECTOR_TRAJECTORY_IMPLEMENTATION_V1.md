# Beyond Ticketing — E0 Sector / Price-area Decision Support v1

Last updated: **2026-10-18**  
Status: **IMPLEMENTED / RUNNING**

This document used to be the E0 implementation plan. The core E0 path is now implemented, so this file records the current contract and remaining evidence boundary rather than presenting E0 as the next build.

Canonical product specification:

`ml/SECTOR_DECISION_PRICING_V1.md`

Current forecasting-quality roadmap:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

## Implemented flow

`sector state -> sector trajectory gap -> no-action sector projection -> real price-area mapping -> pricing scenario -> guarded recommendation`

E0 does **not** wait for C1 promotion or the 20-match C1 gate.

## Canonical sector ownership

The canonical relation remains:

`sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id`

Do **not** use `sector_inventory.event_id` as the ownership key.

A sector observation is identified through the snapshot and belongs to the ticket event resolved from `snapshots.ticket_event_id`.

## Data semantics

Sector and price-area observations represent **public inventory / public availability observed by the scraper**.

They do **not** represent confirmed paid sales.

Use:

- `current_public_availability`;
- `observed_absorption_proxy`;
- `public_sell_through_proxy`;
- `projected_public_availability_at_kickoff`.

Do not claim:

- every disappearing seat is a paid sale;
- sector projection equals final attendance;
- sum of sector projections equals event attendance P50.

## Implemented capabilities

### 1. Sector trajectory

Implemented PIT-safe sector history and current state derived from source snapshots.

Signals include:

- current/reference availability;
- public absorption / sell-through proxy;
- short/medium-window movement;
- trajectory direction;
- release / coverage / data-quality handling;
- time to kickoff.

### 2. Relative sector gap and status

Implemented event-relative diagnosis with statuses:

- `UNDERPERFORMING`;
- `ON_TRACK`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

The status layer is deterministic/versioned and must not interpret release activity as ordinary negative demand.

### 3. No-action sector projection

Implemented bounded continuation projection:

**Projected outcome if current trajectory continues**

Output includes projected public availability at kickoff with confidence/reason semantics.

This is a continuation scenario, not a causal counterfactual.

### 4. Roboticket price evidence

Implemented append-only pricing evidence for supported Roboticket events:

- sector -> `priceAreaId` -> availability;
- `priceAreaId` -> price type -> real observed price;
- price-area name;
- price-type name;
- currency;
- observation timestamp.

Never infer missing prices from sector name or availability.

### 5. Mixed-price sector handling

A sector may contain multiple price areas with materially different real prices.

Current rule:

- never recommend a fake weighted sector price as an executable price;
- split such sectors into their real Roboticket price areas;
- make the detailed pricing decision at `priceAreaId` level.

Example pattern:

`A2 -> Czapczyka price area + Silver price area`

Each price area keeps its own observed base price and recommendation.

### 6. E0 assumption-based scenario engine

Supported scenario grid:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

Maturity label:

`ASSUMPTION_BASED_SCENARIO`

Current E0 does **not** claim learned elasticity.

### 7. Commercial safety guards

Active price actions are guarded by, among other checks:

- real resolvable base price;
- sufficient projected future volume;
- minimum modeled incremental effect vs HOLD;
- trend/status consistency;
- mixed-price sector split before executable recommendation.

`OUTPERFORMING + WEAKENING` does not trigger an automatic increase recommendation.

### 8. Human review only

Automatic production price changes are forbidden:

`auto_price_change_allowed = false`

Recommendations are decision support only.

### 9. Dashboard

Implemented in:

`NiedzielX/BeyondTicketingPanel`

Primary surface:

`Event Detail -> Sector Performance & Pricing`

The UI can show:

- real sector labels where available;
- sector status and no-action projection;
- current real price;
- `DECREASE / HOLD / INCREASE / MONITOR`;
- recommended price where actionable;
- confidence / reason codes;
- individual price-area lines for mixed-price sectors.

## RLS-safe current surfaces

Current product reads sanitized dashboard caches rather than exposing heavy internal calculation paths directly to the browser.

Price-area recommendation cache is refreshed after the Roboticket and sector decision cycles.

## What is deliberately NOT implemented yet

### Club decision / execution workflow

`ACCEPTED / REJECTED / SNOOZED / EXECUTED` workflow is intentionally deferred.

For demos we may simulate:

`Beyond recommendation -> simulated club action -> simulated/observed trajectory outcome`

But simulated uplift must be labeled **simulated** and must never be presented as measured causal club impact.

### Learned elasticity / causal uplift

Not implemented / not proven.

Future E1 requires real intervention evidence or a defensible experimental design before claiming:

- learned elasticity;
- incremental tickets;
- incremental revenue;
- causal ROI.

## Current product-development implication

E0 is no longer the main engineering blocker.

The active forecasting priority is now:

1. strict LOEO + chronological walk-forward validation of the current attendance model;
2. stronger current-season adjustment;
3. richer match context and fixture cannibalization;
4. continuous live demand correction;
5. Structural Prior tuning last.

See:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

## Non-negotiable rules

- public inventory is not paid sales;
- no fake price when price data is missing;
- no fake weighted executable price for mixed-price sectors;
- no causal uplift claim from an assumption-based scenario;
- human review remains required;
- `auto_price_change_allowed = false`;
- event attendance forecast and sector inventory projection remain separate quantities.
