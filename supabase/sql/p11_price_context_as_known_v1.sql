-- P11b target-free price context as-known contract.
-- Purpose: expose only price/inventory information observed by p_as_of_at.
-- Explicit promotions are NOT inferred from price changes.
-- No attendance/outcome table is referenced. No production behavior changes.

create or replace function public.p11_price_context_as_known_v1(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz
)
returns jsonb
language sql
stable
security invoker
set search_path to 'public'
as $function$
with event_row as (
    select id, kickoff_at
    from public.ticket_events
    where id = p_ticket_event_id
), latest_price_at as (
    select max(captured_at) as captured_at
    from public.ticket_price_observations_v1
    where ticket_event_id = p_ticket_event_id
      and captured_at <= p_as_of_at
), previous_price_at as (
    select max(p.captured_at) as captured_at
    from public.ticket_price_observations_v1 p
    cross join latest_price_at l
    where p.ticket_event_id = p_ticket_event_id
      and p.captured_at < l.captured_at
), latest_price as (
    select
        count(*)::int as quote_rows,
        count(distinct price_area_id)::int as price_area_count,
        count(distinct price_type_id)::int as price_type_count,
        count(distinct price)::int as distinct_price_count,
        bool_or(price = 0) as zero_price_present,
        min(price) filter (where price > 0) as min_positive_price,
        percentile_cont(0.5) within group (order by price) filter (where price > 0) as median_positive_price,
        max(price) filter (where price > 0) as max_positive_price
    from public.ticket_price_observations_v1 p
    cross join latest_price_at l
    where p.ticket_event_id = p_ticket_event_id
      and p.captured_at = l.captured_at
), previous_price as (
    select
        percentile_cont(0.5) within group (order by price) filter (where price > 0) as median_positive_price
    from public.ticket_price_observations_v1 p
    cross join previous_price_at l
    where p.ticket_event_id = p_ticket_event_id
      and p.captured_at = l.captured_at
), latest_area_at as (
    select max(captured_at) as captured_at
    from public.sector_price_area_observations_v1
    where ticket_event_id = p_ticket_event_id
      and captured_at <= p_as_of_at
), latest_area_rows as (
    select a.*
    from public.sector_price_area_observations_v1 a
    cross join latest_area_at l
    where a.ticket_event_id = p_ticket_event_id
      and a.captured_at = l.captured_at
), area_totals as (
    select
        count(*)::int as row_count,
        count(distinct sector)::int as sector_count,
        count(distinct price_area_id)::int as price_area_count,
        coalesce(sum(available),0)::bigint as visible_available
    from latest_area_rows
), area_mix_raw as (
    select
        price_area_id,
        max(price_area_name) as price_area_name,
        sum(available)::bigint as available
    from latest_area_rows
    group by price_area_id
), area_total_available as (
    select coalesce(sum(available),0)::numeric as total_available
    from area_mix_raw
), area_mix as (
    select coalesce(
        jsonb_agg(
            jsonb_build_object(
                'price_area_id', r.price_area_id,
                'price_area_name', r.price_area_name,
                'available', r.available,
                'visible_availability_share',
                    case when t.total_available > 0
                         then round(r.available::numeric / t.total_available, 8)
                         else null end
            ) order by r.price_area_id
        ),
        '[]'::jsonb
    ) as payload
    from area_mix_raw r
    cross join area_total_available t
), capture_counts as (
    select count(distinct captured_at)::int as price_capture_count
    from public.ticket_price_observations_v1
    where ticket_event_id = p_ticket_event_id
      and captured_at <= p_as_of_at
)
select jsonb_build_object(
    'version','p11-price-context-as-known-v1',
    'ticket_event_id',p_ticket_event_id,
    'as_of_at',p_as_of_at,
    'kickoff_at',(select kickoff_at from event_row),
    'status',case
        when (select captured_at from latest_price_at) is not null then 'PRICE_CONTEXT_READY'
        when (select captured_at from latest_area_at) is not null then 'PRICE_AREA_ONLY'
        else 'MISSING'
    end,
    'price_observation',jsonb_build_object(
        'captured_at',(select captured_at from latest_price_at),
        'quote_rows',(select quote_rows from latest_price),
        'price_area_count',(select price_area_count from latest_price),
        'price_type_count',(select price_type_count from latest_price),
        'distinct_price_count',(select distinct_price_count from latest_price),
        'zero_price_present',coalesce((select zero_price_present from latest_price),false),
        'min_positive_price',(select min_positive_price from latest_price),
        'median_positive_price',(select median_positive_price from latest_price),
        'max_positive_price',(select max_positive_price from latest_price),
        'previous_captured_at',(select captured_at from previous_price_at),
        'previous_median_positive_price',(select median_positive_price from previous_price),
        'median_positive_price_delta',
            case when (select median_positive_price from latest_price) is not null
                       and (select median_positive_price from previous_price) is not null
                 then (select median_positive_price from latest_price) - (select median_positive_price from previous_price)
                 else null end,
        'median_positive_price_delta_pct',
            case when (select median_positive_price from latest_price) is not null
                       and (select median_positive_price from previous_price) > 0
                 then round(((select median_positive_price from latest_price) - (select median_positive_price from previous_price))
                            / (select median_positive_price from previous_price), 8)
                 else null end,
        'capture_count_as_known',(select price_capture_count from capture_counts)
    ),
    'price_area_inventory',jsonb_build_object(
        'captured_at',(select captured_at from latest_area_at),
        'row_count',(select row_count from area_totals),
        'sector_count',(select sector_count from area_totals),
        'price_area_count',(select price_area_count from area_totals),
        'visible_available',(select visible_available from area_totals),
        'availability_by_price_area',(select payload from area_mix)
    ),
    'promotion',jsonb_build_object(
        'explicit_evidence_available',false,
        'flag',null,
        'rule','DO_NOT_INFER_PROMOTION_FROM_PRICE_CHANGE'
    ),
    'target_values_used',false,
    'production_change',false
);
$function$;

revoke all on function public.p11_price_context_as_known_v1(bigint,timestamptz) from public, anon, authenticated;
grant execute on function public.p11_price_context_as_known_v1(bigint,timestamptz) to service_role;
