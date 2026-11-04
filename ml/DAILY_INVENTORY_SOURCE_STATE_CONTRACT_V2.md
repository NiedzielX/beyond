# Public-inventory source state as known v2

Date:2026-11-04. Status:prepared; isolated database validation pending. This is new source-information infrastructure, not a new forecast or a change to frozen daily/attendance lanes.

## Why

The public snapshot export drops original source active/visible metadata and receipt times. Existing raw Stellis rows retain `captured_at`, `created_at`, `availability_exposed`, parser version and source metadata. Source-off zeros and active inventory are different, while a genuinely exposed literal0must remain0.

## Separate contract

`public.daily_inventory_source_state_as_known_v2(ticket_event_id,as_of_at)`is service-role-only and read-only. It is not called by v1inference or any frozen workflow.

- Reject future or non-pre-match cutoffs.
- Require the tracked event's original `created_at<=as_of_at`; a later-created event is not historically available merely because its source capture date is older.
- Return only matching raw source identities with both `captured_at<=as_of_at`and`created_at<=as_of_at`. Do not emit counts or values of future/late rows.
- `known_at=max(captured_at,created_at)`. Current promotion links are returned only if `promoted_at<=as_of_at`and the linked snapshot matches event/source/time/value; otherwise the public snapshot ID remainsnull.
- `source_active`is the original explicit boolean ornullfor legacy absence. Invalid types fail closed as metadata-invalid; absence is notfalse.
- `source_visible`requires factual exposed availability and no explicit hidden-count flag. Hidden/inactive/malformed records keep a null model-usable count; original raw count remains separately identified for audit. Explicit visible0with active or unknown legacy stage remains0.
- `raw_observation_id`,`raw_created_at`,`source_version`and known timestamp identify provenance. Returned metadata does not establish cryptographic/raw-table immutability. Event creation proves existence, not every historical revision of mutable team/kickoff metadata; original raw identity/time must be preserved by the next experiment.

## Boundaries

Do not join today's audit flags onto old snapshots. Do not remove historical inactive zeros from frozen v1or reinterpret Widzew's literal zero as missing. Any use in a new dataset requires its own version, input contract and evaluation. This RPC reconstructs only already persisted source information; it does not create observations or missed forecasts. No old prediction, score, source record or model is rewritten.

`production_change=false`, `live_adjustment=0`, `target_values_used=false`.
