-- Beyond Ticketing — Price-area Dashboard Cache v1
--
-- RLS-safe current cache for detailed price-area pricing recommendations.
-- The heavy pricing function remains service-role only; browser clients read
-- only this sanitized cache.

create table if not exists public.dashboard_price_area_pricing_current_v1 (
    ticket_event_id bigint not null,
    sector text not null,
    sector_name text,
    sector_status text not null,
    trend_state text not null,
    hours_to_kickoff numeric not null,
    sector_gap_ratio numeric,
    projection_confidence text not null,
    price_area_id integer not null,
    price_area_name text,
    price_type_name text,
    current_price numeric,
    currency text,
    current_public_availability integer not null,
    availability_share_of_sector numeric,
    baseline_projected_public_availability_at_kickoff numeric,
    baseline_additional_absorption_proxy numeric,
    minimum_actionable_absorption numeric,
    recommended_action text not null,
    recommended_price_change_pct numeric,
    recommended_price numeric,
    recommended_projected_public_availability_at_kickoff numeric,
    recommended_projected_additional_absorption numeric,
    additional_absorption_delta_vs_hold numeric,
    scenario_confidence text not null,
    recommendation_reason_code text not null,
    price_data_status text not null,
    requires_human_review boolean not null,
    auto_price_change_allowed boolean not null,
    maturity_label text not null,
    price_area_recommendation_version text not null,
    recommendation_policy_version text not null,
    assumption_set_version text not null,
    price_area_observed_at timestamptz,
    price_observed_at timestamptz,
    point_in_time_validated boolean not null,
    refreshed_at timestamptz not null default now(),
    primary key(ticket_event_id,sector,price_area_id)
);

create index if not exists dashboard_price_area_pricing_event_sector_idx
    on public.dashboard_price_area_pricing_current_v1(ticket_event_id,sector,recommended_action);

alter table public.dashboard_price_area_pricing_current_v1 enable row level security;

drop policy if exists dashboard_price_area_pricing_public_read_v1
    on public.dashboard_price_area_pricing_current_v1;
create policy dashboard_price_area_pricing_public_read_v1
on public.dashboard_price_area_pricing_current_v1
for select
to anon,authenticated
using (true);

revoke all on public.dashboard_price_area_pricing_current_v1 from public,anon,authenticated;
grant select on public.dashboard_price_area_pricing_current_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_price_area_pricing_current_v1 to service_role;

create or replace function public.refresh_dashboard_price_area_pricing_v1()
returns jsonb
language plpgsql
security invoker
set search_path = public
as $function$
declare
    v_row_count integer := 0;
begin
    delete from public.dashboard_price_area_pricing_current_v1;

    insert into public.dashboard_price_area_pricing_current_v1(
        ticket_event_id,sector,sector_name,sector_status,trend_state,hours_to_kickoff,sector_gap_ratio,
        projection_confidence,price_area_id,price_area_name,price_type_name,current_price,currency,
        current_public_availability,availability_share_of_sector,
        baseline_projected_public_availability_at_kickoff,baseline_additional_absorption_proxy,
        minimum_actionable_absorption,recommended_action,recommended_price_change_pct,recommended_price,
        recommended_projected_public_availability_at_kickoff,recommended_projected_additional_absorption,
        additional_absorption_delta_vs_hold,scenario_confidence,recommendation_reason_code,price_data_status,
        requires_human_review,auto_price_change_allowed,maturity_label,price_area_recommendation_version,
        recommendation_policy_version,assumption_set_version,price_area_observed_at,price_observed_at,
        point_in_time_validated,refreshed_at
    )
    select
        p.ticket_event_id,p.sector,p.sector_name,p.sector_status,p.trend_state,p.hours_to_kickoff,p.sector_gap_ratio,
        p.projection_confidence,p.price_area_id,p.price_area_name,p.price_type_name,p.current_price,p.currency,
        p.current_public_availability,p.availability_share_of_sector,
        p.baseline_projected_public_availability_at_kickoff,p.baseline_additional_absorption_proxy,
        p.minimum_actionable_absorption,p.recommended_action,p.recommended_price_change_pct,p.recommended_price,
        p.recommended_projected_public_availability_at_kickoff,p.recommended_projected_additional_absorption,
        p.additional_absorption_delta_vs_hold,p.scenario_confidence,p.recommendation_reason_code,p.price_data_status,
        p.requires_human_review,p.auto_price_change_allowed,p.maturity_label,p.price_area_recommendation_version,
        p.recommendation_policy_version,p.assumption_set_version,p.price_area_observed_at,p.price_observed_at,
        p.point_in_time_validated,now()
    from public.ticket_events e
    cross join lateral public.get_price_area_pricing_recommendation_v1_asof(e.id,now()) p
    where e.kickoff_at>now()
      and exists(
          select 1
          from public.sector_price_area_observations_v1 o
          where o.ticket_event_id=e.id
      );

    get diagnostics v_row_count = row_count;

    return jsonb_build_object(
        'version','price-area-dashboard-cache-v1',
        'rows',v_row_count,
        'events',(select count(distinct ticket_event_id) from public.dashboard_price_area_pricing_current_v1),
        'actionable_rows',(select count(*) from public.dashboard_price_area_pricing_current_v1 where recommended_action in ('DECREASE','INCREASE')),
        'hold_rows',(select count(*) from public.dashboard_price_area_pricing_current_v1 where recommended_action='HOLD'),
        'monitor_rows',(select count(*) from public.dashboard_price_area_pricing_current_v1 where recommended_action='MONITOR'),
        'refreshed_at',now()
    );
end;
$function$;

revoke all on function public.refresh_dashboard_price_area_pricing_v1() from public,anon,authenticated;
grant execute on function public.refresh_dashboard_price_area_pricing_v1() to service_role;

select cron.schedule(
    'e0-price-area-dashboard-v1',
    '13,28,43,58 * * * *',
    'select public.refresh_dashboard_price_area_pricing_v1();'
);

comment on table public.dashboard_price_area_pricing_current_v1 is
'RLS-safe current E0 Roboticket price-area pricing recommendations. Assumption-based decision support only; human review required; automatic price changes disabled.';
