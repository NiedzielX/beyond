-- Beyond Ticketing — Prospective Decision Summary v1
--
-- Read-only composition layer. It does not duplicate or redefine any evidence
-- contract; it exposes the current operational state, the frozen prospective
-- evaluation protocol, and the independently precommitted business-meaningful
-- forecast-gain contract in one response.
--
-- Trajectory and P9 v2 business evidence remain separate lanes.
-- Production remains OFF.

create or replace function public.prospective_decision_summary_v1(
  p_horizon_days integer default 10
)
returns jsonb
language sql
stable
security definer
set search_path = public, private
as $$
select jsonb_build_object(
  'version','prospective-decision-summary-v1',
  'checked_at',now(),
  'production_change',false,
  'live_adjustment',0,
  'production_activation_allowed',false,
  'operational_state',public.prospective_ops_summary_v1(p_horizon_days),
  'prospective_evaluation',public.prospective_attendance_eval_v1(),
  'business_meaningful_gain',jsonb_build_object(
    'trajectory',public.trajectory_business_meaningful_gain_v1(),
    'p9_v2',public.p9_v2_business_meaningful_gain_v1()
  ),
  'business_threshold_contract','ml/BUSINESS_MEANINGFUL_FORECAST_GAIN_V1.md',
  'business_gain_threshold_seats',550,
  'evaluation_contract','ml/PROSPECTIVE_ATTENDANCE_EVALUATION_V1.md'
);
$$;

revoke all on function public.prospective_decision_summary_v1(integer)
  from public, anon, authenticated;
grant execute on function public.prospective_decision_summary_v1(integer)
  to service_role;
