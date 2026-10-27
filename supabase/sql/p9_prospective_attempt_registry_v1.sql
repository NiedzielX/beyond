-- P9 prospective immutable attempt registry v1.
-- Records whether a genuine frozen T-48/T-24 window was evaluated even when
-- the precommitted learner correctly emits no prediction because PIT support
-- is insufficient. This is evidence/observability only: no learner logic,
-- production forecast or live adjustment is changed.

create table if not exists private.p9_booking_curve_prospective_attempts_v1 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  target_as_of_at timestamptz not null,
  attempted_at timestamptz not null default clock_timestamp(),
  status text not null,
  target_incumbent_source_family text,
  selected_neighbor_event_ids bigint[] not null default '{}'::bigint[],
  residual_reference_count integer,
  missing_reference_rows jsonb not null default '[]'::jsonb,
  p9a_manifest_sha256 text not null,
  support_manifest_sha256 text,
  reference_outcomes_sha256 text not null,
  source_version text not null,
  precommit_id text not null,
  github_sha text,
  production_change boolean not null default false,
  constraint p9_prospective_attempt_cutoff check (cutoff_hours in (24,48)),
  constraint p9_prospective_attempt_status check (status in ('PREDICTION_READY','PIT_SUPPORT_INSUFFICIENT','NO_TARGET_INCUMBENT')),
  constraint p9_prospective_attempt_time check (
    attempted_at >= target_as_of_at
    and attempted_at <= target_as_of_at + interval '90 minutes'
  ),
  constraint p9_prospective_attempt_residual_count check (residual_reference_count is null or residual_reference_count >= 0),
  constraint p9_prospective_attempt_p9a_sha check (p9a_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_attempt_support_sha check (support_manifest_sha256 is null or support_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_attempt_outcomes_sha check (reference_outcomes_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_attempt_prod check (production_change=false),
  unique(ticket_event_id,cutoff_hours)
);

create index if not exists p9_booking_curve_prospective_attempts_v1_attempted_at_idx
  on private.p9_booking_curve_prospective_attempts_v1(attempted_at desc);

create index if not exists p9_booking_curve_prospective_attempts_v1_status_idx
  on private.p9_booking_curve_prospective_attempts_v1(status,cutoff_hours);

drop trigger if exists p9_prospective_attempts_immutable_v1 on private.p9_booking_curve_prospective_attempts_v1;
create trigger p9_prospective_attempts_immutable_v1
before update or delete on private.p9_booking_curve_prospective_attempts_v1
for each row execute function private.reject_p9_prospective_mutation_v1();

create or replace function public.record_p9_booking_curve_prospective_attempt_v1(
  p_payload jsonb,
  p_github_sha text default null
)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_diag jsonb;
  v_event public.ticket_events%rowtype;
  v_cutoff integer;
  v_status text;
  v_target_as_of timestamptz;
  v_now timestamptz:=clock_timestamp();
  v_prediction_count integer;
  v_residual_count integer;
  v_selected_neighbors bigint[];
  v_inserted integer:=0;
  v_seen integer:=0;
begin
  if p_payload is null or jsonb_typeof(p_payload)<>'object' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_PAYLOAD_REQUIRED';
  end if;
  if p_payload->>'version'<>'p9-booking-curve-prospective-builder-v1' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_VERSION_MISMATCH';
  end if;
  if p_payload->>'precommit_id'<>'p9-knn-median-residual-k5-v1' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_PRECOMMIT_MISMATCH';
  end if;
  if coalesce((p_payload->>'target_values_used')::boolean,true) then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_TARGET_VALUES_USED';
  end if;
  if coalesce((p_payload->>'production_activation_allowed')::boolean,true) then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_PRODUCTION_ACTIVATION_REJECTED';
  end if;
  if coalesce((p_payload->>'live_adjustment')::numeric,1)<>0 then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_LIVE_ADJUSTMENT_REJECTED';
  end if;
  if coalesce((p_payload->>'production_change')::boolean,true) then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_PRODUCTION_CHANGE_REJECTED';
  end if;
  if lower(p_payload::text) ~ '"(actual_attendance|target_attendance|target_outcome)"\s*:' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_TARGET_KEY_REJECTED';
  end if;
  if coalesce(p_payload->>'p9a_manifest_sha256','') !~ '^[0-9a-f]{64}$' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_P9A_SHA_REJECTED';
  end if;
  if coalesce(p_payload->>'reference_outcomes_sha256','') !~ '^[0-9a-f]{64}$' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_OUTCOMES_SHA_REJECTED';
  end if;
  if jsonb_typeof(p_payload->'diagnostics')<>'array' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_DIAGNOSTICS_ARRAY_REQUIRED';
  end if;
  if jsonb_typeof(p_payload->'predictions')<>'array' then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_PREDICTIONS_ARRAY_REQUIRED';
  end if;

  v_cutoff:=(p_payload->>'cutoff_hours')::integer;
  if v_cutoff not in (24,48) then
    raise exception 'P9_PROSPECTIVE_ATTEMPT_CUTOFF_REJECTED';
  end if;

  for v_diag in select value from jsonb_array_elements(p_payload->'diagnostics') loop
    v_seen:=v_seen+1;
    if coalesce((v_diag->>'cutoff_hours')::integer,-1)<>v_cutoff then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_DIAGNOSTIC_CUTOFF_MISMATCH';
    end if;

    select * into v_event
    from public.ticket_events
    where id=(v_diag->>'ticket_event_id')::bigint;
    if not found then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_EVENT_NOT_FOUND';
    end if;
    if private.normalize_structural_prior_competition_v1(v_event.competition)<>'Ekstraklasa' then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_COMPETITION_REJECTED';
    end if;

    v_target_as_of:=v_event.kickoff_at-make_interval(hours=>v_cutoff);
    if v_now<v_target_as_of or v_now>v_target_as_of+interval '90 minutes' then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_OUTSIDE_IMMUTABLE_WINDOW event=% cutoff=%',v_event.id,v_cutoff;
    end if;
    if exists(
      select 1 from public.ticket_event_outcomes o
      where o.ticket_event_id=v_event.id and o.actual_attendance is not null
    ) then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_TARGET_OUTCOME_ALREADY_PRESENT event=%',v_event.id;
    end if;

    v_status:=v_diag->>'status';
    if v_status not in ('PREDICTION_READY','PIT_SUPPORT_INSUFFICIENT','NO_TARGET_INCUMBENT') then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_STATUS_REJECTED';
    end if;

    select count(*)::integer into v_prediction_count
    from jsonb_array_elements(p_payload->'predictions') p
    where (p->>'ticket_event_id')::bigint=v_event.id
      and (p->>'cutoff_hours')::integer=v_cutoff;

    if v_status='PREDICTION_READY' and v_prediction_count<>1 then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_READY_WITHOUT_SINGLE_PREDICTION event=%',v_event.id;
    end if;
    if v_status<>'PREDICTION_READY' and v_prediction_count<>0 then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_NONREADY_WITH_PREDICTION event=%',v_event.id;
    end if;

    v_residual_count:=case
      when v_diag ? 'residual_reference_count' then (v_diag->>'residual_reference_count')::integer
      else null
    end;
    if v_status='PREDICTION_READY' and coalesce(v_residual_count,0)<3 then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_READY_SUPPORT_REJECTED event=%',v_event.id;
    end if;
    if v_status='PIT_SUPPORT_INSUFFICIENT' and (v_residual_count is null or v_residual_count>=3) then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_INSUFFICIENT_SUPPORT_REJECTED event=%',v_event.id;
    end if;
    if v_status='NO_TARGET_INCUMBENT' and v_residual_count is not null then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_NO_INCUMBENT_RESIDUAL_REJECTED event=%',v_event.id;
    end if;

    if v_diag ? 'support_manifest_sha256'
       and coalesce(v_diag->>'support_manifest_sha256','') !~ '^[0-9a-f]{64}$' then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_SUPPORT_SHA_REJECTED event=%',v_event.id;
    end if;
    if v_status in ('PREDICTION_READY','PIT_SUPPORT_INSUFFICIENT')
       and not (v_diag ? 'support_manifest_sha256') then
      raise exception 'P9_PROSPECTIVE_ATTEMPT_SUPPORT_SHA_REQUIRED event=%',v_event.id;
    end if;

    v_selected_neighbors:=coalesce(
      array(
        select value::bigint
        from jsonb_array_elements_text(coalesce(v_diag->'selected_neighbor_event_ids','[]'::jsonb))
      ),
      '{}'::bigint[]
    );

    insert into private.p9_booking_curve_prospective_attempts_v1(
      ticket_event_id,cutoff_hours,target_as_of_at,attempted_at,status,
      target_incumbent_source_family,selected_neighbor_event_ids,
      residual_reference_count,missing_reference_rows,p9a_manifest_sha256,
      support_manifest_sha256,reference_outcomes_sha256,source_version,
      precommit_id,github_sha,production_change
    ) values (
      v_event.id,v_cutoff,v_target_as_of,v_now,v_status,
      nullif(v_diag->>'target_incumbent_source_family',''),v_selected_neighbors,
      v_residual_count,coalesce(v_diag->'missing_reference_rows','[]'::jsonb),
      p_payload->>'p9a_manifest_sha256',nullif(v_diag->>'support_manifest_sha256',''),
      p_payload->>'reference_outcomes_sha256',p_payload->>'version',
      p_payload->>'precommit_id',nullif(p_github_sha,''),false
    )
    on conflict(ticket_event_id,cutoff_hours) do nothing;

    if found then v_inserted:=v_inserted+1; end if;
  end loop;

  return jsonb_build_object(
    'version','p9-prospective-attempt-registry-v1',
    'diagnostic_count',v_seen,
    'inserted_attempt_count',v_inserted,
    'attempt_count',(select count(*) from private.p9_booking_curve_prospective_attempts_v1),
    'target_values_used',false,
    'production_activation_allowed',false,
    'live_adjustment',0,
    'production_change',false
  );
end;$function$;

revoke all on function public.record_p9_booking_curve_prospective_attempt_v1(jsonb,text) from public;
revoke all on function public.record_p9_booking_curve_prospective_attempt_v1(jsonb,text) from anon;
revoke all on function public.record_p9_booking_curve_prospective_attempt_v1(jsonb,text) from authenticated;
grant execute on function public.record_p9_booking_curve_prospective_attempt_v1(jsonb,text) to service_role;

create or replace function public.p9_booking_curve_prospective_summary_v1()
returns jsonb
language sql
stable
set search_path='public','private'
as $function$
with p as (
  select count(*)::int prediction_rows,
         count(distinct ticket_event_id)::int prediction_events,
         min(predicted_at) first_predicted_at,
         max(predicted_at) last_predicted_at
  from private.p9_booking_curve_prospective_predictions_v1
),
a as (
  select count(*)::int attempt_rows,
         count(distinct ticket_event_id)::int attempt_events,
         count(*) filter (where status='PREDICTION_READY')::int prediction_ready_attempts,
         count(*) filter (where status='PIT_SUPPORT_INSUFFICIENT')::int support_insufficient_attempts,
         count(*) filter (where status='NO_TARGET_INCUMBENT')::int no_target_incumbent_attempts,
         min(attempted_at) first_attempted_at,
         max(attempted_at) last_attempted_at
  from private.p9_booking_curve_prospective_attempts_v1
),
event_scores as (
  select ticket_event_id,
         count(*)::int cutoff_count,
         avg(incumbent_abs_error)::double precision incumbent_event_ae,
         avg(challenger_abs_error)::double precision challenger_event_ae,
         avg(incumbent_bias)::double precision incumbent_event_bias,
         avg(challenger_bias)::double precision challenger_event_bias
  from private.p9_booking_curve_prospective_scores_v1
  group by ticket_event_id
),
s as (
  select count(*)::int scored_events,
         avg(incumbent_event_ae)::double precision incumbent_event_balanced_mae,
         avg(challenger_event_ae)::double precision challenger_event_balanced_mae,
         avg(challenger_event_ae-incumbent_event_ae)::double precision delta_event_balanced_mae,
         avg(incumbent_event_bias)::double precision incumbent_event_balanced_bias,
         avg(challenger_event_bias)::double precision challenger_event_balanced_bias,
         avg(case when challenger_event_ae<incumbent_event_ae then 1.0 else 0.0 end)::double precision event_improvement_rate,
         percentile_cont(0.5) within group(order by challenger_event_ae) challenger_event_median_ae,
         percentile_cont(0.9) within group(order by challenger_event_ae) challenger_event_p90_ae,
         max(challenger_event_ae-incumbent_event_ae)::double precision worst_event_degradation
  from event_scores
)
select jsonb_build_object(
  'version','p9-booking-curve-prospective-summary-v1',
  'checked_at',now(),
  'attempt_rows',(select attempt_rows from a),
  'attempt_events',(select attempt_events from a),
  'prediction_ready_attempts',(select prediction_ready_attempts from a),
  'support_insufficient_attempts',(select support_insufficient_attempts from a),
  'no_target_incumbent_attempts',(select no_target_incumbent_attempts from a),
  'first_attempted_at',(select first_attempted_at from a),
  'last_attempted_at',(select last_attempted_at from a),
  'prediction_rows',(select prediction_rows from p),
  'prediction_events',(select prediction_events from p),
  'first_predicted_at',(select first_predicted_at from p),
  'last_predicted_at',(select last_predicted_at from p),
  'scored_events',(select scored_events from s),
  'incumbent_event_balanced_mae',(select incumbent_event_balanced_mae from s),
  'challenger_event_balanced_mae',(select challenger_event_balanced_mae from s),
  'delta_event_balanced_mae',(select delta_event_balanced_mae from s),
  'incumbent_event_balanced_bias',(select incumbent_event_balanced_bias from s),
  'challenger_event_balanced_bias',(select challenger_event_balanced_bias from s),
  'event_improvement_rate',(select event_improvement_rate from s),
  'challenger_event_median_ae',(select challenger_event_median_ae from s),
  'challenger_event_p90_ae',(select challenger_event_p90_ae from s),
  'worst_event_degradation',(select worst_event_degradation from s),
  'evidence_status',case when (select scored_events from s)=0 then 'PROSPECTIVE_PREDICTIONS_ONLY' else 'PROSPECTIVE_EVIDENCE_ACCUMULATING' end,
  'production_activation_allowed',false,
  'live_adjustment',0,
  'production_change',false
);
$function$;
