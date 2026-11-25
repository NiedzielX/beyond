# Dashboard readiness cache I/O reduction
Date: 2026-11-24
Status: ACTIVE

## Goal and contracts

Remove the repeated full live-feature computation from the two aggregate
readiness functions called by `refresh_dashboard_safe_caches_v1()`, while
preserving every readiness count, threshold, status, field, and access grant.
The product output remains a dashboard cache, not a model/evidence writer.

Affected functions:

- `public.get_live_signal_study_readiness_v1()` and its caller
  `public.get_dashboard_ml_readiness_safe_v1()`;
- `public.get_dashboard_research_readiness_v2()`.

Existing point-in-time, frozen prediction, outcome, source, and model contracts
remain unchanged. No cron cadence, cache table, data row, global timeout,
`work_mem`, database statistics, or paid plan changes are included.

## Audit and ownership

At 2026-11-24 16:23:03 UTC the Supabase project reported `ACTIVE_HEALTHY`
(PostgreSQL 17.11). Read-only `cron.job_run_details` showed cache job 24 at
`:14` failing repeatedly at the 120-second statement timeout (latest observed
16:14:00–16:16:00 UTC). Its error stack named
`get_live_features_v1_asof` → `get_multiclub_feature_store_v2` →
`get_dashboard_research_readiness_v2` → the insert into the research-readiness
cache. Jobs 26 and 27 were succeeding at `:29` and `:44` in the inspected run
history; they are outside this change.

The active `get_dashboard_research_readiness_v2()` counts rows from
`crossclub_live_signal_study_rows_v2`. That view joins the baseline event rows
to `multiclub_feature_store_v4` by event. The live v4 view depends on v3, which
invokes the full `get_multiclub_feature_store_v2()` SQL function; v4 also joins
the weather feature function. The feature-store function selects up to five
event/horizon snapshot keys and then calculates full live features. Its
`get_live_features_v1_asof()` path window-scans each event's full snapshot
history and adjacent sector inventories. The inspected `sector_inventory`
relation has about 1,053,257 estimated rows / 135 MiB table size, while
`snapshots` has about 39,001 estimated rows. An `EXPLAIN (VERBOSE, COSTS,
SETTINGS, FORMAT JSON)` without `ANALYZE` of the readiness aggregate showed
opaque `Function Scan` nodes for both `get_multiclub_feature_store_v2()` and
`get_weather_feature_store_v1()` even though the aggregate only consumes event
and club keys plus row count.

The same cache refresh also calls `get_dashboard_ml_readiness_safe_v1()`,
which calls `get_live_signal_study_readiness_v1()`; that function counts
`live_signal_study_rows_v1`, whose view joins model-lab rows to the same
expensive multiclub feature store. A prior cache failure stack (12:14 UTC)
showed this alternate readiness path failing through the same live-feature
chain. The selected change optimizes both aggregate-only paths so the refresh
does not compute sector features merely to count keys.

The supplied `pg_stat_statements` snapshot has a stats reset of 2026-10-02
17:54:14 UTC. `refresh_dashboard_safe_caches_v1()` shows 3,227 cumulative
calls, 69.9 seconds mean execution time, and 255.2M/256.0M cumulative temp
read/write blocks. These are cumulative executor temporary-block counters,
not a current rate and not proof of physical disk I/O. Current read-only
settings show `work_mem=2184kB`; changing it is out of scope. A separate
read-only key-only query estimated a small indexed snapshot candidate plan
(total cost about 3,935) and returned 24 events, 11 clubs, 67 rows. The last
good cache had the same counts but was generated 2026-11-19, so this is a
sanity comparison only, not same-time output-parity proof.

Risk: medium. The implementation changes only aggregate SQL function bodies and
adds a private read-only key helper. Parent owns integration, tests, publication
and any hosted deployment. Independent review checks exact output and grants.

## Proposed optimization and equivalence invariants

Add a private, service-role-only helper that returns the unique
`(ticket_event_id, club_slug, horizon)` keys and selected `snapshot_id` from
the v2 feature-store candidate CTE. The snapshot ID supports tie-break parity
tests; neither output exposes feature values. It copies the exact five horizon labels/targets/tolerances,
eligibility predicates and deterministic tie-break order
`(hours_to_kickoff-target_hours ASC, captured_at DESC, snapshot_id DESC)` from
the active function. It does not read sector inventory or invoke any feature,
weather, cache, or write function.

Rewrite `get_dashboard_research_readiness_v2()` to join those keys to
`crossclub_baseline_rows_v2`, computing the existing distinct event count,
distinct club count and row count. This is cardinality-equivalent because:

1. The v2 feature function chooses exactly one row per `(event,horizon)` after
   the stated `ROW_NUMBER()` selection; its later feature calculations are
   left joins and do not filter those rows.
2. The v3 seat-map join is at most one row per event/type due to the existing
   `(ticket_event_id, reference_type)` primary key.
3. The v4 weather function returns at most one row per `(event,horizon)` by
   its own `ROW_NUMBER() ... WHERE rn=1`; its join is left-sided.
4. The baseline view yields at most one row per event because outcomes are
   keyed by event. The study view joins on event only, so each eligible
   `(event,horizon)` key contributes exactly one joined row.

Rewrite `get_live_signal_study_readiness_v1()` to join the same unique feature
keys to `get_model_lab_rows_v1()` on event and horizon, retaining its exact
`historical_p50 IS NOT NULL` filter and original outcome counts. The source
study view joins on event and horizon; its feature side is unique on that key,
so this preserves the number of strict rows and distinct model versions
without evaluating full feature values. Preserve the exact output column types,
thresholds, status strings, `now()` behavior, security-definer/invoker
semantics, and existing caller grants.

Implementation may not alter `get_multiclub_feature_store_v2()`, either
feature-store view, source tables, source collection cadence, existing cache
tables, or scheduled jobs. No hosted writes are authorized by this spec.

## Acceptance criteria

1. A synthetic isolated PostgreSQL 16/17 fixture exercises duplicate eligible
   snapshots, horizon ties, each target/tolerance boundary, a missing horizon,
   multiple model rows and outcomes, and missing seat-map/weather rows.
2. The original and replacement implementations return byte/value-identical
   readiness counts, boolean gates, status, targets and types; only
   `generated_at` may differ by call time. Compare both readiness functions
   and their dashboard-safe wrapper.
3. The helper returns at most one row per event/horizon and uses the exact live
   v2 candidate ordering and eligibility conditions. Result cardinality agrees
   with the current joined study views on the fixture.
4. The revised EXPLAIN without execution shows no call to
   `get_multiclub_feature_store_v2()`, `get_live_features_v1_asof()`, or
   `get_weather_feature_store_v1()` in either readiness plan. Benchmark with
   `EXPLAIN ANALYZE` only on an isolated fixture/database, never on the live
   project.
5. Existing function grants and security modes are unchanged. The helper is
   private, fully-qualified, `search_path=''`, read-only, and not executable by
   `PUBLIC`, `anon`, or `authenticated`. Existing service-role calls continue
   through the same endpoints.
6. The refresh job, schedules, cache schemas, grants, and old cache rows remain
   unchanged. A failed cache refresh retains the last successful cache values.
7. Live verification, if separately authorized by the integrator, compares
   function definitions/grants and executes only the exact readiness functions
   through a bounded run with a rollback or other reviewed approach; this spec
   itself performs no hosted write or deployment.

## Verification and delivery

Read-only evidence gathered from `pg_cron`, `pg_stat_statements`, active
function/view definitions, `pg_class` sizes/indexes and non-ANALYZE EXPLAIN is
recorded above. The helper/rewrite SQL is a review draft only. The parent owns
integration. Required next checks: compare exact hosted/local definitions,
implement on an isolated database, prove parity on fixtures, and review the
helper's function ownership/grants before considering any deployment.

## Result

Diagnosis: the failure is caused by repeated full feature-store evaluation on
an aggregate-only cache path. Executor temp-spill pressure is evidenced by
cumulative temp-block counters; physical I/O cause/rate is not established.
Proposed lightweight key-only rewrite is concrete and awaiting independent
review and isolated parity tests. No code or hosted state changed in this
diagnostic checkpoint.
