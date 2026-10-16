-- C1 Alpha v7 Split Context v1
--
-- PostgREST enforces a short statement timeout. The older all-in-one event
-- payload can cross that limit under concurrent scraper traffic. v7 therefore
-- fetches independent context pieces and composes them in GitHub Actions.
--
-- These exports are read-only, service-role-only and intentionally scoped to
-- the current C1-alpha 2026/27 Ekstraklasa evidence contract.

begin;

create or replace function public.export_c1_alpha_v7_events_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with eligible as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    o.actual_attendance,
    ha.club_key as home_club_key,
    aa.club_key as away_club_key
  from public.ticket_events e
  join public.ticket_event_outcomes o
    on o.ticket_event_id=e.id
   and o.actual_attendance is not null
  left join private.structural_prior_club_aliases_v1 ha
    on ha.alias=e.home_team and ha.is_active
  left join private.structural_prior_club_aliases_v1 aa
    on aa.alias=e.away_team and aa.is_active
  where e.kickoff_at<now()
    and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
), enriched as (
  select
    e.*,
    f.season as sporting_season,
    replace(f.season,'-','/') as season,
    f.round_number as round_no,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status
  from eligible e
  left join lateral (
    select s.season,s.round_number
    from public.sporting_league_matches_shadow s
    left join private.structural_prior_club_aliases_v1 sh
      on sh.alias=s.home_team and sh.is_active
    left join private.structural_prior_club_aliases_v1 sa
      on sa.alias=s.away_team and sa.is_active
    where s.event_date=(e.kickoff_at at time zone 'Europe/Warsaw')::date
      and sh.club_key=e.home_club_key
      and sa.club_key=e.away_club_key
    order by s.fetched_at desc
    limit 1
  ) f on true
  left join lateral (
    select c.stadium_capacity,c.source_name,c.source_url,c.verification_status
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key=e.home_club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=c.valid_from
      and (c.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=c.valid_to)
    order by c.valid_from desc,c.id desc
    limit 1
  ) cr on true
), usable as (
  select * from enriched
  where home_club_key is not null
    and away_club_key is not null
    and season is not null
    and round_no is not null
    and stadium_capacity is not null
), payload as (
  select coalesce(jsonb_agg(to_jsonb(u) order by u.kickoff_at,u.ticket_event_id),'[]'::jsonb) as rows
  from usable u
)
select jsonb_build_object(
  'version','c1-alpha-v7-events-v1',
  'eventCount',(select count(*) from usable),
  'events',(select rows from payload)
);
$function$;

create or replace function public.export_c1_alpha_v7_attendance_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with rows as (
  select a.*
  from public.ml_home_attendance_history_v2 a
  where a.competition_key='ekstraklasa'
    and a.season='2026/2027'
), payload as (
  select coalesce(jsonb_agg(to_jsonb(r) order by r.kickoff_at,r.club_slug),'[]'::jsonb) as value
  from rows r
)
select jsonb_build_object(
  'version','c1-alpha-v7-attendance-v1',
  'rowCount',(select count(*) from rows),
  'attendance',(select value from payload)
);
$function$;

create or replace function public.export_c1_alpha_v7_sporting_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with rows as (
  select s.*
  from public.sporting_league_matches_shadow s
  where s.season='2026-2027'
), payload as (
  select coalesce(jsonb_agg(to_jsonb(r) order by r.event_date,r.round_number,r.home_team),'[]'::jsonb) as value
  from rows r
)
select jsonb_build_object(
  'version','c1-alpha-v7-sporting-v1',
  'rowCount',(select count(*) from rows),
  'sportingMatches',(select value from payload)
);
$function$;

create or replace function public.export_c1_alpha_v7_aliases_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with rows as (
  select a.* from public.get_structural_prior_club_aliases_v1() a
), payload as (
  select coalesce(jsonb_agg(to_jsonb(r) order by r.alias),'[]'::jsonb) as value
  from rows r
)
select jsonb_build_object(
  'version','c1-alpha-v7-aliases-v1',
  'rowCount',(select count(*) from rows),
  'aliases',(select value from payload)
);
$function$;

create or replace function public.export_c1_alpha_v7_hybrid_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with eligible_ids as (
  select e.id as ticket_event_id
  from public.ticket_events e
  join public.ticket_event_outcomes o on o.ticket_event_id=e.id and o.actual_attendance is not null
  where e.kickoff_at<now()
    and private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
), rows as (
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
), payload as (
  select coalesce(jsonb_agg(to_jsonb(r) order by r.ticket_event_id),'[]'::jsonb) as value
  from rows r
)
select jsonb_build_object(
  'version','c1-alpha-v7-hybrid-v1',
  'rowCount',(select count(*) from rows),
  'ticketingChallengerRows',(select value from payload),
  'ticketingChallengerContract',jsonb_build_object(
    'checkpoint','T-24h',
    'feature','hybrid_v6',
    'definition','matched sector 6h velocity pct-of-first per hour; raw 6h velocity fallback',
    'pit_rule','feature_snapshot_captured_at <= checkpoint_at',
    'missing_semantics','explicit missing; never reconstructed from outcome'
  )
);
$function$;

revoke all on function public.export_c1_alpha_v7_events_v1() from public,anon,authenticated;
revoke all on function public.export_c1_alpha_v7_attendance_v1() from public,anon,authenticated;
revoke all on function public.export_c1_alpha_v7_sporting_v1() from public,anon,authenticated;
revoke all on function public.export_c1_alpha_v7_aliases_v1() from public,anon,authenticated;
revoke all on function public.export_c1_alpha_v7_hybrid_v1() from public,anon,authenticated;

grant execute on function public.export_c1_alpha_v7_events_v1() to service_role;
grant execute on function public.export_c1_alpha_v7_attendance_v1() to service_role;
grant execute on function public.export_c1_alpha_v7_sporting_v1() to service_role;
grant execute on function public.export_c1_alpha_v7_aliases_v1() to service_role;
grant execute on function public.export_c1_alpha_v7_hybrid_v1() to service_role;

commit;
