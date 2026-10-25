# P7 Long168 Prospective v1 — Bootstrap Addendum

Frozen: **2026-10-25, before the first prospective prediction was persisted**.

This addendum clarifies the bootstrap rule in `P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`.

## No bootstrap backfill

When the prospective lane starts, historical eligible 6h buckets that already existed before the lane became operational are **not** backfilled into the immutable prospective ledger.

For each event, the first prospective run may persist only the **latest currently known eligible snapshot/bucket** while the run itself occurs in the `72 < hours_to_kickoff <= 168` window.

Later scheduled runs may persist later previously unseen eligible snapshot identities as they genuinely arrive.

Therefore:

- prediction persistence time itself must be inside the P7 Long168 window;
- old T-168..T-72 snapshots are not converted retroactively into "prospective" predictions;
- repeated rows from the same event remain dependent observations; the independent unit stays `ticket_event`;
- no outcome information motivated this clarification;
- production remains unchanged.
