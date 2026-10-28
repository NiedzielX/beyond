-- Dashboard-safe P9 family-fallback v2 observability.
--
-- Exposes only aggregate v2 evidence to the browser. The immutable private
-- attempt/prediction/score ledgers remain inaccessible to anon/authenticated.
-- v1 and v2 stay separately auditable and are never combined into one MAE.

create table if not exists public.dashboard_p9_fallback_v2_cache (
  cache_id smallint primary key check (cache_id = 1),
  generated_at timestamptz not null,
  fallback_attempt_events integer not null default 0,
  fallback_attempt_rows integer not null default 0,
  fallback_v1_covered_attempts integer not null default 0,
  fallback_ready_attempts integer not null default 0,
  fallback_support_insufficient_attempts integer not null default 0,
  fallback_prediction_events integer not null default 0,
  fallback_prediction_rows integer not null default 0,
  fallback_scored_events integer not null default 0,
  fallback_incumbent_event_balanced_mae numeric,
  fallback_challenger_event_balanced_mae numeric,
  fallback_delta_event_balanced_mae numeric,
  fallback_event_improvement_rate numeric,
  fallback_worst_event_degradation numeric,
  fallback_first_attempted_at timestamptz,
  fallback_last_attempted_at timestamptz,
  production_activation_allowed boolean not null default false,
  live_adjustment numeric not null default 0,
  production_change boolean not null default false
);

alter table public.dashboard_p9_fallback_v2_cache enable row level security;

drop policy if exists dashboard_p9_fallback_v2_cache_read
  on public.dashboard_p9_fallback_v2_cache;
create policy dashboard_p9_fallback_v2_cache_read
  on public.dashboard_p9_fallback_v2_cache
  for select
  to anon, authenticated
  using (true);

revoke all on table public.dashboard_p9_fallback_v2_cache from public;
grant select on table public.dashboard_p9_fallback_v2_cache to anon, authenticated;
grant select, insert, update, delete on table public.dashboard_p9_fallback_v2_cache to service_role;

create or replace function private.refresh_dashboard_p9_fallback_v2_cache()
returns trigger
language plpgsql
security definer
set search_path = 'public', 'private', 'pg_temp'
as $function$
declare
  j jsonb;
begin
  j := public.p9_booking_curve_prospective_fallback_summary_v2();

  insert into public.dashboard_p9_fallback_v2_cache(
    cache_id,
    generated_at,
    fallback_attempt_events,
    fallback_attempt_rows,
    fallback_v1_covered_attempts,
    fallback_ready_attempts,
    fallback_support_insufficient_attempts,
    fallback_prediction_events,
    fallback_prediction_rows,
    fallback_scored_events,
    fallback_incumbent_event_balanced_mae,
    fallback_challenger_event_balanced_mae,
    fallback_delta_event_balanced_mae,
    fallback_event_improvement_rate,
    fallback_worst_event_degradation,
    fallback_first_attempted_at,
    fallback_last_attempted_at,
    production_activation_allowed,
    live_adjustment,
    production_change
  ) values (
    1,
    now(),
    coalesce((j->>'attempt_events')::integer,0),
    coalesce((j->>'attempt_rows')::integer,0),
    coalesce((j->>'v1_covered_attempts')::integer,0),
    coalesce((j->>'fallback_ready_attempts')::integer,0),
    coalesce((j->>'fallback_support_insufficient_attempts')::integer,0),
    coalesce((j->>'prediction_events')::integer,0),
    coalesce((j->>'prediction_rows')::integer,0),
    coalesce((j->>'scored_events')::integer,0),
    nullif(j->>'incumbent_event_balanced_mae','')::numeric,
    nullif(j->>'challenger_event_balanced_mae','')::numeric,
    nullif(j->>'delta_event_balanced_mae','')::numeric,
    nullif(j->>'event_improvement_rate','')::numeric,
    nullif(j->>'worst_event_degradation','')::numeric,
    nullif(j->>'first_attempted_at','')::timestamptz,
    nullif(j->>'last_attempted_at','')::timestamptz,
    coalesce((j->>'production_activation_allowed')::boolean,false),
    coalesce((j->>'live_adjustment')::numeric,0),
    coalesce((j->>'production_change')::boolean,false)
  )
  on conflict (cache_id) do update set
    generated_at = excluded.generated_at,
    fallback_attempt_events = excluded.fallback_attempt_events,
    fallback_attempt_rows = excluded.fallback_attempt_rows,
    fallback_v1_covered_attempts = excluded.fallback_v1_covered_attempts,
    fallback_ready_attempts = excluded.fallback_ready_attempts,
    fallback_support_insufficient_attempts = excluded.fallback_support_insufficient_attempts,
    fallback_prediction_events = excluded.fallback_prediction_events,
    fallback_prediction_rows = excluded.fallback_prediction_rows,
    fallback_scored_events = excluded.fallback_scored_events,
    fallback_incumbent_event_balanced_mae = excluded.fallback_incumbent_event_balanced_mae,
    fallback_challenger_event_balanced_mae = excluded.fallback_challenger_event_balanced_mae,
    fallback_delta_event_balanced_mae = excluded.fallback_delta_event_balanced_mae,
    fallback_event_improvement_rate = excluded.fallback_event_improvement_rate,
    fallback_worst_event_degradation = excluded.fallback_worst_event_degradation,
    fallback_first_attempted_at = excluded.fallback_first_attempted_at,
    fallback_last_attempted_at = excluded.fallback_last_attempted_at,
    production_activation_allowed = excluded.production_activation_allowed,
    live_adjustment = excluded.live_adjustment,
    production_change = excluded.production_change;

  return new;
end;
$function$;

revoke all on function private.refresh_dashboard_p9_fallback_v2_cache()
  from public, anon, authenticated;

-- Seed the zero/current aggregate state once at migration time.
do $block$
declare
  j jsonb;
begin
  j := public.p9_booking_curve_prospective_fallback_summary_v2();
  insert into public.dashboard_p9_fallback_v2_cache(
    cache_id, generated_at,
    fallback_attempt_events, fallback_attempt_rows,
    fallback_v1_covered_attempts, fallback_ready_attempts,
    fallback_support_insufficient_attempts,
    fallback_prediction_events, fallback_prediction_rows, fallback_scored_events,
    fallback_incumbent_event_balanced_mae, fallback_challenger_event_balanced_mae,
    fallback_delta_event_balanced_mae, fallback_event_improvement_rate,
    fallback_worst_event_degradation,
    fallback_first_attempted_at, fallback_last_attempted_at,
    production_activation_allowed, live_adjustment, production_change
  ) values (
    1, now(),
    coalesce((j->>'attempt_events')::integer,0),
    coalesce((j->>'attempt_rows')::integer,0),
    coalesce((j->>'v1_covered_attempts')::integer,0),
    coalesce((j->>'fallback_ready_attempts')::integer,0),
    coalesce((j->>'fallback_support_insufficient_attempts')::integer,0),
    coalesce((j->>'prediction_events')::integer,0),
    coalesce((j->>'prediction_rows')::integer,0),
    coalesce((j->>'scored_events')::integer,0),
    nullif(j->>'incumbent_event_balanced_mae','')::numeric,
    nullif(j->>'challenger_event_balanced_mae','')::numeric,
    nullif(j->>'delta_event_balanced_mae','')::numeric,
    nullif(j->>'event_improvement_rate','')::numeric,
    nullif(j->>'worst_event_degradation','')::numeric,
    nullif(j->>'first_attempted_at','')::timestamptz,
    nullif(j->>'last_attempted_at','')::timestamptz,
    coalesce((j->>'production_activation_allowed')::boolean,false),
    coalesce((j->>'live_adjustment')::numeric,0),
    coalesce((j->>'production_change')::boolean,false)
  )
  on conflict (cache_id) do update set
    generated_at = excluded.generated_at,
    fallback_attempt_events = excluded.fallback_attempt_events,
    fallback_attempt_rows = excluded.fallback_attempt_rows,
    fallback_v1_covered_attempts = excluded.fallback_v1_covered_attempts,
    fallback_ready_attempts = excluded.fallback_ready_attempts,
    fallback_support_insufficient_attempts = excluded.fallback_support_insufficient_attempts,
    fallback_prediction_events = excluded.fallback_prediction_events,
    fallback_prediction_rows = excluded.fallback_prediction_rows,
    fallback_scored_events = excluded.fallback_scored_events,
    fallback_incumbent_event_balanced_mae = excluded.fallback_incumbent_event_balanced_mae,
    fallback_challenger_event_balanced_mae = excluded.fallback_challenger_event_balanced_mae,
    fallback_delta_event_balanced_mae = excluded.fallback_delta_event_balanced_mae,
    fallback_event_improvement_rate = excluded.fallback_event_improvement_rate,
    fallback_worst_event_degradation = excluded.fallback_worst_event_degradation,
    fallback_first_attempted_at = excluded.fallback_first_attempted_at,
    fallback_last_attempted_at = excluded.fallback_last_attempted_at,
    production_activation_allowed = excluded.production_activation_allowed,
    live_adjustment = excluded.live_adjustment,
    production_change = excluded.production_change;
end;
$block$;

drop trigger if exists p9_fallback_v2_attempt_dashboard_cache
  on private.p9_booking_curve_prospective_fallback_attempts_v2;
create trigger p9_fallback_v2_attempt_dashboard_cache
after insert on private.p9_booking_curve_prospective_fallback_attempts_v2
for each statement execute function private.refresh_dashboard_p9_fallback_v2_cache();

drop trigger if exists p9_fallback_v2_prediction_dashboard_cache
  on private.p9_booking_curve_prospective_fallback_predictions_v2;
create trigger p9_fallback_v2_prediction_dashboard_cache
after insert on private.p9_booking_curve_prospective_fallback_predictions_v2
for each statement execute function private.refresh_dashboard_p9_fallback_v2_cache();

drop trigger if exists p9_fallback_v2_score_dashboard_cache
  on private.p9_booking_curve_prospective_fallback_scores_v2;
create trigger p9_fallback_v2_score_dashboard_cache
after insert on private.p9_booking_curve_prospective_fallback_scores_v2
for each statement execute function private.refresh_dashboard_p9_fallback_v2_cache();

create or replace view public.dashboard_p9_mae_status_v1
with (security_invoker = true)
as
select
  c.generated_at,
  c.historical_t168_events,
  c.historical_t168_clubs,
  c.design_precommitted,
  c.full_window_gate_open,
  c.historical_status,
  c.historical_reason,
  c.historical_comparator_targets_t24 as historical_t24_comparator_targets,
  c.historical_support_ready_targets_t24 as historical_t24_support_ready_targets,
  c.historical_comparator_targets_t48 as historical_t48_comparator_targets,
  c.historical_support_ready_targets_t48 as historical_t48_support_ready_targets,
  c.historical_learner_result_produced as historical_result_produced,
  c.historical_attendance_values_opened,
  c.prospective_evidence_status,
  c.prospective_prediction_events,
  c.prospective_prediction_rows,
  c.prospective_scored_events,
  c.incumbent_event_balanced_mae::double precision as incumbent_event_balanced_mae,
  c.challenger_event_balanced_mae::double precision as challenger_event_balanced_mae,
  c.delta_event_balanced_mae::double precision as delta_event_balanced_mae,
  c.event_improvement_rate::double precision as event_improvement_rate,
  c.worst_event_degradation::double precision as worst_event_degradation,
  c.production_activation_allowed,
  c.live_adjustment::double precision as live_adjustment,
  c.production_change,
  a.prospective_attempt_events,
  a.prospective_attempt_rows,
  a.prospective_prediction_ready_attempts,
  a.prospective_support_insufficient_attempts,
  a.prospective_no_target_incumbent_attempts,
  a.prospective_last_attempted_at,
  f.fallback_attempt_events,
  f.fallback_attempt_rows,
  f.fallback_v1_covered_attempts,
  f.fallback_ready_attempts,
  f.fallback_support_insufficient_attempts,
  f.fallback_prediction_events,
  f.fallback_prediction_rows,
  f.fallback_scored_events,
  f.fallback_incumbent_event_balanced_mae::double precision as fallback_incumbent_event_balanced_mae,
  f.fallback_challenger_event_balanced_mae::double precision as fallback_challenger_event_balanced_mae,
  f.fallback_delta_event_balanced_mae::double precision as fallback_delta_event_balanced_mae,
  f.fallback_event_improvement_rate::double precision as fallback_event_improvement_rate,
  f.fallback_worst_event_degradation::double precision as fallback_worst_event_degradation,
  f.fallback_first_attempted_at,
  f.fallback_last_attempted_at
from public.dashboard_p9_mae_lifecycle_cache_v1 c
cross join public.dashboard_p9_attempt_status_cache_v1 a
cross join public.dashboard_p9_fallback_v2_cache f;

revoke all on public.dashboard_p9_mae_status_v1 from public;
grant select on public.dashboard_p9_mae_status_v1 to anon, authenticated;
