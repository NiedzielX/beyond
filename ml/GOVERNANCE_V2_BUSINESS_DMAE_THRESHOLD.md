# Governance v2 — Business Minimum Meaningful ΔMAE

Status: **FRAMEWORK READY / BUSINESS VALUES PENDING**

Date: **2026-10-25**

## Purpose

Define the smallest attendance-forecast MAE improvement that is **material enough to change a real club/business decision**.

This value must not be chosen from model scorecards. It must be derived independently from operational consequences.

Until an approved threshold exists, the strongest positive research conclusion remains:

`POINT_GAIN_UNCERTAINTY_LIMITED`

and not:

`ROBUST_RESEARCH_ADVANCE`.

## Non-negotiable rule

Do **not** choose a threshold such as `100 seats`, `3%`, or any other convenient number because it makes a model result look good.

The threshold must be documented **before** it is used to judge a challenger.

## Decision areas to quantify

For each area, identify the attendance-error size at which a different operational action would actually be taken.

| Decision area | Decision changed by forecast? | Attendance boundary / band | Cost of over-forecast | Cost of under-forecast | Evidence owner/source |
|---|---|---:|---:|---:|---|
| Security staffing | TBD | TBD | TBD | TBD | TBD |
| Stewarding / event staff | TBD | TBD | TBD | TBD | TBD |
| Catering / F&B | TBD | TBD | TBD | TBD | TBD |
| Transport / parking | TBD | TBD | TBD | TBD | TBD |
| Hospitality | TBD | TBD | TBD | TBD | TBD |
| Cleaning / venue operations | TBD | TBD | TBD | TBD | TBD |
| Other club-specific decision | TBD | TBD | TBD | TBD | TBD |

## Required business inputs

For every material decision family capture:

1. the forecast value or band that changes the decision;
2. how many seats of forecast error can occur without changing the decision;
3. whether under-forecasting is more costly than over-forecasting;
4. approximate operational/financial consequence when the boundary is crossed;
5. whether the boundary is stable across clubs/stadiums or club-specific;
6. source and owner of the assumption;
7. review date.

## Derivation rule

The approved minimum meaningful `ΔMAE` should be based on the smallest **credible, recurring attendance-error reduction** that materially changes one or more downstream decisions.

The derivation must be reproducible from the business inputs above.

If different clubs have materially different operating thresholds, preserve both:

- a portfolio/global research threshold for headline governance;
- club-specific decision thresholds for operational interpretation.

Do not optimize the global research threshold to any challenger result.

## Precision requirement

A practically meaningful point gain is not automatically robust.

Default robust interpretation also requires the predeclared event-block uncertainty criterion to pass. Under Roadmap v4 the default is:

`upper bound of CI(challenger_mae - incumbent_mae) < 0`

unless a future experiment precommits another justified precision rule.

Therefore a challenger should reach `ROBUST_RESEARCH_ADVANCE` only when all are true:

1. point `ΔMAE` favors challenger;
2. event/fold stability guardrails pass;
3. absolute improvement meets/exceeds the approved business threshold;
4. precision criterion passes;
5. PIT/lineage/reproducibility gates pass;
6. no production boundary is violated.

## Application to current evidence

### P7 Long168

Current point improvement: **1069.80 seats / 14.44%**.

Paired event-block 95% interval for challenger-minus-anchor MAE:

`[-2566.13, +174.47]`

The interval crosses zero and the business threshold is not yet approved.

Therefore current P7 classification remains:

`POINT_GAIN_UNCERTAINTY_LIMITED`

regardless of the size of the point estimate.

### Long72 prospective

Current prospective sample is only **2 events**.

No governance threshold may be inferred from the observed `15.74%` point improvement.

## Approval record

Fill only after business derivation is complete.

- Approved global minimum meaningful absolute `ΔMAE`: **TBD seats**
- Optional relative guardrail: **TBD / not required unless independently justified**
- Asymmetric loss policy: **TBD**
- Effective date: **TBD**
- Business owner(s): **TBD**
- Research owner: **TBD**
- Evidence / source references: **TBD**
- Review cadence: **TBD**

## Current decision

Framework is ready. Numerical threshold remains intentionally unset until the business inputs are supplied and approved.
