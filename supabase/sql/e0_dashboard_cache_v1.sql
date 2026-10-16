-- Beyond Ticketing — E0 Dashboard Cache v1
--
-- Materializes sanitized sector decisions into small public RLS-protected
-- tables for fast dashboard reads. Heavy trajectory logic remains service-only.

create table if not exists public.dashboard_sector_decision_current_v1 (
    ticket_event_id bigint not null,
    home_team text not null,
    away_team text not null,
    competition text,
    kickoff_at timestamptz not null,
    sector text not null,
    as_of_at timestamptz not null,
    hours_to_kickoff numeric not null,
    current_public_availability integer not null,
    reference_public_availability integer not null,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    sector_status text not null,
    status_reason_code text not null,
    trend_state text not null,
    projected_public_availability_at_kickoff numeric,
    projected_public_sell_through_proxy numeric,
    projection_confidence text not null,
    projection_reason_code text not null,
    price_data_status text not null,
    current_price numeric,
    currency text,
    pricing_recommendation_status text not null,
    data_quality_status text not null,
    decision_version text not null,
    status_policy_version text not null,
    projection_policy_version text not null,
    refreshed_at timestamptz not null default now(),
    primary key(ticket_event_id,sector)
);

create index if not exists dashboard_sector_decision_status_idx
    on public.dashboard_sector_decision_current_v1(ticket_event_id,sector_status,sector_gap_available desc);

alter table public.dashboard_sector_decision_current_v1 enable row level security;

drop policy if exists dashboard_sector_decision_public_read_v1 on public.dashboard_sector_decision_current_v1;
create policy dashboard_sector_decision_public_read_v1
on public.dashboard_sector_decision_current_v1
for select
to anon,authenticated
using (true);

revoke all on public.dashboard_sector_decision_current_v1 from public,anon,authenticated;
grant select on public.dashboard_sector_decision_current_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_sector_decision_current_v1 to service_role;

create table if not exists public.dashboard_sector_summary_current_v1 (
    ticket_event_id bigint primary key,
    home_team text not null,
    away_team text not null,
    competition text,
    kickoff_at timestamptz not null,
    as_of_at timestamptz not null,
    hours_to_kickoff numeric not null,
    sector_count integer not null,
    underperforming_count integer not null,
    on_track_count integer not null,
    outperforming_count integer not null,
    insufficient_signal_count integer not null,
    projected_sector_count integer not null,
    projection_coverage_ratio numeric,
    projected_known_public_availability_at_kickoff numeric,
    top_underperforming_sector text,
    top_underperforming_gap_available numeric,
    top_underperforming_projected_available numeric,
    price_data_status text not null,
    pricing_recommendation_status text not null,
    decision_version text not null,
    refreshed_at timestamptz not null default now()
);

alter table public.dashboard_sector_summary_current_v1 enable row level security;

drop policy if exists dashboard_sector_summary_public_read_v1 on public.dashboard_sector_summary_current_v1;
create policy dashboard_sector_summary_public_read_v1
on public.dashboard_sector_summary_current_v1
for select
to anon,authenticated
using (true);

revoke all on public.dashboard_sector_summary_current_v1 from public,anon,authenticated;
grant select on public.dashboard_sector_summary_current_v1 to anon,authenticated;
grant select,insert,update,delete on public.dashboard_sector_summary_current_v1 to service_role;

-- The direct RPC wrappers are not needed by the browser after the cache exists.
-- Keep them for service-side diagnostics only.
revoke all on function public.get_dashboard_sector_decision_v1(bigint) from public,anon,authenticated;
revoke all on function public.get_dashboard_sector_summary_v1(bigint) from public,anon,authenticated;
grant execute on function public.get_dashboard_sector_decision_v1(bigint) to service_role;
grant execute on function public.get_dashboard_sector_summary_v1(bigint) to service_role;
revoke all on function private.get_dashboard_sector_decision_v1(bigint) from public,anon,authenticated;
revoke all on function private.get_dashboard_sector_summary_v1(bigint) from public,anon,authenticated;
grant execute on function private.get_dashboard_sector_decision_v1(bigint) to service_role;
grant execute on function private.get_dashboard_sector_summary_v1(bigint) to service_role;

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

    insert into public.dashboard_sector_decision_current_v1(
        ticket_event_id,home_team,away_team,competition,kickoff_at,sector,as_of_at,hours_to_kickoff,
        current_public_availability,reference_public_availability,sector_gap_available,sector_gap_ratio,
        sector_status,status_reason_code,trend_state,projected_public_availability_at_kickoff,
        projected_public_sell_through_proxy,projection_confidence,projection_reason_code,
        price_data_status,current_price,currency,pricing_recommendation_status,data_quality_status,
        decision_version,status_policy_version,projection_policy_version,refreshed_at
    )
    select
        e.id,e.home_team,e.away_team,e.competition,e.kickoff_at,d.sector,d.as_of_at,d.hours_to_kickoff,
        d.current_available,d.reference_available,
        round((d.sector_gap_ratio*d.reference_available)::numeric,2),d.sector_gap_ratio,
        d.sector_status,d.status_reason_code,d.trend_state,d.projected_public_availability_at_kickoff,
        d.projected_public_sell_through_proxy,d.projection_confidence,d.projection_reason_code,
        'PRICE_DATA_MISSING',null::numeric,null::text,'PENDING_PRICE_DATA',
        case when d.sector_status='INSUFFICIENT_SIGNAL' or d.projection_confidence='INSUFFICIENT'
             then 'ATTENTION_REQUIRED' else 'OK' end,
        d.decision_version,d.status_policy_version,d.projection_policy_version,now()
    from public.ticket_events e
    cross join lateral public.get_sector_decision_v1_asof(e.id,now()) d
    where e.kickoff_at>now()
      and exists(select 1 from public.snapshots s where s.ticket_event_id=e.id);

    get diagnostics v_detail_count = row_count;

    insert into public.dashboard_sector_summary_current_v1(
        ticket_event_id,home_team,away_team,competition,kickoff_at,as_of_at,hours_to_kickoff,
        sector_count,underperforming_count,on_track_count,outperforming_count,insufficient_signal_count,
        projected_sector_count,projection_coverage_ratio,projected_known_public_availability_at_kickoff,
        top_underperforming_sector,top_underperforming_gap_available,top_underperforming_projected_available,
        price_data_status,pricing_recommendation_status,decision_version,refreshed_at
    )
    select
        event_rows.ticket_event_id,
        max(event_rows.home_team),
        max(event_rows.away_team),
        max(event_rows.competition),
        max(event_rows.kickoff_at),
        max(event_rows.as_of_at),
        max(event_rows.hours_to_kickoff),
        count(*)::integer,
        count(*) filter(where event_rows.sector_status='UNDERPERFORMING')::integer,
        count(*) filter(where event_rows.sector_status='ON_TRACK')::integer,
        count(*) filter(where event_rows.sector_status='OUTPERFORMING')::integer,
        count(*) filter(where event_rows.sector_status='INSUFFICIENT_SIGNAL')::integer,
        count(*) filter(where event_rows.projected_public_availability_at_kickoff is not null)::integer,
        round(
            count(*) filter(where event_rows.projected_public_availability_at_kickoff is not null)::numeric
            /nullif(count(*),0),6
        ),
        round(sum(event_rows.projected_public_availability_at_kickoff)
            filter(where event_rows.projected_public_availability_at_kickoff is not null),2),
        top_under.sector,
        top_under.sector_gap_available,
        top_under.projected_public_availability_at_kickoff,
        'PRICE_DATA_MISSING',
        'PENDING_PRICE_DATA',
        max(event_rows.decision_version),
        now()
    from public.dashboard_sector_decision_current_v1 event_rows
    left join lateral (
        select u.sector,u.sector_gap_available,u.projected_public_availability_at_kickoff
        from public.dashboard_sector_decision_current_v1 u
        where u.ticket_event_id=event_rows.ticket_event_id
          and u.sector_status='UNDERPERFORMING'
        order by u.sector_gap_available desc nulls last,u.sector
        limit 1
    ) top_under on true
    group by event_rows.ticket_event_id,top_under.sector,top_under.sector_gap_available,
             top_under.projected_public_availability_at_kickoff;

    get diagnostics v_summary_count = row_count;

    return jsonb_build_object(
        'version','e0-dashboard-cache-v1',
        'detail_rows',v_detail_count,
        'summary_rows',v_summary_count,
        'refreshed_at',now(),
        'price_data_status','PRICE_DATA_MISSING'
    );
end;
$function$;

revoke all on function public.refresh_dashboard_sector_decision_v1() from public,anon,authenticated;
grant execute on function public.refresh_dashboard_sector_decision_v1() to service_role;

select cron.schedule(
    'e0-sector-dashboard-v1',
    '12,27,42,57 * * * *',
    'select public.refresh_dashboard_sector_decision_v1();'
);

comment on table public.dashboard_sector_decision_current_v1 is
'Sanitized current E0 sector decision cache for dashboard reads. Public availability only; not paid sales.';
comment on table public.dashboard_sector_summary_current_v1 is
'Sanitized current E0 event-level sector summary cache. Projected known public availability is not attendance.';
