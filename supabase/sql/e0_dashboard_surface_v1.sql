-- Beyond Ticketing — E0 Dashboard Surface v1
--
-- Sanitized read-only RPC surface for BeyondTicketingPanel.
-- Internal helpers stay in the non-exposed private schema.
-- Public wrappers are SECURITY INVOKER and expose only decision-support fields.

create or replace function private.get_dashboard_sector_decision_v1(
    p_ticket_event_id bigint
)
returns table (
    ticket_event_id bigint,
    home_team text,
    away_team text,
    competition text,
    kickoff_at timestamptz,
    sector text,
    as_of_at timestamptz,
    hours_to_kickoff numeric,
    current_public_availability integer,
    reference_public_availability integer,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    sector_status text,
    status_reason_code text,
    trend_state text,
    projected_public_availability_at_kickoff numeric,
    projected_public_sell_through_proxy numeric,
    projection_confidence text,
    projection_reason_code text,
    price_data_status text,
    current_price numeric,
    currency text,
    pricing_recommendation_status text,
    data_quality_status text,
    decision_version text,
    status_policy_version text,
    projection_policy_version text
)
language sql
stable
security definer
set search_path = public, private
as $function$
select
    e.id,
    e.home_team,
    e.away_team,
    e.competition,
    e.kickoff_at,
    d.sector,
    d.as_of_at,
    d.hours_to_kickoff,
    d.current_available,
    d.reference_available,
    round((d.sector_gap_ratio*d.reference_available)::numeric,2) as sector_gap_available,
    d.sector_gap_ratio,
    d.sector_status,
    d.status_reason_code,
    d.trend_state,
    d.projected_public_availability_at_kickoff,
    d.projected_public_sell_through_proxy,
    d.projection_confidence,
    d.projection_reason_code,
    'PRICE_DATA_MISSING'::text,
    null::numeric,
    null::text,
    'PENDING_PRICE_DATA'::text,
    case
        when d.sector_status='INSUFFICIENT_SIGNAL' then 'ATTENTION_REQUIRED'
        when d.projection_confidence='INSUFFICIENT' then 'ATTENTION_REQUIRED'
        else 'OK'
    end::text,
    d.decision_version,
    d.status_policy_version,
    d.projection_policy_version
from public.ticket_events e
cross join lateral public.get_sector_decision_v1_asof(e.id,now()) d
where e.id=p_ticket_event_id
order by
    case d.sector_status
        when 'UNDERPERFORMING' then 1
        when 'INSUFFICIENT_SIGNAL' then 2
        when 'ON_TRACK' then 3
        when 'OUTPERFORMING' then 4
        else 5
    end,
    d.sector_gap_ratio desc nulls last,
    d.sector;
$function$;

revoke all on function private.get_dashboard_sector_decision_v1(bigint) from public;
grant execute on function private.get_dashboard_sector_decision_v1(bigint) to anon,authenticated,service_role;

create or replace function public.get_dashboard_sector_decision_v1(
    p_ticket_event_id bigint
)
returns table (
    ticket_event_id bigint,
    home_team text,
    away_team text,
    competition text,
    kickoff_at timestamptz,
    sector text,
    as_of_at timestamptz,
    hours_to_kickoff numeric,
    current_public_availability integer,
    reference_public_availability integer,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    sector_status text,
    status_reason_code text,
    trend_state text,
    projected_public_availability_at_kickoff numeric,
    projected_public_sell_through_proxy numeric,
    projection_confidence text,
    projection_reason_code text,
    price_data_status text,
    current_price numeric,
    currency text,
    pricing_recommendation_status text,
    data_quality_status text,
    decision_version text,
    status_policy_version text,
    projection_policy_version text
)
language sql
stable
security invoker
set search_path = public, private
as $function$
select * from private.get_dashboard_sector_decision_v1(p_ticket_event_id);
$function$;

revoke all on function public.get_dashboard_sector_decision_v1(bigint) from public;
grant execute on function public.get_dashboard_sector_decision_v1(bigint) to anon,authenticated,service_role;

create or replace function private.get_dashboard_sector_summary_v1(
    p_ticket_event_id bigint
)
returns table (
    ticket_event_id bigint,
    home_team text,
    away_team text,
    competition text,
    kickoff_at timestamptz,
    as_of_at timestamptz,
    hours_to_kickoff numeric,
    sector_count integer,
    underperforming_count integer,
    on_track_count integer,
    outperforming_count integer,
    insufficient_signal_count integer,
    projected_sector_count integer,
    projection_coverage_ratio numeric,
    projected_known_public_availability_at_kickoff numeric,
    top_underperforming_sector text,
    top_underperforming_gap_available numeric,
    top_underperforming_projected_available numeric,
    price_data_status text,
    pricing_recommendation_status text,
    decision_version text
)
language sql
stable
security definer
set search_path = public, private
as $function$
with rows as (
    select * from private.get_dashboard_sector_decision_v1(p_ticket_event_id)
), ranked_under as (
    select
        sector,
        sector_gap_available,
        projected_public_availability_at_kickoff,
        row_number() over (
            order by sector_gap_available desc nulls last,sector
        ) as rn
    from rows
    where sector_status='UNDERPERFORMING'
), agg as (
    select
        max(ticket_event_id) as ticket_event_id,
        max(home_team) as home_team,
        max(away_team) as away_team,
        max(competition) as competition,
        max(kickoff_at) as kickoff_at,
        max(as_of_at) as as_of_at,
        max(hours_to_kickoff) as hours_to_kickoff,
        count(*)::integer as sector_count,
        count(*) filter(where sector_status='UNDERPERFORMING')::integer as underperforming_count,
        count(*) filter(where sector_status='ON_TRACK')::integer as on_track_count,
        count(*) filter(where sector_status='OUTPERFORMING')::integer as outperforming_count,
        count(*) filter(where sector_status='INSUFFICIENT_SIGNAL')::integer as insufficient_signal_count,
        count(*) filter(where projected_public_availability_at_kickoff is not null)::integer as projected_sector_count,
        sum(projected_public_availability_at_kickoff) filter(where projected_public_availability_at_kickoff is not null) as projected_known_public_availability,
        max(decision_version) as decision_version
    from rows
)
select
    a.ticket_event_id,
    a.home_team,
    a.away_team,
    a.competition,
    a.kickoff_at,
    a.as_of_at,
    a.hours_to_kickoff,
    a.sector_count,
    a.underperforming_count,
    a.on_track_count,
    a.outperforming_count,
    a.insufficient_signal_count,
    a.projected_sector_count,
    case when a.sector_count>0
         then round(a.projected_sector_count::numeric/a.sector_count,6) end,
    round(a.projected_known_public_availability,2),
    u.sector,
    u.sector_gap_available,
    u.projected_public_availability_at_kickoff,
    'PRICE_DATA_MISSING'::text,
    'PENDING_PRICE_DATA'::text,
    a.decision_version
from agg a
left join ranked_under u on u.rn=1
where a.ticket_event_id is not null;
$function$;

revoke all on function private.get_dashboard_sector_summary_v1(bigint) from public;
grant execute on function private.get_dashboard_sector_summary_v1(bigint) to anon,authenticated,service_role;

create or replace function public.get_dashboard_sector_summary_v1(
    p_ticket_event_id bigint
)
returns table (
    ticket_event_id bigint,
    home_team text,
    away_team text,
    competition text,
    kickoff_at timestamptz,
    as_of_at timestamptz,
    hours_to_kickoff numeric,
    sector_count integer,
    underperforming_count integer,
    on_track_count integer,
    outperforming_count integer,
    insufficient_signal_count integer,
    projected_sector_count integer,
    projection_coverage_ratio numeric,
    projected_known_public_availability_at_kickoff numeric,
    top_underperforming_sector text,
    top_underperforming_gap_available numeric,
    top_underperforming_projected_available numeric,
    price_data_status text,
    pricing_recommendation_status text,
    decision_version text
)
language sql
stable
security invoker
set search_path = public, private
as $function$
select * from private.get_dashboard_sector_summary_v1(p_ticket_event_id);
$function$;

revoke all on function public.get_dashboard_sector_summary_v1(bigint) from public;
grant execute on function public.get_dashboard_sector_summary_v1(bigint) to anon,authenticated,service_role;

comment on function public.get_dashboard_sector_decision_v1(bigint) is
'Sanitized E0 event-sector decision surface for BeyondTicketingPanel. Read-only; price fields remain explicitly missing until a real price source is connected.';
comment on function public.get_dashboard_sector_summary_v1(bigint) is
'Sanitized E0 event-level sector summary for BeyondTicketingPanel. Projected known public availability is not attendance and may have incomplete sector coverage.';
