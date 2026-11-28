# Rolling72 prospective stable-pair design

Status: experiment design. Requires an exact cohort, an additive runtime,
isolated clock tests, and an activated manifest before it can issue.

## Full policy

At every eligible origin, issue PERS, the existing strict DRIFT24, and
STABLE_PAIR on a single committed bundle at +24, +48 and +72 h. STABLE_PAIR
copies DRIFT24 exactly when strict drift is ready. For a strict
`SCOPE_MISMATCH`, it uses the offline stable-pair rule if support passes.
Every other strict fallback and every unsupported stable-pair interval
keeps PERS exactly. A zero observation remains a legitimate numeric zero.
Per-method status distinguishes an override from inherited drift or PERS.
Record a separate reason for an unsupported stable-pair attempt.

Use this full policy as the primary denominator. Also report the conditional
scope-mismatch and supported-override subsets beside their denominators.
The conditional scores are diagnostics.

## Source, time and shared target

- Use the strict Roboticket source family and `available_total_seats`.
  Bind the database's internal ticket event ID, source manifest, and
  exact seal and attempt identities. Require source capture at or before
  known-at time, then known-at at or before the projection reference.
  Verify commit visibility and content in the source read transaction.
  For offline verification, export database-shaped records with
  PostgreSQL `to_jsonb` in UTC and pass the verified internal IDs to
  the adapter. That adapter checks cross-record bindings and consumes
  the prior verification. It does not attest seal visibility itself.
- Bind the parent's exact selected 24–30 h anchor. Include all visible
  interval seals in capture/snapshot order and reject a missed or invalid
  source attempt anywhere in the interval. Enforce exact endpoints, an
  interior observation, prior links and a 130-seal maximum. Compute the
  pair intersection and frozen 80%/three-sector support only on accepted
  intervals. Retain the source and policy receipts with the issue.
- Stamp one actual issue time after calculation. Bound the issue
  latency to 90 seconds from projection reference and source age to
  one hour at issue. Each method shares `target_at = issued_at + h`.
  All methods refuse target times at or after kickoff consistently.
- Score against one common accepted target seal per issue and horizon.
  Select the latest allowed target observation as of the target time
  with the parent's six-hour source age limit. Never backtrack past a
  known invalid or ambiguous newer observation to obtain a score.

## Experiment and analysis

Create a separate finite forward-only comparator. Bind the exact
implementation, code and source-manifest hashes, event admission rules,
cohort exclusions and windows in its manifest. Leave at least 78 hours
between issue close and score close. Only origins known after activation
can issue. Earlier genuine observations can serve as point-in-time history
for eligible new fixtures. Exclude exposed development matches and old
issues or labels from the formal sample.

Use the same issue, horizon and target-label identity for all three methods.
Report accepted labels, waiting and rejected observations, both fallback
denominators, bias and tail error. Average absolute errors within each
fixture first, then weight fixtures equally. At +72 h require at least
30 independently scored new fixtures from eight home clubs. The primary
contrast is STABLE_PAIR minus PERS. Require at least a 10% reduction in its
event-balanced MAE and a paired 95% bootstrap interval entirely below zero
(10,000 event resamples, seed 42). Require no increase in point MAE versus
PERS at +24/+48 h. Report STABLE_PAIR minus strict DRIFT24 as an incremental
contrast. Keep the same event resamples and label set across methods.

The active December two-method pilot can show operational readiness and
describe source support. The new experiment needs a separately declared
cohort and genuine forecasts committed before any target can be observed.
Reserve club decision validation for confirmed sales, returns and scans
collected through a separate source contract.
