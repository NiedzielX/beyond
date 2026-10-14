# Beyond Ticketing — Model Promotion Governance v1

Status: **active**  
Production impact: **none**

## Purpose

Promotion Governance sits above Model Evidence Scorecard v1 and separates four stages:

1. research signal;
2. evidence gate;
3. frozen candidate package;
4. human review.

Crossing the evidence gate never changes production P50 automatically.

## Package creation rule

A frozen candidate package can be created only when all conditions are true at the same time:

- `decision_status = promotable`;
- `evidence_signal = positive`;
- promotion progress is at least 100%;
- challenger MAE is lower than incumbent MAE;
- uplift versus incumbent is positive;
- if a bias-control MAE exists, challenger MAE must also beat bias control.

The package starts as `ready_for_review`.

## Frozen evidence

Each package freezes:

- category and candidate;
- primary validation protocol;
- research-prior weight;
- validation event and club counts;
- promotion gate counts;
- incumbent, bias-control and challenger MAE;
- uplift metrics;
- scorecard decision reason and next action;
- full scorecard row;
- source-specific supporting research evidence.

Frozen evidence is protected by a database trigger. Later refreshes cannot rewrite it.

A newer qualifying package may supersede an older `ready_for_review` package for the same category, but reviewed packages are retained for audit history.

## Manual review

Internal service-role-only function:

`review_model_promotion_candidate_v1(package_id, decision, reviewer, note)`

Allowed decisions:

- `approved_for_promotion`
- `rejected`

Every decision is also appended to `model_promotion_review_log_v1` with reviewer and timestamp.

The browser dashboard is read-only and cannot submit review decisions.

## No automatic activation

`auto_activation_allowed` is constrained to `false` at database level.

Therefore even `approved_for_promotion` does not change forecasts or activate a model. A separate explicit production-activation process would be required later.

## Current state — 2026-10-14

No real candidate package exists yet.

Nearest category: **Live Ticketing**

- evidence: positive;
- promotion evidence: **8 / 20** independent completed matches;
- progress: **40%**;
- current status: `collecting`.

## Automation

Internal pg_cron job:

`model_promotion_governance_6h`

Schedule: `42 */6 * * *`

The job refreshes the evidence scorecard and then checks whether any category qualifies for a frozen review package. It does not send ChatGPT notifications and does not alter production P50.

## Verification

A transactional dry-run temporarily simulated Ticketing at the 20-event gate and verified:

- first governance refresh created exactly one package;
- second refresh created no duplicate;
- manual review wrote an audit record;
- `auto_activation_allowed` remained false;
- the transaction was rolled back;
- production state remained at zero packages and zero review decisions.
