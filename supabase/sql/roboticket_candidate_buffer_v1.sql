-- Roboticket candidate safety net v1
-- Prevents loss of booking-curve evidence when a genuine match is discovered
-- before exact kickoff/mapping has been promoted into public.ticket_events.
-- Raw candidate captures remain isolated from model-facing public.snapshots
-- until a verified schedule mapping exists.

create table if not exists private.roboticket_verified_schedule_v1 (
  club_slug text not null,
  external_event_id text not null,
  home_team text not null,
  away_team text not null,
  competition text not null default 'Ekstraklasa',
  kickoff_at timestamptz not null,
  source_url text not null,
  source_type text not null,
  verification_confidence text not null default 'verified',
  verified_at timestamptz not null default now(),
  promoted_ticket_event_id bigint references public.ticket_events(id),
  promoted_at timestamptz,
  primary key (club_slug, external_event_id),
  constraint roboticket_verified_schedule_future_identity check (length(trim(home_team))>0 and length(trim(away_team))>0),
  constraint roboticket_verified_schedule_confidence check (verification_confidence in ('verified','high'))
);

create table if not exists private.roboticket_candidate_snapshots_v1 (
  id bigint generated always as identity primary key,
  club_slug text not null,
  external_event_id text not null,
  captured_at timestamptz not null default now(),
  available_total integer,
  sector_count integer,
  state jsonb not null,
  source_url text,
  source_timestamp text,
  collector_version text not null,
  promoted_ticket_event_id bigint references public.ticket_events(id),
  promoted_snapshot_id bigint references public.snapshots(id),
  promoted_at timestamptz,
  created_at timestamptz not null default now(),
  constraint roboticket_candidate_snapshot_available check (available_total is null or available_total >= 0),
  constraint roboticket_candidate_snapshot_sector_count check (sector_count is null or sector_count >= 0),
  constraint roboticket_candidate_snapshot_state_object check (jsonb_typeof(state)='object')
);

create unique index if not exists roboticket_candidate_snapshots_identity_uq
  on private.roboticket_candidate_snapshots_v1(club_slug,external_event_id,captured_at);
create index if not exists roboticket_candidate_snapshots_lookup_idx
  on private.roboticket_candidate_snapshots_v1(club_slug,external_event_id,captured_at desc);

create or replace function public.insert_roboticket_candidate_snapshot_v1(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_club text;
  v_event text;
  v_captured timestamptz;
  v_available integer;
  v_sector_count integer;
  v_inserted_id bigint;
begin
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'ROBOTICKET_CANDIDATE_INVALID_PAYLOAD';
  end if;
  v_club := nullif(trim(p_payload->>'club_slug'),'');
  v_event := nullif(trim(p_payload->>'external_event_id'),'');
  v_captured := coalesce((p_payload->>'captured_at')::timestamptz,clock_timestamp());
  v_available := nullif(p_payload->>'available_total','')::integer;
  v_sector_count := nullif(p_payload->>'sector_count','')::integer;
  if v_club is null or v_event is null then raise exception 'ROBOTICKET_CANDIDATE_IDENTITY_REQUIRED'; end if;
  if v_captured > clock_timestamp() + interval '2 minutes' then raise exception 'ROBOTICKET_CANDIDATE_CAPTURE_FROM_FUTURE'; end if;
  if not exists (
    select 1 from public.roboticket_event_candidates c
    where c.club_slug=v_club and c.external_event_id=v_event
      and coalesce(c.metadata->>'candidate_kind','')='match'
  ) then
    raise exception 'ROBOTICKET_CANDIDATE_NOT_VERIFIED_MATCH';
  end if;
  if exists (
    select 1 from private.roboticket_candidate_snapshots_v1 s
    where s.club_slug=v_club and s.external_event_id=v_event
      and s.captured_at > v_captured - interval '9 minutes'
  ) then
    return jsonb_build_object('version','roboticket-candidate-buffer-v1','inserted',false,'reason','recent_candidate_snapshot','production_change',false);
  end if;

  insert into private.roboticket_candidate_snapshots_v1(
    club_slug,external_event_id,captured_at,available_total,sector_count,state,source_url,source_timestamp,collector_version
  ) values (
    v_club,v_event,v_captured,v_available,v_sector_count,
    coalesce(p_payload->'state','{}'::jsonb),p_payload->>'source_url',p_payload->>'source_timestamp',
    coalesce(nullif(p_payload->>'collector_version',''),'roboticket-candidate-buffer-v1')
  ) returning id into v_inserted_id;

  return jsonb_build_object('version','roboticket-candidate-buffer-v1','inserted',true,'candidate_snapshot_id',v_inserted_id,'target_values_used',false,'production_change',false);
end;
$function$;

create or replace function public.upsert_roboticket_verified_schedule_v1(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_club text := nullif(trim(p_payload->>'club_slug'),'');
  v_event text := nullif(trim(p_payload->>'external_event_id'),'');
begin
  if v_club is null or v_event is null then raise exception 'ROBOTICKET_SCHEDULE_IDENTITY_REQUIRED'; end if;
  if coalesce(p_payload->>'verification_confidence','verified') not in ('verified','high') then raise exception 'ROBOTICKET_SCHEDULE_NOT_VERIFIED'; end if;
  insert into private.roboticket_verified_schedule_v1(
    club_slug,external_event_id,home_team,away_team,competition,kickoff_at,source_url,source_type,verification_confidence,verified_at
  ) values (
    v_club,v_event,p_payload->>'home_team',p_payload->>'away_team',coalesce(nullif(p_payload->>'competition',''),'Ekstraklasa'),
    (p_payload->>'kickoff_at')::timestamptz,p_payload->>'source_url',coalesce(nullif(p_payload->>'source_type',''),'official_schedule'),
    coalesce(nullif(p_payload->>'verification_confidence',''),'verified'),clock_timestamp()
  )
  on conflict(club_slug,external_event_id) do update set
    home_team=excluded.home_team,away_team=excluded.away_team,competition=excluded.competition,kickoff_at=excluded.kickoff_at,
    source_url=excluded.source_url,source_type=excluded.source_type,verification_confidence=excluded.verification_confidence,verified_at=excluded.verified_at;
  return jsonb_build_object('version','roboticket-verified-schedule-v1','upserted',true,'club_slug',v_club,'external_event_id',v_event,'production_change',false);
end;
$function$;

create or replace function public.promote_roboticket_verified_candidates_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v record;
  r record;
  v_ticket_event_id bigint;
  v_snapshot_id bigint;
  v_promoted_events integer := 0;
  v_backfilled integer := 0;
begin
  for v in
    select s.*,c.base_url,c.source_domain
    from private.roboticket_verified_schedule_v1 s
    join public.roboticket_clubs c on c.club_slug=s.club_slug and c.active
    where s.kickoff_at > clock_timestamp()
  loop
    insert into public.ticket_events(
      provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,source_url,
      mapping_source,mapping_confidence,club_slug,source_domain,updated_at
    ) values (
      'roboticket',v.external_event_id,v.home_team,v.away_team,v.competition,
      (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,v.source_url,
      'roboticket_discovery_v6+verified_schedule','verified',v.club_slug,v.source_domain,clock_timestamp()
    )
    on conflict(provider,source_domain,external_event_id) do update set
      home_team=excluded.home_team,away_team=excluded.away_team,competition=excluded.competition,
      match_date=excluded.match_date,kickoff_at=excluded.kickoff_at,source_url=excluded.source_url,
      mapping_source=excluded.mapping_source,mapping_confidence=excluded.mapping_confidence,updated_at=clock_timestamp()
    returning id into v_ticket_event_id;

    update private.roboticket_verified_schedule_v1
      set promoted_ticket_event_id=v_ticket_event_id,promoted_at=coalesce(promoted_at,clock_timestamp())
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
    update public.roboticket_event_candidates
      set status='collecting',metadata=metadata || jsonb_build_object('promoted_ticket_event_id',v_ticket_event_id,'promotion_version','roboticket-candidate-buffer-v1')
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
    v_promoted_events := v_promoted_events + 1;

    for r in
      select * from private.roboticket_candidate_snapshots_v1
      where club_slug=v.club_slug and external_event_id=v.external_event_id
        and promoted_snapshot_id is null and captured_at < v.kickoff_at
      order by captured_at
    loop
      insert into public.snapshots(
        event_id,source,captured_at,ticket_event_id,event_match_date_at_capture,event_kickoff_at_capture,available_total,sector_count
      ) values (
        case when v.external_event_id ~ '^\d+$' then v.external_event_id::bigint else null end,
        'roboticket_candidate_backfill',r.captured_at,v_ticket_event_id,
        (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,r.available_total,r.sector_count
      ) returning id into v_snapshot_id;

      insert into public.sector_inventory(snapshot_id,event_id,sector,available)
      select v_snapshot_id,
             case when v.external_event_id ~ '^\d+$' then v.external_event_id::bigint else null end,
             x->>'sector',coalesce((x->>'available')::integer,0)
      from jsonb_array_elements(coalesce(r.state->'sectors','[]'::jsonb)) x
      where nullif(x->>'sector','') is not null;

      insert into public.sector_price_area_observations_v1(
        ticket_event_id,snapshot_id,captured_at,sector,sector_source_id,price_area_id,price_area_name,available,source
      )
      select v_ticket_event_id,v_snapshot_id,r.captured_at,x->>'sector',nullif(x->>'sectorSourceId','')::bigint,
             (x->>'priceAreaId')::integer,x->>'priceAreaName',coalesce((x->>'available')::integer,0),'roboticket_candidate_backfill'
      from jsonb_array_elements(coalesce(r.state->'sectorPriceAreas','[]'::jsonb)) x
      where nullif(x->>'sector','') is not null and nullif(x->>'priceAreaId','') is not null;

      insert into public.ticket_price_observations_v1(
        ticket_event_id,snapshot_id,captured_at,price_area_id,price_area_name,price_type_id,price_type_name,price,currency,source
      )
      select v_ticket_event_id,v_snapshot_id,r.captured_at,(x->>'priceAreaId')::integer,x->>'priceAreaName',
             (x->>'priceTypeId')::integer,x->>'priceTypeName',(x->>'price')::numeric,x->>'currency','roboticket_candidate_backfill'
      from jsonb_array_elements(coalesce(r.state->'prices','[]'::jsonb)) x
      where nullif(x->>'priceAreaId','') is not null and nullif(x->>'priceTypeId','') is not null and nullif(x->>'price','') is not null;

      update private.roboticket_candidate_snapshots_v1
        set promoted_ticket_event_id=v_ticket_event_id,promoted_snapshot_id=v_snapshot_id,promoted_at=clock_timestamp()
        where id=r.id;
      v_backfilled := v_backfilled + 1;
    end loop;
  end loop;

  return jsonb_build_object(
    'version','roboticket-candidate-promotion-v1','promoted_event_iterations',v_promoted_events,
    'backfilled_candidate_snapshots',v_backfilled,'production_change',false
  );
end;
$function$;

create or replace view public.dashboard_ticketing_ingestion_v1 as
with snapshot_stats as (
  select ticket_event_id,count(*)::integer as snapshot_count,min(captured_at) as first_snapshot_at,max(captured_at) as last_snapshot_at
  from public.snapshots where ticket_event_id is not null group by ticket_event_id
), raw_stats as (
  select club_slug,external_event_id,count(*)::integer as raw_snapshot_count,min(captured_at) as first_raw_snapshot_at,max(captured_at) as last_raw_snapshot_at
  from private.roboticket_candidate_snapshots_v1 group by club_slug,external_event_id
), tracked as (
  select
    'tracked'::text as record_type,e.club_slug,c.club_name,e.external_event_id,
    (e.home_team || ' – ' || e.away_team)::text as label,'match'::text as candidate_kind,
    case when e.kickoff_at < now() then 'COMPLETED_TRACKED' else 'TRACKED' end::text as ingestion_status,
    e.kickoff_at,e.id as ticket_event_id,coalesce(ss.snapshot_count,0) as snapshot_count,ss.first_snapshot_at,ss.last_snapshot_at,
    0::integer as raw_snapshot_count,null::timestamptz as first_raw_snapshot_at,null::timestamptz as last_raw_snapshot_at,
    e.source_url,e.mapping_source,null::text as issue_reason,e.created_at as first_seen_at,e.updated_at as last_seen_at
  from public.ticket_events e
  left join public.roboticket_clubs c on c.club_slug=e.club_slug
  left join snapshot_stats ss on ss.ticket_event_id=e.id
  where e.provider='roboticket'
), candidates as (
  select
    'candidate'::text as record_type,rc.club_slug,c.club_name,rc.external_event_id,rc.label,
    coalesce(rc.metadata->>'candidate_kind','unknown') as candidate_kind,
    case
      when te.id is not null then 'TRACKED'
      when coalesce(rc.metadata->>'candidate_kind','') <> 'match' then 'NON_MATCH_EXCLUDED'
      when vs.kickoff_at is not null then 'READY_TO_PROMOTE'
      when coalesce(rs.raw_snapshot_count,0)>0 then 'BUFFERING_AWAITING_KICKOFF'
      else 'MATCH_DISCOVERED_NO_BUFFER'
    end::text as ingestion_status,
    vs.kickoff_at,te.id as ticket_event_id,coalesce(ss.snapshot_count,0) as snapshot_count,ss.first_snapshot_at,ss.last_snapshot_at,
    coalesce(rs.raw_snapshot_count,0) as raw_snapshot_count,rs.first_raw_snapshot_at,rs.last_raw_snapshot_at,
    coalesce(vs.source_url,rc.source_url) as source_url,te.mapping_source,
    case
      when te.id is not null then null
      when coalesce(rc.metadata->>'candidate_kind','') <> 'match' then 'product is not a first-team match'
      when vs.kickoff_at is null and coalesce(rs.raw_snapshot_count,0)>0 then 'exact kickoff pending; raw curve protected'
      when vs.kickoff_at is null then 'exact kickoff pending and candidate buffer has no snapshot yet'
      else 'verified schedule exists; promotion pending'
    end::text as issue_reason,
    rc.first_seen_at,rc.last_seen_at
  from public.roboticket_event_candidates rc
  left join public.roboticket_clubs c on c.club_slug=rc.club_slug
  left join public.ticket_events te on te.provider='roboticket' and te.club_slug=rc.club_slug and te.external_event_id=rc.external_event_id
  left join private.roboticket_verified_schedule_v1 vs on vs.club_slug=rc.club_slug and vs.external_event_id=rc.external_event_id
  left join raw_stats rs on rs.club_slug=rc.club_slug and rs.external_event_id=rc.external_event_id
  left join snapshot_stats ss on ss.ticket_event_id=te.id
)
select * from tracked
union all
select * from candidates where ticket_event_id is null;

revoke all on private.roboticket_verified_schedule_v1 from public,anon,authenticated;
revoke all on private.roboticket_candidate_snapshots_v1 from public,anon,authenticated;
revoke all on function public.insert_roboticket_candidate_snapshot_v1(jsonb) from public,anon,authenticated;
revoke all on function public.upsert_roboticket_verified_schedule_v1(jsonb) from public,anon,authenticated;
revoke all on function public.promote_roboticket_verified_candidates_v1() from public,anon,authenticated;
grant execute on function public.insert_roboticket_candidate_snapshot_v1(jsonb) to service_role;
grant execute on function public.upsert_roboticket_verified_schedule_v1(jsonb) to service_role;
grant execute on function public.promote_roboticket_verified_candidates_v1() to service_role;
grant select on public.dashboard_ticketing_ingestion_v1 to anon,authenticated,service_role;
