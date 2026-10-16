-- C1 Alpha Training Export v2
-- Adds the existing PIT-safe T-24h Ticketing Challenger hybrid signal to the
-- v1 full-trajectory payload. No outcome-derived fields from the challenger
-- view are exported.

begin;

create or replace function public.export_c1_alpha_training_payload_v2()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with base as (
  select public.export_c1_alpha_training_payload_v1() as payload
), eligible_ids as (
  select (value->>'ticket_event_id')::bigint as ticket_event_id
  from base,
       jsonb_array_elements(payload->'events') value
), hybrid as (
  select
    d.ticket_event_id,
    d.checkpoint_at,
    d.feature_snapshot_id,
    d.feature_snapshot_captured_at,
    d.hybrid_v6::double precision as hybrid_v6,
    d.hybrid_v6_source,
    d.release_activity_flag,
    d.sector_coverage_change_flag,
    d.feature_quality
  from public.ticketing_challenger_dataset_v1 d
  join eligible_ids e on e.ticket_event_id=d.ticket_event_id
), hybrid_json as (
  select coalesce(
    jsonb_agg(to_jsonb(h) order by h.ticket_event_id),
    '[]'::jsonb
  ) as value
  from hybrid h
)
select
  (select payload from base)
  || jsonb_build_object(
       'version','c1-alpha-training-export-v2',
       'ticketingChallengerContract',jsonb_build_object(
         'checkpoint','T-24h',
         'feature','hybrid_v6',
         'definition','matched sector 6h velocity pct-of-first per hour; raw 6h velocity fallback',
         'pit_rule','feature_snapshot_captured_at <= checkpoint_at',
         'missing_semantics','explicit missing; never imputed from outcome'
       ),
       'ticketingChallengerRows',(select value from hybrid_json)
     );
$function$;

revoke all on function public.export_c1_alpha_training_payload_v2() from public,anon,authenticated;
grant execute on function public.export_c1_alpha_training_payload_v2() to service_role;

commit;
