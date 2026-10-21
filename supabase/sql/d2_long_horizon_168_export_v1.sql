-- d2 Long-Horizon Live 168h Export v1
--
-- Additive research export. Does not modify v7-final24 lineage.
-- Uses the same event eligibility, verified-capacity contract, 6h bucket
-- sampling, and point-in-time live feature function as the final-24h export.

begin;

create or replace function public.export_d2_long_horizon_168_rows_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with eligible as (
  select
    e.id as ticket_event_id,
    e.kickoff_at,
    cr.stadium_capacity
  from public.ticket_events e
  join public.ticket_event_outcomes o
    on o.ticket_event_id = e.id
   and o.actual_attendance is not null
  left join private.structural_prior_club_aliases_v1 a
    on a.alias = e.home_team
   and a.is_active
  left join lateral (
    select c.stadium_capacity
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key = a.club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date >= c.valid_from
      and (
        c.valid_to is null
        or (e.kickoff_at at time zone 'Europe/Warsaw')::date <= c.valid_to
      )
    order by c.valid_from desc, c.id desc
    limit 1
  ) cr on true
  where e.kickoff_at < now()
    and private.normalize_structural_prior_competition_v1(e.competition) = 'Ekstraklasa'
    and cr.stadium_capacity is not null
), candidates as (
  select
    s.id as requested_snapshot_id,
    s.ticket_event_id,
    s.captured_at as requested_as_of_at,
    e.kickoff_at,
    e.stadium_capacity,
    extract(epoch from (e.kickoff_at - s.captured_at)) / 3600.0 as hours_to_kickoff,
    floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer as bucket_6h,
    row_number() over (
      partition by
        s.ticket_event_id,
        floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer
      order by s.captured_at desc, s.id desc
    ) as rn
  from public.snapshots s
  join eligible e
    on e.ticket_event_id = s.ticket_event_id
  where s.captured_at < e.kickoff_at
    and s.captured_at >= e.kickoff_at - interval '168 hours'
), live_rows as (
  select
    c.ticket_event_id,
    c.requested_snapshot_id,
    c.requested_as_of_at,
    c.hours_to_kickoff,
    c.bucket_6h,
    to_jsonb(f) as features
  from candidates c
  cross join lateral public.get_live_trajectory_features_v1_1_asof(
    c.ticket_event_id,
    c.requested_as_of_at,
    c.stadium_capacity
  ) f
  where c.rn = 1
    and f.point_in_time_validated
    and f.snapshot_id is not null
), coverage as (
  select
    ticket_event_id,
    count(*) as valid_row_count,
    min(hours_to_kickoff) as closest_hours_to_kickoff,
    max(hours_to_kickoff) as earliest_hours_to_kickoff,
    count(*) filter (
      where hours_to_kickoff >= 0 and hours_to_kickoff <= 24
    ) as rows_0_24h,
    count(*) filter (
      where hours_to_kickoff > 24 and hours_to_kickoff <= 48
    ) as rows_24_48h,
    count(*) filter (
      where hours_to_kickoff > 48 and hours_to_kickoff <= 72
    ) as rows_48_72h,
    count(*) filter (
      where hours_to_kickoff > 72 and hours_to_kickoff <= 168
    ) as rows_72_168h
  from live_rows
  group by ticket_event_id
), live_payload as (
  select coalesce(
    jsonb_agg(to_jsonb(l) order by l.ticket_event_id, l.requested_as_of_at),
    '[]'::jsonb
  ) as rows
  from live_rows l
), coverage_payload as (
  select coalesce(
    jsonb_agg(to_jsonb(c) order by c.ticket_event_id),
    '[]'::jsonb
  ) as rows
  from coverage c
)
select jsonb_build_object(
  'version', 'd2-long-horizon-168-rows-v1',
  'sampling', jsonb_build_object(
    'window_hours', 168,
    'cadence_hours', 6,
    'rule', 'latest snapshot in each event x 6h bucket inside final 168h',
    'pit_feature_function', 'get_live_trajectory_features_v1_1_asof'
  ),
  'eventCount', (select count(distinct ticket_event_id) from live_rows),
  'liveRowCount', (select count(*) from live_rows),
  'coverage', (select rows from coverage_payload),
  'liveRows', (select rows from live_payload)
);
$function$;

revoke all on function public.export_d2_long_horizon_168_rows_v1()
  from public, anon, authenticated;
grant execute on function public.export_d2_long_horizon_168_rows_v1()
  to service_role;

commit;
