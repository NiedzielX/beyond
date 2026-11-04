# Genuine 24-hour inventory drift comparator v1

Recorded 2026-11-04 before implementing or scoring this comparator and before the first daily v1 target outcomes. Separate research comparator, not a replacement for frozen v1. Motivation: the exact coefficient audit found that frozen v1 has zero relative-value-history coefficients and all remaining nonzero terms force a raw decline.

Question: does the most recent genuine daily change carry useful future-inventory signal beyond persistence? One fixed rule, no fitting, no parameter search, no use of attendance or partner sales data. Public inventory changes are not paid sales. A source release can produce a positive change.

## Fixed prediction rule

Use exactly the genuine prefix from a new post-freeze v1 issue. Keep existing minimum 4 hourly observations, 24-hour span, 6-hour latest freshness, measurement identity and zero/hidden semantics. The v1 ledger is read-only and its cohort/metrics remain unchanged.

Let L be the latest real prefix observation. Define anchor cutoff L.captured_at − 24 hours; choose the latest genuine prefix observation A at or before that cutoff, no older than 6 hours relative to it. No interpolation, forward-fill or fallback to a different lookback. If no anchor exists, record DRIFT_ANCHOR_INSUFFICIENT with no forecast.

`velocity_places_per_day = (L.value - A.value) / elapsed_actual_days(A,L)`

For each existing remaining daily target T strictly before kickoff:

`forecast(T) = max(0, L.value + velocity * elapsed_actual_days(L,T))`

Positive and negative slopes are allowed; no monotonicity constraint, capacity cap, damping, club parameter or learned coefficient. Persist velocity, exact anchor/source identities and source/implementation/precommit hashes. Persistence remains L.value. The six-hour tolerance is a freshness guard, not a tunable hyperparameter.

## Prospective contract

Freeze the rule/implementation before its first eligible issue; retain an immutable artifact with actual frozen_at and content hashes. Only genuine new v1 attempts issued after freeze and captured by this comparator during issue…+90 minutes are eligible. Never reconstruct the already-issued Nov 3 points as prospective drift predictions. No historical replay is used to select the rule. All prefixes/horizons of an event remain one independent unit. Failed/insufficient attempts remain coverage evidence. A missed sidecar window remains missing.

Separate local immutable ledger and private content-addressed backup namespace. Do not write to v1 ledger, models, predictions, target scores or production DB. Scoring waits for the matching v1 point's genuine immutable target score; copy its exact target identity/value, recompute drift and persistence errors, and record score receipt time. No target score enters prediction construction. New forecasts must be persisted before targets mature.

## Evaluation and decision

Primary: paired same-target event-balanced path MAE against persistence within this comparator's eligible cohort, using the existing pure evaluator. Report drift eligibility/failed/missed coverage against all new v1 attempts, independent events/clubs, per-lead errors, signed bias, P90 event error, improvement rate and prefix-regime diagnostics. Do not pool old v1 Nov 3 scores with this experiment or replace v1 headline metrics. A separate overlap report may compare v1 and drift only on exactly shared issued targets.

Before 8 independent events with genuine +1 labels from 5 clubs: COLLECTING, no claim of demonstrated advantage. The first cycle meeting both guards is the initial research-review snapshot. Include every scored event then available and report its matured/pending targets; do not select the best eight events or stop on a favorable MAE. This is a research review gate, not a promotion or accuracy guarantee. No automatic activation. If drift does not beat persistence or worsens tail/bias, retain the honest negative result; do not choose a different lookback/damping under this version. Any modification creates a new precommit and future evidence stream.

Implementation verification must cover rise/decline/flat/explicit 0, anchor gap/freshness, future observations, exact issue/target coordinates, input and implementation hashes, post-freeze/window bounds, independent ledger identity, immutable retries/conflicts, exact matched target scores and private backup read-back. Synthetic checks establish correctness only.

`production_change=false`, `live_adjustment=0`. No attendance 550-seat gate changes.
