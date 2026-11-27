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

The three parity/rollback tests passed on PG16 from the release copy,
and GitHub Actions 45994019147 passed for commit 517f74c. The guarded
migration succeeded before 12:54 Warsaw. Catalog readback matched the
new body, retained job 17's exact command and schedule, and found all
three Rolling72 jobs active. The helper ran under service_role against
the four pending keys in 0.314 seconds (two selector rows, zero numeric).
Anonymous and authenticated roles cannot execute it.

The last pre-change natural cycle at 12:49 Warsaw took 89.012 s and
wrote 61,888 temporary blocks (~483.5 MiB) for the monitored statement.
The first post-change natural cycle is due at 13:04 Warsaw. Compare its
cron outcome, the new insert statement's temp counters, and the old
statement's call delta. The read-only smoke is not a cron-cycle result
and supplies no physical Disk IO percentage.
[Machine proof](../../ml/TICKETING_SCORER_IO_DEPLOYMENT_PROOF_2026-11-27.json).

The natural 13:04 Warsaw production cycle succeeded in 0.592 s. The
tracked pg_stat_statements entry advanced by one call and zero temporary
blocks read or written. All three Rolling72 jobs were active and their
most recent runs succeeded. This is one scheduled cycle; host I/O budget
consumption remains unmeasured.
[Scheduled proof](../../ml/TICKETING_SCORER_IO_FIRST_SCHEDULED_PROOF_2026-11-27.json).
