-- Beyond Ticketing — Price-area Pricing Recommendation v1
--
-- Resolves mixed-price sectors by moving the E0 pricing decision from the
-- sector level down to Roboticket priceAreaId. The sector demand signal remains
-- the diagnostic parent; current public inventory and no-action absorption are
-- allocated to active price areas by their current availability share.
--
-- This is assumption-based E0 decision support:
-- - base elasticity assumption: -1.0;
-- - active action requires projected future absorption >= max(5 seats, 2% of
--   current price-area public availability);
-- - non-HOLD action requires modeled incremental effect >= max(1 seat, 0.5% of
--   current price-area public availability);
-- - OUTPERFORMING + WEAKENING => HOLD;
-- - human review always required;
-- - automatic price changes are forbidden.

create or replace function public.get_price_area_pricing_recommendation_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    price_area_recommendation_version text,
    recommendation_policy_version text,
    assumption_set_version text,
    ticket_event_id bigint,
    sector text,
    sector_name text,
    sector_status text,
    trend_state text,
    hours_to_kickoff numeric,
    sector_gap_ratio numeric,
    projection_confidence text,
    price_area_id integer,
    price_area_name text,
    price_type_id integer,
    price_type_name text,
    current_price numeric,
    currency text,
    current_public_availability integer,
    availability_share_of_sector numeric,
    sector_baseline_projected_public_availability_at_kickoff numeric,
    baseline_projected_public_availability_at_kickoff numeric,
    baseline_additional_absorption_proxy numeric,
    minimum_actionable_absorption numeric,
    minimum_incremental_effect numeric,
    recommended_action text,
    recommended_price_change_pct numeric,
    recommended_price numeric,
    recommended_projected_public_availability_at_kickoff numeric,
    recommended_projected_additional_absorption numeric,
    additional_absorption_delta_vs_hold numeric,
    scenario_confidence text,
    recommendation_reason_code text,
    price_data_status text,
    requires_human_review boolean,
    auto_price_change_allowed boolean,
    maturity_label text,
    price_area_observed_at timestamptz,
    price_observed_at timestamptz,
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
        o.sector as sector_name,
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
        d.ticket_event_id,
        d.sector,
        p.sector_name,
        d.sector_status,
        d.trend_state,
        d.hours_to_kickoff,
        d.sector_gap_ratio,
        d.projection_confidence,
        d.current_available as sector_current_available,
        d.projected_public_availability_at_kickoff as sector_projected_available,
        d.point_in_time_validated,
        p.price_area_id,
        p.price_area_name,
        p.available,
        p.captured_at as price_area_observed_at
    from decision d
    join latest_pa p
      on (p.sector_name=d.sector or p.sector_source_id::text=d.sector)
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
), resolved_price as (
    select distinct on (price_area_id)
        price_area_id,
        price_area_name,
        price_type_id,
        price_type_name,
        price,
        currency,
        captured_at as price_observed_at
    from ranked_price
    where resolution_rank is not null
    order by price_area_id,resolution_rank,price desc,price_type_id
), context as (
    select
        a.*,
        coalesce(nullif(a.price_area_name,''),nullif(r.price_area_name,'')) as resolved_price_area_name,
        r.price_type_id,
        r.price_type_name,
        r.price,
        r.currency,
        r.price_observed_at,
        case
            when a.sector_current_available>0 then a.available::numeric/a.sector_current_available::numeric
            else null::numeric
        end as availability_share,
        greatest(
            a.sector_current_available::numeric-coalesce(a.sector_projected_available,a.sector_current_available::numeric),
            0::numeric
        ) as sector_baseline_absorption
    from active_pa a
    left join resolved_price r using(price_area_id)
), allocated as (
    select
        c.*,
        least(
            c.available::numeric,
            greatest(0::numeric,c.sector_baseline_absorption*coalesce(c.availability_share,0::numeric))
        ) as baseline_absorption,
        greatest(5::numeric,c.available::numeric*0.02::numeric) as minimum_actionable_absorption,
        greatest(1::numeric,c.available::numeric*0.005::numeric) as minimum_incremental_effect
    from context c
), candidate as (
    select
        a.*,
        greatest(0::numeric,a.available::numeric-a.baseline_absorption) as baseline_remaining,
        case
            when a.price is null or a.price<=0 then null::numeric
            when a.currency is null then null::numeric
            when a.sector_status='INSUFFICIENT_SIGNAL' then null::numeric
            when a.sector_projected_available is null then null::numeric
            when a.baseline_absorption<a.minimum_actionable_absorption then null::numeric
            when a.sector_status='UNDERPERFORMING' then
                case
                    when a.sector_gap_ratio>=0.25 and a.hours_to_kickoff>24 then -0.10::numeric
                    when a.sector_gap_ratio>=0.20 and a.trend_state='WEAKENING' then -0.10::numeric
                    else -0.05::numeric
                end
            when a.sector_status='OUTPERFORMING' and a.trend_state='WEAKENING' then 0::numeric
            when a.sector_status='OUTPERFORMING' then
                case
                    when greatest(0::numeric,a.available::numeric-a.baseline_absorption)
                         <=greatest(5::numeric,a.available::numeric*0.10::numeric)
                         and a.hours_to_kickoff>24 then 0.10::numeric
                    else 0.05::numeric
                end
            when a.sector_status='ON_TRACK' then 0::numeric
            else null::numeric
        end as candidate_pct
    from allocated a
), impact as (
    select
        c.*,
        case
            when c.candidate_pct is null then null::numeric
            else least(
                c.available::numeric,
                c.baseline_absorption*power((1+c.candidate_pct)::double precision,-1.0::double precision)::numeric
            )
        end as candidate_absorption
    from candidate c
), final_policy as (
    select
        i.*,
        case
            when i.candidate_pct is null then null::numeric
            when i.candidate_pct=0 then 0::numeric
            when i.candidate_absorption is null then null::numeric
            when abs(i.candidate_absorption-i.baseline_absorption)>=i.minimum_incremental_effect then i.candidate_pct
            else null::numeric
        end as product_pct
    from impact i
)
select
    'price-area-pricing-recommendation-v1'::text,
    'E0_PRICE_AREA_RECOMMENDATION_V1_SHARE_VOLUME_EFFECT_TREND_GUARDS'::text,
    'E0_ELASTICITY_ASSUMPTION_V1_BASE_EPS_-1.0'::text,
    f.ticket_event_id,
    f.sector,
    f.sector_name,
    f.sector_status,
    f.trend_state,
    f.hours_to_kickoff,
    f.sector_gap_ratio,
    f.projection_confidence,
    f.price_area_id,
    f.resolved_price_area_name,
    f.price_type_id,
    f.price_type_name,
    f.price,
    f.currency,
    f.available,
    round(f.availability_share,6),
    f.sector_projected_available,
    round(f.baseline_remaining,2),
    round(f.baseline_absorption,2),
    round(f.minimum_actionable_absorption,2),
    round(f.minimum_incremental_effect,2),
    case
        when f.product_pct is null then 'MONITOR'
        when f.product_pct<0 then 'DECREASE'
        when f.product_pct>0 then 'INCREASE'
        else 'HOLD'
    end::text,
    f.product_pct,
    case when f.product_pct is not null then round(f.price*(1+f.product_pct),2) end,
    case when f.product_pct is not null then round(greatest(0::numeric,f.available::numeric-f.candidate_absorption),2) end,
    case when f.product_pct is not null then round(f.candidate_absorption,2) end,
    case when f.product_pct is not null then round(f.candidate_absorption-f.baseline_absorption,2) end,
    case
        when f.product_pct is null then 'LOW'
        when f.projection_confidence in ('HIGH','MEDIUM') then 'MEDIUM'
        else 'LOW'
    end::text,
    case
        when f.price is null or f.price<=0 then 'BASE_PRICE_UNRESOLVED'
        when f.currency is null then 'CURRENCY_MISSING'
        when f.sector_status='INSUFFICIENT_SIGNAL' then 'SECTOR_SIGNAL_INSUFFICIENT'
        when f.sector_projected_available is null then 'NO_SECTOR_NO_ACTION_PROJECTION'
        when f.baseline_absorption<f.minimum_actionable_absorption then 'INSUFFICIENT_PROJECTED_FUTURE_VOLUME'
        when f.candidate_pct is not null and f.candidate_pct<>0 and f.product_pct is null then 'INSUFFICIENT_INCREMENTAL_SCENARIO_EFFECT'
        when f.sector_status='UNDERPERFORMING' and f.product_pct=-0.10 then 'UNDERPERFORMING_MATERIAL_GAP_CONSIDER_STRONGER_DECREASE'
        when f.sector_status='UNDERPERFORMING' and f.product_pct=-0.05 then 'UNDERPERFORMING_CONSIDER_DECREASE'
        when f.sector_status='OUTPERFORMING' and f.trend_state='WEAKENING' and f.product_pct=0 then 'OUTPERFORMING_BUT_WEAKENING_HOLD'
        when f.sector_status='OUTPERFORMING' and f.product_pct=0.10 then 'OUTPERFORMING_SCARCE_CONSIDER_STRONGER_INCREASE'
        when f.sector_status='OUTPERFORMING' and f.product_pct=0.05 then 'OUTPERFORMING_CONSIDER_INCREASE'
        when f.sector_status='ON_TRACK' and f.product_pct=0 then 'ON_TRACK_HOLD'
        else 'MONITOR'
    end::text,
    case
        when f.price is null or f.price<=0 then 'BASE_PRICE_UNRESOLVED'
        when f.currency is null then 'CURRENCY_MISSING'
        else 'READY'
    end::text,
    true,
    false,
    'ASSUMPTION_BASED_PRICE_AREA_SCENARIO'::text,
    f.price_area_observed_at,
    f.price_observed_at,
    f.point_in_time_validated
from final_policy f
order by
    case f.sector_status
        when 'UNDERPERFORMING' then 1
        when 'ON_TRACK' then 2
        when 'OUTPERFORMING' then 3
        else 4
    end,
    f.sector_gap_ratio desc nulls last,
    f.sector,
    f.price_area_id;
$function$;

revoke all on function public.get_price_area_pricing_recommendation_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_price_area_pricing_recommendation_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_price_area_pricing_recommendation_v1_asof(bigint,timestamptz) is
'E0 service-only Roboticket price-area recommendation for mixed-price sectors and detailed pricing analysis. Allocates sector no-action absorption by current price-area availability share. Assumption-based; human review required; auto price change disabled.';
