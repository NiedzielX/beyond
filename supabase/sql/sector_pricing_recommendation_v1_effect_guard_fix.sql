-- Tighten the E0 product recommendation: an active non-HOLD price action must
-- have a material modeled incremental effect versus HOLD under the base
-- assumption, in addition to the existing future-volume guard.
--
-- Minimum incremental effect:
--   max(1 seat, 0.5% of current public availability)

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
), candidate_policy as (
    select
        c.*,
        greatest(
            c.current_public_availability::numeric
            -c.projected_public_availability_at_kickoff,
            0::numeric
        ) as baseline_absorption,
        greatest(5::numeric,c.current_public_availability::numeric*0.02::numeric) as minimum_actionable_absorption,
        greatest(1::numeric,c.current_public_availability::numeric*0.005::numeric) as minimum_incremental_effect,
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
        end as candidate_pct
    from context c
), scenarios as (
    select *
    from public.get_sector_pricing_scenarios_v1_asof(p_ticket_event_id,p_as_of_at)
), candidate_scenario as (
    select
        p.*,
        s.scenario_engine_version,
        s.assumption_set_version,
        s.scenario_price_proxy as candidate_price,
        s.projected_public_availability_at_kickoff_base as candidate_remaining,
        s.projected_additional_absorption_base as candidate_absorption,
        s.projected_future_window_revenue_proxy_base as candidate_revenue,
        s.future_window_revenue_delta_vs_hold as candidate_revenue_delta,
        s.scenario_confidence as engine_scenario_confidence,
        s.commercial_guardrails_status,
        s.maturity_label,
        case
            when p.candidate_pct is null then false
            when p.candidate_pct=0 then true
            when s.projected_additional_absorption_base is null then false
            when abs(s.projected_additional_absorption_base-p.baseline_absorption)>=p.minimum_incremental_effect then true
            else false
        end as incremental_effect_passes
    from candidate_policy p
    left join scenarios s
      on s.sector=p.sector
     and s.scenario_price_change_pct=coalesce(p.candidate_pct,0::numeric)
), final_policy as (
    select
        c.*,
        case when c.candidate_pct is not null and c.incremental_effect_passes then c.candidate_pct end as product_pct
    from candidate_scenario c
)
select
    'sector-pricing-recommendation-v1'::text,
    'E0_PRICE_RECOMMENDATION_V1_VOLUME_AND_EFFECT_GUARD'::text,
    coalesce(f.scenario_engine_version,'sector-pricing-scenarios-v1')::text,
    coalesce(f.assumption_set_version,'E0_ELASTICITY_ASSUMPTIONS_V1_EPS_-0.5_-1.0_-1.5')::text,
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
    f.price_data_status,
    f.projected_public_availability_at_kickoff,
    round(f.baseline_absorption,2),
    round(f.minimum_actionable_absorption,2),
    case
        when f.product_pct is null then 'MONITOR'
        when f.product_pct<0 then 'DECREASE'
        when f.product_pct>0 then 'INCREASE'
        else 'HOLD'
    end::text,
    f.product_pct,
    case when f.product_pct is not null then round(f.candidate_price,2) end,
    case when f.product_pct is not null then round(f.candidate_remaining,2) end,
    case when f.product_pct is not null then round(f.candidate_absorption,2) end,
    case when f.product_pct is not null then round(f.candidate_absorption-f.baseline_absorption,2) end,
    case when f.product_pct is not null then round(f.candidate_revenue,2) end,
    case when f.product_pct is not null then round(f.candidate_revenue_delta,2) end,
    case
        when f.product_pct is null then 'LOW'
        else coalesce(f.engine_scenario_confidence,'LOW')
    end::text,
    case
        when f.price_data_status<>'READY' then 'PRICE_DATA_NOT_READY'
        when not f.scenario_eligible then 'SCENARIO_NOT_ELIGIBLE'
        when f.baseline_absorption<f.minimum_actionable_absorption then 'INSUFFICIENT_PROJECTED_FUTURE_VOLUME'
        when f.candidate_pct is not null and f.candidate_pct<>0 and not f.incremental_effect_passes then 'INSUFFICIENT_INCREMENTAL_SCENARIO_EFFECT'
        when f.sector_status='UNDERPERFORMING' and f.product_pct=-0.10 then 'UNDERPERFORMING_MATERIAL_GAP_CONSIDER_STRONGER_DECREASE'
        when f.sector_status='UNDERPERFORMING' and f.product_pct=-0.05 then 'UNDERPERFORMING_CONSIDER_DECREASE'
        when f.sector_status='OUTPERFORMING' and f.product_pct=0.10 then 'OUTPERFORMING_SCARCE_CONSIDER_STRONGER_INCREASE'
        when f.sector_status='OUTPERFORMING' and f.product_pct=0.05 then 'OUTPERFORMING_CONSIDER_INCREASE'
        when f.sector_status='ON_TRACK' and f.product_pct=0 then 'ON_TRACK_HOLD'
        else 'MONITOR'
    end::text,
    coalesce(f.commercial_guardrails_status,'NOT_CONFIGURED')::text,
    true,
    false,
    coalesce(f.maturity_label,'ASSUMPTION_BASED_SCENARIO')::text,
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
    f.sector;
$function$;

revoke all on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_pricing_recommendation_v1_asof(bigint,timestamptz) is
'E0 product pricing recommendation. Active non-HOLD price action requires real price data, baseline future absorption >= max(5 seats, 2% current availability), and incremental modeled effect >= max(1 seat, 0.5% current availability). Human review required; auto price change disabled.';
