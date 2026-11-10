# Rolling72 v2: actual-time paired shadow ledger

Date: 2026-11-09. Status: IMPLEMENTATION SPECIFICATION, before code or activation.

This implements the separate prospective stage already authorised in
`ml/artifacts/rolling72_v2/precommit.json` and
`2026-11-08-rolling-72h-offline-training-and-shadow-v2.md`. No model fitting,
retuning, old forecast backfill, production activation or frozen v1 change.

## Contract

- New SQLite application/schema and immutable lane freeze, separate from every
  existing ledger. Freeze binds actual time, exact source-code hashes, the trusted
  private model manifest and the original precommitted identity-registry bytes.
- Public API: `create_freeze(destination, artifactdir, registrybytes)`,
  `capture(database, sourcebytes, artifactdir, freeze, registrybytes)`,
  `score(database, sourcebytes, artifactdir, freeze, registrybytes)`, `report(database)`.
  There is no issue-time argument. Tests may opt into synthetic artifacts explicitly;
  those freezes and ledgers stay synthetic and are rejected by normal calls.
- Input receipt is verified from original supplied bytes. All observation/event
  knowledge clocks equal its genuine retrieval bound and must precede actual issue.
  Supplied hashes verify a copy, not independent upstream authenticity.
- Registry SHA must be the exact v2 precommit binding. Provider/club identity must
  agree. Known aliases share a fixture group; choose the lowest ticket-event ID before
  labels and refuse alias metadata conflicts. Unknown/new registry identities are
  blocked pending a separately declared registry receipt; they are never guessed.
- Current contiguous exact-key segment only is passed to v1 canonical features.
  Earlier segments stay in the original source and lineage. Invalid observations in
  the current segment remain invalid; first-point segments are supported. Max live
  age is one hour for the whole comparison. Availability is not paid sales/attendance.
- Frozen learned v2, persistence, observed drift and unavailable/supported pickup
  receive exactly the same canonical issue, nominal targets and later accepted label.
  Learned model must already be frozen; excluded training fixtures are not predicted.
  Persist every status, but only READY numeric values before their future target.
- New issue clocks are actual wallclock, with a bounded 90-second computation/write
  allowance. Duplicate issues are refused. Global original snapshot IDs bind owner
  and material payload across capture/score, including rows not yet target-mature.
- First accepted genuine later label and all paired errors are immutable. The v2
  label guard additionally refuses any unusable/intervening source state, not only
  a bad endpoint. Existing v1 matcher stays unchanged.
- Report each 24/48/72h independently, event-balanced MAE/bias, exact paired
  candidate-baseline cohorts, pending and mature unmatched targets. Empty is not zero
  MAE. Current identities are exposed/unverified: eligible-new count remains zero,
  formal 30-new-fixture/8-club gate CLOSED. No historical validation MAE is created.
- Defaults `production_change=false`, `live_adjustment=0`; separate availability
  errors do not establish the approximately 1200-seat attendance objective.

## Acceptance

Meaningful synthetic integration tests must prove actual-time paired capture and
scoring, receipt/freeze/model/foreign-schema rejection, immutability and rollback,
source transitions and invalid interval handling, first-point support, honest
missing metrics and equal-event/paired cohort accounting. Real activation and
private recovery are later parent-owned steps requiring actual evidence.
