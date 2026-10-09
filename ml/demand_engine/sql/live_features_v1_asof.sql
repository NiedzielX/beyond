-- Beyond Demand Engine v1 — strict point-in-time live features
--
-- Same semantics as get_live_features_v1(ticket_event_id), but every source
-- snapshot is restricted to captured_at <= p_as_of. This is required for
-- canonical-horizon evaluation when the job itself runs a few minutes after the
-- information cutoff.

create or replace function public.get_live_features_v1_asof(
    p_ticket_event_id bigint,
    p_as_of timestamptz
)
returns table(
    snapshot_id bigint,
    captured_at timestamptz,
    available_total integer,
    first_available_total integer,
    available_index numeric,
    net_removed_since_first integer,
    net_removed_since_previous integer,
    velocity_since_previous numeric,
    net_removed_6h bigint,
    velocity_6h numeric,
    net_removed_24h bigint,
    velocity_24h numeric,
    acceleration_6h_vs_24h numeric,
    matched_sector_count bigint,
    entered_sector_count bigint,
    left_sector_count bigint,
    coverage_inventory_effect bigint,
    sector_coverage_change_flag boolean,
    release_activity_flag boolean,
    raw_snapshot_count bigint,
    inventory_interpretation text
)
language sql
stable
security invoker
set search_path = public
as $$
with event_snapshots as (
    select
        s.id as snapshot_id,
        s.ticket_event_id,
        s.captured_at,
        s.available_total,
        s.sector_count,
        lag(s.id) over w as previous_snapshot_id,
        lag(s.captured_at) over w as previous_captured_at,
        lag(s.available_total) over w as previous_available_total,
        first_value(s.available_total) over w_full as first_available_total,
        count(*) over (partition by s.ticket_event_id) as raw_snapshot_count
    from public.snapshots s
    where s.ticket_event_id = p_ticket_event_id
      and s.available_total is not null
      and s.captured_at <= p_as_of
    window
        w as (
            partition by s.ticket_event_id
            order by s.captured_at, s.id
        ),
        w_full as (
            partition by s.ticket_event_id
            order by s.captured_at, s.id
            rows between unbounded preceding and unbounded following
        )
),
pairs as (
    select
        es.*,
        extract(epoch from (es.captured_at - es.previous_captured_at)) / 3600.0 as elapsed_hours
    from event_snapshots es
    where es.previous_snapshot_id is not null
),
sector_universe as (
    select p.*, sectors.sector
    from pairs p
    cross join lateral (
        select si.sector from public.sector_inventory si where si.snapshot_id = p.snapshot_id
        union
        select si.sector from public.sector_inventory si where si.snapshot_id = p.previous_snapshot_id
    ) sectors
),
sector_pairs as (
    select
        u.*,
        prev.available as previous_sector_available,
        cur.available as current_sector_available,
        case
            when prev.sector is not null and cur.sector is not null then 'matched'
            when prev.sector is null and cur.sector is not null then 'entered'
            when prev.sector is not null and cur.sector is null then 'left'
        end as sector_state
    from sector_universe u
    left join public.sector_inventory cur
        on cur.snapshot_id = u.snapshot_id and cur.sector = u.sector
    left join public.sector_inventory prev
        on prev.snapshot_id = u.previous_snapshot_id and prev.sector = u.sector
),
transition_summary as (
    select
        snapshot_id, previous_snapshot_id, ticket_event_id, captured_at,
        previous_captured_at, elapsed_hours, available_total,
        previous_available_total, first_available_total, sector_count,
        raw_snapshot_count,
        count(*) filter (where sector_state = 'matched') as matched_sector_count,
        count(*) filter (where sector_state = 'entered') as entered_sector_count,
        count(*) filter (where sector_state = 'left') as left_sector_count,
        coalesce(sum(greatest(previous_sector_available - current_sector_available, 0))
            filter (where sector_state = 'matched'), 0) as matched_absorption,
        coalesce(sum(greatest(current_sector_available - previous_sector_available, 0))
            filter (where sector_state = 'matched'), 0) as matched_release,
        coalesce(sum(current_sector_available) filter (where sector_state = 'entered'), 0) as entered_available,
        coalesce(sum(previous_sector_available) filter (where sector_state = 'left'), 0) as left_available
    from sector_pairs
    group by snapshot_id, previous_snapshot_id, ticket_event_id, captured_at,
        previous_captured_at, elapsed_hours, available_total,
        previous_available_total, first_available_total, sector_count, raw_snapshot_count
),
base as (
    select
        t.*,
        matched_absorption - matched_release as matched_net_absorption,
        entered_available - left_available as coverage_inventory_effect,
        previous_available_total - available_total as raw_net_removed_since_previous,
        first_available_total - available_total as raw_net_removed_since_first
    from transition_summary t
),
rolling as (
    select
        b.*,
        sum(matched_net_absorption) over w6 as matched_net_removed_6h,
        sum(elapsed_hours) over w6 as elapsed_6h,
        sum(matched_net_absorption) over w24 as matched_net_removed_24h,
        sum(elapsed_hours) over w24 as elapsed_24h
    from base b
    window
        w6 as (
            partition by ticket_event_id
            order by captured_at
            range between interval '6 hours' preceding and current row
        ),
        w24 as (
            partition by ticket_event_id
            order by captured_at
            range between interval '24 hours' preceding and current row
        )
)
select
    r.snapshot_id,
    r.captured_at,
    r.available_total,
    r.first_available_total,
    round((r.available_total::numeric / nullif(r.first_available_total, 0))::numeric, 6),
    r.raw_net_removed_since_first::integer,
    r.raw_net_removed_since_previous::integer,
    round((r.raw_net_removed_since_previous / nullif(r.elapsed_hours, 0))::numeric, 3),
    r.matched_net_removed_6h::bigint,
    round((r.matched_net_removed_6h / nullif(r.elapsed_6h, 0))::numeric, 3),
    r.matched_net_removed_24h::bigint,
    round((r.matched_net_removed_24h / nullif(r.elapsed_24h, 0))::numeric, 3),
    round(((r.matched_net_removed_6h / nullif(r.elapsed_6h, 0)) -
           (r.matched_net_removed_24h / nullif(r.elapsed_24h, 0)))::numeric, 3),
    r.matched_sector_count,
    r.entered_sector_count,
    r.left_sector_count,
    r.coverage_inventory_effect::bigint,
    (r.entered_sector_count > 0 or r.left_sector_count > 0),
    (r.matched_release > 0),
    r.raw_snapshot_count,
    'demand_proxy_not_confirmed_sales'::text
from rolling r
order by r.captured_at desc
limit 1;
$$;

-- Production permissions:
-- revoke all on function public.get_live_features_v1_asof(bigint,timestamptz)
--   from public, anon, authenticated;
-- grant execute on function public.get_live_features_v1_asof(bigint,timestamptz)
--   to service_role;
