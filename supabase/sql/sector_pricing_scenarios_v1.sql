-- Beyond Ticketing — Sector Pricing Scenarios v1
--
-- Assumption-based E0 dynamic-pricing decision support.
-- No learned elasticity and no automatic price changes.
--
-- Constant-elasticity sensitivity set:
--   conservative magnitude: -0.5
--   base assumption:         -1.0
--   high magnitude:          -1.5
--
-- Scenario impact applies the assumed demand multiplier only to projected
-- additional public-inventory absorption from now to kickoff. Revenue is a
-- future-window proxy, not booked/verified revenue.

create or replace function public.get_sector_pricing_scenarios_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    scenario_engine_version text,
    assumption_set_version text,
    recommendation_policy_version text,
    ticket_event_id bigint,
    sector text,
    sector_status text,
    trend_state text,
    hours_to_kickoff numeric,
    current_public_availability integer,
    reference_public_availability integer,
    sector_gap_ratio numeric,
    current_standard_price_proxy numeric,
    currency text,
    price_area_ids integer[],
    price_data_status text,
    scenario_price_change_pct numeric,
    scenario_action text,
    scenario_price_proxy numeric,
    elasticity_conservative numeric,
    elasticity_base numeric,
    elasticity_high_magnitude numeric,
    baseline_projected_public_availability_at_kickoff numeric,
    baseline_additional_absorption_proxy numeric,
    demand_multiplier_conservative numeric,
    demand_multiplier_base numeric,
    demand_multiplier_high_magnitude numeric,
    projected_additional_absorption_base numeric,
    projected_public_availability_at_kickoff_base numeric,
    projected_public_sell_through_proxy_base numeric,
    projected_future_window_revenue_proxy_base numeric,
    hold_future_window_revenue_proxy numeric,
    future_window_revenue_delta_vs_hold numeric,
    projected_public_availability_conservative numeric,
    projected_public_availability_high_magnitude numeric,
    recommended_price_change_pct numeric,
    recommended_action text,
    is_recommended_scenario boolean,
    scenario_confidence text,
    commercial_guardrails_status text,
    requires_human_review boolean,
    auto_price_change_allowed boolean,
    maturity_label text,
    point_in_time_validated boolean
)
language sql
stable
security invoker
set search_path = public
as $function$
with context as (
    select *
    from public.get_sector_pricing_context_v1_asof(p_ticket_event_id,p_as_of_at)
), recommendation as (
    select
        c.*,
        case
            when not c.scenario_eligible then null::numeric
            when c.sector_status='UNDERPERFORMING' then
                case
                    when c.sector_gap_ratio>=0.25 and c.hours_to_kickoff>24 then -0.10::numeric
                    when c.sector_gap_ratio>=0.20 and c.trend_state='WEAKENING' then -0.10::numeric
                    else -0.05::numeric
                end
            when c.sector_status='OUTPERFORMING' then
                case
                    when c.projected_public_availability_at_kickoff<=greatest(5::numeric,c.current_public_availability*0.10::numeric)
                         and c.hours_to_kickoff>24 then 0.10::numeric
                    else 0.05::numeric
                end
            when c.sector_status='ON_TRACK' then 0::numeric
            else null::numeric
        end as recommended_pct
    from context c
), grid as (
    select r.*,g.pct
    from recommendation r
    cross join (values
        (-0.10::numeric),
        (-0.05::numeric),
        (0.00::numeric),
        (0.05::numeric),
        (0.10::numeric)
    ) g(pct)
    where r.scenario_eligible
), baseline as (
    select
        g.*,
        greatest(
            g.current_public_availability::numeric
            -g.projected_public_availability_at_kickoff,
            0::numeric
        ) as baseline_absorption,
        g.current_standard_price_proxy*(1+g.pct) as scenario_price,
        power((1+g.pct)::double precision,-0.5::double precision)::numeric as multiplier_conservative,
        power((1+g.pct)::double precision,-1.0::double precision)::numeric as multiplier_base,
        power((1+g.pct)::double precision,-1.5::double precision)::numeric as multiplier_high
    from grid g
), impacts as (
    select
        b.*,
        least(b.current_public_availability::numeric,b.baseline_absorption*b.multiplier_conservative) as absorption_conservative,
        least(b.current_public_availability::numeric,b.baseline_absorption*b.multiplier_base) as absorption_base,
        least(b.current_public_availability::numeric,b.baseline_absorption*b.multiplier_high) as absorption_high
    from baseline b
), final as (
    select
        i.*,
        greatest(0::numeric,i.current_public_availability-i.absorption_conservative) as remaining_conservative,
        greatest(0::numeric,i.current_public_availability-i.absorption_base) as remaining_base,
        greatest(0::numeric,i.current_public_availability-i.absorption_high) as remaining_high,
        i.scenario_price*i.absorption_base as revenue_base,
        i.current_standard_price_proxy*i.baseline_absorption as hold_revenue
    from impacts i
)
select
    'sector-pricing-scenarios-v1'::text,
    'E0_ELASTICITY_ASSUMPTIONS_V1_EPS_-0.5_-1.0_-1.5'::text,
    'E0_PRICE_RECOMMENDATION_V1_STATUS_GAP_TREND_SCARCITY'::text,
    f.ticket_event_id,
    f.sector,
    f.sector_status,
    f.trend_state,
    f.hours_to_kickoff,
    f.current_public_availability,
    f.reference_public_availability,
    f.sector_gap_ratio,
    f.current_standard_price_proxy,
    f.currency,
    f.price_area_ids,
    f.price_data_status,
    f.pct,
    case
        when f.pct<0 then 'DECREASE'
        when f.pct>0 then 'INCREASE'
        else 'HOLD'
    end::text,
    round(f.scenario_price,2),
    -0.5::numeric,
    -1.0::numeric,
    -1.5::numeric,
    f.projected_public_availability_at_kickoff,
    round(f.baseline_absorption,2),
    round(f.multiplier_conservative,6),
    round(f.multiplier_base,6),
    round(f.multiplier_high,6),
    round(f.absorption_base,2),
    round(f.remaining_base,2),
    case when f.reference_public_availability>0 then
        round(least(1::numeric,greatest(0::numeric,1-(f.remaining_base/f.reference_public_availability))),6)
    end,
    round(f.revenue_base,2),
    round(f.hold_revenue,2),
    round(f.revenue_base-f.hold_revenue,2),
    round(f.remaining_conservative,2),
    round(f.remaining_high,2),
    f.recommended_pct,
    case
        when f.recommended_pct is null then 'MONITOR'
        when f.recommended_pct<0 then 'DECREASE'
        when f.recommended_pct>0 then 'INCREASE'
        else 'HOLD'
    end::text,
    (f.recommended_pct is not null and f.pct=f.recommended_pct),
    case
        when f.projection_confidence='HIGH' then 'MEDIUM'
        when f.projection_confidence='MEDIUM' then 'MEDIUM'
        else 'LOW'
    end::text,
    'NOT_CONFIGURED'::text,
    true,
    false,
    'ASSUMPTION_BASED_SCENARIO'::text,
    f.point_in_time_validated
from final f
order by
    case f.sector_status
        when 'UNDERPERFORMING' then 1
        when 'ON_TRACK' then 2
        when 'OUTPERFORMING' then 3
        else 4
    end,
    f.sector_gap_ratio desc nulls last,
    f.sector,
    f.pct;
$function$;

revoke all on function public.get_sector_pricing_scenarios_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_pricing_scenarios_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_pricing_scenarios_v1_asof(bigint,timestamptz) is
'E0 assumption-based price scenarios using real observed base prices and provisional elasticity assumptions. Human review required; auto price change disabled.';
