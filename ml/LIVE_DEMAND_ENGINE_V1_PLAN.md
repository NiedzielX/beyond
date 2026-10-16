# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-16**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector Decision & Dynamic Pricing MVP: ACTIVE IMPLEMENTATION**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Continuation logic / sector decisions | **ACTIVE** |
| C1-alpha | Frozen v2+v8 package + prospective pre-outcome evidence + scoring | **LIVE** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient fresh evidence | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector Decision & Dynamic Pricing | Sector trajectory, no-action projection, pricing scenarios, dashboard | **ACTIVE — CURRENT BUILD PATH** |
| E1 — Learned Pricing / Intervention | Learned elasticity / intervention uplift | **EVIDENCE-GATED** |

Canonical state:

- `ml/CURRENT_MODEL.md`;
- `AI_BOOTSTRAP.md`;
- `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
- `ml/E0_SECTOR_TRAJECTORY_IMPLEMENTATION_V1.md`;
- `ml/C1_MODEL_TOURNAMENT_V1.md`;
- latest `ml/results/C1_ALPHA_*.md`.

## Product purpose

Beyond must continuously answer:

1. where the event is likely to finish;
2. whether live evidence is strong enough to revise the Structural Prior;
3. which sectors are underperforming / outperforming;
4. what happens if the current trajectory continues;
5. what pricing action should be considered;
6. what happened after the club acted.

Primary decision unit:

`event -> sector -> trajectory -> expert reliability -> no-action projection -> pricing scenario -> recommendation`

## Production forecasting stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> decision layer`

Current promoted learned correction:

`live_adjustment = 0`

v8 remains separate `EXPERIMENTAL_SHADOW` evidence and does not write production forecast values.

## Structural Prior

All five horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled inference is load + predict only.

## C1-alpha development evidence

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Completed ladder:

| Version | Formulation | Main result | Status |
|---|---|---:|---|
| v1 | mixed all-phase trajectory | incumbent remained best | reject |
| v2 | final-24h live expert | **2,929.3 MAE** | retain expert |
| v3 | nested threshold/blend | 3,054.3 | reject |
| v4 | stacked/meta gate | 3,106.8 | reject |
| v5 | stack + hybrid | 3,073.8 | reject |
| v6 | one-row T-24 | 3,873.2 LOEO / 3,989.8 LOCO | reject |
| v7 | reliability diagnostic | disagreement + live direction useful | complete |
| v8 | fixed PIT-safe expert switch | **2,713.3 window / 1,998.1 latest-row** | frozen shadow candidate |

v8 development replay is not fresh validation because the policy was defined after v7 on the same 9 events.

## Frozen C1-alpha package

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Rule:

- one observation: LIVE only if disagreement >= `0.20` capacity;
- >=2 observations: LIVE only if disagreement >= `0.10` and live slope to date > 0;
- otherwise PRIOR.

Artifact SHA256:

`df31af5effcda2d2f1e58265c7e954cc04edf0e90b48501403eb4e4afd94edf2`

Training-contract SHA256:

`0a3edde223d8b6e64652f3fc8f79228998ac0d93a90fdaa9fc48311f98dee304`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Scheduled inference must never fit this package.

## Prospective C1 v8 runtime — LIVE

Operational spec:

`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`

Workflow:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

The live shadow path accepts only naturally due PIT-valid T-1 events, loads the frozen v2 expert, applies frozen v8, persists append-only pre-outcome evidence and scores only previously persisted decisions after outcomes.

Read-only operational surfaces:

- `public.dashboard_c1_shadow_v8_status_v1`;
- `public.dashboard_c1_shadow_v8_events_v1`.

Current prospective evidence is intentionally zero until the first naturally due T-1 decision.

## Prospective validation governance

Do not retune v8 thresholds, auto-retrain the frozen v2 expert, silently expand the training set, backfill missed decisions after outcomes, force T-1 using future timestamps, or relabel development replay as prospective evidence.

Any retrain requires an explicit new package version and governance decision.

## C1 promotion

The 20-independent-completed-match rule remains a later promotion gate.

Promotion requires enough genuinely prospective independent completed events, positive policy uplift vs Structural Prior, acceptable degradation/tail risk, frozen reproducible package and immutable evidence, human review and explicit promotion.

No automatic production promotion exists.

## E0 — Sector Decision & Dynamic Pricing MVP — ACTIVE IMPLEMENTATION

Canonical product specification:

`ml/SECTOR_DECISION_PRICING_V1.md`

Canonical implementation state/roadmap:

`ml/E0_SECTOR_TRAJECTORY_IMPLEMENTATION_V1.md`

### Confirmed live sector data

Real `public.sector_inventory` data is already available on active events.

Canonical event ownership is:

`sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id`

`sector_inventory.event_id` is nullable and must not be used as the E0 ownership key.

Verified runtime coverage at the implementation checkpoint included approximately:

- Lech: 151 sectors;
- Pogoń: 42;
- GKS Katowice: 23;
- Wisła Płock: 17;
- Zagłębie Lubin: 14.

Therefore E0 can operate on real sector histories now.

### E0.1 — Sector trajectory contract — CURRENT NEXT BUILD

Create versioned:

`sector-trajectory-v1`

One PIT-safe row per:

`ticket_event_id + sector + as_of_at`

Required features:

- current/reference/max availability;
- public absorption / sell-through proxy;
- 6h / 24h / 72h / 7d velocity;
- acceleration/deceleration;
- hours to kickoff;
- observation density;
- release / inventory increase / sector appearance/disappearance / coverage-change / data-gap flags.

Every row must trace back to source snapshots.

### E0.2 — Provisional continuous sector gap

Initial expected-progress baseline is relative to the event's stable public-inventory trajectory.

Label:

`PROVISIONAL_RELATIVE_EVENT_BASELINE`

Conceptually:

`expected sector remaining = sector reference availability × event remaining ratio`

`sector gap = observed remaining - expected remaining`

Do not claim a learned sector-specific demand curve yet.

### E0.3 — Status policy

Statuses:

- `UNDERPERFORMING`;
- `ON_TRACK`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

Do not freeze thresholds before continuous gap distributions/stability are observed on real current events.

Threshold policy must be small, deterministic and versioned.

### E0.4 — Sector no-action projection

Preferred wording:

**Projected outcome if current trajectory continues**

Estimate projected public availability at kickoff from stable recent sector velocity, bounded to a valid range and with conservative anomaly handling.

This remains a continuation scenario, not a causal counterfactual.

### E0.5 — Dashboard data surface

Expose read-only event/sector summary and trajectory history for:

`NiedzielX/BeyondTicketingPanel`

Target block:

`Event Detail -> Sector Performance & Pricing`

### E0.6 — Price data contract

Audit whether existing collectors provide current price / currency / price history / category mapping.

If not available, implement explicit POC/MVP configured/imported price source with timestamp/source.

Missing data semantics:

`PRICE_DATA_MISSING`

Never fabricate price.

### E0.7 — Assumption-based pricing scenarios

Initial configurable scenario grid may include:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

Required maturity label:

`ASSUMPTION_BASED_SCENARIO`

No automatic price changes:

`auto_price_change_allowed = false`

### E0.8 — Recommendation evidence loop

Persist recommendation, no-action state, price/action, assumption version, confidence, reason codes, club decision, execution and subsequent outcome from day one.

This becomes the training/evaluation base for E1 learned elasticity/intervention models.

## Immediate implementation sequence

1. **Implement `sector-trajectory-v1` from `snapshots -> sector_inventory`.**
2. Add release-aware continuous movement/gap features.
3. Inspect gap stability and freeze versioned status thresholds.
4. Implement bounded sector no-action projection.
5. Expose read-only E0 dashboard data.
6. Audit and implement price-data contract.
7. Add assumption-based pricing scenarios.
8. Add recommendation/decision/execution persistence.
9. Keep C1 v8 frozen and let prospective evidence accumulate automatically.
10. Keep production `live_adjustment=0`; continue T-30 R&D separately.

## Product target

> **Beyond should tell the club where the event is going, whether the live trajectory is strong enough to override the Structural Prior, which sectors are falling behind, what is likely to remain publicly available if nothing changes, and what price action is worth testing — while learning prospectively from every frozen decision and real intervention.**
