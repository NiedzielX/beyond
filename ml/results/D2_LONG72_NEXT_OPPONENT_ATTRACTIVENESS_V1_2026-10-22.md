# D2 Long72 Next-Opponent Attractiveness v1 — 2026-10-22

## Goal

Extend P4 fixture substitution / cannibalization research with a PIT-safe measure of how attractive the **next home opponent** was expected to be at the exact Long72 forecast cutoff.

This is evidence collection only. It does not change the structural forecast or frozen P2 live correction.

## Two independent PIT gates

A row can become `READY` only if both are true.

### 1. Schedule knowledge

The next home opponent must exist in an immutable fixture schedule batch with:

`schedule_batch.observed_at <= forecast_as_of_at`

No later schedule state may fill an older forecast row.

### 2. Attendance outcome knowledge

Historical attendance used to estimate opponent attractiveness must have been system-known by `forecast_as_of_at`.

For every historical outcome the lookup requires:

- historical kickoff `< forecast_as_of_at`;
- outcome `created_at <= forecast_as_of_at`;
- outcome `updated_at <= forecast_as_of_at`;
- outcome `confirmed_at <= forecast_as_of_at` when present.

This is stricter than simply checking that the historical match occurred before the target match.

## Metric

Within the same club and competition, with a 730-day lookback:

- `club_median_attendance` = median attendance for known historical home outcomes;
- `opponent_median_attendance` = median for the requested opponent;
- `opponent_uplift_pct = (opponent_median / club_median - 1) * 100`.

Readiness gates:

- club history `>=8`;
- opponent history `>=3`.

The feature is intentionally unavailable below those floors.

## Runtime objects

Generic PIT lookup:

`public.opponent_attractiveness_as_known_v1(...)`

Next-home wrapper:

`public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(...)`

Append-only Long72 sidecar:

`private.d2_long72_next_opponent_attractiveness_v1`

Capture RPC:

`public.capture_d2_long72_next_opponent_attractiveness_v1(...)`

Scheduler:

- `d2_long72_next_opponent_attractiveness_v1_15m`;
- `9,24,39,54 * * * *`;
- job id at deployment: `30`.

## Verification

Generic PIT lookup for event 10 / Pogoń Szczecin and `Radomiak Radom` at `2026-10-22 07:20:01.949+00` correctly returned:

- `INSUFFICIENT_CLUB_HISTORY`;
- club history count `1`;
- opponent history count `0`;
- club median attendance `18255`;
- no uplift score.

This confirms the function does not fabricate an opponent score below the declared sample gates.

The next-home wrapper for the same event returned:

`NO_NEXT_HOME_MATCH_IN_SCHEDULE_STATE`

because the schedule batch known at that cutoff contained no later Pogoń home fixture.

## Initial Long72 sidecar materialization

12 reproducible Long72 predictions were processed:

- `2` × `FIXTURE_CONTEXT_NO_SCHEDULE_STATE_AS_OF`;
- `10` × `NO_NEXT_HOME_MATCH_IN_SCHEDULE_STATE`;
- `0` × `READY`.

This is the correct result, not a failure of the pipeline. The evidence layer is explicitly designed to preserve missing knowledge rather than infer future schedule information.

## Research implication

The infrastructure for next-opponent attractiveness is now ready before the data is.

A future row will become scoreable only when:

1. the next home match is genuinely present in the captured schedule state;
2. enough historical club/opponent attendance was already known at that timestamp.

Once labeled READY rows accumulate, P4 can test interactions such as:

- `next_home_match_days`;
- `next_home_opponent_uplift_pct`;
- `next_home_match_days × opponent_uplift_pct`;
- fixture density + next-opponent attractiveness.

Until then, do not replace missing values with later schedule knowledge or a hand-authored opponent score.

## Production boundary

- frozen Long72 P2 unchanged;
- Structural Prior unchanged;
- research sidecar only;
- `live_adjustment = 0`.
