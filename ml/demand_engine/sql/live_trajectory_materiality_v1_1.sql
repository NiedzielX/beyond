-- Beyond Live Demand Engine — material release/anomaly calibration v1.1
--
-- Empirical basis from the current multi-club live sample (2026-10-15):
-- matched-sector release P95=18, P99≈40 seats; entered-sector inventory P95=28;
-- positive raw inventory change P95=30. v1.1 therefore treats a matched-sector
-- release/increase as material only above max(50 seats, 0.5% of first inventory).
-- Sector entry/exit is kept as a separate coverage-change signal.

create or replace function public.get_live_trajectory_features_v1_1_asof(
    p_ticket_event_id bigint,
    p_as_of timestamptz,
    p_stadium_capacity integer default null
)
returns table(
    feature_version text,
    signal_readiness text,
    feature_quality text,
    inventory_interpretation text,
    point_in_time_validated boolean,
    snapshot_id bigint,
    snapshot_captured_at timestamptz,
    as_of_at timestamptz,
    kickoff_at timestamptz,
    hours_to_kickoff numeric,
    days_to_kickoff numeric,
    snapshot_age_minutes numeric,
    checkpoint_label text,
    checkpoint_distance_hours numeric,
    checkpoint_ready boolean,
    available_total integer,
    first_available_total integer,
    available_index numeric,
    available_share_of_capacity numeric,
    public_seat_map_size integer,
    available_pct_of_public_seat_map numeric,
    net_removed_since_first integer,
    net_removed_since_previous integer,
    velocity_since_previous numeric,
    net_removed_6h integer,
    velocity_6h numeric,
    net_removed_24h integer,
    velocity_24h numeric,
    net_removed_72h integer,
    velocity_72h numeric,
    net_removed_7d integer,
    velocity_7d numeric,
    velocity_6h_pct_of_first_per_hour numeric,
    velocity_24h_pct_of_first_per_hour numeric,
    velocity_72h_pct_of_first_per_hour numeric,
    velocity_7d_pct_of_first_per_hour numeric,
    velocity_6h_pct_of_capacity_per_hour numeric,
    velocity_24h_pct_of_capacity_per_hour numeric,
    velocity_72h_pct_of_capacity_per_hour numeric,
    velocity_7d_pct_of_capacity_per_hour numeric,
    acceleration_6h_vs_24h numeric,
    acceleration_24h_vs_72h numeric,
    acceleration_72h_vs_7d numeric,
    matched_sector_count integer,
    entered_sector_count integer,
    left_sector_count integer,
    matched_absorption integer,
    matched_release integer,
    coverage_inventory_effect integer,
    sector_coverage_change_flag boolean,
    release_activity_flag boolean,
    unexplained_inventory_increase_flag boolean,
    raw_snapshot_count integer,
    clean_snapshot_count integer,
    excluded_anomaly_count integer,
    duplicate_timestamp_count integer,
    invalid_snapshot_count integer,
    observation_window_hours numeric,
    max_visible_gap_hours numeric,
    data_gap_detected boolean
)
language sql
stable
set search_path=public
as $function$
with base as (
    select *
    from public.get_live_trajectory_features_v1_asof(
        p_ticket_event_id,
        p_as_of,
        p_stadium_capacity
    )
), scored as (
    select b.*,
           greatest(50,round(coalesce(b.first_available_total,0)*0.005))::integer as material_threshold
    from base b
), classified as (
    select s.*,
           (coalesce(s.matched_release,0) >= s.material_threshold) as material_release,
           (
             coalesce(s.net_removed_since_previous,0) <= -s.material_threshold
             and not (coalesce(s.matched_release,0) >= s.material_threshold)
             and not coalesce(s.sector_coverage_change_flag,false)
           ) as material_unexplained_increase
    from scored s
)
select
    'live-trajectory-v1.1'::text,
    case
      when c.signal_readiness='not_ready' then 'not_ready'
      when c.signal_readiness='partial' then 'partial'
      when c.material_unexplained_increase then 'partial'
      else 'ready'
    end::text,
    c.feature_quality,c.inventory_interpretation,c.point_in_time_validated,
    c.snapshot_id,c.snapshot_captured_at,c.as_of_at,c.kickoff_at,
    c.hours_to_kickoff,c.days_to_kickoff,c.snapshot_age_minutes,
    c.checkpoint_label,c.checkpoint_distance_hours,c.checkpoint_ready,
    c.available_total,c.first_available_total,c.available_index,
    c.available_share_of_capacity,c.public_seat_map_size,c.available_pct_of_public_seat_map,
    c.net_removed_since_first,c.net_removed_since_previous,c.velocity_since_previous,
    c.net_removed_6h,c.velocity_6h,c.net_removed_24h,c.velocity_24h,
    c.net_removed_72h,c.velocity_72h,c.net_removed_7d,c.velocity_7d,
    c.velocity_6h_pct_of_first_per_hour,c.velocity_24h_pct_of_first_per_hour,
    c.velocity_72h_pct_of_first_per_hour,c.velocity_7d_pct_of_first_per_hour,
    c.velocity_6h_pct_of_capacity_per_hour,c.velocity_24h_pct_of_capacity_per_hour,
    c.velocity_72h_pct_of_capacity_per_hour,c.velocity_7d_pct_of_capacity_per_hour,
    c.acceleration_6h_vs_24h,c.acceleration_24h_vs_72h,c.acceleration_72h_vs_7d,
    c.matched_sector_count,c.entered_sector_count,c.left_sector_count,
    c.matched_absorption,c.matched_release,c.coverage_inventory_effect,
    c.sector_coverage_change_flag,
    c.material_release,
    c.material_unexplained_increase,
    c.raw_snapshot_count,c.clean_snapshot_count,c.excluded_anomaly_count,
    c.duplicate_timestamp_count,c.invalid_snapshot_count,c.observation_window_hours,
    c.max_visible_gap_hours,c.data_gap_detected
from classified c;
$function$;

comment on function public.get_live_trajectory_features_v1_1_asof(bigint,timestamptz,integer) is
'Live trajectory v1.1. Material matched-sector release threshold=max(50 seats, 0.5% first observed inventory); sector coverage changes remain separate.';

create or replace view private.ticketing_horizon_readiness_v2_1 as
with horizons(horizon,target_days_before,target_interval) as (
    values ('T-30'::text,30::integer,interval '30 days'),
           ('T-14'::text,14::integer,interval '14 days'),
           ('T-7'::text,7::integer,interval '7 days'),
           ('T-3'::text,3::integer,interval '3 days'),
           ('T-1'::text,1::integer,interval '1 day')
), base as (
    select e.id ticket_event_id,e.club_slug,e.home_team,e.away_team,e.competition,e.external_event_id,e.kickoff_at,
           h.horizon,h.target_days_before,e.kickoff_at-h.target_interval target_as_of_at,
           (e.kickoff_at-h.target_interval<=now()) checkpoint_due
    from public.ticket_events e cross join horizons h
    where e.kickoff_at is not null
)
select b.ticket_event_id,b.club_slug,b.home_team,b.away_team,b.competition,b.external_event_id,b.kickoff_at,
       b.horizon,b.target_days_before,b.target_as_of_at,b.checkpoint_due,
       f.snapshot_id,f.snapshot_captured_at,f.snapshot_age_minutes,f.feature_version,f.feature_quality,
       f.signal_readiness,f.point_in_time_validated,f.available_total,f.first_available_total,f.available_index,
       f.release_activity_flag,f.sector_coverage_change_flag,f.unexplained_inventory_increase_flag,
       f.raw_snapshot_count,f.clean_snapshot_count,f.excluded_anomaly_count,f.max_visible_gap_hours,f.data_gap_detected,
       case when not b.checkpoint_due then false when f.snapshot_id is null then false when f.signal_readiness<>'ready' then false else true end checkpoint_ready,
       case when not b.checkpoint_due then 'not_due' when f.snapshot_id is null then 'missing_snapshot' when f.signal_readiness<>'ready' then 'insufficient_signal' else 'ready' end readiness_status
from base b
left join lateral public.get_live_trajectory_features_v1_1_asof(b.ticket_event_id,b.target_as_of_at,null) f on b.checkpoint_due;

comment on view private.ticketing_horizon_readiness_v2_1 is
'Canonical exact-cutoff readiness using live-trajectory-v1.1 calibrated release/anomaly semantics.';
