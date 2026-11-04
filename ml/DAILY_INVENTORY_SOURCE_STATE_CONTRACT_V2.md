# Public-inventory source state as known v2

Date: 2026-11-04. Status: prepared; isolated RPC→feature integration passed; project deployment blocked. This is new source-information infrastructure, not a new forecast or a change to frozen daily/attendance lanes.

The RPC alone passed 11 new isolated PostgreSQL tests alongside 9 existing persistence contracts in run 41814622537. The complete chain passed in hosted run41816696989:20PostgreSQLcontracts,13feature-adaptertests, actual SQL→feature-row conversion, pinned DB→panel parser, Deno typecheck/policy/HTTPchecks. No live function has been applied. Earlier adapter integration failed due to absent NumPy in the isolated job; the existing pinned dependency was added, with no SQL/model semantic change.

## Why

The public snapshot export drops original source active/visible metadata and receipt times. Existing raw Stellis rows retain `captured_at`, `created_at`, `availability_exposed`, parser version and source metadata. Source-off zeros and active inventory are different, while a genuinely exposed literal 0 must remain 0.

## Separate contract

`public.daily_inventory_source_state_as_known_v2(ticket_event_id,as_of_at)` is service-role-only and read-only. It is not called by v1 inference or any frozen workflow.

- Reject future or non-pre-match cutoffs.
- Require the tracked event's original `created_at<=as_of_at`; a later-created event is not historically available merely because its source capture date is older.
- Return only matching raw source identities with both `captured_at<=as_of_at` and `created_at<=as_of_at`. Do not emit counts or values of future/late rows.
- `known_at=max(captured_at,created_at)`. Current promotion links are returned only if `promoted_at<=as_of_at`and the linked snapshot matches event/source/time/value; otherwise the public snapshot ID remains null.
- `source_active` is the original explicit boolean or null for legacy absence. Invalid types fail closed as metadata-invalid; absence is not false.
- `source_visible` requires factual exposed availability and no explicit hidden-count flag. Hidden/inactive/malformed records keep a null model-usable count; original raw count remains separately identified for audit. Explicit visible 0 with active or unknown legacy stage remains 0.
- `raw_observation_id`,`raw_created_at`,`source_version`and known timestamp identify provenance. Returned metadata does not establish cryptographic/raw-table immutability. Event creation proves existence, not every historical revision of mutable team/kickoff metadata; original raw identity/time must be preserved by the next experiment.

## Fixed feature adapter

`ml.daily_inventory_source_state_features_v2` independently validates the receipt/capture/known-time relationship, source IDs, flags/count consistency and promotion time. It returns seven fixed fields: latest usable count, latest active/visible flags, source age, active-stage knowledge fraction, active fraction given known state, and visible fraction. Unknown values remain null with explicit missing masks; unknown active state is neverfalse. Genuine visible 0 has a nonmissing count of 0.

The 48-hour summaries select the latest genuine capture/id per UTC hour without interpolation. Fractions describe selected observations, not continuous time coverage. Malformed hours reduce the active-knowledge fraction, and latest invalid state never falls back to an older usable count. Parser versions, selected source identities and a response hash remain provenance. These fields do not establish actual on-sale duration or paid demand and do not authorize a model fit.

The adapter accepts only declared source fields; joined outcome/score columns fail closed. Its output is a separate object. Never append v2numeric columns to a frozen incumbent fitting frame:the generic Structural Prior selector discovers numeric columns dynamically, as the earlier C2baseline-isolation fix demonstrated. A future challenger must predeclare its feature list and leave the baseline input frame unchanged.

## Boundaries

Do not join today's audit flags onto old snapshots. Do not remove historical inactive zeros from frozen v1 or reinterpret Widzew's literal zero as missing. Any use in a new dataset requires its own version, input contract and evaluation. This RPC reconstructs only already persisted source information; it does not create observations or missed forecasts. No old prediction, score, source record or model is rewritten.

`production_change=false`, `live_adjustment=0`, `target_values_used=false`.
