# Paired PERS–drift24 runtime

25 November2026. Status: READY FOR IMPLEMENTATION, not activated.
Parent contract: [fixed recipe and prospective evaluation](2026-11-24-rolling72-fresh-paired-drift24.md).
Root reviewed its corrected projection/issue clocks and latest-attempt rules.
The pure two-stage helper and thirteen synthetic tests are preparation evidence,
not live forecasts. No method, hyperparameter or selection criterion is changed.

## Ownership and scope

One writer: new `supabase/sql/rolling72_mvp_paired_drift24_v1.sql` only.
One tester: new `tests/postgres/test_rolling72_mvp_paired_drift24_v1.py` only.
Independent reviewer checks formulas, clocks, labels, denominators and ACLs.
Root owns integration, migration, immutable manifest, scheduling, CI and PR.
All existing source/PERS/E5/B/v5 functions, jobs, ledgers and grants are read-only
dependencies. Do not modify them or attach drift values to earlier PERS issues.

## Executable architecture

Lane `rolling72-mvp-paired-drift24-v1`, append-only private config, bundles,
six method predictions per bundle (24/48/72 × PERS/DRIFT24), source-candidate
attempts, one accepted shared label per bundle/horizon, score attempts and runs.
Store both absolute/signed errors on that one label or a derived projection,
never independent labels for the two methods. Denominator is source-eligible
candidates whose seal known_at is after comparator activation and before its
issue cutoff; preactivation/outside/refused/unattempted counts stay separate.
Earlier source seals may provide past history but may not create new origins.

Four service-only RPCs: `activate_rolling72_mvp_paired_drift24_v1(text,text)`,
`issue_rolling72_mvp_paired_drift24_v1(integer default25)`,
`score_rolling72_mvp_paired_drift24_v1(integer default100)`,
`get_rolling72_mvp_paired_drift24_v1_status()`. Empty search_path, UTC,
fully qualified objects, bounded limits, lane lock and unique guards. Private
tables have RLS/no direct application grants; ledgers reject update/delete/truncate.

Activation binds exact manifest bytes/SHA, source manifest/SQL, this SQL hash,
fixed method/horizons/24–30h anchor/90s latency/3600s source age/6h label age,
and finite cutoffs matching the source lane (including at least78h label grace).
No caller supplies values, labels or runtime clocks. Actual activation follows
validation. Same exact manifest retry is idempotent; drift fails closed.

## Clocks and shared forecast

Read origin seal, its committed attempt/registry/candidates and relevant
history/attempts in one consistent statement. Check immutable content/binding
hashes and full-XID committed visibility at RPC entry. An own or later-committed
source is deferred, not terminally refused. No mutable upstream reconstruction.

Stamp actual projection_reference_at after completed read, calculate both
methods' three values, stamp calculation_completed_at, then actual issued_at.
If the real clock ties, use the tested bounded actual-clock wait (one1us sleep,
then real clock, otherwise retryable40001). No timestamp arithmetic adjustment.
Targets use actual issued_at+h; values use the parent's explicit projection
reference age. Require source age<=3600s at actual issue and read-to-issue<=90s.
Kickoff eligibility is independent per horizon; keep all six method rows with
null values for outside targets. First point/zero issue PERS and paired PERS
fallback when no drift support; do not wait for24h history to issue.

## Anchor and label semantics

Copy the fixed parent anchor window, elapsed-hour slope and lower zero clamp;
no rounding, upper cap, fit or per-horizon variant. Require matching complete
sector and sector/price-area membership sets, registered identity/family/unit,
and no intervening known source break. Fallback reasons and drift-ready support
are explicit. The full drift policy including fallback is primary.

Scoring uses the parent's exact latest-attempt-per-snapshot selector before
validation. Newer invalid/unsealed observations prohibit older READY fallback;
unresolved unknown capture ordering refuses. A common label must be committed,
captured strictly after issue and at/before target, known by scoring read,
<=6h old at target, pre-kickoff and identity/hash valid. Valid scope changes
remain scored with flags. First accepted shared label is immutable.

Status has three separate horizon scorecards with event-balanced PERS/drift
MAE and delta (drift minus PERS), bias, P90/worst, support/fallback, future/due
labels and source/forecast/scoring coverage. Zero labels means null metrics.
Do not mix existing E5/PERS cohorts or claim attendance, causality or1200MAE.

## Verification and release

Dedicated loopback PG16 DB `rolling72_mvp_paired_drift24_test`, port55440,
ENV `ROLLING72_MVP_PAIRED_DRIFT24_TEST_DSN`; synthetic fixtures only.
Reuse existing source fixture helpers without discovering inherited suites or
resetting other DBs. Cover real shared clocks/zero/first point, exact formula,
anchor bounds/ties/PIT/breaks/membership, independent kickoff nulls, stale/refused
denominators, concurrency/idempotency, uncommitted visibility, latest invalid/
unknown/stale labels, genuine zero, unequal-event MAE, immutable labels and ACLs.
Synthetic past fixtures may exercise mature targets; no clock substitution or
hosted history backfill. Independent review and root release-copy verification
precede any activation; a scheduled future-only cycle proves issuance separately.

## Fixed decision evaluator (integration companion)

A pure-stdlib report may consume exported accepted shared-label facts; it never
queries the DB, fits a model, changes labels or generates predictions. Each row
must contain bundle_id, ticket_event_id, club_id, horizon_hours, actual,
pers_prediction and drift24_prediction. Require finite nonnegative numbers,
exact24/48/72 horizons, one row per bundle/horizon and a consistent event/club
mapping. Missing horizons stay empty, with null metrics. Each horizon reports
per-event MAE then its equal-event mean, signed bias and event-level P90/worst.
Bootstrap only the primary+72 paired per-event MAE differences:10,000 event
resamples with seed42 and fixed percentile95% interval. No snapshot resampling.
The support floor applies to accepted+72 events:30 independent events/8clubs.
Below floor is PARTIAL; absent+72 or guardrail horizons is UNKNOWN. With support,
SUPPORTED requires>=10%+72 reduction, upper95%delta<0 and both+24/+48 MAE<=PERS;
otherwise NOT_SUPPORTED. Accepted-label exports alone cannot establish forecast
or scoring coverage; the report explicitly leaves coverage to runtime status.
Synthetic tests cover unequal event size, duplicate/invalid input, no labels,
floors, fixed bootstrap, guardrails and accepted/rejected decisions. This fixed
report logic must precede new paired outcomes; no decision-rule tuning.
