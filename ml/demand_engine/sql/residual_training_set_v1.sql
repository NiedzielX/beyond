-- Beyond Demand Engine v1 — residual/live-correction training set
--
-- Target:
--   target_residual = actual_attendance - historical_p50
--
-- CRITICAL NO-LEAKAGE RULE:
-- Multiple snapshots belong to the same match. Any train/validation/test split
-- MUST group by group_ticket_event_id. Never split individual rows randomly.

create or replace function public.get_demand_engine_v1_residual_training_set()
returns table (
  training_row_id bigint,
  group_ticket_event_id bigint,
  club_slug text,
  home_team text,
  away_team text,
  competition text,
  kickoff_at timestamptz,
  forecast_generated_at timestamptz,
  source_snapshot_id bigint,
  source_snapshot_captured_at timestamptz,
  hours_to_kickoff double precision,
  days_to_match double precision,
  horizon text,
  historical_model text,
  historical_p50 integer,
  actual_attendance integer,
  target_residual integer,
  target_residual_pct numeric,
  live_available_total integer,
  live_first_available_total integer,
  live_available_index double precision,
  live_net_removed_since_first integer,
  live_net_removed_since_previous integer,
  live_velocity_since_previous double precision,
  live_net_removed_6h integer,
  live_velocity_6h double precision,
  live_net_removed_24h integer,
  live_velocity_24h double precision,
  live_acceleration_6h_vs_24h double precision,
  live_raw_snapshot_count integer,
  signal_readiness text,
  sector_coverage_change_flag boolean,
  release_activity_flag boolean,
  entered_sector_count integer,
  left_sector_count integer,
  coverage_inventory_effect integer
)
language sql
stable
security invoker
set search_path = public
as $$
select
  fo.id,
  fo.ticket_event_id,
  te.club_slug,
  te.home_team,
  te.away_team,
  te.competition,
  te.kickoff_at,
  fo.forecast_generated_at,
  fo.source_snapshot_id,
  fo.source_snapshot_captured_at,
  fo.hours_to_kickoff,
  fo.days_to_match,
  fo.horizon,
  fo.historical_model,
  fo.historical_p50,
  o.actual_attendance,
  (o.actual_attendance - fo.historical_p50)::integer,
  round(((o.actual_attendance::numeric - fo.historical_p50::numeric) / nullif(o.actual_attendance::numeric, 0)) * 100, 4),
  fo.live_available_total,
  fo.live_first_available_total,
  fo.live_available_index,
  fo.live_net_removed_since_first,
  fo.live_net_removed_since_previous,
  fo.live_velocity_since_previous,
  fo.live_net_removed_6h,
  fo.live_velocity_6h,
  fo.live_net_removed_24h,
  fo.live_velocity_24h,
  fo.live_acceleration_6h_vs_24h,
  fo.live_raw_snapshot_count,
  fo.signal_readiness,
  coalesce((fo.payload->'live'->>'sector_coverage_change_flag')::boolean, false),
  coalesce((fo.payload->'live'->>'release_activity_flag')::boolean, false),
  nullif(fo.payload->'live'->>'entered_sector_count','')::integer,
  nullif(fo.payload->'live'->>'left_sector_count','')::integer,
  nullif(fo.payload->'live'->>'coverage_inventory_effect','')::integer
from public.forecast_observations fo
join public.ticket_events te on te.id = fo.ticket_event_id
join public.ticket_event_outcomes o on o.ticket_event_id = fo.ticket_event_id
where fo.model_version = 'beyond-demand-engine-v1-shadow'
  and fo.forecast_status = 'shadow'
  and fo.historical_p50 is not null
  and o.actual_attendance is not null
  and fo.source_snapshot_captured_at <= te.kickoff_at
order by fo.ticket_event_id, fo.forecast_generated_at, fo.id;
$$;
