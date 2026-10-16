-- C1 Alpha Event Training Export v1
--
-- Lightweight payload for one-row-per-event experiments such as v6.
-- Deliberately avoids rebuilding the expensive full live trajectory export.
-- Contains only the data needed to replay the frozen Structural Prior and use
-- the existing PIT-safe T-24 hybrid ticketing signal.

begin;

create or replace function public.export_c1_alpha_event_training_payload_v1()
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
), event_seasons as (
  select distinct season from usable_events
), source_seasons as (
  select distinct sporting_season as season from usable_events
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
  join usable_events e on e.ticket_event_id = d.ticket_event_id
), event_json as (
  select coalesce(jsonb_agg(to_jsonb(e) order by e.kickoff_at, e.ticket_event_id), '[]'::jsonb) as value
  from usable_events e
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
), hybrid_json as (
  select coalesce(jsonb_agg(to_jsonb(h) order by h.ticket_event_id), '[]'::jsonb) as value
  from hybrid h
)
select jsonb_build_object(
  'version', 'c1-alpha-event-training-export-v1',
  'eventCount', (select count(*) from usable_events),
  'events', (select value from event_json),
  'attendance', (select value from attendance_json),
  'sportingMatches', (select value from sporting_json),
  'aliases', (select value from aliases_json),
  'ticketingChallengerContract', jsonb_build_object(
    'checkpoint','T-24h',
    'feature','hybrid_v6',
    'definition','matched sector 6h velocity pct-of-first per hour; raw 6h velocity fallback',
    'pit_rule','feature_snapshot_captured_at <= checkpoint_at',
    'missing_semantics','explicit missing; never reconstructed from outcome'
  ),
  'ticketingChallengerRows', (select value from hybrid_json)
);
$function$;

revoke all on function public.export_c1_alpha_event_training_payload_v1() from public, anon, authenticated;
grant execute on function public.export_c1_alpha_event_training_payload_v1() to service_role;

commit;
