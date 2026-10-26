# P9 Historical Support Post-Mortem — 2026-10-26

Status: **FROZEN HISTORICAL COHORT — NOT EVALUABLE**

North Star context: the objective is lower **prospective event-balanced MAE**. This post-mortem explains why the frozen historical P9 cohort cannot provide valid MAE evidence and why the correct continuation is prospective validation rather than retrospective repair.

## Executive conclusion

P9 reached the genuine full-window gate (**9/9 T-168 events / 9 clubs**) and the learner design had already been precommitted as `p9-knn-median-residual-k5-v1`.

The historical evaluation then failed closed **before attendance labels were opened** because the frozen support contract found:

- T-24 comparator targets: **11**;
- T-24 support-ready targets: **0**;
- T-48 comparator targets: **9**;
- T-48 support-ready targets: **0**.

Canonical status:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

This is not evidence that booking curves improve MAE and not evidence that they worsen MAE. No valid challenger-vs-incumbent MAE comparison was produced.

## What the frozen learner required

For each target and cutoff, P9 v1 froze:

1. the target booking-curve representation;
2. up to `k=5` nearest PIT-safe booking-curve neighbors;
3. the target incumbent available at the exact cutoff;
4. the target incumbent **source family**;
5. historical reference incumbent rows from that exact same source family at each reference event's analogous cutoff;
6. genuine historical attendance needed to compute reference residuals only after the target/reference identities were frozen.

A target required at least **3 residual-bearing neighbors**. If fewer than three existed, it failed closed.

## Diagnostic result

### T-24

All 11 frozen comparator targets failed the minimum-three rule.

| Target event | Target incumbent family | Valid reference incumbents | Selected curve neighbors |
|---|---|---:|---:|
| 15 | `structural_prior_forecasts_v1` | 0 | 5 |
| 18 | `structural_prior_forecasts_v1` | 0 | 5 |
| 11 | `structural_prior_forecasts_v1` | 0 | 5 |
| 19 | `structural_prior_forecasts_v1` | 0 | 5 |
| 5 | `structural_prior_forecasts_v1` | 0 | 5 |
| 20 | `structural_prior_forecasts_v1` | **1** | 5 |
| 10 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 16 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 23 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 21 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 22 | `d2_long72_forward_predictions_v1` | 0 | 5 |

Best case was event 20 with only **1/5** valid same-family reference incumbents, still below the frozen minimum of 3.

### T-48

All 9 frozen comparator targets failed the minimum-three rule.

| Target event | Target incumbent family | Valid reference incumbents | Selected curve neighbors |
|---|---|---:|---:|
| 11 | `structural_prior_forecasts_v1` | 0 | 4 |
| 19 | `structural_prior_forecasts_v1` | 0 | 4 |
| 5 | `structural_prior_forecasts_v1` | 0 | 4 |
| 20 | `structural_prior_forecasts_v1` | 0 | 5 |
| 10 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 16 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 23 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 21 | `d2_long72_forward_predictions_v1` | 0 | 5 |
| 22 | `d2_long72_forward_predictions_v1` | 0 | 5 |

## Root cause

The bottleneck is **historical PIT incumbent coverage**, not booking-curve coverage.

The curve-distance layer can identify historical neighbors. However, many of those neighbors occurred before Beyond had persisted the required incumbent source family at the analogous T-24/T-48 cutoff. The frozen contract correctly refuses to reconstruct those missing incumbent forecasts after the fact.

Therefore:

`full T-168 curve exists` does **not** imply `valid P9 learner residual exists`.

A residual requires both:

- a genuine reference outcome; and
- a genuinely persisted PIT incumbent from the exact required family at the historical analogous cutoff.

The second condition is what is missing.

## Why we do not repair the historical cohort

We must not generate or backfill historical incumbent forecasts now and label them as if they had been known at the old cutoff. That would contaminate the comparison with hindsight and would no longer answer the North Star question:

> Would the challenger have reduced MAE using only information genuinely available at the decision time?

The historical cohort is therefore permanently recorded as **not evaluable under the frozen v1 contract**.

## Correct continuation

Continue the already-precommitted prospective lane:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Prospectively, Beyond is now persisting the actual incumbent ledger before outcomes. As this genuine PIT history grows, the same frozen P9 mechanism can obtain legitimate residual-bearing neighbors without reconstruction.

Automation:

`.github/workflows/p9-booking-curve-prospective-v1.yml`

The workflow runs twice per hour and may persist a prediction only inside the frozen 90-minute T-48/T-24 window.

## P9 v2 rule

Do not design P9 v2 simply because P9 v1 historically produced no result.

A P9 v2 becomes justified only if the prospective lane repeatedly enters real prediction windows yet continues to fail for structural support reasons after sufficient new PIT incumbent history has accumulated.

If that happens:

1. diagnose failures using target-free data only;
2. define the new hypothesis/contract before opening evaluation labels;
3. precommit representation, support rules, learner and metric;
4. evaluate prospectively;
5. compare event-balanced MAE against the incumbent.

## Production state

Unchanged:

- `production_activation_allowed=false`;
- `live_adjustment=0`;
- historical P9 result count = 0.
