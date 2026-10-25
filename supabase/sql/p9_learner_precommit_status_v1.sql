-- Machine-readable P9 learner precommit state.
-- This records the scientific design freeze independently of the later
-- target-free identity freeze, which remains blocked until 9/9.

create table if not exists private.p9_learner_precommit_registry_v1 (
  precommit_id text primary key,
  frozen_at timestamptz not null,
  github_commit_sha text not null,
  design_path text not null,
  cutoff_hours integer[] not null,
  fixed_neighbor_k integer not null,
  minimum_residual_neighbors integer not null,
  learner_family text not null,
  production_activation_allowed boolean not null default false,
  live_adjustment numeric not null default 0,
  production_change boolean not null default false,
  constraint p9_precommit_sha check (github_commit_sha ~ '^[0-9a-f]{40}$'),
  constraint p9_precommit_cutoffs check (cutoff_hours = array[48,24]::integer[]),
  constraint p9_precommit_k check (fixed_neighbor_k=5),
  constraint p9_precommit_min_residual check (minimum_residual_neighbors=3),
  constraint p9_precommit_prod check (production_activation_allowed=false and live_adjustment=0 and production_change=false)
);

insert into private.p9_learner_precommit_registry_v1(
  precommit_id,frozen_at,github_commit_sha,design_path,cutoff_hours,
  fixed_neighbor_k,minimum_residual_neighbors,learner_family,
  production_activation_allowed,live_adjustment,production_change
) values (
  'p9-knn-median-residual-k5-v1',
  '2026-10-25T19:10:00Z'::timestamptz,
  'a611b1730579dc53c5c9ac713506fd0d0b3428d6',
  'ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md',
  array[48,24]::integer[],5,3,'nonparametric_curve_analogue_median_residual',
  false,0,false
)
on conflict(precommit_id) do nothing;

create or replace function private.reject_p9_learner_precommit_mutation_v1()
returns trigger
language plpgsql
security definer
set search_path='public','private'
as $function$
begin
  raise exception 'P9_LEARNER_PRECOMMIT_IMMUTABLE';
end;
$function$;

drop trigger if exists p9_learner_precommit_registry_immutable_v1 on private.p9_learner_precommit_registry_v1;
create trigger p9_learner_precommit_registry_immutable_v1
before update or delete on private.p9_learner_precommit_registry_v1
for each row execute function private.reject_p9_learner_precommit_mutation_v1();

create or replace function public.p9_learner_gate_status_v1()
returns jsonb
language sql
stable
security invoker
set search_path='public','private'
as $function$
with readiness as (
  select public.p9_booking_curve_readiness_v1() as r
), p as (
  select * from private.p9_learner_precommit_registry_v1
  where precommit_id='p9-knn-median-residual-k5-v1'
), f as (
  select count(*)::integer as registered_target_free_manifests
  from private.p9_learner_target_freeze_registry_v1
)
select jsonb_build_object(
  'version','p9-learner-gate-status-v1',
  'precommit_id',(select precommit_id from p),
  'design_precommitted',exists(select 1 from p),
  'precommit_github_sha',(select github_commit_sha from p),
  'cutoff_hours',(select to_jsonb(cutoff_hours) from p),
  'fixed_neighbor_k',(select fixed_neighbor_k from p),
  'minimum_residual_neighbors',(select minimum_residual_neighbors from p),
  'readiness_168_events',coalesce(((select r from readiness)#>>'{horizons,168.0,ready_events}')::integer,0),
  'readiness_168_clubs',coalesce(((select r from readiness)#>>'{horizons,168.0,ready_clubs}')::integer,0),
  'full_window_gate_open',(
    coalesce(((select r from readiness)#>>'{horizons,168.0,ready_events}')::integer,0)>=9
    and coalesce(((select r from readiness)#>>'{horizons,168.0,ready_clubs}')::integer,0)>=3
  ),
  'registered_target_free_manifests',(select registered_target_free_manifests from f),
  'labels_export_allowed',(
    coalesce(((select r from readiness)#>>'{horizons,168.0,ready_events}')::integer,0)>=9
    and coalesce(((select r from readiness)#>>'{horizons,168.0,ready_clubs}')::integer,0)>=3
    and (select registered_target_free_manifests from f)>0
  ),
  'model_results_opened',false,
  'production_activation_allowed',false,
  'live_adjustment',0,
  'production_change',false
);
$function$;

revoke all on private.p9_learner_precommit_registry_v1 from public,anon,authenticated;
grant select on private.p9_learner_precommit_registry_v1 to service_role;
grant execute on function public.p9_learner_gate_status_v1() to service_role;
