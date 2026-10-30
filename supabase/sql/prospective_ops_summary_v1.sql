-- Beyond Ticketing — Prospective Ops Summary v1
--
-- Read-only machine-state summary for protected prospective lanes.
-- Source-of-truth is live persistence + existing preflight RPCs, not markdown.
-- No predictions, scores, backfills or model changes are created here.

create or replace function public.prospective_ops_summary_v1(
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
  v_p9 jsonb;
  v_trajectory jsonb;
  v_form5 jsonb;
begin
  v_p9 := public.p9_prospective_preflight_v1(v_days);
  v_trajectory := public.trajectory_frozen_encoder_preflight_v1(v_days);
  v_form5 := public.form5_prospective_summary_v1();

  return jsonb_build_object(
    'version','prospective-ops-summary-v1',
    'checked_at',now(),
    'horizon_days',v_days,
    'production_change',false,
    'live_adjustment',0,
    'evidence_counts',jsonb_build_object(
      'p9_v1',jsonb_build_object(
        'attempts',(select count(*) from private.p9_booking_curve_prospective_attempts_v1),
        'predictions',(select count(*) from private.p9_booking_curve_prospective_predictions_v1),
        'scores',(select count(*) from private.p9_booking_curve_prospective_scores_v1)
      ),
      'p9_v2',jsonb_build_object(
        'attempts',(select count(*) from private.p9_booking_curve_prospective_fallback_attempts_v2),
        'predictions',(select count(*) from private.p9_booking_curve_prospective_fallback_predictions_v2),
        'scores',(select count(*) from private.p9_booking_curve_prospective_fallback_scores_v2)
      ),
      'trajectory_frozen_encoder',jsonb_build_object(
        'attempts',(select count(*) from private.daily_trajectory_attempts_v1 where model_version='trajectory-frozen-encoder-ridge-ratio-head-v1'),
        'predictions',(select count(*) from private.daily_trajectory_predictions_v1 where model_version='trajectory-frozen-encoder-ridge-ratio-head-v1'),
        'scores',(select count(*) from private.daily_trajectory_scores_v1 where model_version='trajectory-frozen-encoder-ridge-ratio-head-v1')
      )
    ),
    'p9_preflight',v_p9,
    'trajectory_preflight',v_trajectory,
    'form5',v_form5
  );
end;
$function$;

revoke all on function public.prospective_ops_summary_v1(integer)
  from public,anon,authenticated;
grant execute on function public.prospective_ops_summary_v1(integer)
  to service_role;
