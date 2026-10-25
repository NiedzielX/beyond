-- Future fixture ingestion watchdog v1.
-- Reverse direction from the sporting schedule: every upcoming Ekstraklasa
-- home fixture should have an onboarded source and either a canonical event or
-- a safely identified candidate/buffer. Missing items become SCHEDULE_GAP.

create or replace view public.dashboard_ticketing_fixture_coverage_v1 as
with latest_fixture as (
  select distinct on (s.source_event_id)
    s.source_event_id,s.event_date,s.home_team,s.away_team,s.round_number,s.season,s.fetched_at
  from public.sporting_league_matches_shadow s
  where s.event_date > current_date
    and s.event_date <= current_date + 28
  order by s.source_event_id,s.fetched_at desc
), mapped as (
  select f.*,ha.club_key home_club_key,aa.club_key away_club_key
  from latest_fixture f
  left join private.structural_prior_club_aliases_v1 ha on ha.is_active and ha.alias=f.home_team
  left join private.structural_prior_club_aliases_v1 aa on aa.is_active and aa.alias=f.away_team
), source_registry as (
  select 'roboticket'::text source_family,c.club_slug,c.club_name,c.base_url,a.club_key
  from public.roboticket_clubs c
  join private.structural_prior_club_aliases_v1 a on a.is_active and lower(a.alias)=lower(c.club_name)
  where c.active
  union all
  select 'stellis',c.club_slug,c.club_name,c.base_url,a.club_key
  from public.stellis_clubs_v1 c
  join private.structural_prior_club_aliases_v1 a on a.is_active and lower(a.alias)=lower(c.club_name)
  where c.active
), coverage as (
  select
    m.source_event_id,m.event_date,m.round_number,m.season,m.home_team,m.away_team,
    m.home_club_key,m.away_club_key,m.fetched_at,
    sr.source_family,sr.club_slug source_club_slug,sr.club_name source_club_name,sr.base_url source_url,
    (
      select e.id
      from public.ticket_events e
      join private.structural_prior_club_aliases_v1 eh on eh.is_active and eh.alias=e.home_team
      join private.structural_prior_club_aliases_v1 ea on ea.is_active and ea.alias=e.away_team
      where e.provider in ('roboticket','stellis')
        and eh.club_key=m.home_club_key and ea.club_key=m.away_club_key
        and (e.kickoff_at at time zone 'Europe/Warsaw')::date between m.event_date-4 and m.event_date+4
      order by abs(((e.kickoff_at at time zone 'Europe/Warsaw')::date-m.event_date))
      limit 1
    ) as ticket_event_id,
    exists(
      select 1
      from public.stellis_event_candidates_v1 c
      where c.home_club_key=m.home_club_key
        and c.away_club_key=m.away_club_key
        and c.status not in ('non_league','invalid')
        and (c.kickoff_at is null or (c.kickoff_at at time zone 'Europe/Warsaw')::date between m.event_date-4 and m.event_date+4)
    ) as stellis_candidate,
    exists(
      select 1
      from private.roboticket_verified_schedule_v1 v
      join private.structural_prior_club_aliases_v1 vh on vh.is_active and vh.alias=v.home_team
      join private.structural_prior_club_aliases_v1 va on va.is_active and va.alias=v.away_team
      where vh.club_key=m.home_club_key and va.club_key=m.away_club_key
        and (v.kickoff_at at time zone 'Europe/Warsaw')::date between m.event_date-4 and m.event_date+4
    ) as robot_verified,
    exists(
      select 1
      from public.roboticket_event_candidates rc
      where rc.club_slug=sr.club_slug
        and rc.status in ('discovered','collecting')
        and coalesce(rc.metadata->>'candidate_kind','')='match'
        and rc.last_seen_at >= now()-interval '14 days'
        and exists(
          select 1 from private.structural_prior_club_aliases_v1 ah
          where ah.is_active and ah.club_key=m.home_club_key
            and position(private.normalize_ticketing_name_v1(ah.alias) in private.normalize_ticketing_name_v1(concat_ws(' ',rc.label,rc.metadata->>'anchor_aria_label',rc.metadata->>'direct_page_h1'))) > 0
        )
        and exists(
          select 1 from private.structural_prior_club_aliases_v1 aa
          where aa.is_active and aa.club_key=m.away_club_key
            and position(private.normalize_ticketing_name_v1(aa.alias) in private.normalize_ticketing_name_v1(concat_ws(' ',rc.label,rc.metadata->>'anchor_aria_label',rc.metadata->>'direct_page_h1'))) > 0
        )
    ) as robot_candidate
  from mapped m
  left join source_registry sr on sr.club_key=m.home_club_key
)
select
  source_event_id,event_date,round_number,season,home_team,away_team,home_club_key,away_club_key,
  source_family,source_club_slug,source_club_name,source_url,ticket_event_id,
  stellis_candidate,robot_verified,robot_candidate,fetched_at,
  case
    when home_club_key is null or away_club_key is null then 'IDENTITY_UNRESOLVED'
    when source_family is null then 'SOURCE_NOT_ONBOARDED'
    when ticket_event_id is not null then 'TRACKED'
    when stellis_candidate or robot_verified or robot_candidate then 'BUFFERING_OR_DISCOVERED'
    else 'SCHEDULE_GAP'
  end::text as coverage_status
from coverage;

grant select on public.dashboard_ticketing_fixture_coverage_v1 to anon,authenticated,service_role;

create or replace function private.refresh_dashboard_ticketing_ingestion_status_v2()
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_base jsonb;
  v_inserted integer := 0;
  v_total integer := 0;
begin
  v_base := private.refresh_dashboard_ticketing_ingestion_status_v1();

  insert into public.dashboard_ticketing_ingestion_status_v1(
    record_key,record_type,club_slug,club_name,external_event_id,label,candidate_kind,
    ingestion_status,kickoff_at,ticket_event_id,snapshot_count,first_snapshot_at,last_snapshot_at,
    raw_snapshot_count,first_raw_snapshot_at,last_raw_snapshot_at,source_url,mapping_source,
    issue_reason,first_seen_at,last_seen_at,refreshed_at
  )
  select
    'schedule:'||f.source_event_id,
    'schedule_gap',
    coalesce(f.source_club_slug,f.home_club_key),
    coalesce(f.source_club_name,f.home_team),
    f.source_event_id,
    f.home_team||' – '||f.away_team,
    'match',
    'SCHEDULE_GAP',
    null,
    null,
    0,null,null,0,null,null,
    f.source_url,
    'schedule-watchdog:'||coalesce(f.source_family,'unmapped'),
    case
      when f.source_family is null then 'upcoming league home fixture has no onboarded ticketing source; fixture date '||f.event_date::text
      else 'upcoming league home fixture has no canonical ticket event or protected candidate yet; fixture date '||f.event_date::text||'; source='||f.source_family
    end,
    f.fetched_at,f.fetched_at,clock_timestamp()
  from public.dashboard_ticketing_fixture_coverage_v1 f
  where f.coverage_status in ('SCHEDULE_GAP','SOURCE_NOT_ONBOARDED')
  on conflict(record_key) do nothing;

  get diagnostics v_inserted=row_count;
  select count(*)::int into v_total from public.dashboard_ticketing_ingestion_status_v1;

  return jsonb_build_object(
    'version','dashboard-ticketing-ingestion-status-v2.1',
    'base_refresh',v_base,
    'schedule_gap_rows',v_inserted,
    'row_count',v_total,
    'refreshed_at',clock_timestamp()
  );
end;
$function$;

-- Replace the old Roboticket-named dashboard cron with the multi-source watchdog refresh.
do $$
declare v_job bigint;
begin
  for v_job in
    select jobid from cron.job
    where jobname in ('roboticket_ingestion_dashboard_10m','ticketing_ingestion_dashboard_10m')
  loop
    perform cron.unschedule(v_job);
  end loop;
end $$;

select cron.schedule(
  'ticketing_ingestion_dashboard_10m',
  '9,19,29,39,49,59 * * * *',
  $$select private.refresh_dashboard_ticketing_ingestion_status_v2();$$
);

select private.refresh_dashboard_ticketing_ingestion_status_v2();
