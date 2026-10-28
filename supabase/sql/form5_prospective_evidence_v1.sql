-- Form5 prospective evidence contract v1.
--
-- Implements the precommitted experiment in ml/FORM5_PROSPECTIVE_PRECOMMIT_V1.md.
-- Evidence only: no production forecast, live_adjustment, or model activation changes.

create or replace view private.form5_prospective_dataset_v1 as
select
  s.id as snapshot_id,
  s.ticket_event_id,
  e.club_slug,
  e.home_team,
  e.away_team,
  e.kickoff_at,
  s.checkpoint_at,
  s.captured_at,
  p.predicted_p50::numeric as baseline_p50,
  p.generated_at as baseline_generated_at,
  (s.context_features->'sport.form5'->>'numeric_value')::numeric as form5_points,
  s.context_features->'sport.form5'->>'source_name' as form5_source_name,
  (s.context_features->'sport.form5'->>'observed_at')::timestamptz as form5_observed_at,
  (s.context_features->'sport.form5'->>'source_observed_at')::timestamptz as form5_source_observed_at,
  s.context_features->'sport.form5'->>'source_record_key' as form5_source_record_key,
  o.actual_attendance::numeric as actual_attendance,
  o.confirmed_at as outcome_confirmed_at,
  ((o.actual_attendance::numeric - p.predicted_p50::numeric) / nullif(p.predicted_p50::numeric,0)) as baseline_residual_ratio
from public.event_context_snapshots_v1 s
join public.ticket_events e on e.id=s.ticket_event_id
join public.context_ablation_predictions_v1 p
  on p.snapshot_id=s.id
 and p.variant_key='baseline'
join public.ticket_event_outcomes o
  on o.ticket_event_id=s.ticket_event_id
join public.event_context_observations fo
  on fo.ticket_event_id=s.ticket_event_id
 and fo.feature_key='sport.form5'
 and fo.source_name='TheSportsDB v1 shadow'
 and fo.source_record_key=s.context_features->'sport.form5'->>'source_record_key'
where s.checkpoint_code='T-24h'
  and s.capture_mode='prospective'
  and public.match_competition_key_v1(e.competition)='ekstraklasa'
  and s.context_features ? 'sport.form5'
  and nullif(s.context_features->'sport.form5'->>'numeric_value','') is not null
  and s.context_features->'sport.form5'->>'source_name'='TheSportsDB v1 shadow'
  and (s.context_features->'sport.form5'->>'observed_at')::timestamptz <= s.checkpoint_at
  and (s.context_features->'sport.form5'->>'source_observed_at')::timestamptz <= s.checkpoint_at
  and fo.observed_at <= s.checkpoint_at
  and fo.created_at <= s.checkpoint_at
  and fo.source_observed_at <= s.checkpoint_at
  and o.actual_attendance is not null
  and o.confirmed_at is not null
  and o.confirmed_at > s.checkpoint_at
  and p.predicted_p50 is not null
  and p.predicted_p50 > 0;

revoke all on private.form5_prospective_dataset_v1 from public, anon, authenticated;
grant select on private.form5_prospective_dataset_v1 to service_role;

create or replace view private.form5_prospective_cv_predictions_v1 as
with protocols as (
  select 'leave_one_club_out'::text as protocol
  union all
  select 'leave_one_event_out'::text
), scored as (
  select
    d.snapshot_id,
    d.ticket_event_id,
    d.club_slug,
    d.home_team,
    d.away_team,
    d.kickoff_at,
    d.checkpoint_at,
    d.baseline_p50,
    d.actual_attendance,
    d.form5_points,
    f.protocol,
    st.n_train,
    st.club_count_train,
    st.x_mean,
    st.x_sd,
    st.y_mean,
    st.beta,
    st.y_mean as bias_only_ratio,
    st.y_mean + st.beta * ((d.form5_points-st.x_mean)/nullif(st.x_sd,0)) as challenger_ratio_raw
  from private.form5_prospective_dataset_v1 d
  cross join protocols f
  cross join lateral (
    with tr as (
      select t.*
      from private.form5_prospective_dataset_v1 t
      where case
        when f.protocol='leave_one_club_out' then t.club_slug<>d.club_slug
        else t.ticket_event_id<>d.ticket_event_id
      end
    ), base as (
      select
        count(*)::integer as n_train,
        count(distinct club_slug)::integer as club_count_train,
        avg(form5_points) as x_mean,
        stddev_pop(form5_points) as x_sd,
        avg(baseline_residual_ratio) as y_mean
      from tr
    )
    select
      b.n_train,
      b.club_count_train,
      b.x_mean,
      b.x_sd,
      b.y_mean,
      sum(((tr.form5_points-b.x_mean)/nullif(b.x_sd,0))*(tr.baseline_residual_ratio-b.y_mean))
        / (sum(power((tr.form5_points-b.x_mean)/nullif(b.x_sd,0),2))+30.0) as beta
    from tr
    cross join base b
    group by b.n_train,b.club_count_train,b.x_mean,b.x_sd,b.y_mean
  ) st
  where st.n_train>=5
    and st.club_count_train>=4
    and st.x_sd>0
), predictions as (
  select
    *,
    greatest(-0.25::numeric,least(0.25::numeric,challenger_ratio_raw)) as challenger_ratio_capped
  from scored
)
select
  snapshot_id,
  ticket_event_id,
  club_slug,
  home_team,
  away_team,
  kickoff_at,
  checkpoint_at,
  protocol,
  form5_points,
  n_train,
  club_count_train,
  x_mean,
  x_sd,
  y_mean,
  beta,
  baseline_p50,
  actual_attendance,
  round(baseline_p50*(1+bias_only_ratio))::integer as bias_only_p50,
  round(baseline_p50*(1+challenger_ratio_capped))::integer as challenger_p50,
  challenger_ratio_raw,
  challenger_ratio_capped,
  abs(challenger_ratio_raw)>0.25 as cap_hit,
  abs(baseline_p50-actual_attendance) as incumbent_abs_error,
  abs(round(baseline_p50*(1+challenger_ratio_capped))::numeric-actual_attendance) as challenger_abs_error,
  baseline_p50-actual_attendance as incumbent_bias,
  round(baseline_p50*(1+challenger_ratio_capped))::numeric-actual_attendance as challenger_bias
from predictions;

revoke all on private.form5_prospective_cv_predictions_v1 from public, anon, authenticated;
grant select on private.form5_prospective_cv_predictions_v1 to service_role;

create or replace function public.form5_prospective_summary_v1()
returns jsonb
language sql
stable
security invoker
set search_path='public','private','pg_temp'
as $function$
with readiness as (
  select
    count(distinct ticket_event_id)::integer as eligible_completed_events,
    count(distinct club_slug)::integer as eligible_completed_clubs,
    count(distinct form5_points)::integer as eligible_distinct_values,
    min(kickoff_at) as first_eligible_kickoff,
    max(kickoff_at) as latest_eligible_kickoff
  from private.form5_prospective_dataset_v1
), stream as (
  select
    count(distinct o.ticket_event_id)::integer as future_stream_events,
    count(distinct e.club_slug)::integer as future_stream_clubs,
    count(distinct o.numeric_value)::integer as future_stream_distinct_values,
    min(e.kickoff_at-interval '24 hours') filter (where e.kickoff_at>now()) as next_t24_at
  from public.event_context_observations o
  join public.ticket_events e on e.id=o.ticket_event_id
  where o.feature_key='sport.form5'
    and o.source_name='TheSportsDB v1 shadow'
    and o.numeric_value is not null
    and e.kickoff_at>now()
    and public.match_competition_key_v1(e.competition)='ekstraklasa'
), primary_metrics as (
  select
    count(*)::integer as scored_events,
    count(distinct club_slug)::integer as scored_clubs,
    avg(incumbent_abs_error)::double precision as incumbent_mae,
    avg(challenger_abs_error)::double precision as challenger_mae,
    avg(challenger_abs_error-incumbent_abs_error)::double precision as delta_mae,
    avg(case when challenger_abs_error<incumbent_abs_error then 1.0 else 0.0 end)::double precision as event_improvement_rate,
    max(challenger_abs_error-incumbent_abs_error)::double precision as worst_event_degradation,
    percentile_cont(0.5) within group(order by challenger_abs_error)::double precision as challenger_median_ae,
    percentile_cont(0.9) within group(order by challenger_abs_error)::double precision as challenger_p90_ae,
    avg(case when cap_hit then 1.0 else 0.0 end)::double precision as cap_hit_rate,
    count(*) filter (where cap_hit)::integer as cap_hit_count,
    count(*) filter (where beta>0)::integer as beta_positive_folds,
    count(*) filter (where beta<0)::integer as beta_negative_folds,
    count(*) filter (where beta=0)::integer as beta_zero_folds,
    min(beta)::double precision as beta_min,
    max(beta)::double precision as beta_max
  from private.form5_prospective_cv_predictions_v1
  where protocol='leave_one_club_out'
), secondary_metrics as (
  select
    count(*)::integer as scored_events,
    avg(incumbent_abs_error)::double precision as incumbent_mae,
    avg(challenger_abs_error)::double precision as challenger_mae,
    avg(challenger_abs_error-incumbent_abs_error)::double precision as delta_mae
  from private.form5_prospective_cv_predictions_v1
  where protocol='leave_one_event_out'
), flags as (
  select
    r.*,
    s.*,
    p.*,
    q.scored_events as loeo_scored_events,
    q.incumbent_mae as loeo_incumbent_mae,
    q.challenger_mae as loeo_challenger_mae,
    q.delta_mae as loeo_delta_mae,
    (r.eligible_completed_events>=8
      and r.eligible_completed_clubs>=5
      and r.eligible_distinct_values>=2) as gate_open,
    (p.scored_events=r.eligible_completed_events and r.eligible_completed_events>0) as fold_support_complete,
    not (coalesce(p.beta_positive_folds,0)>0 and coalesce(p.beta_negative_folds,0)>0) as beta_sign_stable
  from readiness r
  cross join stream s
  cross join primary_metrics p
  cross join secondary_metrics q
)
select jsonb_build_object(
  'version','form5-prospective-summary-v1',
  'precommit_id','form5-prospective-challenger-v1',
  'checked_at',now(),
  'source_name','TheSportsDB v1 shadow',
  'primary_protocol','leave_one_club_out',
  'secondary_protocol','leave_one_event_out',
  'ridge_alpha',30,
  'correction_cap',0.25,
  'minimum_events',8,
  'minimum_clubs',5,
  'minimum_distinct_values',2,
  'eligible_completed_events',eligible_completed_events,
  'eligible_completed_clubs',eligible_completed_clubs,
  'eligible_distinct_values',eligible_distinct_values,
  'first_eligible_kickoff',first_eligible_kickoff,
  'latest_eligible_kickoff',latest_eligible_kickoff,
  'future_stream_events',future_stream_events,
  'future_stream_clubs',future_stream_clubs,
  'future_stream_distinct_values',future_stream_distinct_values,
  'next_t24_at',next_t24_at,
  'gate_open',gate_open,
  'fold_support_complete',fold_support_complete,
  'decision_status',case
    when not gate_open then 'PROSPECTIVE_COLLECTING'
    when not fold_support_complete then 'PROSPECTIVE_COLLECTING'
    when challenger_mae>=incumbent_mae then 'EVALUATED_NO_UPLIFT'
    else 'POINT_GAIN_UNCERTAINTY_LIMITED'
  end,
  'decision_reason',case
    when not gate_open then format('Gate not met: %s/8 completed eligible events, %s/5 clubs, %s/2 distinct values.',eligible_completed_events,eligible_completed_clubs,eligible_distinct_values)
    when not fold_support_complete then format('Global gate met but only %s/%s LOCO folds satisfy frozen training-support rules.',scored_events,eligible_completed_events)
    when challenger_mae>=incumbent_mae then 'Frozen Form5 challenger does not improve prospective LOCO MAE versus the true baseline.'
    else 'Frozen Form5 challenger improves prospective LOCO point MAE, but promotion remains review-gated and uncertainty/downside must be assessed.'
  end,
  'lo_co_scored_events',scored_events,
  'incumbent_event_balanced_mae',case when gate_open and fold_support_complete then incumbent_mae else null end,
  'challenger_event_balanced_mae',case when gate_open and fold_support_complete then challenger_mae else null end,
  'delta_event_balanced_mae',case when gate_open and fold_support_complete then delta_mae else null end,
  'event_improvement_rate',case when gate_open and fold_support_complete then event_improvement_rate else null end,
  'worst_event_degradation',case when gate_open and fold_support_complete then worst_event_degradation else null end,
  'challenger_median_ae',case when gate_open and fold_support_complete then challenger_median_ae else null end,
  'challenger_p90_ae',case when gate_open and fold_support_complete then challenger_p90_ae else null end,
  'cap_hit_count',case when gate_open and fold_support_complete then cap_hit_count else null end,
  'cap_hit_rate',case when gate_open and fold_support_complete then cap_hit_rate else null end,
  'beta_sign_stable',case when gate_open and fold_support_complete then beta_sign_stable else null end,
  'beta_positive_folds',case when gate_open and fold_support_complete then beta_positive_folds else null end,
  'beta_negative_folds',case when gate_open and fold_support_complete then beta_negative_folds else null end,
  'beta_zero_folds',case when gate_open and fold_support_complete then beta_zero_folds else null end,
  'beta_min',case when gate_open and fold_support_complete then beta_min else null end,
  'beta_max',case when gate_open and fold_support_complete then beta_max else null end,
  'loeo_scored_events',loeo_scored_events,
  'loeo_incumbent_mae',case when gate_open and fold_support_complete then loeo_incumbent_mae else null end,
  'loeo_challenger_mae',case when gate_open and fold_support_complete then loeo_challenger_mae else null end,
  'loeo_delta_mae',case when gate_open and fold_support_complete then loeo_delta_mae else null end,
  'target_values_used_at_prediction',false,
  'production_activation_allowed',false,
  'live_adjustment',0,
  'production_change',false
)
from flags;
$function$;

revoke all on function public.form5_prospective_summary_v1() from public, anon, authenticated;
grant execute on function public.form5_prospective_summary_v1() to service_role;
