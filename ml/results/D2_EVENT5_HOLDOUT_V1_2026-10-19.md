# Beyond Ticketing — d2 Event 5 Chronological Holdout v1 — Result

Date: **2026-10-19**

Status: **COMPLETED ONE-PASS HOLDOUT / NO RETUNING / NO PRODUCTION CHANGE**

## Decision

Decision:

`HOLDOUT_COMPLETE_KEEP_D2_FROZEN_PROSPECTIVE_ACCUMULATION`

The frozen d2 package remains:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

No parameter, feature, threshold, model, policy or correction cap is changed from this holdout.

Production remains:

`live_adjustment = 0`

## Canonical evidence

Workflow run:

`39310995137`

Main commit:

`0239d40b99158ff2a31b8bfa9a8433f7bac6ad75`

Artifact:

`d2-event5-holdout-v1-39310995137`

Artifact ID:

`12215538287`

Artifact ZIP SHA256:

`2857f1cb8a0bff9b0cac41bc36520ae840df91ef1400d0b6c4c7b90938b9c867`

Evidence hashes:

- split manifest: `5591880cff101ed316c4acae87fb0cb549ef9d5a987126b63245e154adb5a822`;
- frozen development Stage-0 JSON: `bb8a7c8ef3c719bca0c54da8961aea92d8484168b6493c768fe88c53f316985a`;
- frozen development Stage-0 CSV: `ec7aef2f458ae1db2fdaced7e0a051fe8b9035eccdb3764b0f640c6078aa6954`;
- holdout JSON: `3938ee164781f9272ce64087e4aa6ff9871b5bd7fb41e6e671f1316a86e6a0e7`;
- holdout row CSV: `e57b441fc37d4d6bb42c807c16ea55617c4d3a88f7312024e402e7b6cd1e47f1`;
- persisted C1 v8 comparator: `a82fdb30d3532e0344af524053ded9bad0f19485cef6b04daadce9b133d67685`;
- frozen Stage-2 manifest: `8d04defd1400ca9aadd19abba8b4ba8a0f3ed8c2bad56d8c0b88c5aa79cf7083`.

## Holdout boundary

Event:

- ticket event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- stadium capacity `43,269`;
- 4 final-24h d2 rows.

This event was excluded from:

- Stage-1 model training/selection;
- Stage-2 policy selection;
- all Ridge/P2 parameter choices.

The scorer hard-asserts:

- exact original 9-event / 30-row development set;
- event 5 absent from training;
- frozen Stage-1 expert `ridge-a10`;
- frozen Stage-2 package `d2-stage2-p2-observation-maturity-2026-10-19-v1`;
- frozen Stage-2 policy `P2-observation-maturity`;
- no post-holdout retuning.

## One-pass scorecard

| Forecast | Latest absolute error | Window MAE | Improvement vs Frozen v2 |
|---|---:|---:|---:|
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 | — |
| Raw frozen Ridge | **6,652.81** | **6,170.35** | latest **+3,179.71** / window **+3,662.17** |
| Frozen P2 governed Ridge | **6,652.81** | 7,263.16 | latest **+3,179.71** / window **+2,569.36** |

Relative latest-error reduction vs Frozen v2:

**32.34%**

Relative raw-Ridge window-MAE reduction vs Frozen v2:

**37.24%**

Relative P2 window-MAE reduction vs Frozen v2:

**26.13%**

At the latest observation P2 reliability is `1.0`, therefore raw Ridge and P2 produce the same final forecast/error.

## Row-level trajectory

Frozen-v2 anchor on every row:

`27,574.48`

Actual attendance:

`37,407`

| As-of UTC | Hours to kickoff | Obs | Raw Ridge forecast | Raw error | P2 reliability | P2 forecast | P2 error |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-17 21:15:35 | 18.24 | 1 | 31,901.38 | 5,505.62 | 0.25 | 28,656.20 | 8,750.80 |
| 2026-10-18 03:16:42 | 12.22 | 2 | 30,389.64 | 7,017.36 | 0.60 | 29,263.58 | 8,143.42 |
| 2026-10-18 09:23:07 | 6.11 | 3 | 31,901.38 | 5,505.62 | 1.00 | 31,901.38 | 5,505.62 |
| 2026-10-18 15:18:50 | 0.19 | 4 | 30,754.19 | 6,652.81 | 1.00 | 30,754.19 | 6,652.81 |

Interpretation:

- the live Ridge layer materially corrects the badly missed pre-live anchor;
- the frozen P2 policy is conservative on the first two observations and therefore gives up some useful early Ridge correction on this event;
- once the trajectory is mature, P2 correctly allows full Ridge weight;
- P2 does not improve the final row versus raw Ridge because its reliability is `1.0` by that point;
- this is a valid frozen-policy trade-off and is **not** a reason to retune P2 on event 5.

## Important Pre-Live v2 / b2 diagnostic

Underlying Structural T-1 base before b2:

`29,737.93`

Frozen Pre-Live v2 after b2:

`27,574.48`

b2 correction:

`-2,163.45 seats`

Prior completed same-season Lech home matches:

`5`

b2 EWMA residual fraction:

`-0.11894098185696676`

Errors against actual attendance:

- underlying Structural T-1 base error: `7,669.07`;
- Frozen Pre-Live v2 error: `9,832.52`.

Therefore, on this fresh holdout, the frozen b2 current-season correction moved the pre-live forecast in the wrong direction and worsened error by exactly `2,163.45 seats`.

This is a **prospective warning**, not a post-hoc invitation to retune b2.

Rule:

> Do not reopen or tune b2 from one event. Carry this component diagnostic forward unchanged. If materially more independent prospective events show the same failure mode, create a separately versioned b2/Pre-Live challenger before any retraining.

## C1 v8 prospective comparator

A genuine pre-outcome persisted C1 v8 score exists and was used without reconstruction.

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Latest selected expert:

`PRIOR`

Reason:

`insufficient_disagreement`

C1 v8 errors:

- latest PRIOR/policy error: `7,669.07`;
- latest raw live error: `9,309.62`;
- window PRIOR/policy MAE: `7,669.07`;
- window raw live MAE: `8,495.33`.

Against C1 v8 policy:

- d2 raw/P2 latest error is lower by **1,016.26 seats**;
- d2 raw Ridge window MAE is lower by **1,498.72 seats**;
- d2 P2 window MAE is lower by **405.91 seats**.

Caveat:

C1 v8 used 7 prediction rows / 4 representative buckets, while the d2 holdout scorer uses the 4 canonical final-24h exporter rows. The latest-row comparison is directly aligned; window metrics have slightly different sampling and should be treated as supportive rather than exact apples-to-apples evidence.

## What this holdout proves

This single chronological holdout provides positive independent evidence that:

1. the frozen d2 live layer can materially reduce a large Pre-Live v2 miss;
2. the frozen d2 latest forecast outperformed the persisted C1 v8 decision on this event;
3. P2 correctly reaches full trust once the trajectory becomes mature;
4. the current Pre-Live b2 regime can still create a substantial wrong-direction correction on an individual match.

It does **not** prove production readiness.

One completed holdout is insufficient for promotion and insufficient for retuning.

## Next phase

Status after this result:

`EVENT5 HOLDOUT COMPLETE -> FROZEN PROSPECTIVE ACCUMULATION ACTIVE`

Next rules:

1. keep Pre-Live v2, `ridge-a10` and P2 frozen;
2. score every new eligible completed event append-only;
3. preserve component-level diagnostics for:
   - Structural T-1 base;
   - Frozen Pre-Live v2 / b2;
   - raw Ridge;
   - P2 governed Ridge;
   - persisted C1 comparator where available;
4. never silently fold new outcomes into training;
5. only start a separately versioned retraining/reopening cycle after materially more independent prospective evidence supports a specific failure hypothesis;
6. require materially more prospective events before any production promotion.

## Production boundary

No production change.

No automatic promotion.

No b2 retuning.

No Ridge retuning.

No P2 retuning.

Frozen C1 v8 unchanged.

`live_adjustment = 0`
