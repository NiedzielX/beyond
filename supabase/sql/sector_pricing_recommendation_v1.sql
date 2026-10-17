-- Beyond Ticketing — Sector Pricing Recommendation v1
--
-- Product recommendation layer on top of the full assumption-based scenario grid.
-- The scenario engine may calculate all variants, but this function only emits
-- an active price recommendation when there is enough measurable projected
-- future absorption for the scenario impact to be decision-useful.
--
-- Recommendation volume guard:
--   baseline future absorption >= max(5 seats, 2% of current public availability)
--
-- Human review is always required. Automatic price changes are forbidden.

create or replace function public.get_sector_pricing_recommendation_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    pricing_recommendation_version text,
    recommendation_policy_version text,
    scenario_engine_version text,
    assumption_set_version text,
    ticket_event_id bigint,
    sector text,
    sector_status text,
    trend_state text,
    hours_to_kickoff numeric,
    current_public_availability integer,
    reference_public_availability integer,
    sector_gap_ratio numeric,
    current_price numeric,
    currency text,
    price_data_status text,
    baseline_projected_public_availability_at_kickoff numeric,
    baseline_additional_absorption_proxy numeric,
    minimum_actionable_absorption numeric,
    recommended_action text,
    recommended_price_change_pct numeric,
    recommended_price numeric,
    recommended_projected_public_availability_at_kickoff numeric,
    recommended_projected_additional_absorption numeric,
    additional_absorption_delta_vs_hold numeric,
    recommended_future_window_revenue_proxy numeric,
    future_window_revenue_delta_vs_hold numeric,
    scenario_confidence text,
    recommendation_reason_code text,
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
), policy as (
    select
        c.*,
        greatest(
            c.current_public_availability::numeric
            -c.projected_public_availability_at_kickoff,
            0::numeric
        ) as baseline_absorption,
        greatest(5::numeric,c.current_public_availability::numeric*0.02::numeric) as minimum_actionable_absorption,
        case
            when c.price_data_status<>'READY' then null::numeric
            when not c.scenario_eligible then null::numeric
            when greatest(c.current_public_availability::numeric-c.projected_public_availability_at_kickoff,0::numeric)
                 < greatest(5::numeric,c.current_public_availability::numeric*0.02::numeric) then null::numeric
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
        end as product_recommended_pct
    from context c
), scenarios as (
    select *
    from public.get_sector_pricing_scenarios_v1_asof(p_ticket_event_id,p_as_of_at)
), selected as (
    select
        p.*,
        s.scenario_engine_version,
        s.assumption_set_version,
        s.scenario_price_proxy,
        s.projected_public_availability_at_kickoff_base,
        s.projected_additional_absorption_base,
        s.projected_future_window_revenue_proxy_base,
        s.hold_future_window_revenue_proxy,
        s.future_window_revenue_delta_vs_hold,
        s.scenario_confidence as engine_scenario_confidence,
        s.commercial_guardrails_status,
        s.maturity_label
    from policy p
    left join scenarios s
      on s.sector=p.sector
     and s.scenario_price_change_pct=coalesce(p.product_recommended_pct,0::numeric)
)
select
    'sector-pricing-recommendation-v1'::text,
    'E0_PRICE_RECOMMENDATION_V1_VOLUME_GUARD_MAX5_2PCT'::text,
    coalesce(s.scenario_engine_version,'sector-pricing-scenarios-v1')::text,
    coalesce(s.assumption_set_version,'E0_ELASTICITY_ASSUMPTIONS_V1_EPS_-0.5_-1.0_-1.5')::text,
    s.ticket_event_id,
    s.sector,
    s.sector_status,
    s.trend_state,
    s.hours_to_kickoff,
    s.current_public_availability,
    s.reference_public_availability,
    s.sector_gap_ratio,
    s.current_standard_price_proxy,
    s.currency,
    s.price_data_status,
    s.projected_public_availability_at_kickoff,
    round(s.baseline_absorption,2),
    round(s.minimum_actionable_absorption,2),
    case
        when s.product_recommended_pct is null then 'MONITOR'
        when s.product_recommended_pct<0 then 'DECREASE'
        when s.product_recommended_pct>0 then 'INCREASE'
        else 'HOLD'
    end::text,
    s.product_recommended_pct,
    case when s.product_recommended_pct is not null then round(s.scenario_price_proxy,2) end,
    case when s.product_recommended_pct is not null then round(s.projected_public_availability_at_kickoff_base,2) end,
    case when s.product_recommended_pct is not null then round(s.projected_additional_absorption_base,2) end,
    case when s.product_recommended_pct is not null then
        round(s.projected_additional_absorption_base-s.baseline_absorption,2)
    end,
    case when s.product_recommended_pct is not null then round(s.projected_future_window_revenue_proxy_base,2) end,
    case when s.product_recommended_pct is not null then round(s.future_window_revenue_delta_vs_hold,2) end,
    case
        when s.product_recommended_pct is null then 'LOW'
        else coalesce(s.engine_scenario_confidence,'LOW')
    end::text,
    case
        when s.price_data_status<>'READY' then 'PRICE_DATA_NOT_READY'
        when not s.scenario_eligible then 'SCENARIO_NOT_ELIGIBLE'
        when s.baseline_absorption<s.minimum_actionable_absorption then 'INSUFFICIENT_PROJECTED_FUTURE_VOLUME'
        when s.sector_status='UNDERPERFORMING' and s.product_recommended_pct=-0.10 then 'UNDERPERFORMING_MATERIAL_GAP_CONSIDER_STRONGER_DECREASE'
        when s.sector_status='UNDERPERFORMING' and s.product_recommended_pct=-0.05 then 'UNDERPERFORMING_CONSIDER_DECREASE'
        when s.sector_status='OUTPERFORMING' and s.product_recommended_pct=0.10 then 'OUTPERFORMING_SCARCE_CONSIDER_STRONGER_INCREASE'
        when s.sector_status='OUTPERFORMING' and s.product_recommended_pct=0.05 then 'OUTPERFORMING_CONSIDER_INCREASE'
        when s.sector_status='ON_TRACK' and s.product_recommended_pct=0 then 'ON_TRACK_HOLD'
        else 'MONITOR'
    end::text,
    coalesce(s.commercial_guardrails_status,'NOT_CONFIGURED')::text,
    true,
    false,
    coalesce(s.maturity_label,'ASSUMPTION_BASED_SCENARIO')::text,
    s.point_in_time_validated
from selected s
order by
    case s.sector_status
        when 'UNDERPERFORMING' then 1
        when 'ON_TRACK' then 2
        when 'OUTPERFORMING' then 3
        else 4
    end,
    s.sector_gap_ratio desc nulls last,
    s.sector;
$function$;

revoke all on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) is
'E0 product pricing recommendation. Active price action requires real price data and projected future absorption >= max(5 seats, 2% current public availability). Human review required; auto price change disabled.';
