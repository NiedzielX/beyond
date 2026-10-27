-- Keep dashboard Hype evidence aligned with the real prospective testability gate.
--
-- The underlying scorecard may count completed T-24 snapshots even when the
-- feature is constant. For Hype this can make "10 completed events" look like
-- a testable sample although media_attention currently has only one distinct
-- value and mention_acceleration is still below the 8-event / 5-club gate.
--
-- This view-level correction is presentation/evidence only. It does not mutate
-- the scorecard source table, frozen forecasts, model parameters, labels, or
-- production P50.

create or replace view public.dashboard_model_evidence_scorecard_v1
with (security_invoker = true)
as
with media as (
  select *
  from public.hype_challenger_readiness_v1
  where feature_key='hype.media_attention'
), accel as (
  select *
  from public.hype_challenger_readiness_v1
  where feature_key='hype.mention_acceleration'
)
select
  s.category_key,
  s.sort_order,
  s.display_name,
  s.research_prior_weight_pct,
  s.decision_status,
  s.evidence_signal,
  s.primary_protocol,
  s.candidate_key,
  s.validation_event_count,
  s.validation_club_count,
  case
    when s.category_key='hype'
      and not exists (select 1 from public.hype_challenger_cv_summary_v1)
      then 0
    else s.promotion_evidence_count
  end as promotion_evidence_count,
  s.promotion_event_target,
  s.promotion_club_target,
  (
    case
      when s.category_key='hype'
        and not exists (select 1 from public.hype_challenger_cv_summary_v1)
        then 0.00
      else s.promotion_progress_pct
    end
  )::numeric(6,2) as promotion_progress_pct,
  s.incumbent_mae,
  s.bias_control_mae,
  s.challenger_mae,
  s.uplift_vs_incumbent,
  s.incremental_uplift_vs_bias,
  s.prospective_event_count,
  case
    when s.category_key='hype'
      and not exists (select 1 from public.hype_challenger_cv_summary_v1)
      then format(
        'Attention & Hype is not testable yet. media_attention: %s completed events / %s clubs / %s distinct values (requires 8 / 5 / >=2). mention_acceleration: %s completed events / %s clubs / %s distinct values (requires 8 / 5 / >=2).',
        coalesce((select completed_eligible_count from media),0),
        coalesce((select completed_club_count from media),0),
        coalesce((select distinct_value_count from media),0),
        coalesce((select completed_eligible_count from accel),0),
        coalesce((select completed_club_count from accel),0),
        coalesce((select distinct_value_count from accel),0)
      )
    else s.decision_reason
  end as decision_reason,
  case
    when s.category_key='hype'
      and not exists (select 1 from public.hype_challenger_cv_summary_v1)
      then 'Continue forward-only collection. Do not backfill historical Hype observations. Run cross-club evaluation only after one Hype feature satisfies event, club and non-constant-value gates.'
    else s.next_action
  end as next_action,
  s.production_impact,
  s.source_refreshed_at,
  case
    when s.category_key='hype' then
      coalesce(s.evidence,'{}'::jsonb) || jsonb_build_object(
        'media_attention_readiness_status',coalesce((select readiness_status from media),'missing'),
        'media_attention_distinct_values',coalesce((select distinct_value_count from media),0),
        'mention_acceleration_readiness_status',coalesce((select readiness_status from accel),'missing'),
        'mention_acceleration_completed_events',coalesce((select completed_eligible_count from accel),0),
        'mention_acceleration_distinct_values',coalesce((select distinct_value_count from accel),0),
        'cross_club_result_available',exists(select 1 from public.hype_challenger_cv_summary_v1)
      )
    else s.evidence
  end as evidence,
  s.refreshed_at
from public.model_evidence_scorecard_v1 s
order by s.sort_order;

-- The dashboard surface is intentionally read-only for browser roles.
revoke all privileges on public.dashboard_model_evidence_scorecard_v1 from anon, authenticated;
grant select on public.dashboard_model_evidence_scorecard_v1 to anon, authenticated;
