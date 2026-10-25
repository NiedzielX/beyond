-- P9 learner support-freeze gate v1.
-- Strengthens the order to:
-- 9/9 -> P9a target-free freeze -> target-free incumbent support freeze -> labels.

create table if not exists private.p9_learner_support_freeze_registry_v1 (
  cutoff_hours integer not null,
  p9a_manifest_sha256 text not null,
  support_manifest_sha256 text not null,
  support_version text not null,
  registered_at timestamptz not null default clock_timestamp(),
  support_frozen_targets integer not null,
  support_ready_targets integer not null,
  support_summary jsonb not null,
  github_sha text,
  production_change boolean not null default false,
  primary key (cutoff_hours, support_manifest_sha256),
  constraint p9_support_cutoff check (cutoff_hours in (24,48)),
  constraint p9_support_p9a_sha check (p9a_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_support_sha check (support_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_support_ready check (support_ready_targets >= 1),
  constraint p9_support_prod check (production_change=false)
);

create or replace function private.reject_p9_learner_support_freeze_mutation_v1()
returns trigger
language plpgsql
security definer
set search_path='public','private'
as $function$
begin
  raise exception 'P9_LEARNER_SUPPORT_FREEZE_REGISTRY_IMMUTABLE';
end;
$function$;

drop trigger if exists p9_learner_support_freeze_registry_immutable_v1 on private.p9_learner_support_freeze_registry_v1;
create trigger p9_learner_support_freeze_registry_immutable_v1
before update or delete on private.p9_learner_support_freeze_registry_v1
for each row execute function private.reject_p9_learner_support_freeze_mutation_v1();

create or replace function public.register_p9_learner_support_freeze_v1(p_freeze jsonb, p_github_sha text default null)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_cutoff integer;
  v_p9a_sha text;
  v_support_sha text;
  v_summary jsonb;
  v_frozen integer;
  v_ready integer;
  v_readiness jsonb;
  v_events integer;
  v_clubs integer;
begin
  if p_freeze is null or jsonb_typeof(p_freeze)<>'object' then raise exception 'P9_SUPPORT_FREEZE_OBJECT_REQUIRED'; end if;
  if p_freeze->>'version'<>'p9-learner-support-freeze-v1' then raise exception 'P9_SUPPORT_FREEZE_VERSION_REJECTED'; end if;
  if coalesce((p_freeze->>'attendance_values_opened')::boolean,true) then raise exception 'P9_SUPPORT_FREEZE_ATTENDANCE_OPENED'; end if;
  if coalesce((p_freeze->>'target_values_used')::boolean,true) then raise exception 'P9_SUPPORT_FREEZE_TARGET_VALUES_USED'; end if;
  if coalesce((p_freeze->>'model_training_performed')::boolean,true) then raise exception 'P9_SUPPORT_FREEZE_MODEL_TRAINING_ALREADY_PERFORMED'; end if;
  if coalesce((p_freeze->>'production_change')::boolean,true) then raise exception 'P9_SUPPORT_FREEZE_PRODUCTION_CHANGE_REJECTED'; end if;
  if p_freeze->>'precommit_id'<>'p9-knn-median-residual-k5-v1' then raise exception 'P9_SUPPORT_FREEZE_PRECOMMIT_MISMATCH'; end if;

  v_cutoff := (p_freeze->>'cutoff_hours')::integer;
  if v_cutoff not in (24,48) then raise exception 'P9_SUPPORT_FREEZE_CUTOFF_REJECTED'; end if;
  v_p9a_sha := p_freeze->>'p9a_manifest_sha256';
  v_support_sha := p_freeze->>'manifest_sha256';
  if v_p9a_sha is null or v_p9a_sha !~ '^[0-9a-f]{64}$' then raise exception 'P9_SUPPORT_FREEZE_P9A_SHA_REJECTED'; end if;
  if v_support_sha is null or v_support_sha !~ '^[0-9a-f]{64}$' then raise exception 'P9_SUPPORT_FREEZE_SHA_REJECTED'; end if;

  if not exists(
    select 1 from private.p9_learner_target_freeze_registry_v1 r
    where r.cutoff_hours=v_cutoff and r.manifest_sha256=v_p9a_sha
  ) then raise exception 'P9_SUPPORT_BASE_FREEZE_NOT_REGISTERED'; end if;

  v_readiness := public.p9_booking_curve_readiness_v1();
  v_events := coalesce((v_readiness#>>'{horizons,168.0,ready_events}')::integer,0);
  v_clubs := coalesce((v_readiness#>>'{horizons,168.0,ready_clubs}')::integer,0);
  if v_events < 9 or v_clubs < 3 then raise exception 'P9_LEARNER_GATE_CLOSED readiness_events=% readiness_clubs=%',v_events,v_clubs; end if;

  v_summary := coalesce(p_freeze->'summary','{}'::jsonb);
  v_frozen := coalesce((v_summary->>'support_frozen_targets')::integer,0);
  v_ready := coalesce((v_summary->>'support_ready_targets')::integer,0);
  if v_ready < 1 then raise exception 'P9_SUPPORT_FREEZE_HAS_NO_READY_TARGETS'; end if;

  insert into private.p9_learner_support_freeze_registry_v1(
    cutoff_hours,p9a_manifest_sha256,support_manifest_sha256,support_version,
    support_frozen_targets,support_ready_targets,support_summary,github_sha,production_change
  ) values(
    v_cutoff,v_p9a_sha,v_support_sha,p_freeze->>'version',v_frozen,v_ready,v_summary,nullif(trim(p_github_sha),''),false
  ) on conflict(cutoff_hours,support_manifest_sha256) do nothing;

  return jsonb_build_object(
    'version','p9-learner-support-freeze-registry-v1',
    'registered',true,
    'cutoff_hours',v_cutoff,
    'p9a_manifest_sha256',v_p9a_sha,
    'support_manifest_sha256',v_support_sha,
    'support_ready_targets',v_ready,
    'attendance_values_opened',false,
    'production_change',false
  );
end;
$function$;

-- Disable the weaker v1 label path. It is intentionally retained only to fail
-- closed for any stale caller.
create or replace function public.export_p9_learner_labels_v1(p_cutoff_hours integer, p_manifest_sha256 text)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
begin
  raise exception 'P9_LABEL_EXPORT_V1_DISABLED_USE_V2';
end;
$function$;

create or replace function public.export_p9_learner_labels_v2(
  p_cutoff_hours integer,
  p_p9a_manifest_sha256 text,
  p_support_manifest_sha256 text
)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_readiness jsonb;
  v_events integer;
  v_clubs integer;
begin
  if p_cutoff_hours not in (24,48) then raise exception 'P9_LABEL_EXPORT_CUTOFF_REJECTED'; end if;
  if p_p9a_manifest_sha256 is null or p_p9a_manifest_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'P9_LABEL_EXPORT_P9A_MANIFEST_REJECTED'; end if;
  if p_support_manifest_sha256 is null or p_support_manifest_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'P9_LABEL_EXPORT_SUPPORT_MANIFEST_REJECTED'; end if;

  v_readiness := public.p9_booking_curve_readiness_v1();
  v_events := coalesce((v_readiness#>>'{horizons,168.0,ready_events}')::integer,0);
  v_clubs := coalesce((v_readiness#>>'{horizons,168.0,ready_clubs}')::integer,0);
  if v_events < 9 or v_clubs < 3 then raise exception 'P9_LEARNER_GATE_CLOSED readiness_events=% readiness_clubs=%',v_events,v_clubs; end if;

  if not exists(
    select 1 from private.p9_learner_support_freeze_registry_v1 r
    where r.cutoff_hours=p_cutoff_hours
      and r.p9a_manifest_sha256=p_p9a_manifest_sha256
      and r.support_manifest_sha256=p_support_manifest_sha256
  ) then raise exception 'P9_TARGET_FREE_SUPPORT_FREEZE_NOT_REGISTERED'; end if;

  return (
    with event_rows as (
      select e.id as ticket_event_id,e.club_slug,e.home_team,e.away_team,e.kickoff_at,
             e.kickoff_at-make_interval(hours=>p_cutoff_hours) as analogous_cutoff_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at<now()
    ), outcome_rows as (
      select o.ticket_event_id,o.actual_attendance,o.attendance_definition,o.source_name,o.source_url,o.confirmed_at
      from public.ticket_event_outcomes o
      join event_rows e on e.ticket_event_id=o.ticket_event_id
      where o.actual_attendance is not null
        and o.confirmed_at is not null
        and o.confirmed_at>=e.kickoff_at
    ), structural as (
      select sp.id as row_id,sp.ticket_event_id,'structural_prior_forecasts_v1'::text as source,
             sp.target_as_of_at as as_of_at,sp.created_at as persisted_at,
             sp.p50::double precision as p50,sp.stadium_capacity,sp.model_spec_id,
             sp.point_in_time_validated
      from private.structural_prior_forecasts_v1 sp
      join event_rows e on e.ticket_event_id=sp.ticket_event_id
      where sp.point_in_time_validated
    ), long72 as (
      select d.id as row_id,d.ticket_event_id,'d2_long72_forward_predictions_v1'::text as source,
             d.as_of_at,d.created_at as persisted_at,d.anchor_p50::double precision as p50,
             d.stadium_capacity,d.package_id as model_spec_id,true as point_in_time_validated
      from private.d2_long72_forward_predictions_v1 d
      join event_rows e on e.ticket_event_id=d.ticket_event_id
    ), incumbents as (select * from structural union all select * from long72)
    select jsonb_build_object(
      'version','p9-learner-label-support-v2',
      'generated_at',now(),
      'cutoff_hours',p_cutoff_hours,
      'registered_p9a_manifest_sha256',p_p9a_manifest_sha256,
      'registered_support_manifest_sha256',p_support_manifest_sha256,
      'precommit_id','p9-knn-median-residual-k5-v1',
      'readiness_168_events',v_events,
      'readiness_168_clubs',v_clubs,
      'events',coalesce((select jsonb_agg(to_jsonb(e) order by e.kickoff_at,e.ticket_event_id) from event_rows e),'[]'::jsonb),
      'attendance',coalesce((select jsonb_agg(to_jsonb(o) order by o.ticket_event_id) from outcome_rows o),'[]'::jsonb),
      'incumbents',coalesce((select jsonb_agg(to_jsonb(i) order by i.ticket_event_id,i.source,i.as_of_at,i.persisted_at,i.row_id) from incumbents i),'[]'::jsonb),
      'target_free_support_freeze_registered',true,
      'production_activation_allowed',false,
      'live_adjustment',0,
      'production_change',false
    )
  );
end;
$function$;

revoke all on private.p9_learner_support_freeze_registry_v1 from public,anon,authenticated;
revoke all on function public.register_p9_learner_support_freeze_v1(jsonb,text) from public,anon,authenticated;
revoke all on function public.export_p9_learner_labels_v2(integer,text,text) from public,anon,authenticated;
grant execute on function public.register_p9_learner_support_freeze_v1(jsonb,text) to service_role;
grant execute on function public.export_p9_learner_labels_v2(integer,text,text) to service_role;
