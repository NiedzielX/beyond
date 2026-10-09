-- Beyond Demand Engine v1 — Python shadow forecast persistence RPC
--
-- This function is the only write path used by the Python Demand Engine runner.
-- It intentionally accepts shadow observations only and allocates the legacy
-- forecast_observations id from the existing sequence server-side.

create or replace function public.insert_demand_engine_shadow_forecast_v1(
  p_observation jsonb
)
returns bigint
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_id bigint;
  v_ticket_event_id bigint;
  v_source_snapshot_id bigint;
  v_forecast_generated_at timestamptz;
  v_source_snapshot_captured_at timestamptz;
  v_model_version text;
  v_forecast_status text;
begin
  if p_observation is null then
    raise exception 'p_observation is required';
  end if;

  v_ticket_event_id := nullif(p_observation->>'ticket_event_id', '')::bigint;
  v_source_snapshot_id := nullif(p_observation->>'source_snapshot_id', '')::bigint;
  v_forecast_generated_at := nullif(p_observation->>'forecast_generated_at', '')::timestamptz;
  v_source_snapshot_captured_at := nullif(p_observation->>'source_snapshot_captured_at', '')::timestamptz;
  v_model_version := nullif(p_observation->>'model_version', '');
  v_forecast_status := coalesce(nullif(p_observation->>'forecast_status', ''), 'shadow');

  if v_ticket_event_id is null then
    raise exception 'ticket_event_id is required';
  end if;
  if v_source_snapshot_id is null then
    raise exception 'source_snapshot_id is required';
  end if;
  if v_forecast_generated_at is null then
    raise exception 'forecast_generated_at is required';
  end if;
  if v_source_snapshot_captured_at is null then
    raise exception 'source_snapshot_captured_at is required';
  end if;
  if v_model_version is null then
    raise exception 'model_version is required';
  end if;
  if v_forecast_status <> 'shadow' then
    raise exception 'Python Demand Engine writer accepts shadow forecasts only';
  end if;
  if not exists (
    select 1 from public.ticket_events te where te.id = v_ticket_event_id
  ) then
    raise exception 'ticket_event_id % does not exist', v_ticket_event_id;
  end if;
  if not exists (
    select 1
    from public.snapshots s
    where s.id = v_source_snapshot_id
      and s.ticket_event_id = v_ticket_event_id
  ) then
    raise exception 'source_snapshot_id % does not belong to ticket_event_id %',
      v_source_snapshot_id, v_ticket_event_id;
  end if;

  -- Idempotency for a scheduled/checkpoint runner: an identical model/event/
  -- source-snapshot/checkpoint cannot be inserted twice.
  select fo.id
  into v_id
  from public.forecast_observations fo
  where fo.ticket_event_id = v_ticket_event_id
    and fo.source_snapshot_id = v_source_snapshot_id
    and fo.model_version = v_model_version
    and fo.forecast_status = 'shadow'
    and fo.forecast_generated_at = v_forecast_generated_at
  order by fo.id desc
  limit 1;

  if found then
    return v_id;
  end if;

  v_id := nextval('public.forecast_observations_id_seq');

  insert into public.forecast_observations (
    id,
    ticket_event_id,
    source_snapshot_id,
    forecast_generated_at,
    source_snapshot_captured_at,
    hours_to_kickoff,
    days_to_match,
    horizon,
    model_version,
    historical_model,
    historical_p10,
    historical_p50,
    historical_p90,
    live_adjustment,
    final_p10,
    final_p50,
    final_p90,
    forecast_status,
    correction_status,
    signal_readiness,
    live_available_total,
    live_first_available_total,
    live_available_index,
    live_net_removed_since_first,
    live_net_removed_since_previous,
    live_velocity_since_previous,
    live_net_removed_6h,
    live_velocity_6h,
    live_net_removed_24h,
    live_velocity_24h,
    live_acceleration_6h_vs_24h,
    live_raw_snapshot_count,
    live_clean_snapshot_count,
    live_excluded_anomaly_count,
    payload
  ) values (
    v_id,
    v_ticket_event_id,
    v_source_snapshot_id,
    v_forecast_generated_at,
    v_source_snapshot_captured_at,
    nullif(p_observation->>'hours_to_kickoff', '')::double precision,
    nullif(p_observation->>'days_to_match', '')::double precision,
    nullif(p_observation->>'horizon', ''),
    v_model_version,
    nullif(p_observation->>'historical_model', ''),
    nullif(p_observation->>'historical_p10', '')::integer,
    nullif(p_observation->>'historical_p50', '')::integer,
    nullif(p_observation->>'historical_p90', '')::integer,
    coalesce(nullif(p_observation->>'live_adjustment', '')::integer, 0),
    nullif(p_observation->>'final_p10', '')::integer,
    nullif(p_observation->>'final_p50', '')::integer,
    nullif(p_observation->>'final_p90', '')::integer,
    v_forecast_status,
    coalesce(nullif(p_observation->>'correction_status', ''), 'shadow'),
    nullif(p_observation->>'signal_readiness', ''),
    nullif(p_observation->>'live_available_total', '')::integer,
    nullif(p_observation->>'live_first_available_total', '')::integer,
    nullif(p_observation->>'live_available_index', '')::double precision,
    nullif(p_observation->>'live_net_removed_since_first', '')::integer,
    nullif(p_observation->>'live_net_removed_since_previous', '')::integer,
    nullif(p_observation->>'live_velocity_since_previous', '')::double precision,
    nullif(p_observation->>'live_net_removed_6h', '')::integer,
    nullif(p_observation->>'live_velocity_6h', '')::double precision,
    nullif(p_observation->>'live_net_removed_24h', '')::integer,
    nullif(p_observation->>'live_velocity_24h', '')::double precision,
    nullif(p_observation->>'live_acceleration_6h_vs_24h', '')::double precision,
    nullif(p_observation->>'live_raw_snapshot_count', '')::integer,
    nullif(p_observation->>'live_clean_snapshot_count', '')::integer,
    nullif(p_observation->>'live_excluded_anomaly_count', '')::integer,
    coalesce(p_observation->'payload', '{}'::jsonb)
  );

  return v_id;
end;
$$;

revoke all on function public.insert_demand_engine_shadow_forecast_v1(jsonb)
  from public, anon, authenticated;
grant execute on function public.insert_demand_engine_shadow_forecast_v1(jsonb)
  to service_role;
