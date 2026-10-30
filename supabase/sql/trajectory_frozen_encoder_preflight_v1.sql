-- Beyond Ticketing — Frozen Encoder Prospective Shadow Preflight v1
--
-- Goal: protect immutable P-7/P-3/P-1 windows before they open and distinguish
-- genuine readiness, captured fail-closed attempts and actually missed windows.
-- This function is target-free and read-only. It does not create predictions.
--
-- Frozen input contract mirrored from trajectory-frozen-encoder-ridge-ratio-head-v1:
-- - context limited to the 168h before the exact target cutoff;
-- - hourly-bucket observations;
-- - >=4 observations;
-- - >=24h observed prefix span;
-- - first genuine available_total > 0;
-- - PIT-valid structural prior available by the exact cutoff.
--
-- Operational activation guard:
-- - checkpoints before 2026-10-29 16:11:35 UTC predate the fully persisted/current
--   frozen shadow phase and are reported as PRE_ACTIVATION_NOT_EXPECTED rather than
--   false operational misses.

create or replace function public.trajectory_frozen_encoder_preflight_v1(
  p_horizon_days integer default 10
)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public','private'
as $function$
declare
  v_days integer := greatest(1, least(coalesce(p_horizon_days,10),31));
  v_model_version text := 'trajectory-frozen-encoder-ridge-ratio-head-v1';
  v_operational_activation_at timestamptz := '2026-10-29 16:11:35+00'::timestamptz;
begin
  return (
    with horizons(days_to_event) as (
      values (7),(3),(1)
    ), future_events as (
      select
        e.id as ticket_event_id,
        e.club_slug,
        e.home_team,
        e.away_team,
        e.kickoff_at,
        h.days_to_event,
        e.kickoff_at - make_interval(days=>h.days_to_event) as cutoff_at
      from public.ticket_events e
      cross join horizons h
      where e.kickoff_at is not null
        and e.kickoff_at > now()
        and e.kickoff_at <= now() + make_interval(days=>v_days)
        and not exists (
          select 1
          from public.ticket_event_outcomes o
          where o.ticket_event_id=e.id
            and o.actual_attendance is not null
        )
    ), evidence as (
      select
        f.*,
        prior.id as structural_prior_id,
        prior.p50::double precision as structural_p50,
        prior.generated_at as structural_generated_at,
        coalesce(obs.observation_count,0) as observation_count,
        obs.prefix_start_at,
        obs.prefix_end_at,
        coalesce(obs.prefix_span_hours,0.0) as prefix_span_hours,
        obs.first_available_total,
        attempt.status as attempt_status,
        attempt.attempted_at,
        pred.id as prediction_id,
        pred.predicted_at
      from future_events f
      left join lateral (
        select p.id,p.p50,p.generated_at
        from private.structural_prior_forecasts_v1 p
        where p.ticket_event_id=f.ticket_event_id
          and p.point_in_time_validated=true
          and p.target_as_of_at <= f.cutoff_at
          and p.generated_at <= f.cutoff_at
        order by p.target_as_of_at desc,p.generated_at desc,p.id desc
        limit 1
      ) prior on true
      left join lateral (
        with raw as (
          select
            s.id as snapshot_id,
            s.captured_at,
            s.available_total,
            floor(extract(epoch from (f.kickoff_at-s.captured_at))/3600.0)::int as hour_bucket
          from public.snapshots s
          where s.ticket_event_id=f.ticket_event_id
            and s.captured_at <= f.cutoff_at
            and s.captured_at >= f.cutoff_at - interval '168 hours'
            and s.captured_at < f.kickoff_at
            and s.available_total is not null
            and s.available_total >= 0
        ), dedup_ts as (
          select distinct on (captured_at)
            snapshot_id,captured_at,available_total,hour_bucket
          from raw
          order by captured_at,snapshot_id desc
        ), hourly as (
          select distinct on (hour_bucket)
            snapshot_id,captured_at,available_total,hour_bucket
          from dedup_ts
          order by hour_bucket,captured_at desc,snapshot_id desc
        )
        select
          count(*)::integer as observation_count,
          min(captured_at) as prefix_start_at,
          max(captured_at) as prefix_end_at,
          coalesce(extract(epoch from (max(captured_at)-min(captured_at)))/3600.0,0.0) as prefix_span_hours,
          (array_agg(available_total order by captured_at,snapshot_id))[1]::integer as first_available_total
        from hourly
      ) obs on true
      left join lateral (
        select a.status,a.attempted_at
        from private.daily_trajectory_attempts_v1 a
        where a.ticket_event_id=f.ticket_event_id
          and a.days_to_event=f.days_to_event
          and a.model_version=v_model_version
        order by a.attempted_at desc,a.id desc
        limit 1
      ) attempt on true
      left join lateral (
        select p.id,p.predicted_at
        from private.daily_trajectory_predictions_v1 p
        where p.ticket_event_id=f.ticket_event_id
          and p.days_to_event=f.days_to_event
          and p.model_version=v_model_version
        order by p.predicted_at desc,p.id desc
        limit 1
      ) pred on true
    ), classified as (
      select
        e.*,
        (
          e.structural_prior_id is not null
          and e.observation_count >= 4
          and e.prefix_span_hours >= 24.0
          and coalesce(e.first_available_total,0) > 0
        ) as input_ready,
        case
          when e.prediction_id is not null then 'CAPTURED'
          when e.attempt_status='PREDICTION_READY' then 'CRITICAL_PREDICTION_PERSISTENCE_GAP'
          when e.attempt_status is not null then 'CAPTURED_' || e.attempt_status
          when e.cutoff_at < v_operational_activation_at then 'PRE_ACTIVATION_NOT_EXPECTED'
          when now() > e.cutoff_at + interval '90 minutes' then 'MISSED_WINDOW'
          when now() >= e.cutoff_at and e.structural_prior_id is null then 'WINDOW_OPEN_NO_INCUMBENT'
          when now() >= e.cutoff_at and (
            e.observation_count < 4
            or e.prefix_span_hours < 24.0
            or coalesce(e.first_available_total,0) <= 0
          ) then 'WINDOW_OPEN_INPUT_INSUFFICIENT'
          when now() >= e.cutoff_at then 'WINDOW_OPEN_READY'
          when now() >= e.cutoff_at - interval '48 hours' and e.structural_prior_id is null then 'CRITICAL_NO_INCUMBENT'
          when now() >= e.cutoff_at - interval '48 hours' and e.observation_count < 4 then 'CRITICAL_TOO_FEW_OBSERVATIONS'
          when now() >= e.cutoff_at - interval '48 hours' and e.prefix_span_hours < 24.0 then 'CRITICAL_PREFIX_SPAN_INSUFFICIENT'
          when now() >= e.cutoff_at - interval '48 hours' and coalesce(e.first_available_total,0) <= 0 then 'CRITICAL_FIRST_INVENTORY_INVALID'
          when e.structural_prior_id is null then 'WATCH_NO_INCUMBENT'
          when e.observation_count < 4 then 'WATCH_TOO_FEW_OBSERVATIONS'
          when e.prefix_span_hours < 24.0 then 'WATCH_PREFIX_SPAN_INSUFFICIENT'
          when coalesce(e.first_available_total,0) <= 0 then 'WATCH_FIRST_INVENTORY_INVALID'
          else 'READY'
        end as status
      from evidence e
    )
    select jsonb_build_object(
      'version','trajectory-frozen-encoder-preflight-v1',
      'model_version',v_model_version,
      'operational_activation_at',v_operational_activation_at,
      'checked_at',now(),
      'horizon_days',v_days,
      'target_values_used',false,
      'production_change',false,
      'ready_count',coalesce((select count(*) from classified where status='READY'),0),
      'open_count',coalesce((select count(*) from classified where status like 'WINDOW_OPEN%'),0),
      'captured_count',coalesce((select count(*) from classified where status='CAPTURED' or status like 'CAPTURED_%'),0),
      'pre_activation_count',coalesce((select count(*) from classified where status='PRE_ACTIVATION_NOT_EXPECTED'),0),
      'watch_count',coalesce((select count(*) from classified where status like 'WATCH_%'),0),
      'critical_count',coalesce((select count(*) from classified where status like 'CRITICAL_%' or status='MISSED_WINDOW'),0),
      'checkpoints',coalesce((
        select jsonb_agg(jsonb_build_object(
          'ticket_event_id',c.ticket_event_id,
          'club_slug',c.club_slug,
          'home_team',c.home_team,
          'away_team',c.away_team,
          'kickoff_at',c.kickoff_at,
          'days_to_event',c.days_to_event,
          'cutoff_at',c.cutoff_at,
          'hours_to_cutoff',round((extract(epoch from (c.cutoff_at-now()))/3600.0)::numeric,2),
          'status',c.status,
          'input_ready',c.input_ready,
          'structural_prior_id',c.structural_prior_id,
          'structural_p50',c.structural_p50,
          'structural_generated_at',c.structural_generated_at,
          'observation_count',c.observation_count,
          'prefix_start_at',c.prefix_start_at,
          'prefix_end_at',c.prefix_end_at,
          'prefix_span_hours',round(c.prefix_span_hours::numeric,2),
          'first_available_total',c.first_available_total,
          'attempt_status',c.attempt_status,
          'attempted_at',c.attempted_at,
          'prediction_id',c.prediction_id,
          'predicted_at',c.predicted_at
        ) order by c.cutoff_at,c.ticket_event_id)
        from classified c
      ),'[]'::jsonb)
    )
  );
end;
$function$;

revoke all on function public.trajectory_frozen_encoder_preflight_v1(integer)
  from public,anon,authenticated;
grant execute on function public.trajectory_frozen_encoder_preflight_v1(integer)
  to service_role;
