# Rolling72 club pilot data contract v1

**Purpose.** Import privacy-safe club aggregates to evaluate two distinct targets: ticket sales and final attendance. Sales or public inventory must never stand in for attendance. This is a data contract for a shadow pilot; it does not authorize pricing, promotion, or production changes.

## Grain and time

One row represents one event × measure × pool (when applicable) × UTC time bucket × source revision. Use fixed one-hour buckets in v1, with half-open intervals `[bucket_start_at, bucket_end_at)`. A source may deliver coarser buckets; preserve their actual boundaries and do not split or fabricate hourly values. Store timestamps as RFC 3339 UTC.

Required dimensions on every row:

| Field | Meaning |
| --- | --- |
| `schema_version` | `rolling72-club-pilot-v1` |
| `club_id`, `event_id` | Pseudonymous stable IDs; no names or free-text identifiers |
| `kickoff_at` | Scheduled kickoff in UTC as known in this revision |
| `source_id` | Stable source-system code, not a credential |
| `metric_family` | `ticket_sales`, `refunds`, `inventory_pool`, `season_membership`, or `entry_scans` |
| `bucket_start_at`, `bucket_end_at` | UTC bucket boundaries |
| `measure` | Metric code from the definitions below |
| `value` | Nonnegative integer aggregate, except signed `pool_delta` and `net_sold_delta` |
| `unit` | `tickets`, `scans` or `people` as defined below |
| `value_status` | `observed`, `unknown`, or `not_applicable` |
| `known_at` | First UTC time this exact value/revision was available to the forecasting process |
| `revision` | Monotonically increasing integer per source/event/metric/bucket; corrections append a revision, never overwrite history |
| `source_record_ref` | Opaque, non-personal source batch/row reference for reconciliation |

Each event also needs an event record with `club_id`, `event_id`, `kickoff_at`, `known_at`, `revision`, and source reference. A kickoff change is a new event revision. Historical forecasts and features must use only rows with `known_at <= forecast_issued_at` and the latest such revision. Retain the kickoff value that was known at issue time; never rewrite an old issue against a later schedule.

## Measures and interpretation

- `ticket_sales`: `gross_sold_delta` and `net_sold_delta`, in tickets, by sale bucket. Net sales are gross sales less ticket cancellations/refunds recorded in the same accounting convention. Also provide `gross_sold_cumulative` and `net_sold_cumulative` snapshots where the source supports them. Do not infer a zero from a missing bucket.
- `refunds`: `refund_delta` in tickets by refund-processing bucket. Refunds are separate from sales so timing and reconciliation remain visible; do not subtract them twice from a source-provided net measure.
- `inventory_pool`: `available_pool_snapshot` in tickets and signed `pool_delta` in tickets, separately by source-defined pool/sector code. Provide a stable `pool_id`, using an explicit event-wide code when appropriate. A pool opening or closure is an inventory change, not a sale. `available_pool_snapshot` is not attendance or unsold demand.
- `season_membership`: `member_entitlement_snapshot` in tickets (entitlements eligible for the event) and `member_reservation_delta` in tickets when reservations are separately tracked. Do not treat entitlements as attendance.
- `entry_scans`: `scan_accepted_delta`, `scan_rejected_delta`, and `scan_reversed_delta` in scans by scan bucket. Aggregate by event only; exclude person, seat, ticket, device, and gate identifiers. Scans are an attendance signal, not the final attendance label.
- Final attendance target: a separate event-level `final_attendance` value in people, with `known_at`, `revision`, source and reconciliation status. It must be the club's declared authoritative post-event count, with a documented rule for staff, guests, and re-entry. Do not derive it by summing accepted scans unless the club explicitly certifies that method as its authoritative count.

Represent unavailable, unreported, or not yet delivered values as `value=null, value_status=unknown`; represent a true measured zero as `value=0, value_status=observed`. Use `not_applicable` only when the measure does not apply. No row means no evidence, not zero. Conflicting or unreconciled revisions remain flagged and must not be silently resolved by choosing the larger value.

## Privacy and handling

Only event-level aggregates and pseudonymous club/event/source/pool codes are in scope. Reject names, emails, phone numbers, account IDs, ticket IDs, seat-level records, device IDs, IP addresses, and free-text notes. Keep the source's aggregate provenance reference, but no lookup back to a person. Apply the same aggregation and privacy boundary to scans, season tickets, refunds, and all revisions.

## First-pilot acceptance

Accept an event feed for shadow evaluation only when all conditions hold:

1. Event identity, club, kickoff, bucket boundaries, source, `known_at`, revision and value status are present and valid; timestamps parse as UTC and buckets do not overlap for the same source/measure/pool.
2. The club documents the sales, refund, pool, membership, scan, and authoritative final-attendance definitions and their units. Sales and refunds reconcile to the club's event ledger within 1% or an explicitly documented rounding tolerance; every discrepancy is retained with a status and explanation code.
3. Missingness is represented as unknown rather than zero; pool changes, sales/refunds, and scan outcomes are separately represented. Revisions are append-only and reproduce the values known at each historical issue time.
4. Report per-club and per-event results, event-balanced aggregates, and the fixture and club counts. Treat early results as pilot observations. The existing 30-new-match / eight-club decision rule applies to the separate PERS–drift24 availability comparison. Score sales-path errors and final-attendance errors separately; report coverage and missingness for each.
5. For attendance, compare against the declared structural/PERS baseline and report event-balanced MAE at +24/+48/+72 hours when eligible. The approximately 1,200-seat MAE goal is a research milestone, not an acceptance claim from sales accuracy, scan counts, or a small cohort. No intervention effect is inferred from these observational feeds.

## Alert and club decision log

For every displayed alert, persist an immutable record with `alert_id`, `club_id`, `event_id`, `issued_at`, `data_as_of_at`, `horizon_hours` (24/48/72), forecast target and interval, baseline, alert reason code, freshness age, and model/feed version. Record `lead_time_hours = kickoff_at - issued_at` and whether the alert was available at least 48 hours before kickoff; report its distribution, not only its average.

Append a decision record linked to `alert_id`: `decision_at`, `decision_status` (`accepted`, `rejected`, `deferred`, `no_action`, `unknown`), controlled action category (`pricing`, `promotion`, `advertising`, `pool/sector`, `other`, `none`), and optional aggregate rationale code. No personal or free-text rationale. Record subsequent decision revisions as new records. Pilot reporting must include alert count, freshness, lead-time distribution, decision status/action counts, and outcome coverage. These logs describe operational response; they do not establish that an action caused a sales or attendance change. Test intervention effectiveness separately with a preplanned control design.

## Local verification before connecting a feed

Run `python -m ml.rolling72_club_pilot_validate_v1 path/to/aggregates.jsonl`
from the repository root. Supply UTF-8 JSONL, one metric record per line.
The command reports row count and error codes without printing field values.
Observed bucket data must be known at or after bucket close. Inventory rows
require a stable opaque pool code such as `all` for an event-wide pool.
Use the separate reconciliation record for final attendance. This command
checks the five operational metric families and rejects attendance records.
Validation checks structure and clocks. Source identity, ledger reconciliation
and authorization require evidence from the club.
