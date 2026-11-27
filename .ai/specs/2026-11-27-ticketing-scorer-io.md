# Reduce I/O in the T-24 ticketing scorer

The 27 November investigation correlated one ticketing-class call with about
484 MiB of temporary writes. The scheduled scorer joins the broad feature
view before selecting unresolved prospective checkpoints. The deployed
feature function performs ranking and feature work across all events and five
horizons. The scorer uses two velocity columns from a single horizon.

Implement a separate private T-24 feature query restricted to unresolved event
IDs. Preserve exact 24–36 h boundaries, snapshot ties, first and six-hour
anchor selection, numeric rounding, fallback and all existing same-statement
PIT checks. Keep the original output rows, duplicate/error behavior, scoring
formula, owner, public function privileges and cron. Preserve multiplicity
from the outcome and inventory-reference joins. The deployed weather selector
returns at most one row per event/horizon and supplies no used field, so its
left join is redundant here. No write to the existing feature views.

Verify with isolated PostgreSQL cases for actual selector and insert parity,
including missing/late/null features, tie IDs, model training time, existing
predictions and join multiplicity. Verify that resolve calls are limited to
unresolved event keys. Guard any hosted apply against the reviewed source
definitions, function ACL/settings and a fresh check of the scheduled job.
Capture the original function definition for guarded rollback. The first
normal scheduled cycle verifies operation; reduced temporary blocks, rather
than elapsed time alone, is the I/O success measure.
