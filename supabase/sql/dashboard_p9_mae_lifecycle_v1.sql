-- Dashboard-safe P9 MAE lifecycle contract.
--
-- Purpose:
-- - expose only aggregate P9 research status to the browser;
-- - keep private research tables/functions inaccessible to anon/authenticated;
-- - make prospective event-balanced MAE the canonical model-result surface;
-- - preserve legacy dashboard_p9_mae_status_v1 consumers without SECURITY DEFINER views.
--
-- The cache is refreshed by the existing service-role-only dashboard safe-cache job.
-- Production activation remains explicitly blocked by the underlying P9 contracts.

create table if not exists public.dashboard_p9_mae_lifecycle_cache_v1 (
  cache_id smallint primary key check (cache_id = 1),
  version text not null,
  generated_at timestamptz not null,
  historical_t168_events integer not null default 0,
  historical_t168_clubs integer not null default 0,
  design_precommitted boolean not null default false,
  full_window_gate_open boolean not null default false,
  historical_status text,
  historical_reason text,
  historical_comparator_targets_t24 integer not null default 0,
  historical_support_ready_targets_t24 integer not null default 0,
  historical_comparator_targets_t48 integer not null default 0,
  historical_support_ready_targets_t48 integer not null default 0,
  historical_attendance_values_opened boolean not null default false,
  historical_learner_result_produced boolean not null default false,
  prospective_prediction_events integer not null default 0,
  prospective_prediction_rows integer not null default 0,
  prospective_scored_events integer not null default 0,
  prospective_evidence_status text,
  incumbent_event_balanced_mae numeric,
  challenger_event_balanced_mae numeric,
  delta_event_balanced_mae numeric,
  event_improvement_rate numeric,
  worst_event_degradation numeric,
  production_activation_allowed boolean not null default false,
  live_adjustment numeric not null default 0,
  production_change boolean not null default false
);

-- Forward-compatible upgrades if the cache was created by an earlier iteration.
alter table public.dashboard_p9_mae_lifecycle_cache_v1
  add column if not exists historical_t168_events integer not null default 0,
  add column if not exists historical_t168_clubs integer not null default 0,
  add column if not exists design_precommitted boolean not null default false,
  add column if not exists full_window_gate_open boolean not null default false,
  add column if not exists historical_reason text;

alter table public.dashboard_p9_mae_lifecycle_cache_v1 enable row level security;

drop policy if exists dashboard_p9_mae_lifecycle_cache_read_v1
  on public.dashboard_p9_mae_lifecycle_cache_v1;
create policy dashboard_p9_mae_lifecycle_cache_read_v1
  on public.dashboard_p9_mae_lifecycle_cache_v1
  for select
  to anon, authenticated
  using (true);

revoke all on table public.dashboard_p9_mae_lifecycle_cache_v1 from public;
grant select on table public.dashboard_p9_mae_lifecycle_cache_v1 to anon, authenticated;
grant select, insert, update, delete on table public.dashboard_p9_mae_lifecycle_cache_v1 to service_role;

create or replace view public.dashboard_p9_mae_lifecycle_v1
with (security_invoker = true)
as
select
  version,
  generated_at,
  historical_status,
  historical_comparator_targets_t24,
  historical_support_ready_targets_t24,
  historical_comparator_targets_t48,
  historical_support_ready_targets_t48,
  historical_attendance_values_opened,
  historical_learner_result_produced,
  prospective_prediction_events,
  prospective_prediction_rows,
  prospective_scored_events,
  prospective_evidence_status,
  incumbent_event_balanced_mae,
  challenger_event_balanced_mae,
  delta_event_balanced_mae,
  event_improvement_rate,
  worst_event_degradation,
  production_activation_allowed,
  live_adjustment,
  production_change
from public.dashboard_p9_mae_lifecycle_cache_v1;

revoke all on public.dashboard_p9_mae_lifecycle_v1 from public;
grant select on public.dashboard_p9_mae_lifecycle_v1 to anon, authenticated;

-- Replace the older P9 status projection with a cache-only, security-invoker view.
-- Drop/recreate is deliberate because the prior view exposed some floating-point
-- columns as double precision while the cache stores numeric values.
drop view if exists public.dashboard_p9_mae_status_v1;
create view public.dashboard_p9_mae_status_v1
with (security_invoker = true)
as
select
  generated_at,
  historical_t168_events,
  historical_t168_clubs,
  design_precommitted,
  full_window_gate_open,
  historical_status,
  historical_reason,
  historical_comparator_targets_t24 as historical_t24_comparator_targets,
  historical_support_ready_targets_t24 as historical_t24_support_ready_targets,
  historical_comparator_targets_t48 as historical_t48_comparator_targets,
  historical_support_ready_targets_t48 as historical_t48_support_ready_targets,
  historical_learner_result_produced as historical_result_produced,
  historical_attendance_values_opened,
  prospective_evidence_status,
  prospective_prediction_events,
  prospective_prediction_rows,
  prospective_scored_events,
  incumbent_event_balanced_mae::double precision as incumbent_event_balanced_mae,
  challenger_event_balanced_mae::double precision as challenger_event_balanced_mae,
  delta_event_balanced_mae::double precision as delta_event_balanced_mae,
  event_improvement_rate::double precision as event_improvement_rate,
  worst_event_degradation::double precision as worst_event_degradation,
  production_activation_allowed,
  live_adjustment::double precision as live_adjustment,
  production_change
from public.dashboard_p9_mae_lifecycle_cache_v1;

revoke all on public.dashboard_p9_mae_status_v1 from public;
grant select on public.dashboard_p9_mae_status_v1 to anon, authenticated;

-- The browser must not call the private-reading prospective summary RPC directly.
revoke execute on function public.p9_booking_curve_prospective_summary_v1()
  from public, anon, authenticated;

-- Extend the existing safe-cache refresh. The scheduled refresh runs as the
-- database owner/service context; anon/authenticated receive only cache rows.
create or replace function public.refresh_dashboard_safe_caches_v1()
returns integer
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_rows integer := 0;
  v_n integer;
begin
  delete from public.dashboard_event_live_state_cache_v1;
  insert into public.dashboard_event_live_state_cache_v1
  select * from public.get_dashboard_event_live_state_safe_v1();
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  delete from public.dashboard_ml_readiness_cache_v1;
  insert into public.dashboard_ml_readiness_cache_v1(
    independent_outcome_events, clubs_with_outcome, strict_study_rows, models_with_strict_rows,
    cross_club_gate_met, learned_correction_gate_met, status, cross_club_event_target,
    cross_club_club_target, learned_correction_event_target, generated_at
  )
  select * from public.get_dashboard_ml_readiness_safe_v1();
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  delete from public.dashboard_research_readiness_cache_v2;
  insert into public.dashboard_research_readiness_cache_v2(
    crossclub_study_events, crossclub_study_clubs, strict_study_rows, crossclub_gate_met,
    crossclub_event_target, crossclub_club_target, independent_outcome_events_total, outcome_clubs_total,
    learned_correction_gate_met, learned_correction_event_target, generated_at
  )
  select * from public.get_dashboard_research_readiness_v2();
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  delete from public.dashboard_weather_latest_cache_v1;
  insert into public.dashboard_weather_latest_cache_v1
  select * from public.get_dashboard_weather_latest_safe_v1();
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  delete from public.dashboard_weather_research_cache_v1;
  insert into public.dashboard_weather_research_cache_v1(
    historical_study_version, historical_sample_size, historical_seasons, baseline_mae,
    loocv_weather_mae, loocv_uplift, loso_weather_mae, loso_uplift, historical_signal_status,
    prospective_weather_events, prospective_weather_rows, prospective_t24_outcome_pairs, generated_at
  )
  select * from public.get_dashboard_weather_research_v1();
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  delete from public.dashboard_p9_mae_lifecycle_cache_v1;
  insert into public.dashboard_p9_mae_lifecycle_cache_v1(
    cache_id, version, generated_at,
    historical_t168_events, historical_t168_clubs, design_precommitted, full_window_gate_open,
    historical_status, historical_reason,
    historical_comparator_targets_t24, historical_support_ready_targets_t24,
    historical_comparator_targets_t48, historical_support_ready_targets_t48,
    historical_attendance_values_opened, historical_learner_result_produced,
    prospective_prediction_events, prospective_prediction_rows, prospective_scored_events,
    prospective_evidence_status, incumbent_event_balanced_mae, challenger_event_balanced_mae,
    delta_event_balanced_mae, event_improvement_rate, worst_event_degradation,
    production_activation_allowed, live_adjustment, production_change
  )
  with
    g as (select public.p9_learner_gate_status_v1() as j),
    h as (select public.p9_historical_cohort_status_v1() as j),
    p as (select public.p9_booking_curve_prospective_summary_v1() as j)
  select
    1,
    'dashboard-p9-mae-lifecycle-v1',
    now(),
    coalesce((g.j->>'readiness_168_events')::int, 0),
    coalesce((g.j->>'readiness_168_clubs')::int, 0),
    coalesce((g.j->>'design_precommitted')::boolean, false),
    coalesce((g.j->>'full_window_gate_open')::boolean, false),
    h.j->>'status',
    h.j->>'reason',
    coalesce((h.j->>'comparator_targets_t24')::int, 0),
    coalesce((h.j->>'support_ready_targets_t24')::int, 0),
    coalesce((h.j->>'comparator_targets_t48')::int, 0),
    coalesce((h.j->>'support_ready_targets_t48')::int, 0),
    coalesce((h.j->>'attendance_values_opened')::boolean, false),
    coalesce((h.j->>'learner_result_produced')::boolean, false),
    coalesce((p.j->>'prediction_events')::int, 0),
    coalesce((p.j->>'prediction_rows')::int, 0),
    coalesce((p.j->>'scored_events')::int, 0),
    p.j->>'evidence_status',
    nullif(p.j->>'incumbent_event_balanced_mae', '')::numeric,
    nullif(p.j->>'challenger_event_balanced_mae', '')::numeric,
    nullif(p.j->>'delta_event_balanced_mae', '')::numeric,
    nullif(p.j->>'event_improvement_rate', '')::numeric,
    nullif(p.j->>'worst_event_degradation', '')::numeric,
    coalesce((p.j->>'production_activation_allowed')::boolean, false),
    coalesce((p.j->>'live_adjustment')::numeric, 0),
    coalesce((p.j->>'production_change')::boolean, false)
  from g cross join h cross join p;
  get diagnostics v_n = row_count;
  v_rows := v_rows + v_n;

  return v_rows;
end;
$function$;

revoke all on function public.refresh_dashboard_safe_caches_v1()
  from public, anon, authenticated;
grant execute on function public.refresh_dashboard_safe_caches_v1()
  to service_role;
