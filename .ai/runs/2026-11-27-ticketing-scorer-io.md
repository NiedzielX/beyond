# Ticketing scorer I/O optimization, 27 November

The working target is job 17, the legacy T-24 ticketing challenger. It runs
at minutes 04, 19, 34 and 49. Prior runs failed around 120s and the error
context pointed to the global feature-store query. A ticketing-class call
increased Postgres temporary writes by about 484 MiB. The instance's
physical Disk I/O budget remains unmeasured by these checks.

Three lower-cost agents independently reviewed the query, checked live
catalog and logs, and built PostgreSQL parity fixtures. Root built the
bounded selector, reviewed the original catalog definitions and wrote the
apply guard and rollback. The scorer keeps a same-statement unresolved
queue and the original formula, point-in-time guards and write cardinality.
The feature selector evaluates only unresolved event keys at T-24. It
keeps the outcome and reference joins that can multiply rows and omits
the unused weather join because the deployed selector is unique per
event/horizon. The helper stays private and service-only.

At 12:46 Warsaw a read-only probe of the exact selector body over the four
known unresolved event IDs completed in 0.383 seconds and returned two
feature rows, both without a numeric velocity. This is a bounded selector
smoke, not full scorer parity or a measured Disk I/O reduction. The live
definition/owner/ACL/role/cron guard passed without applying the change.

Local PostgreSQL parity must pass before applying any changes. A guarded
apply concatenates guard then core SQL in one transaction. Rollback checks
the optimized function body before restoring the exact pre-change scorer
body and dropping only the private helper. Job 17 needs a natural
scheduled cycle after apply and a fresh temporary-block delta for proof.
