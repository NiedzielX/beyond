# P12 — Demand Regime / Capacity / Commercial Constraints Audit Plan

Status: **PRE-PLAN / LOWER PRIORITY THAN P9–P11**

Date: **2026-10-25**

## Objective

Determine whether observed ticket/inventory signals behave differently when attendance or visible inventory is constrained/censored by venue and commercial mechanics rather than pure demand.

Potential constraints include:

- stadium/public capacity;
- sector releases or holds;
- complimentary allocations;
- reopened inventory;
- public seat-map coverage changes;
- no-shows;
- near-sellout regimes.

This work is intentionally lower priority than P9 trajectory representation and P11 context collection.

## Research question

> Does forecast error, especially live-signal error, differ materially between unconstrained-demand events and capacity/release-constrained events, and is a separate interpretation or model treatment justified?

## Stage 1 — target-free data audit

Before any model comparison:

1. inventory existing capacity/release/coverage/anomaly evidence already present in the repo/database;
2. document PIT availability for every candidate regime indicator;
3. confirm which indicators are genuinely known by each forecast cutoff;
4. quantify missingness and club/event coverage;
5. identify whether near-sellout/constrained events can be classified without using final attendance or future inventory;
6. freeze regime-definition rules before opening outcome comparisons.

Do not infer a regime from future target-event observations.

## Stage 2 — descriptive error audit

Only after the regime definition is frozen:

- compare incumbent MAE by regime;
- compare bias / median AE / P90 AE / worst-event degradation;
- use event as the independent unit;
- report event counts and club coverage;
- preserve forward/time-respecting evaluation.

The first question is diagnostic: **does regime actually explain a material error pattern?**

## Stage 3 — challenger only if justified

A separate regime-aware challenger is allowed only if Stage 2 shows a stable, meaningful mechanism.

Possible treatments to evaluate later, each under a separate precommit:

- regime-specific interpretation/shrinkage;
- capped correction when inventory is censored;
- explicit constrained-demand indicator;
- separate residual correction for near-sellout states.

Do not introduce a regime model merely because a flag exists.

## Guardrails

- no target-event future snapshots;
- no final attendance used to construct a PIT feature;
- no post-hoc threshold chosen from the same error matrix it will judge;
- keep existing release/coverage anomaly flags in all data-quality decisions;
- no automatic production activation;
- `live_adjustment=0`.

## Start condition

P12 remains **deferred** while higher-value representation work is data-bound/in progress:

- P9 full 168h is currently 5/9;
- P11 genuine PIT odds collection has not yet started;
- Long72 prospective N is still small.

The audit plan exists now so the research question and leakage boundaries are explicit before any P12 result is inspected.
