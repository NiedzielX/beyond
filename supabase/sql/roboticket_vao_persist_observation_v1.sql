-- Beyond Ticketing — Roboticket VAO persistence contract v1
--
-- Atomic persistence boundary for the Wisla VAO collector.
-- Always records a complete VAO source observation in private raw evidence.
-- Creates a public ticket snapshot only when selectable_seats > 0.
-- selectable_seats = 0 is valid raw evidence but is never promoted as inventory.

create or replace function public.persist_roboticket_vao_observation_v1(
  p_ticket_event_id bigint,
  p_club_slug text,
  p_external_event_id text,
  p_captured_at timestamptz,
  p_geometry_seats integer,
  p_vao_key_count integer,
  p_response_unique_ids integer,
  p_extra_response_ids integer,
  p_selectable_seats integer,
  p_rights_true integer,
  p_occ_counts jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_event public.ticket_events%rowtype;
  v_raw_id bigint;
  v_snapshot_id bigint;
  v_status text;
begin
  select * into v_event
  from public.ticket_events
  where id=p_ticket_event_id
  for share;

  if not found then
    raise exception 'ticket_event_id % not found',p_ticket_event_id;
  end if;

  if v_event.provider <> 'roboticket' then
    raise exception 'event % is not Roboticket',p_ticket_event_id;
  end if;

  if v_event.club_slug is distinct from p_club_slug
     or v_event.external_event_id is distinct from p_external_event_id then
    raise exception 'event identity mismatch for %',p_ticket_event_id;
  end if;

  if p_club_slug <> 'wislakrakow' then
    raise exception 'VAO v1 persistence is hard-scoped to wislakrakow';
  end if;

  if p_captured_at is null
     or p_captured_at > clock_timestamp() + interval '2 minutes'
     or p_captured_at >= v_event.kickoff_at then
    raise exception 'invalid capture timestamp for event %',p_ticket_event_id;
  end if;

  if p_geometry_seats < 1000
     or p_vao_key_count <= 0
     or p_response_unique_ids < p_geometry_seats
     or p_extra_response_ids <> p_response_unique_ids - p_geometry_seats
     or p_selectable_seats < 0
     or p_selectable_seats > p_geometry_seats
     or p_rights_true < 0
     or p_rights_true > p_geometry_seats
     or p_occ_counts is null then
    raise exception 'invalid VAO observation counters for event %',p_ticket_event_id;
  end if;

  v_status := case when p_selectable_seats > 0
    then 'PUBLIC_SELECTABLE_SEATS'
    else 'NO_PUBLIC_SELECTABLE_SEATS'
  end;

  insert into private.roboticket_vao_observations_v1(
    ticket_event_id,club_slug,external_event_id,captured_at,
    geometry_seats,vao_key_count,response_unique_ids,geometry_matched_rows,
    extra_response_ids,selectable_seats,rights_true,occ_counts,status,
    source_version,production_change
  ) values (
    p_ticket_event_id,p_club_slug,p_external_event_id,p_captured_at,
    p_geometry_seats,p_vao_key_count,p_response_unique_ids,p_geometry_seats,
    p_extra_response_ids,p_selectable_seats,p_rights_true,p_occ_counts,v_status,
    'roboticket-vao-collect-v1',false
  ) returning id into v_raw_id;

  if p_selectable_seats > 0 then
    insert into public.snapshots(
      event_id,source,captured_at,ticket_event_id,event_match_date_at_capture,
      event_kickoff_at_capture,available_total,sector_count
    ) values (
      case when p_external_event_id ~ '^\d+$' then p_external_event_id::bigint else null end,
      'roboticket_vao_selectable_v1',p_captured_at,p_ticket_event_id,
      v_event.match_date,v_event.kickoff_at,p_selectable_seats,null
    ) returning id into v_snapshot_id;

    update private.roboticket_vao_observations_v1
    set promoted_snapshot_id=v_snapshot_id
    where id=v_raw_id;
  end if;

  return jsonb_build_object(
    'version','roboticket-vao-persist-v1',
    'raw_observation_id',v_raw_id,
    'status',v_status,
    'selectable_seats',p_selectable_seats,
    'promoted_snapshot_id',v_snapshot_id,
    'production_change',false
  );
end;
$function$;

revoke all on function public.persist_roboticket_vao_observation_v1(
  bigint,text,text,timestamptz,integer,integer,integer,integer,integer,integer,jsonb
) from public,anon,authenticated;
grant execute on function public.persist_roboticket_vao_observation_v1(
  bigint,text,text,timestamptz,integer,integer,integer,integer,integer,integer,jsonb
) to service_role;
