-- Beyond cross-club retrospective baseline and live-signal study v2
--
-- Purpose:
-- - keep frozen Live Signal Study v1 unchanged;
-- - create a leakage-safe retrospective attendance baseline for multi-club outcomes;
-- - join that baseline to canonical-horizon inventory features for exploratory analysis;
-- - never backdate forecast_observations or present retrospective rows as prospective forecasts.

create or replace view public.ml_home_attendance_history_v2 as
with combined as (
  select
    h.club_slug,
    h.kickoff_at,
    h.actual_attendance,
    coalesce(h.competition_key, lower(regexp_replace(h.competition, '[^a-zA-Z0-9]+', '_', 'g'))) as competition_key,
    h.season,
    h.source_name,
    h.source_url,
    1 as source_priority
  from public.ml_match_history h
  union all
  select
    e.club_slug,
    e.kickoff_at,
    o.actual_attendance,
    'ekstraklasa'::text as competition_key,
    case
      when extract(month from e.kickoff_at at time zone 'Europe/Warsaw') >= 7
        then extract(year from e.kickoff_at at time zone 'Europe/Warsaw')::int::text || '/' || (extract(year from e.kickoff_at at time zone 'Europe/Warsaw')::int + 1)::text
      else (extract(year from e.kickoff_at at time zone 'Europe/Warsaw')::int - 1)::text || '/' || extract(year from e.kickoff_at at time zone 'Europe/Warsaw')::int::text
    end as season,
    o.source_name,
    o.source_url,
    2 as source_priority
  from public.ticket_event_outcomes o
  join public.ticket_events e on e.id = o.ticket_event_id
  where lower(e.competition) like '%ekstraklasa%'
), dedup as (
  select distinct on (club_slug, kickoff_at)
    club_slug, kickoff_at, actual_attendance, competition_key, season, source_name, source_url
  from combined
  where competition_key = 'ekstraklasa'
  order by club_slug, kickoff_at, source_priority desc
)
select * from dedup;

create or replace view public.crossclub_baseline_rows_v2 as
select
  e.id as ticket_event_id,
  e.club_slug,
  e.home_team,
  e.away_team,
  e.competition,
  e.kickoff_at,
  o.actual_attendance,
  hist.history_count,
  hist.history_first_at,
  hist.history_last_at,
  hist.baseline_mean,
  hist.baseline_median as baseline_p50,
  (o.actual_attendance - hist.baseline_median)::numeric as baseline_signed_residual,
  abs(o.actual_attendance - hist.baseline_median)::numeric as baseline_absolute_error,
  'club_trailing_home_median_v2'::text as baseline_model,
  'retrospective_point_in_time'::text as evaluation_mode
from public.ticket_event_outcomes o
join public.ticket_events e on e.id = o.ticket_event_id
cross join lateral (
  select
    count(*)::int as history_count,
    min(h.kickoff_at) as history_first_at,
    max(h.kickoff_at) as history_last_at,
    avg(h.actual_attendance)::numeric as baseline_mean,
    percentile_cont(0.5) within group (order by h.actual_attendance)::numeric as baseline_median
  from public.ml_home_attendance_history_v2 h
  where h.club_slug = e.club_slug
    and h.kickoff_at < e.kickoff_at
    and h.competition_key = 'ekstraklasa'
) hist
where lower(e.competition) like '%ekstraklasa%'
  and hist.history_count >= 3;

create or replace view public.crossclub_live_signal_study_rows_v2 as
select
  f.ticket_event_id,
  f.club_slug,
  f.home_team,
  f.away_team,
  f.kickoff_at,
  f.horizon,
  f.target_hours,
  f.snapshot_id,
  f.snapshot_captured_at,
  f.hours_to_kickoff as feature_hours_to_kickoff,
  b.actual_attendance,
  b.history_count,
  b.baseline_model,
  b.baseline_p50,
  b.baseline_signed_residual,
  b.baseline_absolute_error,
  f.feature_quality,
  f.normalization_quality,
  f.observation_window_hours,
  f.snapshots_visible,
  f.available_index,
  f.available_pct_of_first,
  f.public_seat_map_size,
  f.available_pct_of_public_seat_map,
  f.raw_velocity_6h_pct_of_first_per_hour,
  f.raw_velocity_24h_pct_of_first_per_hour,
  f.raw_acceleration_pct_of_first_per_hour,
  f.raw_velocity_6h_pct_of_public_seat_map_per_hour,
  f.raw_velocity_24h_pct_of_public_seat_map_per_hour,
  f.raw_acceleration_pct_of_public_seat_map_per_hour,
  f.matched_velocity_6h_pct_of_first_per_hour,
  f.matched_velocity_24h_pct_of_first_per_hour,
  f.matched_acceleration_pct_of_first_per_hour,
  f.matched_velocity_6h_pct_of_public_seat_map_per_hour,
  f.matched_velocity_24h_pct_of_public_seat_map_per_hour,
  f.matched_acceleration_pct_of_public_seat_map_per_hour,
  f.release_activity_flag,
  f.sector_coverage_change_flag,
  f.coverage_inventory_effect,
  'exploratory_crossclub_baseline_v2'::text as study_use
from public.crossclub_baseline_rows_v2 b
join public.multiclub_feature_store_v4 f on f.ticket_event_id = b.ticket_event_id;

create or replace function public.get_crossclub_live_signal_study_readiness_v2()
returns table (
  independent_events bigint,
  clubs bigint,
  strict_rows bigint,
  gate_event_target integer,
  gate_club_target integer,
  cross_club_gate_met boolean,
  status text
)
language sql
security invoker
set search_path = public
as $$
  select
    count(distinct ticket_event_id)::bigint,
    count(distinct club_slug)::bigint,
    count(*)::bigint,
    8,
    3,
    count(distinct ticket_event_id) >= 8 and count(distinct club_slug) >= 3,
    case
      when count(distinct ticket_event_id) >= 8 and count(distinct club_slug) >= 3
        then 'run_exploratory_crossclub_baseline_v2'
      when count(distinct ticket_event_id) < 8
        then 'insufficient_independent_events'
      else 'insufficient_club_diversity'
    end
  from public.crossclub_live_signal_study_rows_v2;
$$;

create or replace function public.get_crossclub_live_signal_study_summary_v2()
returns table (
  horizon text,
  independent_events bigint,
  clubs bigint,
  baseline_mae numeric,
  baseline_bias numeric,
  rows_available_index bigint,
  rows_raw_velocity_6h bigint,
  rows_raw_velocity_24h bigint,
  rows_matched_velocity_6h bigint,
  rows_matched_velocity_24h bigint,
  rows_public_seat_map bigint,
  corr_available_index_to_signed_residual numeric,
  corr_raw_velocity_6h_to_signed_residual numeric,
  corr_raw_velocity_24h_to_signed_residual numeric,
  corr_matched_velocity_6h_to_signed_residual numeric,
  corr_matched_velocity_24h_to_signed_residual numeric,
  release_activity_events bigint,
  coverage_change_events bigint
)
language sql
security invoker
set search_path = public
as $$
  select
    s.horizon,
    count(distinct s.ticket_event_id)::bigint,
    count(distinct s.club_slug)::bigint,
    round(avg(s.baseline_absolute_error), 3),
    round(avg(s.baseline_signed_residual), 3),
    count(s.available_index)::bigint,
    count(s.raw_velocity_6h_pct_of_first_per_hour)::bigint,
    count(s.raw_velocity_24h_pct_of_first_per_hour)::bigint,
    count(s.matched_velocity_6h_pct_of_first_per_hour)::bigint,
    count(s.matched_velocity_24h_pct_of_first_per_hour)::bigint,
    count(s.available_pct_of_public_seat_map)::bigint,
    round(corr(s.available_index::double precision, s.baseline_signed_residual::double precision)::numeric, 4),
    round(corr(s.raw_velocity_6h_pct_of_first_per_hour::double precision, s.baseline_signed_residual::double precision)::numeric, 4),
    round(corr(s.raw_velocity_24h_pct_of_first_per_hour::double precision, s.baseline_signed_residual::double precision)::numeric, 4),
    round(corr(s.matched_velocity_6h_pct_of_first_per_hour::double precision, s.baseline_signed_residual::double precision)::numeric, 4),
    round(corr(s.matched_velocity_24h_pct_of_first_per_hour::double precision, s.baseline_signed_residual::double precision)::numeric, 4),
    count(distinct s.ticket_event_id) filter (where s.release_activity_flag is true)::bigint,
    count(distinct s.ticket_event_id) filter (where s.sector_coverage_change_flag is true)::bigint
  from public.crossclub_live_signal_study_rows_v2 s
  group by s.horizon
  order by case s.horizon when 'T-30' then 1 when 'T-14' then 2 when 'T-7' then 3 when 'T-3' then 4 when 'T-24h' then 5 else 99 end;
$$;

revoke all on public.ml_home_attendance_history_v2 from anon, authenticated;
revoke all on public.crossclub_baseline_rows_v2 from anon, authenticated;
revoke all on public.crossclub_live_signal_study_rows_v2 from anon, authenticated;
revoke all on function public.get_crossclub_live_signal_study_readiness_v2() from public, anon, authenticated;
revoke all on function public.get_crossclub_live_signal_study_summary_v2() from public, anon, authenticated;
grant select on public.ml_home_attendance_history_v2 to service_role;
grant select on public.crossclub_baseline_rows_v2 to service_role;
grant select on public.crossclub_live_signal_study_rows_v2 to service_role;
grant execute on function public.get_crossclub_live_signal_study_readiness_v2() to service_role;
grant execute on function public.get_crossclub_live_signal_study_summary_v2() to service_role;

comment on view public.crossclub_baseline_rows_v2 is
  'Leakage-safe retrospective club baseline: median of at least three verified prior home Ekstraklasa attendances strictly before each target kickoff.';
comment on view public.crossclub_live_signal_study_rows_v2 is
  'Exploratory cross-club live-signal rows joining leakage-safe trailing attendance baseline to strict canonical-horizon inventory features; does not alter frozen Live Signal Study v1.';
