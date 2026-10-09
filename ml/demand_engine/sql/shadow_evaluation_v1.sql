-- Beyond Demand Engine v1 — shadow evaluation
--
-- Positive live_uplift_* means the final forecast is closer to actual attendance
-- than the historical baseline. Negative means the live layer made it worse.
-- Current no-op shadow runs should therefore produce exactly zero uplift once
-- outcomes become available.

create or replace function public.get_demand_engine_v1_shadow_evaluation()
returns table (
  forecast_observation_id bigint,
  ticket_event_id bigint,
  home_team text,
  away_team text,
  kickoff_at timestamptz,
  forecast_generated_at timestamptz,
  horizon text,
  historical_model text,
  historical_p50 integer,
  final_p50 integer,
  actual_attendance integer,
  historical_error integer,
  final_error integer,
  historical_absolute_error integer,
  final_absolute_error integer,
  live_uplift_absolute_error integer,
  historical_ape_pct numeric,
  final_ape_pct numeric,
  live_uplift_ape_pp numeric,
  live_adjustment integer,
  signal_readiness text,
  live_available_index double precision,
  live_velocity_6h double precision,
  live_velocity_24h double precision,
  live_acceleration_6h_vs_24h double precision
)
language sql
stable
security invoker
set search_path = public
as $$
select
  fo.id,
  fo.ticket_event_id,
  te.home_team,
  te.away_team,
  te.kickoff_at,
  fo.forecast_generated_at,
  fo.horizon,
  fo.historical_model,
  fo.historical_p50,
  fo.final_p50,
  o.actual_attendance,
  (fo.historical_p50 - o.actual_attendance)::integer,
  (fo.final_p50 - o.actual_attendance)::integer,
  abs(fo.historical_p50 - o.actual_attendance)::integer,
  abs(fo.final_p50 - o.actual_attendance)::integer,
  (abs(fo.historical_p50 - o.actual_attendance) - abs(fo.final_p50 - o.actual_attendance))::integer,
  round((abs(fo.historical_p50::numeric - o.actual_attendance::numeric) / nullif(o.actual_attendance::numeric, 0)) * 100, 3),
  round((abs(fo.final_p50::numeric - o.actual_attendance::numeric) / nullif(o.actual_attendance::numeric, 0)) * 100, 3),
  round(
    ((abs(fo.historical_p50::numeric - o.actual_attendance::numeric) - abs(fo.final_p50::numeric - o.actual_attendance::numeric))
      / nullif(o.actual_attendance::numeric, 0)) * 100,
    3
  ),
  fo.live_adjustment,
  fo.signal_readiness,
  fo.live_available_index,
  fo.live_velocity_6h,
  fo.live_velocity_24h,
  fo.live_acceleration_6h_vs_24h
from public.forecast_observations fo
join public.ticket_events te on te.id = fo.ticket_event_id
join public.ticket_event_outcomes o on o.ticket_event_id = fo.ticket_event_id
where fo.model_version = 'beyond-demand-engine-v1-shadow'
  and fo.forecast_status = 'shadow'
  and fo.historical_p50 is not null
  and fo.final_p50 is not null
  and o.actual_attendance is not null
order by fo.forecast_generated_at, fo.id;
$$;
