-- Stellis state-transition hardening v1.
-- Preserve the ~9 minute cadence dedup only when the observed state is
-- unchanged. A visibility transition or inventory change must be persisted
-- immediately, otherwise the booking-curve opening point can be lost.

alter table public.stellis_event_candidates_v1
  drop constraint if exists stellis_candidate_status;

alter table public.stellis_event_candidates_v1
  add constraint stellis_candidate_status
  check (status in (
    'discovered',
    'collecting',
    'hidden_availability',
    'awaiting_fixture',
    'non_league',
    'invalid'
  ));

create or replace function public.insert_stellis_raw_observation_v1(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_id bigint;
  v_captured timestamptz := coalesce((p_payload->>'captured_at')::timestamptz,clock_timestamp());
  v_visibility boolean := coalesce((p_payload->>'availability_exposed')::boolean,false);
  v_available integer := nullif(p_payload->>'available_total','')::integer;
  v_sold integer := nullif(p_payload->>'sold_total','')::integer;
begin
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'STELLIS_INVALID_PAYLOAD';
  end if;
  if coalesce((p_payload->>'target_values_used')::boolean,false) then
    raise exception 'STELLIS_TARGET_USE_REJECTED';
  end if;
  if v_captured > clock_timestamp() + interval '2 minutes' then
    raise exception 'STELLIS_CAPTURE_FROM_FUTURE';
  end if;
  if nullif(p_payload->>'club_slug','') is null or nullif(p_payload->>'external_event_id','') is null then
    raise exception 'STELLIS_IDENTITY_REQUIRED';
  end if;
  if not exists (
    select 1 from public.stellis_clubs_v1 c
    where c.club_slug=p_payload->>'club_slug' and c.active
  ) then
    raise exception 'STELLIS_CLUB_NOT_ACTIVE';
  end if;

  -- Deduplicate only an unchanged state. Inventory movement or a transition
  -- from hidden -> visible must be recorded immediately even inside 9 minutes.
  if exists (
    select 1
    from private.stellis_raw_observations_v1 r
    where r.club_slug=p_payload->>'club_slug'
      and r.external_event_id=p_payload->>'external_event_id'
      and r.captured_at > v_captured - interval '9 minutes'
      and r.captured_at <= v_captured + interval '1 minute'
      and r.availability_exposed = v_visibility
      and r.available_total is not distinct from v_available
      and r.sold_total is not distinct from v_sold
      and r.home_club_key is not distinct from nullif(p_payload->>'home_club_key','')
      and r.away_club_key is not distinct from nullif(p_payload->>'away_club_key','')
      and r.kickoff_at is not distinct from nullif(p_payload->>'kickoff_at','')::timestamptz
  ) then
    return jsonb_build_object(
      'version','stellis-raw-insert-v1.1',
      'inserted',false,
      'reason','recent_unchanged_observation',
      'target_values_used',false,
      'production_change',false
    );
  end if;

  insert into private.stellis_raw_observations_v1(
    club_slug,external_event_id,captured_at,event_name,home_team,away_team,
    home_club_key,away_club_key,kickoff_at,availability_exposed,available_total,
    sold_total,source_url,source_version,raw_metadata
  ) values (
    p_payload->>'club_slug',p_payload->>'external_event_id',v_captured,
    p_payload->>'event_name',p_payload->>'home_team',p_payload->>'away_team',
    nullif(p_payload->>'home_club_key',''),nullif(p_payload->>'away_club_key',''),
    nullif(p_payload->>'kickoff_at','')::timestamptz,v_visibility,v_available,v_sold,
    p_payload->>'source_url',coalesce(nullif(p_payload->>'source_version',''),'stellis-collector-v3'),
    coalesce(p_payload->'raw_metadata','{}'::jsonb)
  ) returning id into v_id;

  return jsonb_build_object(
    'version','stellis-raw-insert-v1.1',
    'inserted',true,
    'raw_observation_id',v_id,
    'target_values_used',false,
    'production_change',false
  );
end;
$function$;

revoke all on function public.insert_stellis_raw_observation_v1(jsonb) from public,anon,authenticated;
grant execute on function public.insert_stellis_raw_observation_v1(jsonb) to service_role;
