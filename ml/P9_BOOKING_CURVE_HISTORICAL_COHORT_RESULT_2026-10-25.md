# P9 Booking Curve v1 — Historical Cohort Result

Date: **2026-10-25**

Status: **NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Decision

The first full-window P9 cohort reached the precommitted **9/9** trajectory-readiness gate, but the fixed learner cannot be evaluated honestly on this historical cohort because its nearest historical booking-curve references do not contain enough point-in-time incumbent forecasts persisted by the analogous historical cutoffs.

This is a data-lineage limitation, not a negative attendance-model result.

**No P9 attendance labels were opened to the learner and no P9 MAE was calculated.**

The frozen learner design is not changed.

## Frozen design

Canonical precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Frozen requirements include:

- T-48 and T-24 only;
- canonical P9 booking-curve representation;
- weighted-L1 curve distance;
- fixed `k=5` nearest curves;
- minimum 3 residual-bearing neighbors;
- the target and reference residual must use the same incumbent source family;
- reference incumbent must have been genuinely persisted by the analogous historical cutoff;
- no fitted coefficient or candidate sweep.

None of these rules are relaxed after reaching 9/9.

## 9/9 readiness

The full T-168 trajectory gate reached:

- ready events: **9**;
- ready clubs: **9**;
- full-window event IDs: `[5,10,15,18,19,20,21,22,23]`.

The ninth genuine label was event 22, Legia Warszawa vs Lech Poznań, reported attendance **27,410**.

Before the ninth label was available, the learner design and hard freeze-before-label DB gates had already been committed.

## Registered target-free representation freezes

The evaluation workflow reproduced and registered the exact target-free P9a manifests before any learner label export.

### T-24

- manifest: `ef54d64b5b0f74d767b5e8fcdc4f7fa5b2912905466fcd98db392b966dcd8249`;
- freeze-ready targets: 14;
- comparator-ready targets: 11.

### T-48

- manifest: `a8dc3899a26ff4969ff7fe8656c70466d0d3ef66da3f12e2e4be1abe7289da29`;
- freeze-ready targets: 12;
- comparator-ready targets: 9.

These manifests are immutable evidence of the target/reference curve identities selected before label export.

## Target-free support diagnostic

Diagnostic workflow:

`P9 Booking Curve Support Diagnostic v1`

Run:

`40226730395`

Artifact:

`p9-booking-curve-support-diagnostic-v1-40226730395`

Artifact ZIP SHA256:

`780a4b4a92675275b59ef1acc5d0733bdc2151da7a94e2d83e968534526b0a29`

Attendance opened:

**false**

Target values used:

**false**

### T-24 support

- comparator targets: 11;
- support-frozen targets: 11;
- targets with >=3 valid same-family PIT reference incumbents: **0**.

Examples:

- events 15, 18, 11, 19 and 5 select older curve neighbors such as events 2/3/4/7/14; none of those reference events has a qualifying historical `structural_prior_forecasts_v1` row persisted by its analogous T-24 cutoff;
- event 20 has exactly **1** valid same-family reference incumbent (event 11), below the frozen minimum of 3;
- targets 10, 16, 21, 22 and 23 use `d2_long72_forward_predictions_v1` as their target incumbent family, but their nearest historical curve neighbors do not have qualifying historical Long72 rows at the analogous cutoff.

### T-48 support

- comparator targets: 9;
- support-frozen targets: 9;
- targets with >=3 valid same-family PIT reference incumbents: **0**.

Every target remains below the frozen minimum of 3 residual-bearing neighbors.

## Independent database audit

A separate target-free audit confirmed that the support failure comes from historical forecast lineage, not from the curve representation code.

Across 20 completed Ekstraklasa ticket events:

### T-24

- events with any structural forecast row: 11;
- events with a PIT-valid structural forecast persisted by the historical cutoff: 11;
- events with an eligible <=6h-stale Long72 row: 5.

### T-48

- events with any structural forecast row: 11;
- events with a PIT-valid structural forecast persisted by the historical cutoff: 9;
- events with an eligible <=6h-stale Long72 row: 5.

Many older booking-curve references have **no persisted incumbent forecast at all**. For some later events, forecasts exist today but were created after the historical cutoff and therefore cannot be used retrospectively.

## Why the historical learner is not executed

The frozen learner needs reference residuals:

`actual attendance of reference - incumbent P50 of reference at analogous historical cutoff`

If the incumbent was not genuinely persisted at that cutoff, reconstructing/backfilling it now would violate the PIT contract.

Therefore:

- no same-family rule is relaxed;
- no persistence-time rule is relaxed;
- no historical incumbent is synthesized;
- no attendance label export is opened just to see what the MAE would have been;
- no learner result is registered.

Support-freeze registry remains empty.

P9 result registry remains empty.

## Interpretation

This result does **not** mean booking-curve shape has no value.

It means the first historical cohort cannot provide an honest residual-model evaluation because our forecast-persistence infrastructure did not exist early enough for the nearest historical references.

The correct continuation is prospective.

## Next lane

Keep the exact same precommitted learner mechanism and validate it on future targets for which:

1. booking curves are collected prospectively;
2. target incumbent forecasts are persisted before each T-48/T-24 cutoff;
3. prior reference events also have genuine booking curves, genuine outcomes and PIT-persisted same-family incumbents;
4. prediction is persisted before target attendance is available;
5. evaluation occurs only after genuine post-match attendance is confirmed.

No redesign is justified by the historical support failure.

## Guardrails

- no P9 historical attendance labels were opened to the evaluator;
- no historical PIT forecast was backfilled;
- no target/reference support threshold changed;
- no model result was produced;
- no production activation;
- `live_adjustment = 0`.
