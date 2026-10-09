-- Beyond Demand Engine v1 — shadow runner
--
-- Purpose:
-- 1. Reuse the current persisted v0.3 historical forecast as the incumbent.
-- 2. Attach live-features-v1 from get_live_features_v1(ticket_event_id).
-- 3. Persist a new observation with live_adjustment = 0.
-- 4. Mark the observation as forecast_status='shadow' so the production
--    dashboard can exclude it by default.
--
-- The deployed Supabase migration also schedules run_all_demand_engine_v1_shadow()
-- every 6 hours at minute 10. The batch runner skips a match when the latest
-- live snapshot has already been recorded by the shadow engine.

create or replace function public.run_demand_engine_v1_shadow(p_ticket_event_id bigint)
returns table (
  forecast_observation_id bigint,
  ticket_event_id bigint,
  source_snapshot_id bigint,
  model_version text,
  forecast_status text,
  historical_p50 integer,
  live_adjustment integer,
  final_p50 integer,
  signal_readiness text
)
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_event record;
  v_hist record;
  v_live record;
  v_now timestamptz := now();
  v_hours double precision;
  v_horizon text;
  v_id bigint;
begin
  select te.id, te.kickoff_at
  into v_event
  from public.ticket_events te
  where te.id = p_ticket_event_id;

  if not found then
    raise exception 'ticket_event_id % does not exist', p_ticket_event_id;
  end if;

  if v_event.kickoff_at is null then
    raise exception 'ticket_event_id % has no kickoff_at', p_ticket_event_id;
  end if;

  select
    fo.historical_model,
    fo.historical_p10,
    fo.historical_p50,
    fo.historical_p90,
    fo.forecast_generated_at
  into v_hist
  from public.forecast_observations fo
  where fo.ticket_event_id = p_ticket_event_id
    and fo.model_version = 'beyond-forecast-v0.3'
    and fo.historical_p10 is not null
    and fo.historical_p50 is not null
    and fo.historical_p90 is not null
    and coalesce(fo.forecast_status, '') <> 'shadow'
    and fo.forecast_generated_at <= v_now
  order by fo.forecast_generated_at desc, fo.id desc
  limit 1;

  if not found then
    raise exception 'No eligible beyond-forecast-v0.3 historical forecast for ticket_event_id %', p_ticket_event_id;
  end if;

  select *
  into v_live
  from public.get_live_features_v1(p_ticket_event_id);

  if not found then
    raise exception 'No live_features_v1 row for ticket_event_id %', p_ticket_event_id;
  end if;

  v_hours := extract(epoch from (v_event.kickoff_at - v_now)) / 3600.0;

  v_horizon := case
    when abs(v_hours - 720.0) <= 240.0 then 'T-30'
    when abs(v_hours - 336.0) <= 110.88 then 'T-14'
    when abs(v_hours - 168.0) <= 55.44 then 'T-7'
    when abs(v_hours - 72.0) <= 23.76 then 'T-3'
    when abs(v_hours - 24.0) <= 12.0 then 'T-24h'
    else 'continuous'
  end;

  v_id := nextval('public.forecast_observations_id_seq');

  insert into public.forecast_observations (
    id, ticket_event_id, source_snapshot_id, forecast_generated_at,
    source_snapshot_captured_at, hours_to_kickoff, days_to_match, horizon,
    model_version, historical_model, historical_p10, historical_p50,
    historical_p90, live_adjustment, final_p10, final_p50, final_p90,
    forecast_status, correction_status, signal_readiness,
    live_available_total, live_first_available_total, live_available_index,
    live_net_removed_since_first, live_net_removed_since_previous,
    live_velocity_since_previous, live_net_removed_6h, live_velocity_6h,
    live_net_removed_24h, live_velocity_24h, live_acceleration_6h_vs_24h,
    live_raw_snapshot_count, live_clean_snapshot_count,
    live_excluded_anomaly_count, payload
  ) values (
    v_id, p_ticket_event_id, v_live.snapshot_id, v_now, v_live.captured_at,
    v_hours, v_hours / 24.0, v_horizon,
    'beyond-demand-engine-v1-shadow', v_hist.historical_model,
    v_hist.historical_p10, v_hist.historical_p50, v_hist.historical_p90,
    0,
    v_hist.historical_p10, v_hist.historical_p50, v_hist.historical_p90,
    'shadow', 'shadow', 'partial',
    v_live.available_total, v_live.first_available_total,
    v_live.available_index::double precision,
    v_live.net_removed_since_first, v_live.net_removed_since_previous,
    v_live.velocity_since_previous::double precision,
    v_live.net_removed_6h::integer, v_live.velocity_6h::double precision,
    v_live.net_removed_24h::integer, v_live.velocity_24h::double precision,
    v_live.acceleration_6h_vs_24h::double precision,
    v_live.raw_snapshot_count::integer,
    null, null,
    jsonb_build_object(
      'engine', jsonb_build_object(
        'engine_version', 'beyond-demand-engine-v1-shadow',
        'mode', 'shadow',
        'source_model_version', 'beyond-forecast-v0.3',
        'historical_model_name', v_hist.historical_model,
        'historical_interval_method', 'stored_legacy_interval_unverified',
        'historical_calibration_version', null,
        'live_feature_version', 'live-features-v1',
        'correction_version', 'live-correction-noop-v1',
        'correction_reason', 'Shadow migration: live features observed, historical forecast preserved.',
        'source_historical_forecast_generated_at', v_hist.forecast_generated_at
      ),
      'live', jsonb_build_object(
        'inventory_interpretation', 'demand_proxy_not_confirmed_sales',
        'sector_coverage_change_flag', v_live.sector_coverage_change_flag,
        'release_activity_flag', v_live.release_activity_flag,
        'matched_sector_count', v_live.matched_sector_count,
        'entered_sector_count', v_live.entered_sector_count,
        'left_sector_count', v_live.left_sector_count,
        'coverage_inventory_effect', v_live.coverage_inventory_effect
      )
    )
  );

  return query
  select v_id, p_ticket_event_id, v_live.snapshot_id,
    'beyond-demand-engine-v1-shadow'::text, 'shadow'::text,
    v_hist.historical_p50, 0, v_hist.historical_p50, 'partial'::text;
end;
$$;

create or replace function public.run_all_demand_engine_v1_shadow()
returns integer
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_event_id bigint;
  v_latest_live_snapshot bigint;
  v_latest_shadow_snapshot bigint;
  v_inserted integer := 0;
begin
  for v_event_id in
    select te.id
    from public.ticket_events te
    where te.kickoff_at > now()
      and exists (
        select 1
        from public.forecast_observations fo
        where fo.ticket_event_id = te.id
          and fo.model_version = 'beyond-forecast-v0.3'
          and fo.historical_p10 is not null
          and fo.historical_p50 is not null
          and fo.historical_p90 is not null
          and coalesce(fo.forecast_status, '') <> 'shadow'
      )
    order by te.kickoff_at
  loop
    select lf.snapshot_id
    into v_latest_live_snapshot
    from public.get_live_features_v1(v_event_id) lf;

    if v_latest_live_snapshot is null then
      continue;
    end if;

    select fo.source_snapshot_id
    into v_latest_shadow_snapshot
    from public.forecast_observations fo
    where fo.ticket_event_id = v_event_id
      and fo.model_version = 'beyond-demand-engine-v1-shadow'
      and fo.forecast_status = 'shadow'
    order by fo.forecast_generated_at desc, fo.id desc
    limit 1;

    if v_latest_shadow_snapshot is not distinct from v_latest_live_snapshot then
      continue;
    end if;

    perform public.run_demand_engine_v1_shadow(v_event_id);
    v_inserted := v_inserted + 1;
  end loop;

  return v_inserted;
end;
$$;

-- Production deployment permissions:
-- revoke all on function public.run_demand_engine_v1_shadow(bigint)
--   from public, anon, authenticated;
-- grant execute on function public.run_demand_engine_v1_shadow(bigint) to service_role;
-- revoke all on function public.run_all_demand_engine_v1_shadow()
--   from public, anon, authenticated;
-- grant execute on function public.run_all_demand_engine_v1_shadow() to service_role;
--
-- Production schedule deployed in Supabase:
-- 10 */6 * * *  -> select public.run_all_demand_engine_v1_shadow();
