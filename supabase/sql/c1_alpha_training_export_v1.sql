-- C1 Alpha Training Export v1
--
-- Versioned export for small-N / full-trajectory live-correction training.
-- Primary domain: completed Ekstraklasa ticket events with verified outcomes.
-- Sampling: at most one live feature row per event per 6-hour pre-kickoff bucket.
-- Security: service_role only; SECURITY INVOKER.

begin;

create or replace function public.export_c1_alpha_training_payload_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with eligible_events as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    o.actual_attendance
  from public.ticket_events e
  join public.ticket_event_outcomes o
    on o.ticket_event_id = e.id
   and o.actual_attendance is not null
  where e.kickoff_at < now()
    and private.normalize_structural_prior_competition_v1(e.competition) = 'Ekstraklasa'
), mapped_events as (
  select
    e.*,
    ha.club_key as home_club_key,
    aa.club_key as away_club_key
  from eligible_events e
  left join private.structural_prior_club_aliases_v1 ha
    on ha.alias = e.home_team and ha.is_active
  left join private.structural_prior_club_aliases_v1 aa
    on aa.alias = e.away_team and aa.is_active
), event_fixture as (
  select
    e.*,
    f.season as sporting_season,
    replace(f.season, '-', '/') as season,
    f.round_number as round_no
  from mapped_events e
  left join lateral (
    select s.season, s.round_number
    from public.sporting_league_matches_shadow s
    left join private.structural_prior_club_aliases_v1 sh
      on sh.alias = s.home_team and sh.is_active
    left join private.structural_prior_club_aliases_v1 sa
      on sa.alias = s.away_team and sa.is_active
    where s.event_date = (e.kickoff_at at time zone 'Europe/Warsaw')::date
      and sh.club_key = e.home_club_key
      and sa.club_key = e.away_club_key
    order by s.fetched_at desc
    limit 1
  ) f on true
), event_capacity as (
  select
    e.*,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status
  from event_fixture e
  left join lateral (
    select c.*
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key = e.home_club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date >= c.valid_from
      and (c.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date <= c.valid_to)
    order by c.valid_from desc, c.id desc
    limit 1
  ) cr on true
), usable_events as (
  select *
  from event_capacity
  where home_club_key is not null
    and away_club_key is not null
    and season is not null
    and round_no is not null
    and stadium_capacity is not null
), snapshot_candidates as (
  select
    s.id as snapshot_id,
    s.ticket_event_id,
    s.captured_at,
    floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer as bucket_6h,
    row_number() over (
      partition by s.ticket_event_id,
                   floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer
      order by s.captured_at desc, s.id desc
    ) as rn
  from public.snapshots s
  join usable_events e on e.ticket_event_id = s.ticket_event_id
  where s.captured_at < e.kickoff_at
    and s.captured_at >= e.kickoff_at - interval '31 days'
), sampled_snapshots as (
  select snapshot_id, ticket_event_id, captured_at, bucket_6h
  from snapshot_candidates
  where rn = 1
), live_rows as (
  select
    ss.ticket_event_id,
    ss.snapshot_id as requested_snapshot_id,
    ss.captured_at as requested_as_of_at,
    ss.bucket_6h,
    to_jsonb(f) as features
  from sampled_snapshots ss
  join usable_events e on e.ticket_event_id = ss.ticket_event_id
  cross join lateral public.get_live_trajectory_features_v1_1_asof(
    ss.ticket_event_id,
    ss.captured_at,
    e.stadium_capacity
  ) f
  where f.point_in_time_validated
    and f.snapshot_id is not null
), event_seasons as (
  select distinct season from usable_events where season is not null
), source_seasons as (
  select distinct sporting_season as season from usable_events where sporting_season is not null
), event_json as (
  select coalesce(jsonb_agg(to_jsonb(e) order by e.kickoff_at, e.ticket_event_id), '[]'::jsonb) as value
  from usable_events e
), live_json as (
  select coalesce(jsonb_agg(to_jsonb(l) order by l.ticket_event_id, l.requested_as_of_at), '[]'::jsonb) as value
  from live_rows l
), attendance_json as (
  select coalesce(jsonb_agg(to_jsonb(a) order by a.kickoff_at, a.club_slug), '[]'::jsonb) as value
  from public.ml_home_attendance_history_v2 a
  where a.competition_key = 'ekstraklasa'
    and a.season in (select season from event_seasons)
), sporting_json as (
  select coalesce(jsonb_agg(to_jsonb(s) order by s.event_date, s.round_number, s.home_team), '[]'::jsonb) as value
  from public.sporting_league_matches_shadow s
  where s.season in (select season from source_seasons)
), aliases_json as (
  select coalesce(jsonb_agg(to_jsonb(a) order by a.alias), '[]'::jsonb) as value
  from public.get_structural_prior_club_aliases_v1() a
)
select jsonb_build_object(
  'version', 'c1-alpha-training-export-v1',
  'sampling', jsonb_build_object(
    'cadence_hours', 6,
    'window_days', 31,
    'rule', 'latest snapshot in each event x 6h pre-kickoff bucket'
  ),
  'eventCount', (select count(*) from usable_events),
  'liveRowCount', (select count(*) from live_rows),
  'events', (select value from event_json),
  'liveRows', (select value from live_json),
  'attendance', (select value from attendance_json),
  'sportingMatches', (select value from sporting_json),
  'aliases', (select value from aliases_json)
);
$function$;

revoke all on function public.export_c1_alpha_training_payload_v1() from public, anon, authenticated;
grant execute on function public.export_c1_alpha_training_payload_v1() to service_role;

commit;
