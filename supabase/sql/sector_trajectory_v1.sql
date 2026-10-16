-- Beyond Ticketing — Sector Trajectory v1
--
-- Canonical point-in-time sector feature contract for E0.
-- Ownership is derived ONLY through:
--   sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id
-- sector_inventory.event_id is intentionally ignored.
--
-- Semantics:
-- - availability = observed public inventory, NOT confirmed paid sales;
-- - positive velocity = observed public availability decreased;
-- - availability increases are surfaced explicitly and never interpreted as
--   negative sales;
-- - the provisional relative-event gap compares each currently visible sector
--   with the current visible-sector set. It is not a learned demand curve.

create or replace function public.get_sector_trajectory_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    feature_version text,
    baseline_version text,
    ticket_event_id bigint,
    sector text,
    source_snapshot_id bigint,
    as_of_at timestamptz,
    kickoff_at timestamptz,
    hours_to_kickoff numeric,
    current_available integer,
    previous_available integer,
    previous_observed_at timestamptz,
    first_observed_at timestamptz,
    first_observed_available integer,
    max_observed_available integer,
    min_observed_available integer,
    reference_available integer,
    observation_count integer,
    availability_6h_ago integer,
    observed_hours_6h numeric,
    velocity_6h numeric,
    availability_24h_ago integer,
    observed_hours_24h numeric,
    velocity_24h numeric,
    availability_72h_ago integer,
    observed_hours_72h numeric,
    velocity_72h numeric,
    availability_7d_ago integer,
    observed_hours_7d numeric,
    velocity_7d numeric,
    acceleration_6h_vs_24h numeric,
    public_absorption_proxy integer,
    public_sell_through_proxy numeric,
    current_snapshot_sector_count integer,
    previous_snapshot_sector_count integer,
    sector_coverage_delta integer,
    event_current_available integer,
    event_reference_available bigint,
    event_remaining_ratio numeric,
    expected_sector_available numeric,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    inventory_increase_flag boolean,
    availability_increase_24h_flag boolean,
    max_positive_availability_delta_24h integer,
    sector_appeared_within_24h_flag boolean,
    sector_coverage_gap_flag boolean,
    sector_coverage_change_flag boolean,
    data_gap_flag boolean,
    trajectory_readiness text,
    point_in_time_validated boolean
)
language sql
stable
security invoker
set search_path = public
as $function$
with event_row as (
    select e.id,e.kickoff_at
    from public.ticket_events e
    where e.id=p_ticket_event_id
), latest_snapshot as (
    select s.id,s.captured_at,s.sector_count,s.available_total
    from public.snapshots s
    where s.ticket_event_id=p_ticket_event_id
      and s.captured_at<=p_as_of_at
    order by s.captured_at desc,s.id desc
    limit 1
), previous_snapshot as (
    select s.id,s.captured_at,s.sector_count,s.available_total
    from public.snapshots s
    cross join latest_snapshot l
    where s.ticket_event_id=p_ticket_event_id
      and (s.captured_at,s.id)<(l.captured_at,l.id)
    order by s.captured_at desc,s.id desc
    limit 1
), current_sector as (
    select
        si.sector,
        si.available as current_available
    from latest_snapshot l
    join public.sector_inventory si on si.snapshot_id=l.id
), history as (
    select
        si.sector,
        si.available,
        s.id as snapshot_id,
        s.captured_at
    from public.snapshots s
    join public.sector_inventory si on si.snapshot_id=s.id
    cross join latest_snapshot l
    where s.ticket_event_id=p_ticket_event_id
      and (s.captured_at,s.id)<=(l.captured_at,l.id)
), ranked_desc as (
    select
        h.*,
        row_number() over (
            partition by h.sector
            order by h.captured_at desc,h.snapshot_id desc
        ) as rn_desc
    from history h
), sector_stats as (
    select
        h.sector,
        min(h.captured_at) as first_observed_at,
        (array_agg(h.available order by h.captured_at,h.snapshot_id))[1]::integer as first_observed_available,
        max(h.available)::integer as max_observed_available,
        min(h.available)::integer as min_observed_available,
        count(*)::integer as observation_count
    from history h
    group by h.sector
), previous_sector as (
    select sector,available as previous_available,captured_at as previous_observed_at
    from ranked_desc
    where rn_desc=2
), w6 as (
    select distinct on (h.sector)
        h.sector,h.available,h.captured_at
    from history h
    cross join latest_snapshot l
    where h.captured_at<=l.captured_at-interval '6 hours'
    order by h.sector,h.captured_at desc,h.snapshot_id desc
), w24 as (
    select distinct on (h.sector)
        h.sector,h.available,h.captured_at
    from history h
    cross join latest_snapshot l
    where h.captured_at<=l.captured_at-interval '24 hours'
    order by h.sector,h.captured_at desc,h.snapshot_id desc
), w72 as (
    select distinct on (h.sector)
        h.sector,h.available,h.captured_at
    from history h
    cross join latest_snapshot l
    where h.captured_at<=l.captured_at-interval '72 hours'
    order by h.sector,h.captured_at desc,h.snapshot_id desc
), w7d as (
    select distinct on (h.sector)
        h.sector,h.available,h.captured_at
    from history h
    cross join latest_snapshot l
    where h.captured_at<=l.captured_at-interval '7 days'
    order by h.sector,h.captured_at desc,h.snapshot_id desc
), delta_history_24h as (
    select
        h.sector,
        h.available,
        lag(h.available) over (
            partition by h.sector
            order by h.captured_at,h.snapshot_id
        ) as previous_available
    from history h
    cross join latest_snapshot l
    where h.captured_at>=l.captured_at-interval '24 hours'
), delta_stats_24h as (
    select
        sector,
        coalesce(max(greatest(available-previous_available,0)),0)::integer as max_positive_delta
    from delta_history_24h
    group by sector
), assembled as (
    select
        c.sector,
        c.current_available,
        ps.previous_available,
        ps.previous_observed_at,
        st.first_observed_at,
        st.first_observed_available,
        st.max_observed_available,
        st.min_observed_available,
        st.max_observed_available as reference_available,
        st.observation_count,
        w6.available as availability_6h_ago,
        w6.captured_at as observed_at_6h,
        w24.available as availability_24h_ago,
        w24.captured_at as observed_at_24h,
        w72.available as availability_72h_ago,
        w72.captured_at as observed_at_72h,
        w7d.available as availability_7d_ago,
        w7d.captured_at as observed_at_7d,
        coalesce(d24.max_positive_delta,0) as max_positive_delta_24h
    from current_sector c
    join sector_stats st on st.sector=c.sector
    left join previous_sector ps on ps.sector=c.sector
    left join w6 on w6.sector=c.sector
    left join w24 on w24.sector=c.sector
    left join w72 on w72.sector=c.sector
    left join w7d on w7d.sector=c.sector
    left join delta_stats_24h d24 on d24.sector=c.sector
), event_totals as (
    select
        coalesce(sum(a.current_available),0)::integer as event_current_available,
        coalesce(sum(a.reference_available),0)::bigint as event_reference_available
    from assembled a
), metrics as (
    select
        a.*,
        case when a.observed_at_6h is not null
             then extract(epoch from (l.captured_at-a.observed_at_6h))/3600.0 end as hours_6h,
        case when a.observed_at_24h is not null
             then extract(epoch from (l.captured_at-a.observed_at_24h))/3600.0 end as hours_24h,
        case when a.observed_at_72h is not null
             then extract(epoch from (l.captured_at-a.observed_at_72h))/3600.0 end as hours_72h,
        case when a.observed_at_7d is not null
             then extract(epoch from (l.captured_at-a.observed_at_7d))/3600.0 end as hours_7d,
        case when a.observed_at_6h is not null and l.captured_at>a.observed_at_6h
             then (a.availability_6h_ago-a.current_available)
                  /(extract(epoch from (l.captured_at-a.observed_at_6h))/3600.0) end as velocity_6h_value,
        case when a.observed_at_24h is not null and l.captured_at>a.observed_at_24h
             then (a.availability_24h_ago-a.current_available)
                  /(extract(epoch from (l.captured_at-a.observed_at_24h))/3600.0) end as velocity_24h_value,
        case when a.observed_at_72h is not null and l.captured_at>a.observed_at_72h
             then (a.availability_72h_ago-a.current_available)
                  /(extract(epoch from (l.captured_at-a.observed_at_72h))/3600.0) end as velocity_72h_value,
        case when a.observed_at_7d is not null and l.captured_at>a.observed_at_7d
             then (a.availability_7d_ago-a.current_available)
                  /(extract(epoch from (l.captured_at-a.observed_at_7d))/3600.0) end as velocity_7d_value,
        et.event_current_available,
        et.event_reference_available,
        case when et.event_reference_available>0
             then et.event_current_available::numeric/et.event_reference_available end as event_remaining_ratio
    from assembled a
    cross join latest_snapshot l
    cross join event_totals et
)
select
    'sector-trajectory-v1'::text as feature_version,
    'PROVISIONAL_RELATIVE_EVENT_BASELINE_V1_CURRENT_VISIBLE_SET'::text as baseline_version,
    p_ticket_event_id as ticket_event_id,
    m.sector,
    l.id as source_snapshot_id,
    l.captured_at as as_of_at,
    e.kickoff_at,
    round((extract(epoch from (e.kickoff_at-l.captured_at))/3600.0)::numeric,4) as hours_to_kickoff,
    m.current_available,
    m.previous_available,
    m.previous_observed_at,
    m.first_observed_at,
    m.first_observed_available,
    m.max_observed_available,
    m.min_observed_available,
    m.reference_available,
    m.observation_count,
    m.availability_6h_ago,
    round(m.hours_6h::numeric,4),
    round(m.velocity_6h_value::numeric,6),
    m.availability_24h_ago,
    round(m.hours_24h::numeric,4),
    round(m.velocity_24h_value::numeric,6),
    m.availability_72h_ago,
    round(m.hours_72h::numeric,4),
    round(m.velocity_72h_value::numeric,6),
    m.availability_7d_ago,
    round(m.hours_7d::numeric,4),
    round(m.velocity_7d_value::numeric,6),
    case when m.velocity_6h_value is not null and m.velocity_24h_value is not null
         then round((m.velocity_6h_value-m.velocity_24h_value)::numeric,6) end,
    greatest(m.reference_available-m.current_available,0)::integer as public_absorption_proxy,
    case when m.reference_available>0
         then round((greatest(m.reference_available-m.current_available,0)::numeric/m.reference_available),6) end,
    coalesce(l.sector_count,(select count(*)::integer from current_sector)) as current_snapshot_sector_count,
    p.sector_count as previous_snapshot_sector_count,
    case when p.sector_count is not null
         then coalesce(l.sector_count,(select count(*)::integer from current_sector))-p.sector_count end,
    m.event_current_available,
    m.event_reference_available,
    round(m.event_remaining_ratio,6),
    case when m.event_remaining_ratio is not null
         then round((m.reference_available*m.event_remaining_ratio)::numeric,4) end,
    case when m.event_remaining_ratio is not null
         then round((m.current_available-(m.reference_available*m.event_remaining_ratio))::numeric,4) end,
    case when m.event_remaining_ratio is not null and m.reference_available>0
         then round(((m.current_available-(m.reference_available*m.event_remaining_ratio))/m.reference_available)::numeric,6) end,
    (m.previous_available is not null and m.current_available>m.previous_available) as inventory_increase_flag,
    (m.max_positive_delta_24h>0) as availability_increase_24h_flag,
    m.max_positive_delta_24h as max_positive_availability_delta_24h,
    (m.first_observed_at>=l.captured_at-interval '24 hours') as sector_appeared_within_24h_flag,
    (
        p.captured_at is not null
        and (m.previous_observed_at is null or m.previous_observed_at<p.captured_at)
    ) as sector_coverage_gap_flag,
    case
        when p.sector_count is null then false
        else abs(
            coalesce(l.sector_count,(select count(*)::integer from current_sector))-p.sector_count
        )>=greatest(3,ceil(p.sector_count*0.20)::integer)
    end as sector_coverage_change_flag,
    (
        m.previous_observed_at is null
        or l.captured_at-m.previous_observed_at>interval '45 minutes'
    ) as data_gap_flag,
    case
        when m.observation_count<3 or m.previous_available is null then 'INSUFFICIENT_HISTORY'
        when p.captured_at is not null and (m.previous_observed_at is null or m.previous_observed_at<p.captured_at) then 'COVERAGE_UNSTABLE'
        when l.captured_at-m.previous_observed_at>interval '45 minutes' then 'DATA_GAP'
        else 'READY'
    end::text as trajectory_readiness,
    true as point_in_time_validated
from metrics m
cross join event_row e
cross join latest_snapshot l
left join previous_snapshot p on true
order by m.sector;
$function$;

revoke all on function public.get_sector_trajectory_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_trajectory_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_trajectory_v1_asof(bigint,timestamptz) is
'PIT-safe E0 sector trajectory contract. Public availability is a demand proxy, not paid sales. sector_inventory.event_id is intentionally ignored; ownership is resolved through snapshots.ticket_event_id.';
