-- Stellis ingestion v1
-- PIT-safe ticket availability collection for clubs using Stellis.
-- Only explicitly exposed visible availability may enter model-facing snapshots.
-- Hidden availability / sold-only evidence remains private and does not alter P9/P7 inputs.

create table if not exists public.stellis_clubs_v1 (
  club_slug text primary key,
  club_name text not null,
  base_url text not null,
  source_domain text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.stellis_event_candidates_v1 (
  club_slug text not null references public.stellis_clubs_v1(club_slug),
  external_event_id text not null,
  event_name text,
  home_team text,
  away_team text,
  home_club_key text,
  away_club_key text,
  kickoff_at timestamptz,
  source_url text not null,
  availability_exposed boolean not null default false,
  available_total integer,
  sold_total integer,
  status text not null default 'discovered',
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  primary key(club_slug,external_event_id),
  constraint stellis_candidate_available_nonnegative check (available_total is null or available_total >= 0),
  constraint stellis_candidate_sold_nonnegative check (sold_total is null or sold_total >= 0),
  constraint stellis_candidate_status check (status in ('discovered','collecting','hidden_availability','non_league','invalid'))
);

create table if not exists private.stellis_raw_observations_v1 (
  id bigint generated always as identity primary key,
  club_slug text not null,
  external_event_id text not null,
  captured_at timestamptz not null default clock_timestamp(),
  event_name text,
  home_team text,
  away_team text,
  home_club_key text,
  away_club_key text,
  kickoff_at timestamptz,
  availability_exposed boolean not null,
  available_total integer,
  sold_total integer,
  source_url text not null,
  source_version text not null,
  raw_metadata jsonb not null default '{}'::jsonb,
  promoted_ticket_event_id bigint references public.ticket_events(id),
  promoted_snapshot_id bigint references public.snapshots(id),
  promoted_at timestamptz,
  created_at timestamptz not null default clock_timestamp(),
  constraint stellis_raw_available_nonnegative check (available_total is null or available_total >= 0),
  constraint stellis_raw_sold_nonnegative check (sold_total is null or sold_total >= 0),
  constraint stellis_raw_visible_requires_available check (not availability_exposed or available_total is not null)
);

create index if not exists stellis_raw_lookup_idx
  on private.stellis_raw_observations_v1(club_slug,external_event_id,captured_at desc);

create or replace function public.insert_stellis_raw_observation_v1(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_id bigint;
  v_captured timestamptz := coalesce((p_payload->>'captured_at')::timestamptz,clock_timestamp());
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

  if exists (
    select 1
    from private.stellis_raw_observations_v1 r
    where r.club_slug=p_payload->>'club_slug'
      and r.external_event_id=p_payload->>'external_event_id'
      and r.captured_at > v_captured - interval '9 minutes'
      and r.captured_at <= v_captured + interval '1 minute'
  ) then
    return jsonb_build_object(
      'version','stellis-raw-insert-v1',
      'inserted',false,
      'reason','recent_observation',
      'target_values_used',false,
      'production_change',false
    );
  end if;

  insert into private.stellis_raw_observations_v1(
    club_slug,external_event_id,captured_at,event_name,home_team,away_team,home_club_key,away_club_key,kickoff_at,
    availability_exposed,available_total,sold_total,source_url,source_version,raw_metadata
  ) values (
    p_payload->>'club_slug',p_payload->>'external_event_id',v_captured,p_payload->>'event_name',p_payload->>'home_team',p_payload->>'away_team',
    p_payload->>'home_club_key',p_payload->>'away_club_key',nullif(p_payload->>'kickoff_at','')::timestamptz,
    coalesce((p_payload->>'availability_exposed')::boolean,false),nullif(p_payload->>'available_total','')::integer,
    nullif(p_payload->>'sold_total','')::integer,p_payload->>'source_url',coalesce(nullif(p_payload->>'source_version',''),'stellis-collector-v1'),
    coalesce(p_payload->'raw_metadata','{}'::jsonb)
  ) returning id into v_id;

  return jsonb_build_object(
    'version','stellis-raw-insert-v1',
    'inserted',true,
    'raw_observation_id',v_id,
    'target_values_used',false,
    'production_change',false
  );
end;
$function$;

create or replace function public.promote_stellis_visible_observations_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v record;
  v_fixture record;
  v_raw record;
  v_fixture_count integer;
  v_ticket_event_id bigint;
  v_snapshot_id bigint;
  v_promoted_events integer := 0;
  v_promoted_snapshots integer := 0;
begin
  for v in
    select distinct on (r.club_slug,r.external_event_id)
      r.*,c.source_domain
    from private.stellis_raw_observations_v1 r
    join public.stellis_clubs_v1 c on c.club_slug=r.club_slug and c.active
    where r.availability_exposed
      and r.available_total is not null
      and r.kickoff_at is not null
      and r.kickoff_at > clock_timestamp()
    order by r.club_slug,r.external_event_id,r.captured_at desc
  loop
    if v.home_club_key is null or v.away_club_key is null or v.home_club_key <> v.club_slug then
      continue;
    end if;

    select count(*) into v_fixture_count
    from (
      select distinct s.source_event_id
      from public.sporting_league_matches_shadow s
      join private.structural_prior_club_aliases_v1 ha
        on ha.alias=s.home_team and ha.is_active and ha.club_key=v.home_club_key
      join private.structural_prior_club_aliases_v1 aa
        on aa.alias=s.away_team and aa.is_active and aa.club_key=v.away_club_key
      where s.event_date=(v.kickoff_at at time zone 'Europe/Warsaw')::date
    ) q;

    if v_fixture_count <> 1 then
      update public.stellis_event_candidates_v1
        set status='non_league',last_seen_at=clock_timestamp()
        where club_slug=v.club_slug and external_event_id=v.external_event_id;
      continue;
    end if;

    select distinct on (s.source_event_id)
      s.home_team,s.away_team,s.event_date
    into v_fixture
    from public.sporting_league_matches_shadow s
    join private.structural_prior_club_aliases_v1 ha
      on ha.alias=s.home_team and ha.is_active and ha.club_key=v.home_club_key
    join private.structural_prior_club_aliases_v1 aa
      on aa.alias=s.away_team and aa.is_active and aa.club_key=v.away_club_key
    where s.event_date=(v.kickoff_at at time zone 'Europe/Warsaw')::date
    order by s.source_event_id,s.fetched_at desc;

    insert into public.ticket_events(
      provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,source_url,
      mapping_source,mapping_confidence,club_slug,source_domain,updated_at
    ) values (
      'stellis',v.external_event_id,v_fixture.home_team,v_fixture.away_team,'Ekstraklasa',v_fixture.event_date,v.kickoff_at,v.source_url,
      'stellis-visible-availability-v1+league-fixture-date','verified',v.club_slug,v.source_domain,clock_timestamp()
    )
    on conflict(provider,source_domain,external_event_id) do update set
      home_team=excluded.home_team,
      away_team=excluded.away_team,
      competition=excluded.competition,
      match_date=excluded.match_date,
      kickoff_at=excluded.kickoff_at,
      source_url=excluded.source_url,
      mapping_source=excluded.mapping_source,
      mapping_confidence=excluded.mapping_confidence,
      updated_at=clock_timestamp()
    returning id into v_ticket_event_id;

    update public.stellis_event_candidates_v1
      set status='collecting',last_seen_at=clock_timestamp()
      where club_slug=v.club_slug and external_event_id=v.external_event_id;
    v_promoted_events := v_promoted_events + 1;

    for v_raw in
      select r.*
      from private.stellis_raw_observations_v1 r
      where r.club_slug=v.club_slug
        and r.external_event_id=v.external_event_id
        and r.availability_exposed
        and r.available_total is not null
        and r.promoted_snapshot_id is null
        and r.captured_at < v.kickoff_at
      order by r.captured_at
    loop
      insert into public.snapshots(
        event_id,source,captured_at,ticket_event_id,event_match_date_at_capture,event_kickoff_at_capture,available_total,sector_count
      ) values (
        case when v.external_event_id ~ '^\d+$' then v.external_event_id::bigint else null end,
        'stellis_visible_available',v_raw.captured_at,v_ticket_event_id,
        (v.kickoff_at at time zone 'Europe/Warsaw')::date,v.kickoff_at,v_raw.available_total,null
      ) returning id into v_snapshot_id;

      update private.stellis_raw_observations_v1
        set promoted_ticket_event_id=v_ticket_event_id,promoted_snapshot_id=v_snapshot_id,promoted_at=clock_timestamp()
        where id=v_raw.id;
      v_promoted_snapshots := v_promoted_snapshots + 1;
    end loop;
  end loop;

  return jsonb_build_object(
    'version','stellis-visible-promotion-v1',
    'promoted_event_iterations',v_promoted_events,
    'promoted_snapshots',v_promoted_snapshots,
    'production_change',false
  );
end;
$function$;

revoke all on public.stellis_clubs_v1 from anon,authenticated;
revoke all on public.stellis_event_candidates_v1 from anon,authenticated;
revoke all on private.stellis_raw_observations_v1 from public,anon,authenticated;
revoke all on function public.insert_stellis_raw_observation_v1(jsonb) from public,anon,authenticated;
revoke all on function public.promote_stellis_visible_observations_v1() from public,anon,authenticated;
grant select on public.stellis_clubs_v1 to service_role;
grant select,insert,update on public.stellis_event_candidates_v1 to service_role;
grant execute on function public.insert_stellis_raw_observation_v1(jsonb) to service_role;
grant execute on function public.promote_stellis_visible_observations_v1() to service_role;
