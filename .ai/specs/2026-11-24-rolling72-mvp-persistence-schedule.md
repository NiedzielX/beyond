# Finite PERS issuance/scoring schedule

24 November 2026. Root owns integration; independent reviewer owns SQL review.
Parent: [P0-4c](2026-11-23-rolling72-mvp-persistence-issuance.md).

P0-4c passed ten isolated PostgreSQL16 tests and independent exact-hash review.
Its hosted lane activated at15:05:13.023044UTC, before any new fixture source
seal existed. Automate actual future calls without reconstructing an earlier
issue or changing the source capture job, collectors or frozen experiments.

Add one named job `rolling72_mvp_persistence_v1_tick`, schedule
`0-59/5 * * * *`. The source job runs one minute earlier. Each tick calls
issue(25) only before the issue cutoff, then score(100) through the score
cutoff. Missing configuration or expired scoring cutoff removes this job.
After issue cutoff, the scorer continues through the label-only grace.

Installation must verify the exact active PERS manifest
`22290ba42d6f93d63c694c93ed77401e12c943040a0ee298739d9fbef26391ad`,
source manifest binding, issue cutoff1December00:00UTC and score cutoff
4December06:00UTC. An existing job is accepted only if its command, schedule,
active state, database and owner match exactly; otherwise fail without changes.

Acceptance: independent exact-file review; isolated PostgreSQL guard exercise
with stub cron functions covering installation/retry, issue+score, score-only,
expiry/missing-config removal, conflicting-job refusal and unchanged old job;
hosted post-install comparison of all previous jobs and protected function
bodies; actual genuine source→issue proof separately. No credentials, paid
changes, source import, old-lane mutation or production adjustment.
