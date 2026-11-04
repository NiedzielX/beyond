# Genuine 24-hour inventory drift comparator v1

Recorded2026-11-04before implementing or scoring this comparator and before the first daily v1target outcomes. Separate research comparator, not a replacement for frozenv1. Motivation:the exact coefficient audit found that frozenv1has zero relative-value-history coefficients and all remaining nonzero terms force a raw decline.

Question:does the most recent genuine daily change carry useful future-inventory signal beyond persistence? One fixed rule, no fitting, no parameter search, no use of attendance or partner sales data. Public inventory changes are not paid sales. A source release can produce a positive change.

## Fixed prediction rule

Use exactly the genuine prefix from a new post-freeze v1issue. Keep existing minimum4hourly observations,24-hour span,6-hour latest freshness, measurement identity and zero/hidden semantics. The v1ledger is read-only and its cohort/metrics remain unchanged.

LetLbe the latest real prefix observation. Define anchor cutoffL.captured_at−24hours; choose the latest genuine prefix observationAat or before that cutoff, no older than6hours relative to it. No interpolation, forward-fill or fallback to a different lookback. If no anchor exists, recordDRIFT_ANCHOR_INSUFFICIENTwith no forecast.

`velocity_places_per_day = (L.value - A.value) / elapsed_actual_days(A,L)`

For each existing remaining daily targetTstrictly before kickoff:

`forecast(T) = max(0, L.value + velocity * elapsed_actual_days(L,T))`

Positive and negative slopes are allowed; no monotonicity constraint, capacity cap, damping, club parameter or learned coefficient. Persist velocity, exact anchor/source identities and source/implementation/precommit hashes. Persistence remainsL.value. The six-hour tolerance is a freshness guard, not a tunable hyperparameter.

## Prospective contract

Freeze the rule/implementation before its first eligible issue; retain an immutable artifact with actual frozen_at and content hashes. Only genuine new v1attempts issued after freeze and captured by this comparator during issue…+90minutes are eligible. Never reconstruct the already-issuedNov3points as prospective drift predictions. No historical replay is used to select the rule. All prefixes/horizons of an event remain one independent unit. Failed/insufficient attempts remain coverage evidence. A missed sidecar window remains missing.

Separate local immutable ledger and private content-addressed backup namespace. Do not write to v1ledger, models, predictions, target scores or production DB. Scoring waits for the matching v1point's genuine immutable target score; copy its exact target identity/value, recompute drift and persistence errors, and record score receipt time. No target score enters prediction construction. New forecasts must be persisted before targets mature.

## Evaluation and decision

Primary:paired same-target event-balanced path MAE against persistence within this comparator's eligible cohort, using the existing pure evaluator. Report drift eligibility/failed/missed coverage against all new v1attempts, independent events/clubs, per-lead errors, signed bias, P90 event error, improvement rate and prefix-regime diagnostics. Do not pool old v1Nov3scores with this experiment or replace v1headline metrics. A separate overlap report may compare v1and drift only on exactly shared issued targets.

Before8independent events with genuine+1labels from5clubs:COLLECTING, no claim of demonstrated advantage. The first cycle meeting both guards is the initial research-review snapshot. Include every scored event then available and report its matured/pending targets; do not select the best eight events or stop on a favorable MAE. This is a research review gate, not a promotion or accuracy guarantee. No automatic activation. If drift does not beat persistence or worsens tail/bias, retain the honest negative result; do not choose a different lookback/damping under this version. Any modification creates a new precommit and future evidence stream.

Implementation verification must cover rise/decline/flat/explicit0, anchor gap/freshness, future observations, exact issue/target coordinates, input and implementation hashes, post-freeze/window bounds, independent ledger identity, immutable retries/conflicts, exact matched target scores and private backup read-back. Synthetic checks establish correctness only.

`production_change=false`, `live_adjustment=0`. No attendance550-seat gate changes.
