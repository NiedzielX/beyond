-- Beyond Ticketing — Sector Decision v1
--
-- E0 decision layer built on release-aware sector-gap-v1.
-- Produces:
-- - deterministic horizon-aware sector status;
-- - trend state from recent velocity/acceleration;
-- - bounded projected public availability at kickoff if current trajectory continues.
--
-- This is NOT a causal counterfactual and NOT a paid-sales forecast.

create or replace function public.get_sector_decision_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    decision_version text,
    status_policy_version text,
    projection_policy_version text,
    ticket_event_id bigint,
    sector text,
    source_snapshot_id bigint,
    as_of_at timestamptz,
    kickoff_at timestamptz,
    hours_to_kickoff numeric,
    current_available integer,
    reference_available integer,
    sector_gap_ratio numeric,
    material_gap_threshold numeric,
    sector_status text,
    status_reason_code text,
    trend_state text,
    gap_reliability text,
    projection_velocity numeric,
    projection_velocity_method text,
    projected_public_availability_at_kickoff numeric,
    projected_public_inventory_change numeric,
    projected_additional_absorption_proxy numeric,
    projected_public_sell_through_proxy numeric,
    projection_confidence text,
    projection_reason_code text,
    potential_release_activity_flag boolean,
    coverage_stable_flag boolean,
    point_in_time_validated boolean
)
language sql
stable
security invoker
set search_path = public
as $function$
with gap as (
    select *
    from public.get_sector_gap_v1_asof(p_ticket_event_id,p_as_of_at)
), classified as (
    select
        g.*,
        case
            when g.hours_to_kickoff<=24 then 0.10::numeric
            when g.hours_to_kickoff<=72 then 0.15::numeric
            else 0.20::numeric
        end as threshold_value,
        case
            when g.velocity_6h is null then 'UNKNOWN'
            when g.velocity_24h is null then
                case
                    when g.velocity_6h>0 then 'IMPROVING'
                    when g.velocity_6h<0 then 'WEAKENING'
                    else 'FLAT'
                end
            when g.velocity_6h>g.velocity_24h and g.velocity_6h>0 then 'IMPROVING'
            when g.velocity_6h<g.velocity_24h and g.velocity_6h<=0 then 'WEAKENING'
            else 'STABLE'
        end::text as trend_state_value
    from gap g
), status_layer as (
    select
        c.*,
        case
            when not c.gap_usable_for_status then 'INSUFFICIENT_SIGNAL'
            when c.sector_gap_ratio>=c.threshold_value then 'UNDERPERFORMING'
            when c.sector_gap_ratio<=-c.threshold_value then 'OUTPERFORMING'
            else 'ON_TRACK'
        end::text as sector_status_value,
        case
            when not c.gap_usable_for_status and c.potential_release_activity_flag then 'MATERIAL_AVAILABILITY_RELEASE_RISK'
            when not c.gap_usable_for_status and not c.coverage_stable_flag then 'COVERAGE_UNSTABLE'
            when not c.gap_usable_for_status then 'INSUFFICIENT_TRAJECTORY_SIGNAL'
            when c.sector_gap_ratio>=c.threshold_value then 'POSITIVE_GAP_ABOVE_HORIZON_THRESHOLD'
            when c.sector_gap_ratio<=-c.threshold_value then 'NEGATIVE_GAP_BELOW_HORIZON_THRESHOLD'
            else 'GAP_WITHIN_HORIZON_THRESHOLD'
        end::text as status_reason
    from classified c
), projection_input as (
    select
        s.*,
        case
            when not s.gap_usable_for_status then null::numeric
            when s.hours_to_kickoff<=24 and s.velocity_6h is not null and s.velocity_24h is not null
                then 0.60*s.velocity_6h+0.40*s.velocity_24h
            when s.velocity_24h is not null and s.velocity_72h is not null
                then 0.70*s.velocity_24h+0.30*s.velocity_72h
            when s.velocity_24h is not null then s.velocity_24h
            when s.velocity_72h is not null then s.velocity_72h
            when s.velocity_7d is not null then s.velocity_7d
            when s.velocity_6h is not null then s.velocity_6h
            else null::numeric
        end as chosen_velocity,
        case
            when not s.gap_usable_for_status then 'NONE'
            when s.hours_to_kickoff<=24 and s.velocity_6h is not null and s.velocity_24h is not null then 'BLEND_60_V6H_40_V24H'
            when s.velocity_24h is not null and s.velocity_72h is not null then 'BLEND_70_V24H_30_V72H'
            when s.velocity_24h is not null then 'V24H'
            when s.velocity_72h is not null then 'V72H'
            when s.velocity_7d is not null then 'V7D'
            when s.velocity_6h is not null then 'V6H'
            else 'NONE'
        end::text as velocity_method
    from status_layer s
), projected as (
    select
        p.*,
        case
            when p.chosen_velocity is null then null::numeric
            else least(
                p.reference_available::numeric,
                greatest(
                    0::numeric,
                    p.current_available::numeric-(p.chosen_velocity*greatest(p.hours_to_kickoff,0))
                )
            )
        end as projected_available
    from projection_input p
)
select
    'sector-decision-v1'::text,
    'SECTOR_STATUS_V1_HORIZON_10_15_20'::text,
    'SECTOR_NO_ACTION_PROJECTION_V1_BOUNDED_VELOCITY_BLEND'::text,
    p.ticket_event_id,
    p.sector,
    p.source_snapshot_id,
    p.as_of_at,
    p.kickoff_at,
    p.hours_to_kickoff,
    p.current_available,
    p.reference_available,
    p.sector_gap_ratio,
    p.threshold_value,
    p.sector_status_value,
    p.status_reason,
    p.trend_state_value,
    p.gap_reliability,
    round(p.chosen_velocity,6),
    p.velocity_method,
    round(p.projected_available,2),
    case when p.projected_available is not null
         then round((p.projected_available-p.current_available)::numeric,2) end,
    case when p.projected_available is not null
         then round(greatest(p.current_available-p.projected_available,0)::numeric,2) end,
    case when p.projected_available is not null and p.reference_available>0
         then round((1-(p.projected_available/p.reference_available))::numeric,6) end,
    case
        when p.projected_available is null then 'INSUFFICIENT'
        when p.gap_reliability='HIGH' and p.velocity_method like 'BLEND_%' then 'HIGH'
        when p.gap_reliability in ('HIGH','MEDIUM') then 'MEDIUM'
        else 'LOW'
    end::text,
    case
        when p.projected_available is null and p.potential_release_activity_flag then 'NO_PROJECTION_MATERIAL_RELEASE_RISK'
        when p.projected_available is null and not p.coverage_stable_flag then 'NO_PROJECTION_COVERAGE_UNSTABLE'
        when p.projected_available is null then 'NO_PROJECTION_INSUFFICIENT_SIGNAL'
        when p.chosen_velocity<0 then 'CURRENT_TRAJECTORY_IMPLIES_MORE_PUBLIC_AVAILABILITY'
        when p.chosen_velocity=0 then 'CURRENT_TRAJECTORY_FLAT'
        else 'CURRENT_TRAJECTORY_CONTINUES'
    end::text,
    p.potential_release_activity_flag,
    p.coverage_stable_flag,
    p.point_in_time_validated
from projected p
order by p.sector;
$function$;

revoke all on function public.get_sector_decision_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_decision_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_decision_v1_asof(bigint,timestamptz) is
'E0 sector status plus bounded public-inventory continuation projection. Decision support only; not paid sales, not causal uplift, not automatic pricing.';
