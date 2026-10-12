-- Follow-up for Event Context Layer v0.1.
-- source_record_key may be NULL; a normal UNIQUE index still allows multiple NULLs,
-- while PostgREST can infer the full-column conflict target used by the collector.

drop index if exists public.uq_event_context_source_record;
create unique index uq_event_context_source_record
    on public.event_context_observations(ticket_event_id, feature_key, source_name, source_record_key);
