-- C1 v8 Prospective Shadow Dashboard Status v1
--
-- Sanitized read-only surfaces for operations/dashboard consumers.
-- Private prediction metadata and write paths remain private.

begin;

create or replace function public.get_c1_shadow_v8_status_v1()
returns table (
    status text,
    package_version text,
    live_model_id text,
    policy_id text,
    production_live_adjustment integer,
    prediction_row_count bigint,
    prospective_event_count bigint,
    scored_event_count bigint,
    latest_prediction_at timestamptz,
    latest_score_at timestamptz,
    latest_row_prior_mae numeric,
    latest_row_live_mae numeric,
    latest_row_policy_mae numeric,
    representative_window_prior_mae numeric,
    representative_window_live_mae numeric,
    representative_window_policy_mae numeric,
    validation_state text,
    refreshed_at timestamptz
)
language sql
stable
security definer
set search_path = public, private
as $function$
with latest_scores as (
    select distinct on (s.ticket_event_id,s.package_version)
        s.*
    from private.c1_shadow_v8_event_scores_v1 s
    where s.package_version='c1-shadow-v8-frozen-2026-10-16-n9'
    order by s.ticket_event_id,s.package_version,s.outcome_version_at desc,s.id desc
), prediction_summary as (
    select
        count(*) as prediction_row_count,
        count(distinct p.ticket_event_id) as prospective_event_count,
        max(p.as_of_at) as latest_prediction_at
    from private.c1_shadow_v8_predictions_v1 p
    where p.package_version='c1-shadow-v8-frozen-2026-10-16-n9'
), score_summary as (
    select
        count(*) as scored_event_count,
        max(scored_at) as latest_score_at,
        avg(latest_prior_error) as latest_row_prior_mae,
        avg(latest_live_error) as latest_row_live_mae,
        avg(latest_policy_error) as latest_row_policy_mae,
        avg(window_prior_mae) as representative_window_prior_mae,
        avg(window_live_mae) as representative_window_live_mae,
        avg(window_policy_mae) as representative_window_policy_mae
    from latest_scores
)
select
    'EXPERIMENTAL_SHADOW'::text,
    'c1-shadow-v8-frozen-2026-10-16-n9'::text,
    'c1-v2-live-ridge-directocc-compact-generic-a10'::text,
    'c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single'::text,
    0::integer,
    p.prediction_row_count,
    p.prospective_event_count,
    s.scored_event_count,
    p.latest_prediction_at,
    s.latest_score_at,
    s.latest_row_prior_mae,
    s.latest_row_live_mae,
    s.latest_row_policy_mae,
    s.representative_window_prior_mae,
    s.representative_window_live_mae,
    s.representative_window_policy_mae,
    case
        when s.scored_event_count >= 20 then 'PROMOTION_REVIEW_ELIGIBLE'
        when s.scored_event_count > 0 then 'COLLECTING_PROSPECTIVE_EVIDENCE'
        else 'AWAITING_FIRST_PROSPECTIVE_SCORE'
    end::text,
    now()
from prediction_summary p
cross join score_summary s;
$function$;

create or replace function public.get_c1_shadow_v8_events_v1()
returns table (
    ticket_event_id bigint,
    home_team text,
    away_team text,
    kickoff_at timestamptz,
    latest_as_of_at timestamptz,
    hours_to_kickoff numeric,
    structural_prior_p50 numeric,
    v2_live_p50 numeric,
    policy_prediction numeric,
    selected_expert text,
    reason_code text,
    abs_disagreement_occupancy numeric,
    live_observation_count_to_date integer,
    live_slope_occupancy_per_hour_to_date numeric,
    package_version text,
    outcome_available boolean,
    actual_attendance integer,
    latest_prior_error numeric,
    latest_live_error numeric,
    latest_policy_error numeric,
    window_prior_mae numeric,
    window_live_mae numeric,
    window_policy_mae numeric,
    scored_at timestamptz
)
language sql
stable
security definer
set search_path = public, private
as $function$
with latest_predictions as (
    select distinct on (p.ticket_event_id,p.package_version)
        p.*
    from private.c1_shadow_v8_predictions_v1 p
    where p.package_version='c1-shadow-v8-frozen-2026-10-16-n9'
    order by p.ticket_event_id,p.package_version,p.as_of_at desc,p.id desc
), latest_scores as (
    select distinct on (s.ticket_event_id,s.package_version)
        s.*
    from private.c1_shadow_v8_event_scores_v1 s
    where s.package_version='c1-shadow-v8-frozen-2026-10-16-n9'
    order by s.ticket_event_id,s.package_version,s.outcome_version_at desc,s.id desc
)
select
    p.ticket_event_id,
    e.home_team,
    e.away_team,
    p.kickoff_at,
    p.as_of_at,
    p.hours_to_kickoff,
    p.structural_prior_p50,
    p.v2_live_p50,
    p.policy_prediction,
    p.selected_expert,
    p.reason_code,
    p.abs_disagreement_occupancy,
    p.live_observation_count_to_date,
    p.live_slope_occupancy_per_hour_to_date,
    p.package_version,
    (s.id is not null),
    s.actual_attendance,
    s.latest_prior_error,
    s.latest_live_error,
    s.latest_policy_error,
    s.window_prior_mae,
    s.window_live_mae,
    s.window_policy_mae,
    s.scored_at
from latest_predictions p
join public.ticket_events e on e.id=p.ticket_event_id
left join latest_scores s
  on s.ticket_event_id=p.ticket_event_id
 and s.package_version=p.package_version
order by p.kickoff_at,p.ticket_event_id;
$function$;

revoke all on function public.get_c1_shadow_v8_status_v1() from public;
revoke all on function public.get_c1_shadow_v8_events_v1() from public;
grant execute on function public.get_c1_shadow_v8_status_v1() to anon, authenticated, service_role;
grant execute on function public.get_c1_shadow_v8_events_v1() to anon, authenticated, service_role;

create or replace view public.dashboard_c1_shadow_v8_status_v1
with (security_invoker=true)
as
select * from public.get_c1_shadow_v8_status_v1();

create or replace view public.dashboard_c1_shadow_v8_events_v1
with (security_invoker=true)
as
select * from public.get_c1_shadow_v8_events_v1();

revoke all on public.dashboard_c1_shadow_v8_status_v1 from public;
revoke all on public.dashboard_c1_shadow_v8_events_v1 from public;
grant select on public.dashboard_c1_shadow_v8_status_v1 to anon, authenticated, service_role;
grant select on public.dashboard_c1_shadow_v8_events_v1 to anon, authenticated, service_role;

comment on view public.dashboard_c1_shadow_v8_status_v1 is
'Sanitized read-only status for frozen C1 v8 prospective validation. No production activation.';
comment on view public.dashboard_c1_shadow_v8_events_v1 is
'Sanitized latest event-level prospective C1 v8 shadow evidence and post-outcome score, when available.';

commit;
