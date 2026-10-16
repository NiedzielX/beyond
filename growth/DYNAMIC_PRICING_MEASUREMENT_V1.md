# Beyond Growth — Dynamic Pricing Measurement v1

Status: **product measurement contract / not automatic execution**  
Effective: **2026-10-16**

Canonical decision spec:

`ml/SECTOR_DECISION_PRICING_V1.md`

## Purpose

Dynamic pricing starts as assumption-based decision support, but every real price decision should generate evidence that can later support learned price elasticity and intervention uplift.

Target learning loop:

`sector signal -> price recommendation -> club decision -> price execution -> subsequent trajectory -> final sell-through/revenue -> elasticity evidence`

## MVP pricing recommendation

Before learned elasticity exists, recommendations are scenario-based and versioned.

Example scenario grid:

- -10%;
- -5%;
- HOLD;
- +5%;
- +10%.

The grid must be configurable and constrained by club commercial rules.

Every scenario stores:

- current price;
- proposed price;
- percentage change;
- assumption-set version;
- assumed elasticity / demand-response rule;
- projected sell-through / availability proxy;
- projected revenue proxy;
- no-action projection;
- confidence;
- reason codes.

## Required execution evidence

When the club changes price, capture:

- event id;
- sector / price-band id;
- recommendation id where applicable;
- old price;
- new price;
- currency;
- effective timestamp;
- executed-by source / mode;
- availability immediately before change;
- trajectory state immediately before change;
- subsequent availability checkpoints;
- final public availability / sell-through proxy;
- final attendance where verified;
- revenue outcome where available.

## Measurement designs

### 1. Controlled randomized pricing test — strongest where operationally possible

Use only when the club/ticketing setup can support a valid and commercially acceptable randomized design.

Potential assignment units depend on the system and club policy and must be explicitly defined. Never assume customer-level price discrimination is acceptable or technically possible.

### 2. Matched-sector / matched-event comparison

Compare a price-changed sector/event with a pre-registered comparable sector/event where price is held.

Label as quasi-experimental.

### 3. Staggered / time-series intervention

Compare trajectory before and after a price change with explicit controls for time-to-kickoff, release activity and other concurrent interventions.

Label as quasi-experimental unless a stronger design exists.

### 4. Descriptive-only

When there is no credible comparison, still log the action and subsequent trajectory but do not call the observed difference causal uplift.

## Elasticity semantics

Future learned elasticity should estimate a context-conditional relationship such as:

`relative demand change / relative price change`

but must account for at least:

- time to kickoff;
- sector scarcity / availability;
- event demand level;
- Structural Prior / live forecast;
- baseline sector trajectory;
- opponent / event context;
- simultaneous campaigns / interventions;
- release / replenishment changes;
- price history.

Do not estimate elasticity from raw before/after change alone without time and demand context.

## Primary outcomes

Sector-level:

- sell-through proxy;
- remaining public availability;
- velocity after price change;
- trajectory-gap improvement;
- revenue proxy / actual revenue where available.

Event-level:

- final attendance / demand;
- total ticket revenue;
- contribution where costs are known.

## Recommendation quality metrics

Before a learned pricing model exists:

- recommendation acceptance rate;
- execution rate;
- scenario calibration;
- direction correctness;
- data-quality coverage;
- post-action trajectory movement.

After learned elasticity exists:

- elasticity calibration;
- expected vs actual sell-through change;
- expected vs actual revenue change;
- incremental revenue / contribution;
- regret vs alternative action where estimable;
- uncertainty calibration.

## Guardrails

- no automatic price execution in MVP;
- do not claim causal uplift from descriptive before/after movement;
- store every assumption/model version;
- preserve exact timestamps;
- account for release / sector-coverage changes;
- maintain club-configured min/max price and commercial restrictions;
- do not fabricate price data when missing.

## Relationship to existing Growth

Existing Growth v2 ITT measurement remains appropriate for campaign experiments.

Dynamic pricing may use a different experimental unit and should not be forced into a customer-level treatment/holdout shape when the commercial system cannot support it.

However the common principle remains:

> **Beyond should measure what happened after a recommendation instead of assuming that the recommendation caused the result.**

## Promotion path

### E0

Assumption-based scenarios + human decision + full logging.

### E1

Learned elasticity / pricing response after enough clean executed interventions exist.

A learned pricing model must remain shadow/challenger until its prospective evidence shows stable value under the agreed governance process.
