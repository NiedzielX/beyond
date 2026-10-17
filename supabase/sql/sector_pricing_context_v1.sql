-- Beyond Ticketing — Sector Pricing Context v1
--
-- Maps the E0 sector decision layer to Roboticket price-area observations and
-- resolves a conservative current/base price for assumption-based pricing.
--
-- Price resolution policy, in order:
-- 1. exact standard type: Normalny / Normal / Regular / Standard;
-- 2. exact price-type name == price-area name (e.g. Silver -> Silver);
-- 3. the only positive price type in a price area;
-- otherwise the base price is unresolved.
--
-- No price is inferred from sector name or inventory. This function is
-- service-role only and does not change production prices.

create or replace function public.get_sector_pricing_context_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    pricing_context_version text,
    standard_price_policy_version text,
    ticket_event_id bigint,
    sector text,
    sector_status text,
    trend_state text,
    hours_to_kickoff numeric,
    current_public_availability integer,
    reference_public_availability integer,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    projected_public_availability_at_kickoff numeric,
    projection_confidence text,
    price_area_count integer,
    resolved_price_area_count integer,
    price_area_ids integer[],
    price_area_names text[],
    resolved_price_type_names text[],
    current_standard_price_proxy numeric,
    standard_price_min numeric,
    standard_price_max numeric,
    currency text,
    price_area_observed_at timestamptz,
    price_observed_at timestamptz,
    price_data_status text,
    scenario_eligible boolean,
    point_in_time_validated boolean
)
language sql
stable
security invoker
set search_path = public
as $function$
with decision as (
    select *
    from public.get_sector_decision_v1_asof(p_ticket_event_id,p_as_of_at)
), latest_pa as (
    select distinct on (o.sector_source_id,o.sector,o.price_area_id)
        o.ticket_event_id,
        o.sector,
        o.sector_source_id,
        o.price_area_id,
        o.price_area_name,
        o.available,
        o.captured_at
    from public.sector_price_area_observations_v1 o
    where o.ticket_event_id=p_ticket_event_id
      and o.captured_at<=p_as_of_at
    order by o.sector_source_id,o.sector,o.price_area_id,o.captured_at desc,o.id desc
), active_pa as (
    select
        d.sector as decision_sector,
        p.price_area_id,
        p.price_area_name,
        p.available,
        p.captured_at
    from decision d
    join latest_pa p
      on (p.sector=d.sector or p.sector_source_id::text=d.sector)
    where p.available>0
), latest_prices as (
    select distinct on (o.price_area_id,o.price_type_id)
        o.price_area_id,
        o.price_area_name,
        o.price_type_id,
        o.price_type_name,
        o.price,
        o.currency,
        o.captured_at
    from public.ticket_price_observations_v1 o
    where o.ticket_event_id=p_ticket_event_id
      and o.captured_at<=p_as_of_at
    order by o.price_area_id,o.price_type_id,o.captured_at desc,o.id desc
), positive_counts as (
    select price_area_id,count(*) filter(where price>0)::integer as positive_price_type_count
    from latest_prices
    group by price_area_id
), ranked_price as (
    select
        p.*,
        case
            when p.price<=0 then null
            when lower(trim(coalesce(p.price_type_name,''))) in ('normalny','normal','regular','standard') then 1
            when lower(trim(coalesce(p.price_type_name,'')))=lower(trim(coalesce(p.price_area_name,'')))
                 and trim(coalesce(p.price_area_name,''))<>'' then 2
            when pc.positive_price_type_count=1 then 3
            else null
        end as resolution_rank
    from latest_prices p
    left join positive_counts pc using(price_area_id)
), resolved_area_price as (
    select distinct on (price_area_id)
        price_area_id,
        coalesce(price_area_name,'') as price_area_name,
        price_type_id,
        price_type_name,
        price,
        currency,
        captured_at,
        resolution_rank
    from ranked_price
    where resolution_rank is not null
    order by price_area_id,resolution_rank,price desc,price_type_id
), sector_price_rows as (
    select
        a.decision_sector,
        a.price_area_id,
        coalesce(nullif(a.price_area_name,''),nullif(r.price_area_name,'')) as price_area_name,
        a.available,
        a.captured_at as price_area_observed_at,
        r.price_type_name,
        r.price,
        r.currency,
        r.captured_at as price_observed_at
    from active_pa a
    left join resolved_area_price r using(price_area_id)
), sector_price_agg as (
    select
        decision_sector,
        count(*)::integer as price_area_count,
        count(*) filter(where price is not null)::integer as resolved_price_area_count,
        array_agg(price_area_id order by price_area_id) as price_area_ids,
        array_agg(coalesce(price_area_name,'') order by price_area_id) as price_area_names,
        array_agg(coalesce(price_type_name,'') order by price_area_id)
            filter(where price is not null) as resolved_price_type_names,
        case
            when sum(available) filter(where price is not null)>0 then
                sum(available::numeric*price) filter(where price is not null)
                /sum(available) filter(where price is not null)
        end as weighted_price,
        min(price) filter(where price is not null) as min_price,
        max(price) filter(where price is not null) as max_price,
        case when count(distinct currency) filter(where price is not null)=1
             then max(currency) filter(where price is not null) end as currency,
        max(price_area_observed_at) as price_area_observed_at,
        max(price_observed_at) as price_observed_at,
        count(distinct currency) filter(where price is not null) as currency_count
    from sector_price_rows
    group by decision_sector
), joined as (
    select
        d.*,
        a.price_area_count,
        a.resolved_price_area_count,
        a.price_area_ids,
        a.price_area_names,
        a.resolved_price_type_names,
        a.weighted_price,
        a.min_price,
        a.max_price,
        a.currency,
        a.price_area_observed_at,
        a.price_observed_at,
        a.currency_count,
        case
            when coalesce(a.price_area_count,0)=0 then 'PRICE_AREA_MAPPING_MISSING'
            when coalesce(a.resolved_price_area_count,0)=0 then 'BASE_PRICE_UNRESOLVED'
            when a.currency_count>1 then 'CURRENCY_MISMATCH'
            when a.resolved_price_area_count<a.price_area_count then 'PARTIAL_PRICE_DATA'
            when coalesce(a.weighted_price,0)<=0 then 'NON_POSITIVE_BASE_PRICE'
            else 'READY'
        end::text as price_status
    from decision d
    left join sector_price_agg a on a.decision_sector=d.sector
)
select
    'sector-pricing-context-v1'::text,
    'STANDARD_PRICE_POLICY_V1_EXACT_NORMAL_AREA_NAME_UNIQUE_POSITIVE'::text,
    j.ticket_event_id,
    j.sector,
    j.sector_status,
    j.trend_state,
    j.hours_to_kickoff,
    j.current_available,
    j.reference_available,
    round((j.sector_gap_ratio*j.reference_available)::numeric,2),
    j.sector_gap_ratio,
    j.projected_public_availability_at_kickoff,
    j.projection_confidence,
    coalesce(j.price_area_count,0),
    coalesce(j.resolved_price_area_count,0),
    j.price_area_ids,
    j.price_area_names,
    j.resolved_price_type_names,
    round(j.weighted_price,2),
    j.min_price,
    j.max_price,
    j.currency,
    j.price_area_observed_at,
    j.price_observed_at,
    j.price_status,
    (
        j.price_status='READY'
        and j.sector_status<>'INSUFFICIENT_SIGNAL'
        and j.projected_public_availability_at_kickoff is not null
        and j.current_available>0
        and coalesce(j.weighted_price,0)>0
    ),
    j.point_in_time_validated
from joined j
order by
    case j.sector_status
        when 'UNDERPERFORMING' then 1
        when 'ON_TRACK' then 2
        when 'OUTPERFORMING' then 3
        else 4
    end,
    j.sector_gap_ratio desc nulls last,
    j.sector;
$function$;

revoke all on function public.get_sector_pricing_context_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_pricing_context_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_pricing_context_v1_asof(bigint,timestamptz) is
'E0 service-only sector pricing context. Resolves real observed Roboticket prices conservatively; no inferred prices and no automatic price action.';
