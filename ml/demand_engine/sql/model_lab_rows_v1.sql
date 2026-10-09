-- Beyond Model Lab v1 — row-level strict canonical-horizon selections
--
-- Used to audit exactly which forecast row enters each model/event/horizon score.
-- Canonical horizon is derived from hours_to_kickoff; legacy stored horizon labels
-- are deliberately ignored.

create or replace function public.get_model_lab_rows_v1()
returns table(
    forecast_observation_id bigint,
    ticket_event_id bigint,
    home_team text,
    away_team text,
    kickoff_at timestamptz,
    model_version text,
    forecast_mode text,
    horizon text,
    forecast_generated_at timestamptz,
    hours_to_kickoff double precision,
    source_snapshot_id bigint,
    historical_model text,
    historical_p10 integer,
    historical_p50 integer,
    historical_p90 integer,
    live_adjustment integer,
    final_p10 integer,
    final_p50 integer,
    final_p90 integer,
    actual_attendance integer,
    historical_absolute_error integer,
    final_absolute_error integer,
    final_ape_pct numeric,
    live_uplift_absolute_error integer,
    interval_covered boolean,
    live_available_index double precision,
    live_velocity_6h double precision,
    live_velocity_24h double precision,
    live_acceleration_6h_vs_24h double precision,
    signal_readiness text
)
language sql
stable
security invoker
set search_path = public
as $$
with horizons(label,target_hours,tolerance_hours,ord) as (
    values
        ('T-30'::text, 720.0::double precision, 240.0::double precision, 1),
        ('T-14', 336.0, 96.0, 2),
        ('T-7', 168.0, 48.0, 3),
        ('T-3', 72.0, 24.0, 4),
        ('T-24h', 24.0, 12.0, 5)
),
eligible as (
    select
        fo.*,
        te.home_team,
        te.away_team,
        te.kickoff_at,
        o.actual_attendance,
        h.label as canonical_horizon,
        h.target_hours,
        h.ord,
        case when fo.forecast_status = 'shadow' then 'shadow' else 'production' end as forecast_mode
    from public.forecast_observations fo
    join public.ticket_events te on te.id = fo.ticket_event_id
    join public.ticket_event_outcomes o on o.ticket_event_id = fo.ticket_event_id
    cross join horizons h
    where o.actual_attendance is not null
      and fo.final_p50 is not null
      and fo.hours_to_kickoff is not null
      and fo.hours_to_kickoff >= h.target_hours
      and fo.hours_to_kickoff <= h.target_hours + h.tolerance_hours
),
ranked as (
    select
        e.*,
        row_number() over (
            partition by e.model_version, e.ticket_event_id, e.canonical_horizon, e.forecast_mode
            order by
                (e.hours_to_kickoff - e.target_hours) asc,
                e.forecast_generated_at desc,
                e.id desc
        ) as rn
    from eligible e
)
select
    id as forecast_observation_id,
    ticket_event_id,
    home_team,
    away_team,
    kickoff_at,
    model_version,
    forecast_mode,
    canonical_horizon as horizon,
    forecast_generated_at,
    hours_to_kickoff,
    source_snapshot_id,
    historical_model,
    historical_p10,
    historical_p50,
    historical_p90,
    live_adjustment,
    final_p10,
    final_p50,
    final_p90,
    actual_attendance,
    case when historical_p50 is not null then abs(historical_p50 - actual_attendance)::integer end,
    abs(final_p50 - actual_attendance)::integer,
    round(abs(final_p50::numeric - actual_attendance::numeric)
        / nullif(actual_attendance::numeric, 0) * 100.0, 3),
    case when historical_p50 is not null
        then (abs(historical_p50 - actual_attendance) - abs(final_p50 - actual_attendance))::integer
    end,
    case when final_p10 is not null and final_p90 is not null
        then actual_attendance between final_p10 and final_p90
    end,
    live_available_index,
    live_velocity_6h,
    live_velocity_24h,
    live_acceleration_6h_vs_24h,
    signal_readiness
from ranked
where rn = 1
order by ord, kickoff_at, forecast_mode, model_version;
$$;

-- Production permissions:
-- revoke all on function public.get_model_lab_rows_v1()
--   from public, anon, authenticated;
-- grant execute on function public.get_model_lab_rows_v1()
--   to service_role;
