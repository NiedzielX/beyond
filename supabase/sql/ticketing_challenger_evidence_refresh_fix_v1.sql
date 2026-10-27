-- Fix stale Live Ticketing evidence refresh.
--
-- The previous refresh function copied dashboard_ticketing_challenger_v1 back
-- into its own backing summary table. Once the summary became stale, refreshes
-- could never incorporate newer CV rows. Recompute the summary directly from
-- ticketing_challenger_cv_predictions_v1 instead.
--
-- Research/evidence only. No production P50, live_adjustment or frozen model
-- parameters are changed.

create or replace function public.refresh_ticketing_challenger_dashboard_v1()
returns integer
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_rows integer := 0;
begin
  delete from public.ticketing_challenger_dashboard_summary_v1;

  insert into public.ticketing_challenger_dashboard_summary_v1(
    protocol,
    event_count,
    club_count,
    baseline_mae,
    bias_control_mae,
    challenger_mae,
    uplift_vs_baseline,
    incremental_ticketing_uplift,
    challenger_bias,
    candidate_model,
    protocol_status,
    refreshed_at
  )
  with metrics as (
    select
      p.protocol,
      count(distinct p.ticket_event_id)::integer as event_count,
      count(distinct p.club_slug)::integer as club_count,
      round(avg(abs(p.baseline_p50 - p.actual_attendance))::numeric, 1) as baseline_mae,
      round(avg(abs(p.bias_only_p50 - p.actual_attendance))::numeric, 1) as bias_control_mae,
      round(avg(abs(p.challenger_p50 - p.actual_attendance))::numeric, 1) as challenger_mae,
      round((
        avg(abs(p.baseline_p50 - p.actual_attendance))
        - avg(abs(p.challenger_p50 - p.actual_attendance))
      )::numeric, 1) as uplift_vs_baseline,
      round((
        avg(abs(p.bias_only_p50 - p.actual_attendance))
        - avg(abs(p.challenger_p50 - p.actual_attendance))
      )::numeric, 1) as incremental_ticketing_uplift,
      round(avg(p.challenger_p50 - p.actual_attendance)::numeric, 1) as challenger_bias
    from public.ticketing_challenger_cv_predictions_v1 p
    group by p.protocol
  ),
  current_model as (
    select
      m.feature_key || '_ridge_alpha' || round(m.ridge_alpha)::integer::text as candidate_model
    from public.ticketing_challenger_models_v1 m
    where m.status = 'shadow_active'
    order by m.trained_at desc
    limit 1
  )
  select
    m.protocol,
    m.event_count,
    m.club_count,
    m.baseline_mae,
    m.bias_control_mae,
    m.challenger_mae,
    m.uplift_vs_baseline,
    m.incremental_ticketing_uplift,
    m.challenger_bias,
    coalesce(cm.candidate_model, 'hybrid_v6_ridge_alpha30'),
    case
      when m.event_count < 8 or m.club_count < 5 then 'insufficient_sample'
      when m.uplift_vs_baseline > 0 and m.incremental_ticketing_uplift > 0
        then 'positive_research_signal'
      else 'rejected_no_uplift'
    end,
    now()
  from metrics m
  left join current_model cm on true
  order by m.protocol;

  get diagnostics v_rows = row_count;
  return v_rows;
end;
$function$;

-- Do not keep describing Ticketing as evidence-backed after a larger sample
-- invalidates the earlier positive signal.
create or replace view public.dashboard_model_evidence_summary_v1
with (security_invoker = true)
as
select
  count(*)::integer as category_count,
  count(*) filter (where decision_status = 'promotable')::integer as promotable_count,
  count(*) filter (where decision_status = 'collecting')::integer as collecting_count,
  count(*) filter (where decision_status = 'rejected')::integer as rejected_count,
  count(*) filter (where decision_status = 'blocked')::integer as blocked_count,
  count(*) filter (where evidence_signal = 'positive')::integer as positive_signal_count,
  case
    when coalesce(bool_or(category_key = 'ticketing' and evidence_signal = 'positive'), false)
      then 'Baseline + Ticketing (shadow evidence chain)'
    else 'Baseline only (no positive challenger evidence)'
  end as current_evidence_backed_chain,
  'No context layer is automatically promoted to production P50.'::text as governance_note,
  max(refreshed_at) as refreshed_at
from public.model_evidence_scorecard_v1;

revoke all on public.dashboard_model_evidence_summary_v1 from public;
grant select on public.dashboard_model_evidence_summary_v1 to anon, authenticated;

-- Rebuild derived evidence immediately from the already-computed leakage-safe
-- CV rows. Promotion governance remains review-gated and production-safe.
select public.refresh_ticketing_challenger_dashboard_v1();
select public.refresh_model_evidence_scorecard_v1();
select public.refresh_model_promotion_governance_v1();
