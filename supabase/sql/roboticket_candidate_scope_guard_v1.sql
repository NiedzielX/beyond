-- Roboticket candidate scope guard + dashboard cache v1.
-- Defense in depth: candidate buffering is allowed only for a pair of known
-- football clubs from the canonical alias universe (or a verified schedule).
-- Public dashboard data is materialized into an RLS-protected cache table.

create or replace function private.normalize_ticketing_name_v1(p_value text)
returns text
language sql
immutable
strict
set search_path='private'
as $function$
  select trim(regexp_replace(
    translate(lower(p_value),'ąćęłńóśźż','acelnoszz'),
    '[^a-z0-9]+',' ','g'
  ));
$function$;

create or replace function private.roboticket_candidate_football_club_keys_v1(p_text text)
returns text[]
language sql
stable
security invoker
set search_path='public','private'
as $function$
  select coalesce(array_agg(distinct a.club_key order by a.club_key),array[]::text[])
  from private.structural_prior_club_aliases_v1 a
  where a.is_active
    and position(
      ' ' || private.normalize_ticketing_name_v1(a.alias) || ' '
      in ' ' || private.normalize_ticketing_name_v1(coalesce(p_text,'')) || ' '
    ) > 0;
$function$;

create or replace function private.roboticket_candidate_is_known_football_match_v1(
  p_club_slug text,
  p_text text
)
returns boolean
language sql
stable
security invoker
set search_path='public','private'
as $function$
with club as (
  select club_name from public.roboticket_clubs where club_slug=p_club_slug limit 1
), home_key as (
  select a.club_key
  from private.structural_prior_club_aliases_v1 a, club c
  where a.is_active
    and private.normalize_ticketing_name_v1(a.alias)=private.normalize_ticketing_name_v1(c.club_name)
  order by a.club_key
  limit 1
), keys as (
  select private.roboticket_candidate_football_club_keys_v1(p_text) as value
)
select
  exists(select 1 from private.roboticket_verified_schedule_v1 s where s.club_slug=p_club_slug and s.external_event_id is not null and s.kickoff_at>now())
  or (
    cardinality((select value from keys)) >= 2
    and (
      (select club_key from home_key) is null
      or (select club_key from home_key)=any((select value from keys))
      or p_club_slug=any((select value from keys))
    )
  );
$function$;

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
  v_candidate_text text;
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

  select concat_ws(' ',c.label,c.metadata->>'anchor_aria_label',c.metadata->>'direct_page_h1')
    into v_candidate_text
  from public.roboticket_event_candidates c
  where c.club_slug=v_club and c.external_event_id=v_event
    and coalesce(c.metadata->>'candidate_kind','')='match'
  limit 1;
  if v_candidate_text is null then raise exception 'ROBOTICKET_CANDIDATE_NOT_VERIFIED_MATCH'; end if;
  if not private.roboticket_candidate_is_known_football_match_v1(v_club,v_candidate_text) then
    raise exception 'ROBOTICKET_CANDIDATE_NOT_KNOWN_FOOTBALL_PAIR';
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

create table if not exists public.dashboard_ticketing_ingestion_status_v1 (
  record_key text primary key,
  record_type text not null,
  club_slug text,
  club_name text,
  external_event_id text,
  label text,
  candidate_kind text,
  ingestion_status text not null,
  kickoff_at timestamptz,
  ticket_event_id bigint,
  snapshot_count integer not null default 0,
  first_snapshot_at timestamptz,
  last_snapshot_at timestamptz,
  raw_snapshot_count integer not null default 0,
  first_raw_snapshot_at timestamptz,
  last_raw_snapshot_at timestamptz,
  source_url text,
  mapping_source text,
  issue_reason text,
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  refreshed_at timestamptz not null default now()
);

alter table public.dashboard_ticketing_ingestion_status_v1 enable row level security;
revoke all on public.dashboard_ticketing_ingestion_status_v1 from public;
grant select on public.dashboard_ticketing_ingestion_status_v1 to anon,authenticated,service_role;
drop policy if exists dashboard_ticketing_ingestion_status_public_read on public.dashboard_ticketing_ingestion_status_v1;
create policy dashboard_ticketing_ingestion_status_public_read
  on public.dashboard_ticketing_ingestion_status_v1
  for select to anon,authenticated
  using (true);

create or replace function private.refresh_dashboard_ticketing_ingestion_status_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare v_count integer;
begin
  truncate table public.dashboard_ticketing_ingestion_status_v1;

  insert into public.dashboard_ticketing_ingestion_status_v1(
    record_key,record_type,club_slug,club_name,external_event_id,label,candidate_kind,ingestion_status,kickoff_at,
    ticket_event_id,snapshot_count,first_snapshot_at,last_snapshot_at,raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
    source_url,mapping_source,issue_reason,first_seen_at,last_seen_at,refreshed_at
  )
  with snapshot_stats as (
    select ticket_event_id,count(*)::integer snapshot_count,min(captured_at) first_snapshot_at,max(captured_at) last_snapshot_at
    from public.snapshots where ticket_event_id is not null group by ticket_event_id
  ), raw_stats as (
    select club_slug,external_event_id,count(*)::integer raw_snapshot_count,min(captured_at) first_raw_snapshot_at,max(captured_at) last_raw_snapshot_at
    from private.roboticket_candidate_snapshots_v1 group by club_slug,external_event_id
  ), tracked as (
    select
      'event:'||e.id::text record_key,'tracked'::text record_type,e.club_slug,c.club_name,e.external_event_id,
      (e.home_team||' – '||e.away_team)::text label,'match'::text candidate_kind,
      case when e.kickoff_at<now() then 'COMPLETED_TRACKED' else 'TRACKED' end::text ingestion_status,
      e.kickoff_at,e.id ticket_event_id,coalesce(ss.snapshot_count,0) snapshot_count,ss.first_snapshot_at,ss.last_snapshot_at,
      0::integer raw_snapshot_count,null::timestamptz first_raw_snapshot_at,null::timestamptz last_raw_snapshot_at,
      e.source_url,e.mapping_source,null::text issue_reason,e.created_at first_seen_at,e.updated_at last_seen_at
    from public.ticket_events e
    left join public.roboticket_clubs c on c.club_slug=e.club_slug
    left join snapshot_stats ss on ss.ticket_event_id=e.id
    where e.provider='roboticket'
  ), candidate_base as (
    select rc.*,c.club_name,te.id ticket_event_id,te.kickoff_at tracked_kickoff,te.mapping_source,
      vs.kickoff_at verified_kickoff,coalesce(rs.raw_snapshot_count,0) raw_snapshot_count,rs.first_raw_snapshot_at,rs.last_raw_snapshot_at,
      concat_ws(' ',rc.label,rc.metadata->>'anchor_aria_label',rc.metadata->>'direct_page_h1') candidate_text
    from public.roboticket_event_candidates rc
    left join public.roboticket_clubs c on c.club_slug=rc.club_slug
    left join public.ticket_events te on te.provider='roboticket' and te.club_slug=rc.club_slug and te.external_event_id=rc.external_event_id
    left join private.roboticket_verified_schedule_v1 vs on vs.club_slug=rc.club_slug and vs.external_event_id=rc.external_event_id
    left join raw_stats rs on rs.club_slug=rc.club_slug and rs.external_event_id=rc.external_event_id
  ), candidates as (
    select
      'candidate:'||club_slug||':'||external_event_id record_key,'candidate'::text record_type,club_slug,club_name,external_event_id,label,
      coalesce(metadata->>'candidate_kind','unknown') candidate_kind,
      case
        when ticket_event_id is not null then 'TRACKED'
        when coalesce(metadata->>'candidate_kind','')='non_match' then 'NON_MATCH_EXCLUDED'
        when coalesce(metadata->>'candidate_kind','')<>'match' then 'UNKNOWN_EXCLUDED'
        when not private.roboticket_candidate_is_known_football_match_v1(club_slug,candidate_text) then 'NON_FOOTBALL_EXCLUDED'
        when verified_kickoff is not null then 'READY_TO_PROMOTE'
        when raw_snapshot_count>0 then 'BUFFERING_AWAITING_KICKOFF'
        else 'MATCH_DISCOVERED_NO_BUFFER'
      end::text ingestion_status,
      coalesce(tracked_kickoff,verified_kickoff) kickoff_at,ticket_event_id,0::integer snapshot_count,
      null::timestamptz first_snapshot_at,null::timestamptz last_snapshot_at,
      raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,
      coalesce((select source_url from private.roboticket_verified_schedule_v1 s where s.club_slug=candidate_base.club_slug and s.external_event_id=candidate_base.external_event_id),source_url) source_url,
      mapping_source,
      case
        when ticket_event_id is not null then null
        when coalesce(metadata->>'candidate_kind','')='non_match' then 'non-match product intentionally excluded'
        when coalesce(metadata->>'candidate_kind','')<>'match' then 'candidate identity insufficient'
        when not private.roboticket_candidate_is_known_football_match_v1(club_slug,candidate_text) then 'not a pair of known football clubs in the model universe'
        when verified_kickoff is null and raw_snapshot_count>0 then 'exact kickoff pending; raw curve protected'
        when verified_kickoff is null then 'exact kickoff pending and candidate buffer has no snapshot yet'
        else 'verified schedule exists; promotion pending'
      end::text issue_reason,
      first_seen_at,last_seen_at
    from candidate_base
  )
  select tracked.*,clock_timestamp() from tracked
  union all
  select candidates.*,clock_timestamp() from candidates where ticket_event_id is null;

  get diagnostics v_count=row_count;
  return jsonb_build_object('version','dashboard-ticketing-ingestion-status-v1','row_count',v_count,'refreshed_at',clock_timestamp());
end;
$function$;

revoke all on function private.normalize_ticketing_name_v1(text) from public;
revoke all on function private.roboticket_candidate_football_club_keys_v1(text) from public;
revoke all on function private.roboticket_candidate_is_known_football_match_v1(text,text) from public;
revoke all on function private.refresh_dashboard_ticketing_ingestion_status_v1() from public;

select private.refresh_dashboard_ticketing_ingestion_status_v1();

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='roboticket_ingestion_dashboard_10m' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;
select cron.schedule(
  'roboticket_ingestion_dashboard_10m',
  '9,19,29,39,49,59 * * * *',
  $$select private.refresh_dashboard_ticketing_ingestion_status_v1();$$
);
