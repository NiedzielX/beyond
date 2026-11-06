-- Operator diagnostic, NOT a migration. Run with database administrator access.
-- Read-only statistics and estimated plans; no ANALYZE, DDL, resets or cleanup.
-- Keep results private: query IDs and system statistics, no SQL literal text.
-- Record TWO snapshots >=60 seconds apart to compute rates. Cumulative totals
-- alone do not establish today's cause or Supabase physical-disk budget usage.
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SET LOCAL lock_timeout = '1s';
SET LOCAL search_path = pg_catalog, public, extensions;

SELECT clock_timestamp() AS captured_at, current_database() AS database,
       current_setting('server_version') AS postgres_version,
       pg_postmaster_start_time() AS server_started_at;

SELECT datname, stats_reset, blks_read, blks_hit, temp_files, temp_bytes,
       blk_read_time, blk_write_time, deadlocks
FROM pg_stat_database WHERE datname = current_database();

SELECT schemaname, relname, seq_scan, seq_tup_read, idx_scan,
       n_live_tup, n_dead_tup, n_mod_since_analyze,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'private', 'storage')
ORDER BY seq_tup_read DESC LIMIT 25;

SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname IN ('public', 'private', 'storage')
ORDER BY idx_tup_read DESC LIMIT 25;

SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname IN ('public', 'private')
  AND tablename IN ('snapshots', 'sector_snapshots',
                    'c1_shadow_v8_predictions_v1', 'c1_shadow_v8_event_scores_v1');

-- Supabase normally enables pg_stat_statements. If unavailable, report that
-- limitation; do not install an extension or reset its counters for this audit.
SELECT e.extname, n.nspname AS extension_schema
FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace
WHERE e.extname = 'pg_stat_statements';

-- JSON field access tolerates PostgreSQL/extension timing-column renames.
SELECT s.queryid, s.calls, s.rows, s.shared_blks_read, s.shared_blks_hit,
       s.shared_blks_written, s.temp_blks_read, s.temp_blks_written,
       COALESCE(to_jsonb(s)->>'total_exec_time', to_jsonb(s)->>'total_time') AS total_exec_ms,
       COALESCE(to_jsonb(s)->>'shared_blk_read_time', to_jsonb(s)->>'blk_read_time') AS block_read_ms
FROM pg_stat_statements s
WHERE s.dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
ORDER BY s.shared_blks_read DESC LIMIT 20;

EXPLAIN (COSTS TRUE, FORMAT JSON)
SELECT id, captured_at FROM public.snapshots
WHERE ticket_event_id = 5091 AND captured_at <= now()
ORDER BY captured_at DESC, id DESC LIMIT 1;

ROLLBACK;
-- PostgreSQL16+ optional, execute as a separate read-only query if available:
-- SELECT backend_type, object, context, reads, read_time, writes, write_time,
--        evictions, fsyncs, stats_reset FROM pg_stat_io;
