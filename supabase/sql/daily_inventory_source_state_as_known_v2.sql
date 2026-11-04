-- PREPARED, NOT APPLIED TO PROJECT. Independent, read-only research contract.
-- No frozen predictor/export/promotion function is modified by this migration.
begin;
create or replace function public.daily_inventory_source_state_as_known_v2(
 p_ticket_event_id bigint, p_as_of_at timestamptz
)
returns jsonb language plpgsql stable security definer
set search_path=pg_catalog,public,private set timezone='UTC' as $$
declare e public.ticket_events%rowtype;
begin
 if p_ticket_event_id is null or p_ticket_event_id<=0 or p_as_of_at is null
 or p_as_of_at>clock_timestamp() then raise exception 'SOURCE_STATE_INVALID_CUTOFF'; end if;
 select * into e from public.ticket_events where id=p_ticket_event_id;
 if not found then
  return jsonb_build_object('version','daily-inventory-source-state-as-known-v2',
   'ticket_event_id',p_ticket_event_id,'as_of_at',p_as_of_at,'status','EVENT_NOT_FOUND',
   'observations','[]'::jsonb,'production_change',false,'live_adjustment',0,'target_values_used',false);
 end if;
 if e.kickoff_at is null or p_as_of_at>=e.kickoff_at then raise exception 'SOURCE_STATE_PREMATCH_CUTOFF_REQUIRED'; end if;
 return jsonb_build_object(
  'version','daily-inventory-source-state-as-known-v2','ticket_event_id',e.id,'as_of_at',p_as_of_at,
  'status',case when e.created_at is null or e.created_at>p_as_of_at then 'EVENT_NOT_KNOWN_AS_OF'
                when e.provider is distinct from 'stellis' then 'UNSUPPORTED_PROVIDER' else 'SOURCE_STATE_EXPORT' end,
  'observations',case when e.created_at is null or e.created_at>p_as_of_at or e.provider is distinct from 'stellis'
   then '[]'::jsonb else coalesce((
    with eligible as (
     select r.*,
      case when jsonb_typeof(r.raw_metadata->'has_active_stage')='boolean'
           then (r.raw_metadata->>'has_active_stage')::boolean end as active,
      case when jsonb_typeof(r.raw_metadata->'show_available_tickets_count')='boolean'
           then (r.raw_metadata->>'show_available_tickets_count')::boolean end as show_count,
      (jsonb_typeof(r.raw_metadata) is distinct from 'object'
       or (r.raw_metadata ? 'has_active_stage' and jsonb_typeof(r.raw_metadata->'has_active_stage') is distinct from 'boolean')
       or (r.raw_metadata ? 'show_available_tickets_count' and jsonb_typeof(r.raw_metadata->'show_available_tickets_count') is distinct from 'boolean')) as invalid_flags
     from private.stellis_raw_observations_v1 r
     where r.club_slug=e.club_slug and r.external_event_id=e.external_event_id
      and r.captured_at<=p_as_of_at and r.created_at<=p_as_of_at
      and r.captured_at>=e.kickoff_at-interval '60 days'
      and r.kickoff_at=e.kickoff_at
    ), classified as (
     select r.*,r.availability_exposed and r.show_count is distinct from false as visible
     from eligible r
    )
    select jsonb_agg(jsonb_build_object(
      'raw_observation_id',r.id,'captured_at',r.captured_at,'raw_created_at',r.created_at,
      'known_at',greatest(r.captured_at,r.created_at),'source_version',r.source_version,
      'source_active',r.active,'source_visible',r.visible,'raw_available_total',r.available_total,
      'available_total',case when not r.invalid_flags and r.visible and r.active is distinct from false then r.available_total end,
      'status',case when r.invalid_flags then 'INVALID_SOURCE_METADATA'
                    when not r.visible then 'HIDDEN_SOURCE'
                    when r.active=false then 'INACTIVE_STAGE'
                    when r.available_total is null then 'VISIBLE_COUNT_MISSING'
                    when r.active is null then 'VISIBLE_LEGACY_STAGE_UNKNOWN' else 'VISIBLE_ACTIVE' end,
      'public_snapshot_id',case when r.promoted_at<=p_as_of_at and r.promoted_ticket_event_id=e.id
                                  and s.id is not null then s.id end,
      'promotion_known_at',case when r.promoted_at<=p_as_of_at and r.promoted_ticket_event_id=e.id
                                  and s.id is not null then r.promoted_at end
     ) order by r.captured_at,r.id)
     from classified r left join public.snapshots s on s.id=r.promoted_snapshot_id
       and s.ticket_event_id=e.id and s.source='stellis_visible_available'
       and s.captured_at=r.captured_at and s.available_total is not distinct from r.available_total
   ),'[]'::jsonb) end,
  'raw_table_immutability_independently_proven',false,
  'historical_event_revisions_independently_proven',false,
  'production_change',false,'live_adjustment',0,'target_values_used',false
 );
end; $$;
revoke all on function public.daily_inventory_source_state_as_known_v2(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.daily_inventory_source_state_as_known_v2(bigint,timestamptz) to service_role;
commit;
