-- Beyond Ticketing — Live Signal Study v1
-- Purpose: strict exploratory measurement of whether live inventory features
-- contain signal relative to the historical forecast baseline.
--
-- Protocol:
-- * canonical horizons come from get_model_lab_rows_v1();
-- * live features come from multiclub_feature_store_v3;
-- * join key = ticket_event_id + canonical horizon;
-- * no post-checkpoint fallback;
-- * one independent event contributes at most one row per model/version/horizon;
-- * historical_p50 is required because target = actual - historical baseline;
-- * exploratory cross-club interpretation requires >=8 completed events and >=3 clubs;
-- * learned correction promotion remains blocked until >=20 independent completed events.

create or replace view public.live_signal_study_rows_v1
with (security_invoker=true)
as
select
    ml.forecast_observation_id,
    ml.ticket_event_id,
    f.club_slug,
    ml.home_team,
    ml.away_team,
    ml.kickoff_at,
    ml.horizon,
    ml.model_version,
    ml.forecast_mode,
    ml.forecast_generated_at,
    ml.hours_to_kickoff as forecast_hours_to_kickoff,
    f.snapshot_id as feature_snapshot_id,
    f.snapshot_captured_at as feature_snapshot_captured_at,
    f.hours_to_kickoff as feature_hours_to_kickoff,
    ml.actual_attendance,
    ml.historical_p50,
    ml.final_p50,
    (ml.actual_attendance - ml.historical_p50)::integer as baseline_signed_residual,
    ml.historical_absolute_error as baseline_absolute_error,
    ml.final_absolute_error,
    ml.live_uplift_absolute_error,
    ml.live_adjustment,
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
    'exploratory_live_signal_study_only'::text as study_use
from public.get_model_lab_rows_v1() ml
join public.multiclub_feature_store_v3 f
  on f.ticket_event_id=ml.ticket_event_id
 and f.horizon=ml.horizon
where ml.historical_p50 is not null;

revoke all on public.live_signal_study_rows_v1 from public,anon,authenticated;
grant select on public.live_signal_study_rows_v1 to service_role;

create or replace function public.get_live_signal_study_summary_v1()
returns table(
    model_version text,
    forecast_mode text,
    horizon text,
    independent_events bigint,
    clubs bigint,
    baseline_mae numeric,
    final_mae numeric,
    observed_live_uplift_mae numeric,
    rows_available_index bigint,
    rows_raw_velocity_6h bigint,
    rows_raw_velocity_24h bigint,
    rows_matched_velocity_6h bigint,
    rows_public_seat_map bigint,
    corr_available_index_to_signed_residual numeric,
    corr_available_index_to_abs_error numeric,
    corr_raw_velocity_6h_to_signed_residual numeric,
    corr_raw_velocity_24h_to_signed_residual numeric,
    corr_matched_velocity_6h_to_signed_residual numeric,
    corr_matched_velocity_24h_to_signed_residual numeric,
    release_activity_events bigint,
    coverage_change_events bigint,
    evidence_status text
)
language sql
stable
security invoker
set search_path=public
as $$
with base as (
    select * from public.live_signal_study_rows_v1
),
agg as (
    select
        model_version,
        forecast_mode,
        horizon,
        count(distinct ticket_event_id)::bigint as independent_events,
        count(distinct club_slug)::bigint as clubs,
        round(avg(baseline_absolute_error)::numeric,3) as baseline_mae,
        round(avg(final_absolute_error)::numeric,3) as final_mae,
        round((avg(baseline_absolute_error)-avg(final_absolute_error))::numeric,3) as observed_live_uplift_mae,
        count(*) filter(where available_index is not null)::bigint as rows_available_index,
        count(*) filter(where raw_velocity_6h_pct_of_first_per_hour is not null)::bigint as rows_raw_velocity_6h,
        count(*) filter(where raw_velocity_24h_pct_of_first_per_hour is not null)::bigint as rows_raw_velocity_24h,
        count(*) filter(where matched_velocity_6h_pct_of_first_per_hour is not null)::bigint as rows_matched_velocity_6h,
        count(*) filter(where public_seat_map_size is not null)::bigint as rows_public_seat_map,
        round(corr(available_index::double precision,baseline_signed_residual::double precision)::numeric,4) as corr_available_index_to_signed_residual,
        round(corr(available_index::double precision,baseline_absolute_error::double precision)::numeric,4) as corr_available_index_to_abs_error,
        round(corr(raw_velocity_6h_pct_of_first_per_hour::double precision,baseline_signed_residual::double precision)::numeric,4) as corr_raw_velocity_6h_to_signed_residual,
        round(corr(raw_velocity_24h_pct_of_first_per_hour::double precision,baseline_signed_residual::double precision)::numeric,4) as corr_raw_velocity_24h_to_signed_residual,
        round(corr(matched_velocity_6h_pct_of_first_per_hour::double precision,baseline_signed_residual::double precision)::numeric,4) as corr_matched_velocity_6h_to_signed_residual,
        round(corr(matched_velocity_24h_pct_of_first_per_hour::double precision,baseline_signed_residual::double precision)::numeric,4) as corr_matched_velocity_24h_to_signed_residual,
        count(*) filter(where release_activity_flag is true)::bigint as release_activity_events,
        count(*) filter(where sector_coverage_change_flag is true)::bigint as coverage_change_events
    from base
    group by model_version,forecast_mode,horizon
)
select
    a.*,
    case
      when independent_events < 8 then 'insufficient_independent_events'
      when clubs < 3 then 'insufficient_club_diversity'
      else 'exploratory_cross_club_ready'
    end as evidence_status
from agg a
order by horizon,forecast_mode,model_version;
$$;

revoke all on function public.get_live_signal_study_summary_v1() from public,anon,authenticated;
grant execute on function public.get_live_signal_study_summary_v1() to service_role;

create or replace function public.get_live_signal_study_readiness_v1()
returns table(
    independent_outcome_events bigint,
    clubs_with_outcome bigint,
    strict_study_rows bigint,
    models_with_strict_rows bigint,
    cross_club_gate_met boolean,
    learned_correction_gate_met boolean,
    status text
)
language sql
stable
security invoker
set search_path=public
as $$
with outcomes as (
    select
      count(distinct te.id)::bigint as events,
      count(distinct te.club_slug)::bigint as clubs
    from public.ticket_events te
    join public.ticket_event_outcomes o on o.ticket_event_id=te.id
    where o.actual_attendance is not null
), rows as (
    select
      count(*)::bigint as study_rows,
      count(distinct model_version)::bigint as models
    from public.live_signal_study_rows_v1
)
select
    o.events,
    o.clubs,
    r.study_rows,
    r.models,
    (o.events>=8 and o.clubs>=3),
    (o.events>=20),
    case
      when o.events<8 then 'collect_more_independent_outcomes'
      when o.clubs<3 then 'collect_more_club_outcomes'
      when o.events<20 then 'run_exploratory_cross_club_study_no_promotion'
      else 'eligible_for_grouped_live_residual_challenger_benchmark'
    end
from outcomes o cross join rows r;
$$;

revoke all on function public.get_live_signal_study_readiness_v1() from public,anon,authenticated;
grant execute on function public.get_live_signal_study_readiness_v1() to service_role;
