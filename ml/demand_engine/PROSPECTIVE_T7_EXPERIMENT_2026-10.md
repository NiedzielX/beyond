# Beyond exact v1.7 T-7 prospective shadow experiment

Pre-registered: 2026-10-09

## Purpose

Obtain the first genuinely future, audit-safe observation for the exactly
recovered Lech Historical v1.7 T-7 champion inside Beyond Demand Engine v1.

This experiment is intentionally narrow. It is not a production promotion and
it does not train or tune a live correction.

## Target event

- ticket_event_id: 5
- home: Lech Poznań
- away: Korona Kielce
- competition: Ekstraklasa
- round: 11
- kickoff: 2026-10-18 17:30 Europe/Warsaw
- canonical T-7 information cutoff: 2026-10-11 17:30 Europe/Warsaw

## Locked point model

- model: `lech-v17-t7-recovered-exact`
- engine row version: `beyond-demand-engine-v1-v17-t7-shadow`
- feature set: `v17-t7-recovered-exact-v1`
- Ridge alpha: 0.3
- capacity cap: 43,269
- live correction: `live-correction-noop-v1`, adjustment exactly 0

No point-model parameter may be changed after the canonical cutoff for this
experiment.

## Locked probabilistic interval

- method: 80% split-conformal absolute residual interval
- calibration: `v17-split-conformal-80-v1:T-7`
- radius: 8,336.593429081528
- lower bound: max(0, P50 - radius)
- upper bound: min(43,269, P50 + radius)

The interval must not be recalibrated using the Korona outcome.

## Locked information semantics

### Attendance history

Use only eligible Lech home league attendance known strictly before the exact
T-7 timestamp.

### Sporting/table state

Use only completed Ekstraklasa results whose Europe/Warsaw local calendar date
is strictly earlier than 2026-10-11.

Therefore:

- all eligible matches from 2026-10-10 are visible;
- matches played on 2026-10-11 are excluded even if they finish before 17:30.

### Live inventory

- inventory interpretation: `demand_proxy_not_confirmed_sales`;
- source snapshot = latest snapshot captured at or before canonical T-7;
- 6h/24h velocity and acceleration are computed only from snapshots at or before
  canonical T-7;
- snapshots captured after canonical T-7 are forbidden for this forecast.

The scheduled job may physically execute after 17:30, but
`forecast_generated_at` must equal the canonical information cutoff and actual
execution time must be retained separately in audit metadata.

## Persistence gate

Persist only if the fail-closed T-7 preflight passes, including:

- event identity and kickoff;
- complete league team mapping;
- independently verified expected visible league-result count;
- independently verified expected visible Lech-home-attendance count;
- no result/attendance after the relevant cutoff;
- source URLs and `verified_at` audit block;
- point-in-time source snapshot at or before T-7.

If evidence is incomplete, the correct experiment outcome is **no forecast
persisted**, not an imputed or partially sourced forecast.

## Scheduled execution

- 2026-10-11 10:00 Europe/Warsaw: evidence preflight + dry run only;
- 2026-10-11 17:35 Europe/Warsaw: re-verification and persistence if all guards
  pass.

## Outcome

The target outcome is verified official match attendance for Lech Poznań vs
Korona Kielce. The outcome must be sourced independently from the model inputs.

Do not modify the point forecast after observing the outcome.

## Locked evaluation

The prospective row is evaluated through the strict Model Lab protocol:

- one nearest pre/exact-checkpoint forecast per model/event/horizon/mode;
- canonical horizon derived from `hours_to_kickoff`, never trusted from a legacy
  stored label;
- no post-checkpoint fallback.

Report for exact v1.7 T-7:

- absolute error;
- APE;
- interval coverage;
- interval width;
- P50 bias sign;
- P10/P50/P90 values.

Where a valid comparison row exists for the same event and horizon, also report:

- current Beyond production forecast error;
- generic shadow forecast error;
- exact v1.7 T-7 forecast error;
- historical-vs-final live uplift for each shadow engine.

## Promotion decision

One genuinely future match cannot promote a model or live correction.

This event contributes one independent observation to the prospective evidence
set. Promotion decisions require a larger independent sample and the existing
registry gates.

In particular, non-zero live correction remains blocked until at least 20
independent completed matches are available under the grouped evaluation
protocol.

## What is explicitly NOT allowed

- modifying v1.7 after seeing the Korona outcome;
- recalibrating the interval on the Korona outcome;
- using post-T-7 league results, attendance information or ticket snapshots;
- calling inventory movement confirmed sales;
- replacing production v0.3 with this shadow observation;
- treating one successful future prediction as production validation.
