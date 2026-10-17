-- Beyond Ticketing — E0 Dashboard Pricing v1
--
-- Extends the existing RLS-safe current dashboard cache with only the final
-- volume/effect/commercial-safety-guarded product recommendation. The full
-- scenario grid remains service-role only.

alter table public.dashboard_sector_decision_current_v1
    add column if not exists recommended_price_change_pct numeric,
    add column if not exists recommended_price numeric,
    add column if not exists pricing_recommendation_action text,
    add column if not exists pricing_scenario_confidence text,
    add column if not exists pricing_recommendation_reason_code text,
    add column if not exists pricing_maturity_label text,
    add column if not exists pricing_commercial_guardrails_status text,
    add column if not exists pricing_projected_public_availability_at_kickoff numeric,
    add column if not exists pricing_additional_absorption_delta_vs_hold numeric,
    add column if not exists pricing_revenue_proxy_delta_vs_hold numeric,
    add column if not exists pricing_requires_human_review boolean,
    add column if not exists auto_price_change_allowed boolean,
    add column if not exists pricing_recommendation_version text,
    add column if not exists pricing_assumption_set_version text;

alter table public.dashboard_sector_summary_current_v1
    add column if not exists priced_sector_count integer,
    add column if not exists pricing_actionable_count integer,
    add column if not exists pricing_decrease_count integer,
    add column if not exists pricing_hold_count integer,
    add column if not exists pricing_increase_count integer,
    add column if not exists pricing_monitor_count integer,
    add column if not exists top_pricing_sector text,
    add column if not exists top_pricing_action text,
    add column if not exists top_pricing_current_price numeric,
    add column if not exists top_pricing_recommended_price numeric,
    add column if not exists top_pricing_change_pct numeric,
    add column if not exists pricing_maturity_label text;

create or replace function public.refresh_dashboard_sector_decision_v1()
returns jsonb
language plpgsql
security invoker
set search_path = public,private
as $function$
declare
    v_detail_count integer := 0;
    v_summary_count integer := 0;
begin
    delete from public.dashboard_sector_decision_current_v1;
    delete from public.dashboard_sector_summary_current_v1;

    with active_events as materialized (
        select e.*
        from public.ticket_events e
        where e.kickoff_at>now()
          and exists(select 1 from public.snapshots s where s.ticket_event_id=e.id)
    ), decisions as materialized (
        select e.id as event_id,d.*
        from active_events e
        cross join lateral public.get_sector_decision_v1_asof(e.id,now()) d
    ), pricing as materialized (
        select e.id as event_id,p.*
        from active_events e
        cross join lateral public.get_sector_pricing_recommendation_v1_asof(e.id,now()) p
        where exists(
            select 1 from public.sector_price_area_observations_v1 po
            where po.ticket_event_id=e.id
        )
    )
    insert into public.dashboard_sector_decision_current_v1(
        ticket_event_id,home_team,away_team,competition,kickoff_at,sector,as_of_at,hours_to_kickoff,
        current_public_availability,reference_public_availability,sector_gap_available,sector_gap_ratio,
        sector_status,status_reason_code,trend_state,projected_public_availability_at_kickoff,
        projected_public_sell_through_proxy,projection_confidence,projection_reason_code,
        price_data_status,current_price,currency,pricing_recommendation_status,data_quality_status,
        decision_version,status_policy_version,projection_policy_version,refreshed_at,
        recommended_price_change_pct,recommended_price,pricing_recommendation_action,pricing_scenario_confidence,
        pricing_recommendation_reason_code,pricing_maturity_label,pricing_commercial_guardrails_status,
        pricing_projected_public_availability_at_kickoff,pricing_additional_absorption_delta_vs_hold,
        pricing_revenue_proxy_delta_vs_hold,pricing_requires_human_review,auto_price_change_allowed,
        pricing_recommendation_version,pricing_assumption_set_version
    )
    select
        e.id,e.home_team,e.away_team,e.competition,e.kickoff_at,d.sector,d.as_of_at,d.hours_to_kickoff,
        d.current_available,d.reference_available,
        round((d.sector_gap_ratio*d.reference_available)::numeric,2),d.sector_gap_ratio,
        d.sector_status,d.status_reason_code,d.trend_state,d.projected_public_availability_at_kickoff,
        d.projected_public_sell_through_proxy,d.projection_confidence,d.projection_reason_code,
        coalesce(p.price_data_status,'PRICE_DATA_MISSING'),
        p.current_price,p.currency,
        case
            when p.ticket_event_id is null then 'PENDING_PRICE_DATA'
            when p.recommended_action in ('DECREASE','INCREASE') then 'ACTIONABLE_SCENARIO'
            when p.recommended_action='HOLD' then 'HOLD'
            else 'MONITOR'
        end,
        case when d.sector_status='INSUFFICIENT_SIGNAL' or d.projection_confidence='INSUFFICIENT'
             then 'ATTENTION_REQUIRED' else 'OK' end,
        d.decision_version,d.status_policy_version,d.projection_policy_version,now(),
        p.recommended_price_change_pct,p.recommended_price,p.recommended_action,p.scenario_confidence,
        p.recommendation_reason_code,p.maturity_label,p.commercial_guardrails_status,
        p.recommended_projected_public_availability_at_kickoff,p.additional_absorption_delta_vs_hold,
        p.future_window_revenue_delta_vs_hold,p.requires_human_review,p.auto_price_change_allowed,
        p.pricing_recommendation_version,p.assumption_set_version
    from active_events e
    join decisions d on d.event_id=e.id
    left join pricing p on p.event_id=e.id and p.sector=d.sector;

    get diagnostics v_detail_count = row_count;

    insert into public.dashboard_sector_summary_current_v1(
        ticket_event_id,home_team,away_team,competition,kickoff_at,as_of_at,hours_to_kickoff,
        sector_count,underperforming_count,on_track_count,outperforming_count,insufficient_signal_count,
        projected_sector_count,projection_coverage_ratio,projected_known_public_availability_at_kickoff,
        top_underperforming_sector,top_underperforming_gap_available,top_underperforming_projected_available,
        price_data_status,pricing_recommendation_status,decision_version,refreshed_at,
        priced_sector_count,pricing_actionable_count,pricing_decrease_count,pricing_hold_count,
        pricing_increase_count,pricing_monitor_count,top_pricing_sector,top_pricing_action,
        top_pricing_current_price,top_pricing_recommended_price,top_pricing_change_pct,pricing_maturity_label
    )
    select
        r.ticket_event_id,
        max(r.home_team),max(r.away_team),max(r.competition),max(r.kickoff_at),max(r.as_of_at),max(r.hours_to_kickoff),
        count(*)::integer,
        count(*) filter(where r.sector_status='UNDERPERFORMING')::integer,
        count(*) filter(where r.sector_status='ON_TRACK')::integer,
        count(*) filter(where r.sector_status='OUTPERFORMING')::integer,
        count(*) filter(where r.sector_status='INSUFFICIENT_SIGNAL')::integer,
        count(*) filter(where r.projected_public_availability_at_kickoff is not null)::integer,
        round(count(*) filter(where r.projected_public_availability_at_kickoff is not null)::numeric/nullif(count(*),0),6),
        round(sum(r.projected_public_availability_at_kickoff) filter(where r.projected_public_availability_at_kickoff is not null),2),
        top_under.sector,top_under.sector_gap_available,top_under.projected_public_availability_at_kickoff,
        case
            when count(*) filter(where r.price_data_status='READY')=count(*) then 'READY'
            when count(*) filter(where r.price_data_status='READY')>0 then 'PARTIAL_PRICE_DATA'
            else 'PRICE_DATA_MISSING'
        end,
        case
            when count(*) filter(where r.pricing_recommendation_action in ('DECREASE','INCREASE'))>0 then 'ACTIONABLE_SCENARIOS'
            when count(*) filter(where r.pricing_recommendation_action='HOLD')>0 then 'HOLD_OR_MONITOR'
            when count(*) filter(where r.pricing_recommendation_action='MONITOR')>0 then 'MONITOR'
            else 'PENDING_PRICE_DATA'
        end,
        max(r.decision_version),now(),
        count(*) filter(where r.current_price is not null)::integer,
        count(*) filter(where r.pricing_recommendation_action in ('DECREASE','INCREASE'))::integer,
        count(*) filter(where r.pricing_recommendation_action='DECREASE')::integer,
        count(*) filter(where r.pricing_recommendation_action='HOLD')::integer,
        count(*) filter(where r.pricing_recommendation_action='INCREASE')::integer,
        count(*) filter(where r.pricing_recommendation_action='MONITOR')::integer,
        top_price.sector,top_price.pricing_recommendation_action,top_price.current_price,
        top_price.recommended_price,top_price.recommended_price_change_pct,
        max(r.pricing_maturity_label) filter(where r.pricing_maturity_label is not null)
    from public.dashboard_sector_decision_current_v1 r
    left join lateral (
        select u.sector,u.sector_gap_available,u.projected_public_availability_at_kickoff
        from public.dashboard_sector_decision_current_v1 u
        where u.ticket_event_id=r.ticket_event_id and u.sector_status='UNDERPERFORMING'
        order by u.sector_gap_available desc nulls last,u.sector
        limit 1
    ) top_under on true
    left join lateral (
        select u.sector,u.pricing_recommendation_action,u.current_price,u.recommended_price,u.recommended_price_change_pct
        from public.dashboard_sector_decision_current_v1 u
        where u.ticket_event_id=r.ticket_event_id
          and u.pricing_recommendation_action in ('DECREASE','INCREASE')
        order by
            case u.pricing_recommendation_action when 'DECREASE' then 1 else 2 end,
            abs(coalesce(u.sector_gap_available,0)) desc,
            u.sector
        limit 1
    ) top_price on true
    group by r.ticket_event_id,
             top_under.sector,top_under.sector_gap_available,top_under.projected_public_availability_at_kickoff,
             top_price.sector,top_price.pricing_recommendation_action,top_price.current_price,
             top_price.recommended_price,top_price.recommended_price_change_pct;

    get diagnostics v_summary_count = row_count;

    return jsonb_build_object(
        'version','e0-dashboard-cache-v1-pricing',
        'detail_rows',v_detail_count,
        'summary_rows',v_summary_count,
        'priced_events',(select count(distinct ticket_event_id) from public.dashboard_sector_decision_current_v1 where current_price is not null),
        'actionable_pricing_rows',(select count(*) from public.dashboard_sector_decision_current_v1 where pricing_recommendation_action in ('DECREASE','INCREASE')),
        'refreshed_at',now()
    );
end;
$function$;

comment on table public.dashboard_sector_decision_current_v1 is
'RLS-safe current E0 sector decision + guarded assumption-based pricing recommendation cache. Public inventory is not paid sales; auto price changes are disabled.';
