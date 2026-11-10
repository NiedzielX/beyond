# Rolling72 paired shadow v2 implementation

Date: 2026-11-09. Scope delegated by the parent agent under the user's explicit
request for parallel continuing work. Parent owns publication, real fit, activation,
canonical status and private recovery; this subtask performs none of those actions.

## Goal and authorised contract

Implement a small separate prospective evidence ledger under
`ml/artifacts/rolling72_v2/precommit.json`, without changing frozen v1 source,
parameters, old predictions or workers. Specification was written before code:
`.ai/specs/2026-11-09-rolling72-paired-shadow-v2.md`.

## Changes

- New `ml/rolling72_paired_shadow_v2.py` provides actual-time freeze, paired capture,
  first-label immutable scoring and read-only per-horizon reports.
- Distinct SQLite application ID `0x52374C32`; exact eight-table namespace. Freeze
  binds actual time, trusted model manifest, original pinned registry and all reused
  source-code dependencies. Synthetic models require explicit test mode throughout.
- Reuses frozen input/label/baseline functions without editing them. Current
  contiguous exact-key segment enters canonical features; all raw rows and prior
  incompatible segment IDs stay in lineage/source registration. Invalid current
  state is not cleaned away. A one-hour freshness limit applies symmetrically.
- Provider/club and each supplied domain/URL/external-ID must agree with the
  registry. Independent audit found the initially ignored conflicting URL/domain
  combination; fixed and covered by a rejection test.
- Actual write clock is read after SQLite locking/inserts, immediately before
  commit; a delay beyond90seconds rolls the transaction back. No issue-time input.
- Each accepted label scores all READY models on the same issue/target. Intervening
  source-key transitions and invalid states block labels. Old snapshot revisions
  roll back the complete source/score transaction.
- Reports independent fixture-balanced MAE/bias and exact paired candidate-baseline
  cohorts, pending/mature missing targets. Empty score cohorts remain missing.
  All current identities remain exposed/unverified; formal30new/8club gate CLOSED.

## Verification and limits

20 synthetic integration tests pass, including same-input/target pairing,
first-observation support, exact identity fields, foreign-ledger refusal,
synthetic-default rejection, actual final write clock, transaction rollback,
immutable labels/scores and unequal fixture-frequency accounting. Tests fit only
an explicitly synthetic artifact in a temporary directory; no real fit/refit.
Python compilation and `git diff --check` pass.

This is locally tested implementation, not published/activated collection or an
end-to-end source→private recovery proof. Parent and sibling tasks own those next
steps. No prospective MAE has been observed by this subtask. Availability error
does not establish the approximately1200-seat attendance objective. Defaults remain
`production_change=false`, `live_adjustment=0`.
