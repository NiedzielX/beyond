-- Beyond Ticketing — Prospective Attendance Evaluation v1
--
-- Machine-readable implementation of ml/PROSPECTIVE_ATTENDANCE_EVALUATION_V1.md.
-- Created before the first scored Frozen Encoder / P9-v2 target outcome.
-- Read-only; no prediction, scoring, backfill or production mutation.

create or replace function public.prospective_attendance_eval_v1()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public','private'
as $function$
declare
  v_min_events constant integer := 8;
  v_min_clubs constant integer := 5;
  v_trajectory jsonb;
  v_p9_v2 jsonb;
begin
  with scored as (
    select
      s.ticket_event_id,
      e.club_slug,
      s.days_to_event,
      s.incumbent_abs_error,
      s.challenger_abs_error,
      s.delta_abs_error
    from private.daily_trajectory_scores_v1 s
    join public.ticket_events e on e.id=s.ticket_event_id
    where s.model_version='trajectory-frozen-encoder-ridge-ratio-head-v1'
      and s.production_change=false
  ), event_level as (
    select
      ticket_event_id,
      max(club_slug) as club_slug,
      avg(incumbent_abs_error) as incumbent_event_ae,
      avg(challenger_abs_error) as challenger_event_ae,
      avg(delta_abs_error) as event_delta_ae,
      count(*) as horizon_rows
    from scored
    group by ticket_event_id
  ), overall as (
    select
      count(*)::integer as scored_events,
      count(distinct club_slug)::integer as distinct_clubs,
      avg(incumbent_event_ae) as incumbent_event_balanced_mae,
      avg(challenger_event_ae) as challenger_event_balanced_mae,
      avg(event_delta_ae) as delta_mae,
      avg((event_delta_ae<0)::integer::numeric) as event_improvement_rate,
      percentile_cont(0.5) within group(order by event_delta_ae) as median_event_delta_ae,
      max(event_delta_ae) filter(where event_delta_ae>0) as worst_event_degradation,
      min(event_delta_ae) filter(where event_delta_ae<0) as best_event_improvement
    from event_level
  ), per_horizon as (
    select
      days_to_event,
      count(*)::integer as scored_rows,
      count(distinct ticket_event_id)::integer as scored_events,
      count(distinct club_slug)::integer as distinct_clubs,
      avg(incumbent_abs_error) as incumbent_mae,
      avg(challenger_abs_error) as challenger_mae,
      avg(delta_abs_error) as delta_mae,
      avg((delta_abs_error<0)::integer::numeric) as event_improvement_rate,
      percentile_cont(0.5) within group(order by delta_abs_error) as median_delta_ae,
      max(delta_abs_error) filter(where delta_abs_error>0) as worst_event_degradation,
      min(delta_abs_error) filter(where delta_abs_error<0) as best_event_improvement
    from scored
    group by days_to_event
  )
  select jsonb_build_object(
    'lane','trajectory-frozen-encoder-ridge-ratio-head-v1',
    'status',case when o.scored_events>=v_min_events and o.distinct_clubs>=v_min_clubs then 'EVIDENCE_REVIEW_READY' else 'PROSPECTIVE_COLLECTING' end,
    'review_gate',jsonb_build_object(
      'minimum_events',v_min_events,
      'minimum_clubs',v_min_clubs,
      'open',o.scored_events>=v_min_events and o.distinct_clubs>=v_min_clubs
    ),
    'prediction_count',(select count(*) from private.daily_trajectory_predictions_v1 where model_version='trajectory-frozen-encoder-ridge-ratio-head-v1' and production_change=false),
    'score_row_count',(select count(*) from scored),
    'scored_event_count',o.scored_events,
    'distinct_club_count',o.distinct_clubs,
    'incumbent_event_balanced_mae',o.incumbent_event_balanced_mae,
    'challenger_event_balanced_mae',o.challenger_event_balanced_mae,
    'delta_mae',o.delta_mae,
    'event_improvement_rate',o.event_improvement_rate,
    'median_event_delta_ae',o.median_event_delta_ae,
    'worst_event_degradation',o.worst_event_degradation,
    'best_event_improvement',o.best_event_improvement,
    'per_horizon',coalesce((select jsonb_agg(jsonb_build_object(
      'days_to_event',h.days_to_event,
      'label','P-'||h.days_to_event,
      'scored_rows',h.scored_rows,
      'scored_events',h.scored_events,
      'distinct_clubs',h.distinct_clubs,
      'incumbent_mae',h.incumbent_mae,
      'challenger_mae',h.challenger_mae,
      'delta_mae',h.delta_mae,
      'event_improvement_rate',h.event_improvement_rate,
      'median_delta_ae',h.median_delta_ae,
      'worst_event_degradation',h.worst_event_degradation,
      'best_event_improvement',h.best_event_improvement
    ) order by h.days_to_event desc) from per_horizon h),'[]'::jsonb)
  ) into v_trajectory
  from overall o;

  with scored as (
    select
      s.ticket_event_id,
      e.club_slug,
      s.cutoff_hours,
      s.incumbent_abs_error,
      s.challenger_abs_error,
      s.delta_abs_error
    from private.p9_booking_curve_prospective_fallback_scores_v2 s
    join public.ticket_events e on e.id=s.ticket_event_id
    where s.production_change=false
  ), event_level as (
    select
      ticket_event_id,
      max(club_slug) as club_slug,
      avg(incumbent_abs_error) as incumbent_event_ae,
      avg(challenger_abs_error) as challenger_event_ae,
      avg(delta_abs_error) as event_delta_ae,
      count(*) as cutoff_rows
    from scored
    group by ticket_event_id
  ), overall as (
    select
      count(*)::integer as scored_events,
      count(distinct club_slug)::integer as distinct_clubs,
      avg(incumbent_event_ae) as incumbent_event_balanced_mae,
      avg(challenger_event_ae) as challenger_event_balanced_mae,
      avg(event_delta_ae) as delta_mae,
      avg((event_delta_ae<0)::integer::numeric) as event_improvement_rate,
      percentile_cont(0.5) within group(order by event_delta_ae) as median_event_delta_ae,
      max(event_delta_ae) filter(where event_delta_ae>0) as worst_event_degradation,
      min(event_delta_ae) filter(where event_delta_ae<0) as best_event_improvement
    from event_level
  ), per_horizon as (
    select
      cutoff_hours,
      count(*)::integer as scored_rows,
      count(distinct ticket_event_id)::integer as scored_events,
      count(distinct club_slug)::integer as distinct_clubs,
      avg(incumbent_abs_error) as incumbent_mae,
      avg(challenger_abs_error) as challenger_mae,
      avg(delta_abs_error) as delta_mae,
      avg((delta_abs_error<0)::integer::numeric) as event_improvement_rate,
      percentile_cont(0.5) within group(order by delta_abs_error) as median_delta_ae,
      max(delta_abs_error) filter(where delta_abs_error>0) as worst_event_degradation,
      min(delta_abs_error) filter(where delta_abs_error<0) as best_event_improvement
    from scored
    group by cutoff_hours
  )
  select jsonb_build_object(
    'lane','p9-knn-median-residual-k5-family-fallback-v2',
    'status',case when o.scored_events>=v_min_events and o.distinct_clubs>=v_min_clubs then 'EVIDENCE_REVIEW_READY' else 'PROSPECTIVE_COLLECTING' end,
    'review_gate',jsonb_build_object(
      'minimum_events',v_min_events,
      'minimum_clubs',v_min_clubs,
      'open',o.scored_events>=v_min_events and o.distinct_clubs>=v_min_clubs
    ),
    'prediction_count',(select count(*) from private.p9_booking_curve_prospective_fallback_predictions_v2 where production_change=false),
    'score_row_count',(select count(*) from scored),
    'scored_event_count',o.scored_events,
    'distinct_club_count',o.distinct_clubs,
    'incumbent_event_balanced_mae',o.incumbent_event_balanced_mae,
    'challenger_event_balanced_mae',o.challenger_event_balanced_mae,
    'delta_mae',o.delta_mae,
    'event_improvement_rate',o.event_improvement_rate,
    'median_event_delta_ae',o.median_event_delta_ae,
    'worst_event_degradation',o.worst_event_degradation,
    'best_event_improvement',o.best_event_improvement,
    'per_horizon',coalesce((select jsonb_agg(jsonb_build_object(
      'cutoff_hours',h.cutoff_hours,
      'label','T-'||h.cutoff_hours,
      'scored_rows',h.scored_rows,
      'scored_events',h.scored_events,
      'distinct_clubs',h.distinct_clubs,
      'incumbent_mae',h.incumbent_mae,
      'challenger_mae',h.challenger_mae,
      'delta_mae',h.delta_mae,
      'event_improvement_rate',h.event_improvement_rate,
      'median_delta_ae',h.median_delta_ae,
      'worst_event_degradation',h.worst_event_degradation,
      'best_event_improvement',h.best_event_improvement
    ) order by h.cutoff_hours desc) from per_horizon h),'[]'::jsonb)
  ) into v_p9_v2
  from overall o;

  return jsonb_build_object(
    'version','prospective-attendance-eval-v1',
    'precommit','ml/PROSPECTIVE_ATTENDANCE_EVALUATION_V1.md',
    'checked_at',now(),
    'minimum_review_events',v_min_events,
    'minimum_review_clubs',v_min_clubs,
    'business_meaningful_effect_threshold',null,
    'production_activation_allowed',false,
    'production_change',false,
    'trajectory',v_trajectory,
    'p9_v2',v_p9_v2
  );
end;
$function$;

revoke all on function public.prospective_attendance_eval_v1()
  from public,anon,authenticated;
grant execute on function public.prospective_attendance_eval_v1()
  to service_role;
