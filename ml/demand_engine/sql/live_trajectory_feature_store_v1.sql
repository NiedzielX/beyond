-- Beyond Live Demand Engine — canonical live trajectory feature contract v1
--
-- This is a new versioned contract. It intentionally does not mutate the
-- earlier get_live_features_v1_asof / multiclub_feature_store_v3/v4 layers so
-- prior experiments remain reproducible.

create or replace function public.get_live_trajectory_features_v1_asof(
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
set search_path = public
as $function$
with event_row as (
    select id, kickoff_at
    from public.ticket_events
    where id = p_ticket_event_id
      and kickoff_at is not null
),
raw_visible as (
    select s.id, s.captured_at, s.available_total, s.sector_count
    from public.snapshots s
    where s.ticket_event_id = p_ticket_event_id
      and s.captured_at <= p_as_of
),
valid as (
    select *
    from raw_visible
    where available_total is not null
      and available_total >= 0
),
deduped as (
    select distinct on (captured_at)
        id, captured_at, available_total, sector_count
    from valid
    order by captured_at, id desc
),
ordered as (
    select
        d.*,
        lag(id) over (order by captured_at, id) as previous_snapshot_id,
        lag(captured_at) over (order by captured_at, id) as previous_captured_at,
        lag(available_total) over (order by captured_at, id) as previous_available_total,
        extract(epoch from (
            captured_at - lag(captured_at) over (order by captured_at, id)
        )) / 3600.0 as gap_hours
    from deduped d
),
current_s as (
    select * from ordered order by captured_at desc, id desc limit 1
),
first_s as (
    select * from ordered order by captured_at asc, id asc limit 1
),
counts as (
    select
        (select count(*) from raw_visible)::integer as raw_count,
        (select count(*) from deduped)::integer as clean_count,
        (select count(*) from raw_visible where available_total is null or available_total < 0)::integer as invalid_count,
        ((select count(*) from valid) - (select count(*) from deduped))::integer as duplicate_count,
        (select max(gap_hours) from ordered)::numeric as max_gap_hours
),
anchor6 as (
    select d.*
    from deduped d, current_s c
    where d.captured_at <= c.captured_at - interval '6 hours'
    order by d.captured_at desc, d.id desc
    limit 1
),
anchor24 as (
    select d.*
    from deduped d, current_s c
    where d.captured_at <= c.captured_at - interval '24 hours'
    order by d.captured_at desc, d.id desc
    limit 1
),
anchor72 as (
    select d.*
    from deduped d, current_s c
    where d.captured_at <= c.captured_at - interval '72 hours'
    order by d.captured_at desc, d.id desc
    limit 1
),
anchor168 as (
    select d.*
    from deduped d, current_s c
    where d.captured_at <= c.captured_at - interval '168 hours'
    order by d.captured_at desc, d.id desc
    limit 1
),
sector_universe as (
    select si.sector
    from public.sector_inventory si, current_s c
    where si.snapshot_id = c.id and si.available >= 0
    union
    select si.sector
    from public.sector_inventory si, current_s c
    where si.snapshot_id = c.previous_snapshot_id and si.available >= 0
),
sector_pairs as (
    select
        u.sector,
        p.available as previous_available,
        n.available as current_available,
        case
            when p.sector is not null and n.sector is not null then 'matched'
            when p.sector is null and n.sector is not null then 'entered'
            when p.sector is not null and n.sector is null then 'left'
        end as sector_state
    from sector_universe u
    cross join current_s c
    left join public.sector_inventory p
      on p.snapshot_id = c.previous_snapshot_id
     and p.sector = u.sector
     and p.available >= 0
    left join public.sector_inventory n
      on n.snapshot_id = c.id
     and n.sector = u.sector
     and n.available >= 0
),
sector_stats as (
    select
        count(*) filter (where sector_state = 'matched')::integer as matched_count,
        count(*) filter (where sector_state = 'entered')::integer as entered_count,
        count(*) filter (where sector_state = 'left')::integer as left_count,
        coalesce(sum(greatest(previous_available - current_available, 0)) filter (where sector_state = 'matched'), 0)::integer as matched_absorption,
        coalesce(sum(greatest(current_available - previous_available, 0)) filter (where sector_state = 'matched'), 0)::integer as matched_release,
        coalesce(sum(current_available) filter (where sector_state = 'entered'), 0)::integer as entered_available,
        coalesce(sum(previous_available) filter (where sector_state = 'left'), 0)::integer as left_available,
        (count(*) > 0) as sector_data_available
    from sector_pairs
),
reference as (
    select r.reference_value::integer as public_map_size
    from public.ticket_event_inventory_reference r
    where r.ticket_event_id = p_ticket_event_id
      and r.reference_type = 'public_seat_map_size'
    order by r.observed_at desc nulls last
    limit 1
),
base as (
    select
        e.kickoff_at,
        c.id as snapshot_id,
        c.captured_at,
        c.available_total,
        c.previous_snapshot_id,
        c.previous_captured_at,
        c.previous_available_total,
        f.available_total as first_available_total,
        co.raw_count,
        co.clean_count,
        co.invalid_count,
        co.duplicate_count,
        co.max_gap_hours,
        ss.matched_count,
        ss.entered_count,
        ss.left_count,
        ss.matched_absorption,
        ss.matched_release,
        (ss.entered_available - ss.left_available)::integer as coverage_effect,
        ss.sector_data_available,
        ref.public_map_size,
        extract(epoch from (e.kickoff_at - p_as_of)) / 3600.0 as htk,
        extract(epoch from (p_as_of - c.captured_at)) / 60.0 as snapshot_age_min,
        extract(epoch from (c.captured_at - f.captured_at)) / 3600.0 as observation_hours,
        case when a6.id is not null and extract(epoch from ((c.captured_at - interval '6 hours') - a6.captured_at))/3600.0 <= 3.0
             then a6.available_total end as a6_available,
        case when a6.id is not null and extract(epoch from ((c.captured_at - interval '6 hours') - a6.captured_at))/3600.0 <= 3.0
             then extract(epoch from (c.captured_at - a6.captured_at))/3600.0 end as a6_elapsed,
        case when a24.id is not null and extract(epoch from ((c.captured_at - interval '24 hours') - a24.captured_at))/3600.0 <= 6.0
             then a24.available_total end as a24_available,
        case when a24.id is not null and extract(epoch from ((c.captured_at - interval '24 hours') - a24.captured_at))/3600.0 <= 6.0
             then extract(epoch from (c.captured_at - a24.captured_at))/3600.0 end as a24_elapsed,
        case when a72.id is not null and extract(epoch from ((c.captured_at - interval '72 hours') - a72.captured_at))/3600.0 <= 18.0
             then a72.available_total end as a72_available,
        case when a72.id is not null and extract(epoch from ((c.captured_at - interval '72 hours') - a72.captured_at))/3600.0 <= 18.0
             then extract(epoch from (c.captured_at - a72.captured_at))/3600.0 end as a72_elapsed,
        case when a168.id is not null and extract(epoch from ((c.captured_at - interval '168 hours') - a168.captured_at))/3600.0 <= 42.0
             then a168.available_total end as a168_available,
        case when a168.id is not null and extract(epoch from ((c.captured_at - interval '168 hours') - a168.captured_at))/3600.0 <= 42.0
             then extract(epoch from (c.captured_at - a168.captured_at))/3600.0 end as a168_elapsed
    from event_row e
    cross join current_s c
    cross join first_s f
    cross join counts co
    cross join sector_stats ss
    left join reference ref on true
    left join anchor6 a6 on true
    left join anchor24 a24 on true
    left join anchor72 a72 on true
    left join anchor168 a168 on true
),
metrics as (
    select
        b.*,
        case when previous_available_total is not null then previous_available_total - available_total end as prev_removed,
        case when previous_available_total is not null and captured_at > previous_captured_at
             then (previous_available_total - available_total)::numeric /
                  nullif(extract(epoch from (captured_at - previous_captured_at))/3600.0,0) end as prev_velocity,
        case when a6_available is not null then a6_available - available_total end as r6,
        case when a6_available is not null then (a6_available - available_total)::numeric / nullif(a6_elapsed,0) end as v6,
        case when a24_available is not null then a24_available - available_total end as r24,
        case when a24_available is not null then (a24_available - available_total)::numeric / nullif(a24_elapsed,0) end as v24,
        case when a72_available is not null then a72_available - available_total end as r72,
        case when a72_available is not null then (a72_available - available_total)::numeric / nullif(a72_elapsed,0) end as v72,
        case when a168_available is not null then a168_available - available_total end as r168,
        case when a168_available is not null then (a168_available - available_total)::numeric / nullif(a168_elapsed,0) end as v168,
        (entered_count > 0 or left_count > 0) as coverage_change,
        (matched_release > 0 or entered_count > 0) as release_activity,
        greatest(100, round(first_available_total * 0.05))::integer as material_increase_threshold
    from base b
),
finalized as (
    select
        m.*,
        (previous_available_total is not null
         and available_total - previous_available_total >= material_increase_threshold
         and not release_activity
         and not coverage_change) as unexplained_increase,
        ((max_gap_hours is not null and max_gap_hours > 12.0) or snapshot_age_min > 720.0) as has_data_gap,
        case
          when 720.0 <= htk and htk <= 792.0 then 'T-30'
          when 336.0 <= htk and htk <= 384.0 then 'T-14'
          when 168.0 <= htk and htk <= 192.0 then 'T-7'
          when 72.0 <= htk and htk <= 90.0 then 'T-3'
          when 24.0 <= htk and htk <= 36.0 then 'T-1'
          else null
        end as cp_label,
        case
          when 720.0 <= htk and htk <= 792.0 then htk - 720.0
          when 336.0 <= htk and htk <= 384.0 then htk - 336.0
          when 168.0 <= htk and htk <= 192.0 then htk - 168.0
          when 72.0 <= htk and htk <= 90.0 then htk - 72.0
          when 24.0 <= htk and htk <= 36.0 then htk - 24.0
          else null
        end as cp_distance
    from metrics m
)
select
    'live-trajectory-v1'::text,
    case
      when clean_count < 2 then 'not_ready'
      when clean_count < 4 or observation_hours < 24.0 or has_data_gap or unexplained_increase then 'partial'
      else 'ready'
    end::text as signal_readiness,
    case
      when clean_count = 1 then 'single_snapshot_only'
      when sector_data_available then 'sector_matched_plus_raw'
      else 'raw_total_only'
    end::text as feature_quality,
    'demand_proxy_not_confirmed_sales'::text,
    true,
    snapshot_id,
    captured_at,
    p_as_of,
    kickoff_at,
    round(htk::numeric,6),
    round((htk/24.0)::numeric,6),
    round(snapshot_age_min::numeric,3),
    cp_label,
    round(cp_distance::numeric,3),
    (cp_label is not null),
    available_total,
    first_available_total,
    round(available_total::numeric/nullif(first_available_total,0),8),
    case when p_stadium_capacity is not null and p_stadium_capacity > 0
         then round(available_total::numeric/p_stadium_capacity,8) end,
    public_map_size,
    case when public_map_size is not null and public_map_size > 0
         then round(available_total::numeric/public_map_size*100.0,6) end,
    (first_available_total - available_total)::integer,
    prev_removed::integer,
    round(prev_velocity::numeric,6),
    r6::integer,
    round(v6::numeric,6),
    r24::integer,
    round(v24::numeric,6),
    r72::integer,
    round(v72::numeric,6),
    r168::integer,
    round(v168::numeric,6),
    case when first_available_total > 0 then round(v6/first_available_total*100.0,10) end,
    case when first_available_total > 0 then round(v24/first_available_total*100.0,10) end,
    case when first_available_total > 0 then round(v72/first_available_total*100.0,10) end,
    case when first_available_total > 0 then round(v168/first_available_total*100.0,10) end,
    case when p_stadium_capacity is not null and p_stadium_capacity > 0 then round(v6/p_stadium_capacity*100.0,10) end,
    case when p_stadium_capacity is not null and p_stadium_capacity > 0 then round(v24/p_stadium_capacity*100.0,10) end,
    case when p_stadium_capacity is not null and p_stadium_capacity > 0 then round(v72/p_stadium_capacity*100.0,10) end,
    case when p_stadium_capacity is not null and p_stadium_capacity > 0 then round(v168/p_stadium_capacity*100.0,10) end,
    round((v6-v24)::numeric,6),
    round((v24-v72)::numeric,6),
    round((v72-v168)::numeric,6),
    case when sector_data_available then matched_count end,
    case when sector_data_available then entered_count end,
    case when sector_data_available then left_count end,
    case when sector_data_available then matched_absorption end,
    case when sector_data_available then matched_release end,
    case when sector_data_available then coverage_effect end,
    case when sector_data_available then coverage_change end,
    case when sector_data_available then release_activity end,
    unexplained_increase,
    raw_count,
    clean_count,
    (invalid_count + duplicate_count)::integer,
    duplicate_count,
    invalid_count,
    round(observation_hours::numeric,3),
    round(max_gap_hours::numeric,3),
    has_data_gap
from finalized;
$function$;

comment on function public.get_live_trajectory_features_v1_asof(bigint,timestamptz,integer) is
'Canonical point-in-time Beyond live trajectory feature contract v1. Public ticket inventory is a demand proxy, not confirmed paid sales.';

create or replace view private.live_trajectory_checkpoint_features_v1 as
with horizons(horizon,target_interval) as (
    values
      ('T-30'::text, interval '30 days'),
      ('T-14'::text, interval '14 days'),
      ('T-7'::text, interval '7 days'),
      ('T-3'::text, interval '3 days'),
      ('T-1'::text, interval '1 day')
)
select
    te.id as ticket_event_id,
    te.club_slug,
    te.home_team,
    te.away_team,
    te.competition,
    te.kickoff_at,
    h.horizon as target_horizon,
    te.kickoff_at - h.target_interval as target_as_of_at,
    f.*
from public.ticket_events te
cross join horizons h
left join lateral public.get_live_trajectory_features_v1_asof(
    te.id,
    te.kickoff_at - h.target_interval,
    null
) f on true
where te.kickoff_at is not null
  and te.kickoff_at - h.target_interval <= now();

comment on view private.live_trajectory_checkpoint_features_v1 is
'Leakage-safe canonical checkpoint projection for Live Demand Engine v1. Each row is computed at the exact T-30/T-14/T-7/T-3/T-1 information cutoff.';
