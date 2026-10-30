-- Beyond Ticketing — P9 v2 Business Meaningful Forecast Gain evaluator v1
--
-- Implements the same ex-ante business threshold frozen in
-- ml/BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md, while keeping P9 v2 evidence
-- completely separate from trajectory, P9 v1 and Form5.
--
-- Read-only, service-role-only, no production effect.
-- Frozen business threshold: >=550 seats MAE gain at a given cutoff.
-- Earliest directional evidence gate: >=8 independent scored events / >=5 clubs.

create or replace function public.p9_v2_business_meaningful_gain_v1()
returns jsonb
language sql
stable
security definer
set search_path = public, private
as $$
with params as (
  select
    550.0::double precision as business_gain_threshold_seats,
    8::integer as min_events,
    5::integer as min_clubs
), cutoffs(cutoff_hours) as (
  values (48),(24)
), eligible as (
  select
    s.ticket_event_id,
    e.club_slug,
    s.cutoff_hours,
    s.actual_attendance::double precision as actual_attendance,
    p.incumbent_p50,
    p.challenger_p50,
    s.incumbent_abs_error,
    s.challenger_abs_error,
    s.delta_abs_error,
    s.incumbent_bias,
    s.challenger_bias,
    s.predicted_at,
    s.attendance_confirmed_at,
    s.scored_at
  from private.p9_booking_curve_prospective_fallback_scores_v2 s
  join private.p9_booking_curve_prospective_fallback_predictions_v2 p
    on p.id=s.prediction_id
   and p.ticket_event_id=s.ticket_event_id
   and p.cutoff_hours=s.cutoff_hours
  join public.ticket_events e
    on e.id=s.ticket_event_id
  where s.production_change=false
    and p.production_change=false
    and s.predicted_at=s.predicted_at
    and s.predicted_at < s.attendance_confirmed_at
    and p.predicted_at < p.target_at
    and s.cutoff_hours in (48,24)
), metrics as (
  select
    c.cutoff_hours,
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
    avg(e.incumbent_bias)::double precision as incumbent_signed_bias,
    avg(e.challenger_bias)::double precision as challenger_signed_bias,
    min(e.predicted_at) as first_prediction_at,
    max(e.scored_at) as last_scored_at
  from cutoffs c
  left join eligible e on e.cutoff_hours=c.cutoff_hours
  group by c.cutoff_hours
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
  'version','p9-v2-business-meaningful-gain-v1',
  'lane','p9-knn-median-residual-k5-family-fallback-v2',
  'checked_at',now(),
  'business_gain_threshold_seats',(select business_gain_threshold_seats from params),
  'minimum_directional_events',(select min_events from params),
  'minimum_directional_clubs',(select min_clubs from params),
  'production_change',false,
  'cutoffs',coalesce((
    select jsonb_agg(jsonb_build_object(
      'cutoff_hours',c.cutoff_hours,
      'horizon','T-' || c.cutoff_hours::text,
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
    ) order by c.cutoff_hours desc)
    from classified c
  ),'[]'::jsonb)
);
$$;

revoke all on function public.p9_v2_business_meaningful_gain_v1()
  from public, anon, authenticated;
grant execute on function public.p9_v2_business_meaningful_gain_v1()
  to service_role;
