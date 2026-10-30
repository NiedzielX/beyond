-- Beyond Ticketing — Business Meaningful Forecast Gain evaluator v1
--
-- Implements ml/BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md.
-- Read-only, service-role-only, no production effect.
--
-- Frozen business threshold: >=550 seats event-balanced MAE gain.
-- Earliest directional evidence gate: >=8 independent scored events / >=5 clubs.
-- Risk guards: majority improvement, median Delta AE < 0, non-worse P90 AE,
-- and non-worse absolute signed bias.

create or replace function public.trajectory_business_meaningful_gain_v1(
  p_model_version text default 'trajectory-frozen-encoder-ridge-ratio-head-v1'
)
returns jsonb
language sql
stable
security definer
set search_path = public, private
as $$
with params as (
  select
    p_model_version as model_version,
    550.0::double precision as business_gain_threshold_seats,
    8::integer as min_events,
    5::integer as min_clubs
), horizons(days_to_event) as (
  values (7),(3),(1)
), eligible as (
  select
    s.ticket_event_id,
    e.club_slug,
    s.days_to_event,
    s.actual_attendance::double precision as actual_attendance,
    s.incumbent_p50,
    s.challenger_p50,
    s.incumbent_abs_error,
    s.challenger_abs_error,
    s.delta_abs_error,
    (s.incumbent_p50 - s.actual_attendance::double precision) as incumbent_error,
    (s.challenger_p50 - s.actual_attendance::double precision) as challenger_error,
    s.predicted_at,
    s.attendance_confirmed_at,
    s.scored_at
  from private.daily_trajectory_scores_v1 s
  join private.daily_trajectory_predictions_v1 p
    on p.id=s.prediction_id
  join private.daily_trajectory_attempts_v1 a
    on a.id=p.attempt_id
  join public.ticket_events e
    on e.id=s.ticket_event_id
  cross join params x
  where s.model_version=x.model_version
    and p.model_version=x.model_version
    and a.model_version=x.model_version
    and p.target_values_used=false
    and a.target_values_used=false
    and p.production_change=false
    and a.production_change=false
    and s.production_change=false
    and s.predicted_at < s.attendance_confirmed_at
    and p.predicted_at < p.target_at
    and s.days_to_event in (7,3,1)
), metrics as (
  select
    h.days_to_event,
    count(distinct e.ticket_event_id)::integer as event_count,
    count(distinct e.club_slug)::integer as club_count,
    avg(e.incumbent_abs_error)::double precision as incumbent_mae,
    avg(e.challenger_abs_error)::double precision as challenger_mae,
    avg(e.delta_abs_error)::double precision as delta_mae,
    (avg(e.incumbent_abs_error)-avg(e.challenger_abs_error))::double precision as business_gain_seats,
    avg(case when e.delta_abs_error < 0 then 1.0 else 0.0 end)::double precision as event_improvement_rate,
    percentile_cont(0.5) within group (order by e.delta_abs_error)::double precision as median_delta_abs_error,
    percentile_cont(0.9) within group (order by e.incumbent_abs_error)::double precision as incumbent_p90_abs_error,
    percentile_cont(0.9) within group (order by e.challenger_abs_error)::double precision as challenger_p90_abs_error,
    avg(e.incumbent_error)::double precision as incumbent_signed_bias,
    avg(e.challenger_error)::double precision as challenger_signed_bias,
    min(e.predicted_at) as first_prediction_at,
    max(e.scored_at) as last_scored_at
  from horizons h
  left join eligible e on e.days_to_event=h.days_to_event
  group by h.days_to_event
), classified as (
  select
    m.*,
    p.business_gain_threshold_seats,
    p.min_events,
    p.min_clubs,
    coalesce(m.event_improvement_rate > 0.5,false) as guard_majority_events_improve,
    coalesce(m.median_delta_abs_error < 0,false) as guard_median_event_improves,
    coalesce(m.challenger_p90_abs_error <= m.incumbent_p90_abs_error,false) as guard_p90_not_worse,
    coalesce(abs(m.challenger_signed_bias) <= abs(m.incumbent_signed_bias),false) as guard_abs_bias_not_worse,
    case
      when m.event_count < p.min_events or m.club_count < p.min_clubs
        then 'INSUFFICIENT_PROSPECTIVE_EVIDENCE'
      when coalesce(m.delta_mae,0) >= 0
        then 'NOT_SUPPORTED'
      when coalesce(m.business_gain_seats,0) < p.business_gain_threshold_seats
        then 'RESEARCH_POSITIVE_NOT_BUSINESS_MEANINGFUL'
      when not (
        coalesce(m.event_improvement_rate > 0.5,false)
        and coalesce(m.median_delta_abs_error < 0,false)
        and coalesce(m.challenger_p90_abs_error <= m.incumbent_p90_abs_error,false)
        and coalesce(abs(m.challenger_signed_bias) <= abs(m.incumbent_signed_bias),false)
      )
        then 'BUSINESS_GAIN_WITH_RISK_GUARD_FAIL'
      else 'BUSINESS_MEANINGFUL_REVIEW_ELIGIBLE'
    end as decision_label
  from metrics m
  cross join params p
)
select jsonb_build_object(
  'version','trajectory-business-meaningful-gain-v1',
  'model_version',(select model_version from params),
  'checked_at',now(),
  'business_gain_threshold_seats',(select business_gain_threshold_seats from params),
  'minimum_directional_events',(select min_events from params),
  'minimum_directional_clubs',(select min_clubs from params),
  'target_values_used',false,
  'production_change',false,
  'horizons',coalesce((
    select jsonb_agg(jsonb_build_object(
      'days_to_event',c.days_to_event,
      'horizon','P-' || c.days_to_event::text,
      'decision_label',c.decision_label,
      'event_count',c.event_count,
      'club_count',c.club_count,
      'incumbent_mae',c.incumbent_mae,
      'challenger_mae',c.challenger_mae,
      'delta_mae',c.delta_mae,
      'business_gain_seats',c.business_gain_seats,
      'event_improvement_rate',c.event_improvement_rate,
      'median_delta_abs_error',c.median_delta_abs_error,
      'incumbent_p90_abs_error',c.incumbent_p90_abs_error,
      'challenger_p90_abs_error',c.challenger_p90_abs_error,
      'incumbent_signed_bias',c.incumbent_signed_bias,
      'challenger_signed_bias',c.challenger_signed_bias,
      'risk_guards',jsonb_build_object(
        'majority_events_improve',c.guard_majority_events_improve,
        'median_event_improves',c.guard_median_event_improves,
        'p90_not_worse',c.guard_p90_not_worse,
        'abs_bias_not_worse',c.guard_abs_bias_not_worse
      ),
      'first_prediction_at',c.first_prediction_at,
      'last_scored_at',c.last_scored_at
    ) order by c.days_to_event desc)
    from classified c
  ),'[]'::jsonb)
);
$$;

revoke all on function public.trajectory_business_meaningful_gain_v1(text)
  from public, anon, authenticated;
grant execute on function public.trajectory_business_meaningful_gain_v1(text)
  to service_role;
