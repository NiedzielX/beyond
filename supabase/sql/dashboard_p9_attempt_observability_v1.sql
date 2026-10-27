-- Dashboard-safe P9 prospective attempt observability v1.
--
-- Purpose:
-- - distinguish "no immutable window has run yet" from a captured window that
--   correctly failed closed because PIT support was insufficient;
-- - expose only aggregate attempt evidence to anon/authenticated clients;
-- - keep the private immutable attempt registry inaccessible to the browser;
-- - avoid changing the frozen P9 learner, thresholds, predictions or production state.

create table if not exists public.dashboard_p9_attempt_status_cache_v1 (
  cache_id smallint primary key check (cache_id = 1),
  generated_at timestamptz not null,
  prospective_attempt_events integer not null default 0,
  prospective_attempt_rows integer not null default 0,
  prospective_prediction_ready_attempts integer not null default 0,
  prospective_support_insufficient_attempts integer not null default 0,
  prospective_no_target_incumbent_attempts integer not null default 0,
  prospective_last_attempted_at timestamptz
);

alter table public.dashboard_p9_attempt_status_cache_v1 enable row level security;

drop policy if exists dashboard_p9_attempt_status_cache_read_v1
  on public.dashboard_p9_attempt_status_cache_v1;
create policy dashboard_p9_attempt_status_cache_read_v1
  on public.dashboard_p9_attempt_status_cache_v1
  for select
  to anon, authenticated
  using (true);

revoke all on table public.dashboard_p9_attempt_status_cache_v1 from public;
grant select on table public.dashboard_p9_attempt_status_cache_v1 to anon, authenticated;
grant select, insert, update, delete on table public.dashboard_p9_attempt_status_cache_v1 to service_role;

insert into public.dashboard_p9_attempt_status_cache_v1(
  cache_id,
  generated_at,
  prospective_attempt_events,
  prospective_attempt_rows,
  prospective_prediction_ready_attempts,
  prospective_support_insufficient_attempts,
  prospective_no_target_incumbent_attempts,
  prospective_last_attempted_at
)
select
  1,
  now(),
  count(distinct ticket_event_id)::integer,
  count(*)::integer,
  count(*) filter (where status = 'PREDICTION_READY')::integer,
  count(*) filter (where status = 'PIT_SUPPORT_INSUFFICIENT')::integer,
  count(*) filter (where status = 'NO_TARGET_INCUMBENT')::integer,
  max(attempted_at)
from private.p9_booking_curve_prospective_attempts_v1
on conflict (cache_id) do update set
  generated_at = excluded.generated_at,
  prospective_attempt_events = excluded.prospective_attempt_events,
  prospective_attempt_rows = excluded.prospective_attempt_rows,
  prospective_prediction_ready_attempts = excluded.prospective_prediction_ready_attempts,
  prospective_support_insufficient_attempts = excluded.prospective_support_insufficient_attempts,
  prospective_no_target_incumbent_attempts = excluded.prospective_no_target_incumbent_attempts,
  prospective_last_attempted_at = excluded.prospective_last_attempted_at;

create or replace function private.refresh_dashboard_p9_attempt_status_cache_v1()
returns trigger
language plpgsql
security definer
set search_path = 'public', 'private', 'pg_temp'
as $function$
begin
  insert into public.dashboard_p9_attempt_status_cache_v1(
    cache_id,
    generated_at,
    prospective_attempt_events,
    prospective_attempt_rows,
    prospective_prediction_ready_attempts,
    prospective_support_insufficient_attempts,
    prospective_no_target_incumbent_attempts,
    prospective_last_attempted_at
  )
  select
    1,
    now(),
    count(distinct ticket_event_id)::integer,
    count(*)::integer,
    count(*) filter (where status = 'PREDICTION_READY')::integer,
    count(*) filter (where status = 'PIT_SUPPORT_INSUFFICIENT')::integer,
    count(*) filter (where status = 'NO_TARGET_INCUMBENT')::integer,
    max(attempted_at)
  from private.p9_booking_curve_prospective_attempts_v1
  on conflict (cache_id) do update set
    generated_at = excluded.generated_at,
    prospective_attempt_events = excluded.prospective_attempt_events,
    prospective_attempt_rows = excluded.prospective_attempt_rows,
    prospective_prediction_ready_attempts = excluded.prospective_prediction_ready_attempts,
    prospective_support_insufficient_attempts = excluded.prospective_support_insufficient_attempts,
    prospective_no_target_incumbent_attempts = excluded.prospective_no_target_incumbent_attempts,
    prospective_last_attempted_at = excluded.prospective_last_attempted_at;

  return new;
end;
$function$;

revoke all on function private.refresh_dashboard_p9_attempt_status_cache_v1() from public, anon, authenticated;

drop trigger if exists p9_prospective_attempt_dashboard_cache_v1
  on private.p9_booking_curve_prospective_attempts_v1;
create trigger p9_prospective_attempt_dashboard_cache_v1
after insert on private.p9_booking_curve_prospective_attempts_v1
for each statement execute function private.refresh_dashboard_p9_attempt_status_cache_v1();

-- Preserve the existing lifecycle/status contract and append aggregate attempt
-- observability. security_invoker remains enabled; browser roles only see the
-- two public cache tables, never the private attempt registry.
create or replace view public.dashboard_p9_mae_lifecycle_v1
with (security_invoker = true)
as
select
  c.version,
  c.generated_at,
  c.historical_status,
  c.historical_comparator_targets_t24,
  c.historical_support_ready_targets_t24,
  c.historical_comparator_targets_t48,
  c.historical_support_ready_targets_t48,
  c.historical_attendance_values_opened,
  c.historical_learner_result_produced,
  c.prospective_prediction_events,
  c.prospective_prediction_rows,
  c.prospective_scored_events,
  c.prospective_evidence_status,
  c.incumbent_event_balanced_mae,
  c.challenger_event_balanced_mae,
  c.delta_event_balanced_mae,
  c.event_improvement_rate,
  c.worst_event_degradation,
  c.production_activation_allowed,
  c.live_adjustment,
  c.production_change,
  a.prospective_attempt_events,
  a.prospective_attempt_rows,
  a.prospective_prediction_ready_attempts,
  a.prospective_support_insufficient_attempts,
  a.prospective_no_target_incumbent_attempts,
  a.prospective_last_attempted_at
from public.dashboard_p9_mae_lifecycle_cache_v1 c
cross join public.dashboard_p9_attempt_status_cache_v1 a;

revoke all on public.dashboard_p9_mae_lifecycle_v1 from public;
grant select on public.dashboard_p9_mae_lifecycle_v1 to anon, authenticated;

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
  a.prospective_last_attempted_at
from public.dashboard_p9_mae_lifecycle_cache_v1 c
cross join public.dashboard_p9_attempt_status_cache_v1 a;

revoke all on public.dashboard_p9_mae_status_v1 from public;
grant select on public.dashboard_p9_mae_status_v1 to anon, authenticated;
