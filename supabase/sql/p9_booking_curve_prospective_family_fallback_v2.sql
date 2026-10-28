-- P9 Booking Curve prospective incumbent-family fallback v2.
-- Scientific contract: ml/P9_BOOKING_CURVE_PROSPECTIVE_FAMILY_FALLBACK_V2.md
-- Fallback-only: never overwrites or replaces P9 v1 evidence.
-- No production activation.

create table if not exists private.p9_booking_curve_prospective_fallback_attempts_v2 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  target_as_of_at timestamptz not null,
  attempted_at timestamptz not null default clock_timestamp(),
  status text not null,
  v1_target_incumbent_source_family text,
  v1_residual_reference_count integer,
  fallback_target_incumbent_source_family text,
  fallback_residual_reference_count integer,
  selected_neighbor_event_ids bigint[] not null default '{}'::bigint[],
  support_manifest_sha256 text,
  source_version text not null,
  precommit_id text not null,
  github_sha text,
  production_change boolean not null default false,
  constraint p9_fallback_attempt_cutoff_v2 check (cutoff_hours in (24,48)),
  constraint p9_fallback_attempt_status_v2 check (status in (
    'NO_TARGET_INCUMBENT',
    'V1_COVERED',
    'FALLBACK_NOT_ALLOWED_FOR_V1_FAMILY',
    'FALLBACK_NO_STRUCTURAL_TARGET_INCUMBENT',
    'FALLBACK_SUPPORT_INSUFFICIENT',
    'FALLBACK_PREDICTION_READY'
  )),
  constraint p9_fallback_attempt_time_v2 check (
    attempted_at>=target_as_of_at and attempted_at<=target_as_of_at+interval '90 minutes'
  ),
  constraint p9_fallback_attempt_v1_support_v2 check (v1_residual_reference_count is null or v1_residual_reference_count>=0),
  constraint p9_fallback_attempt_support_v2 check (fallback_residual_reference_count is null or fallback_residual_reference_count>=0),
  constraint p9_fallback_attempt_sha_v2 check (support_manifest_sha256 is null or support_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_fallback_attempt_prod_v2 check (production_change=false),
  unique(ticket_event_id,cutoff_hours)
);

create table if not exists private.p9_booking_curve_prospective_fallback_predictions_v2 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  target_as_of_at timestamptz not null,
  predicted_at timestamptz not null default clock_timestamp(),
  target_at timestamptz not null,
  stadium_capacity integer not null,
  fallback_from_family text not null,
  v1_residual_reference_count integer not null,
  incumbent_source text not null,
  incumbent_row_id bigint not null,
  incumbent_p50 double precision not null,
  trajectory_residual double precision not null,
  challenger_p50 double precision not null,
  selected_neighbor_event_ids bigint[] not null,
  residual_reference_event_ids bigint[] not null,
  reference_incumbent_row_ids bigint[] not null,
  p9a_manifest_sha256 text not null,
  support_manifest_sha256 text not null,
  reference_outcomes_sha256 text not null,
  prediction_identity_sha256 text not null,
  source_version text not null,
  github_sha text,
  created_at timestamptz not null default clock_timestamp(),
  production_change boolean not null default false,
  constraint p9_fallback_prediction_cutoff_v2 check (cutoff_hours in (24,48)),
  constraint p9_fallback_prediction_capacity_v2 check (stadium_capacity>0),
  constraint p9_fallback_prediction_anchor_v2 check (incumbent_p50>=0 and incumbent_p50<=stadium_capacity),
  constraint p9_fallback_prediction_challenger_v2 check (challenger_p50>=0 and challenger_p50<=stadium_capacity),
  constraint p9_fallback_prediction_time_v2 check (
    predicted_at>=target_as_of_at and predicted_at<=target_as_of_at+interval '90 minutes' and predicted_at<target_at
  ),
  constraint p9_fallback_prediction_refs_v2 check (
    cardinality(selected_neighbor_event_ids)=5
    and cardinality(residual_reference_event_ids)>=3
    and cardinality(reference_incumbent_row_ids)=cardinality(residual_reference_event_ids)
  ),
  constraint p9_fallback_prediction_policy_v2 check (
    fallback_from_family='d2_long72_forward_predictions_v1'
    and incumbent_source='structural_prior_forecasts_v1'
    and v1_residual_reference_count<3
  ),
  constraint p9_fallback_prediction_sha1_v2 check (p9a_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_fallback_prediction_sha2_v2 check (support_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_fallback_prediction_sha3_v2 check (reference_outcomes_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_fallback_prediction_sha4_v2 check (prediction_identity_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_fallback_prediction_prod_v2 check (production_change=false),
  unique(ticket_event_id,cutoff_hours)
);

create table if not exists private.p9_booking_curve_prospective_fallback_scores_v2 (
  prediction_id bigint primary key references private.p9_booking_curve_prospective_fallback_predictions_v2(id),
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  predicted_at timestamptz not null,
  actual_attendance integer not null,
  attendance_confirmed_at timestamptz not null,
  incumbent_abs_error double precision not null,
  challenger_abs_error double precision not null,
  delta_abs_error double precision not null,
  incumbent_bias double precision not null,
  challenger_bias double precision not null,
  improved boolean not null,
  scored_at timestamptz not null default clock_timestamp(),
  production_change boolean not null default false,
  constraint p9_fallback_score_time_v2 check (attendance_confirmed_at>predicted_at),
  constraint p9_fallback_score_prod_v2 check (production_change=false)
);

create index if not exists p9_fallback_attempts_v2_attempted_at_idx
  on private.p9_booking_curve_prospective_fallback_attempts_v2(attempted_at desc);
create index if not exists p9_fallback_predictions_v2_predicted_at_idx
  on private.p9_booking_curve_prospective_fallback_predictions_v2(predicted_at desc);
create index if not exists p9_fallback_scores_v2_ticket_event_idx
  on private.p9_booking_curve_prospective_fallback_scores_v2(ticket_event_id);

drop trigger if exists p9_fallback_attempts_immutable_v2 on private.p9_booking_curve_prospective_fallback_attempts_v2;
create trigger p9_fallback_attempts_immutable_v2
before update or delete on private.p9_booking_curve_prospective_fallback_attempts_v2
for each row execute function private.reject_p9_prospective_mutation_v1();

drop trigger if exists p9_fallback_predictions_immutable_v2 on private.p9_booking_curve_prospective_fallback_predictions_v2;
create trigger p9_fallback_predictions_immutable_v2
before update or delete on private.p9_booking_curve_prospective_fallback_predictions_v2
for each row execute function private.reject_p9_prospective_mutation_v1();

drop trigger if exists p9_fallback_scores_immutable_v2 on private.p9_booking_curve_prospective_fallback_scores_v2;
create trigger p9_fallback_scores_immutable_v2
before update or delete on private.p9_booking_curve_prospective_fallback_scores_v2
for each row execute function private.reject_p9_prospective_mutation_v1();

create or replace function public.record_p9_booking_curve_prospective_fallback_attempt_v2(
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
  v_target_as_of timestamptz;
  v_now timestamptz:=clock_timestamp();
  v_status text;
  v_prediction_count integer;
  v_inserted integer:=0;
begin
  if p_payload is null or jsonb_typeof(p_payload)<>'object' then raise exception 'P9_FALLBACK_V2_PAYLOAD_REQUIRED'; end if;
  if p_payload->>'version'<>'p9-booking-curve-prospective-family-fallback-builder-v2' then raise exception 'P9_FALLBACK_V2_VERSION_MISMATCH'; end if;
  if p_payload->>'precommit_id'<>'p9-knn-median-residual-k5-family-fallback-v2' then raise exception 'P9_FALLBACK_V2_PRECOMMIT_MISMATCH'; end if;
  if coalesce((p_payload->>'target_values_used')::boolean,true) then raise exception 'P9_FALLBACK_V2_TARGET_VALUES_USED'; end if;
  if coalesce((p_payload->>'production_activation_allowed')::boolean,true) then raise exception 'P9_FALLBACK_V2_PRODUCTION_ACTIVATION_REJECTED'; end if;
  if coalesce((p_payload->>'live_adjustment')::numeric,1)<>0 then raise exception 'P9_FALLBACK_V2_LIVE_ADJUSTMENT_REJECTED'; end if;
  if coalesce((p_payload->>'production_change')::boolean,true) then raise exception 'P9_FALLBACK_V2_PRODUCTION_CHANGE_REJECTED'; end if;
  if lower(p_payload::text) ~ '"(actual_attendance|target_attendance|target_outcome)"\s*:' then raise exception 'P9_FALLBACK_V2_TARGET_KEY_REJECTED'; end if;
  if jsonb_typeof(p_payload->'diagnostics')<>'array' then raise exception 'P9_FALLBACK_V2_DIAGNOSTICS_REQUIRED'; end if;
  if jsonb_typeof(p_payload->'predictions')<>'array' then raise exception 'P9_FALLBACK_V2_PREDICTIONS_REQUIRED'; end if;

  v_cutoff:=(p_payload->>'cutoff_hours')::integer;
  if v_cutoff not in (24,48) then raise exception 'P9_FALLBACK_V2_CUTOFF_REJECTED'; end if;

  for v_diag in select value from jsonb_array_elements(p_payload->'diagnostics') loop
    if coalesce((v_diag->>'cutoff_hours')::integer,-1)<>v_cutoff then raise exception 'P9_FALLBACK_V2_DIAGNOSTIC_CUTOFF_MISMATCH'; end if;
    select * into v_event from public.ticket_events where id=(v_diag->>'ticket_event_id')::bigint;
    if not found then raise exception 'P9_FALLBACK_V2_EVENT_NOT_FOUND'; end if;
    if private.normalize_structural_prior_competition_v1(v_event.competition)<>'Ekstraklasa' then raise exception 'P9_FALLBACK_V2_COMPETITION_REJECTED'; end if;

    v_target_as_of:=v_event.kickoff_at-make_interval(hours=>v_cutoff);
    if v_now<v_target_as_of or v_now>v_target_as_of+interval '90 minutes' then raise exception 'P9_FALLBACK_V2_WINDOW_CLOSED event=% cutoff=%',v_event.id,v_cutoff; end if;
    if exists(select 1 from public.ticket_event_outcomes o where o.ticket_event_id=v_event.id and o.actual_attendance is not null) then raise exception 'P9_FALLBACK_V2_TARGET_OUTCOME_ALREADY_KNOWN'; end if;

    v_status:=v_diag->>'status';
    if v_status not in ('NO_TARGET_INCUMBENT','V1_COVERED','FALLBACK_NOT_ALLOWED_FOR_V1_FAMILY','FALLBACK_NO_STRUCTURAL_TARGET_INCUMBENT','FALLBACK_SUPPORT_INSUFFICIENT','FALLBACK_PREDICTION_READY') then
      raise exception 'P9_FALLBACK_V2_STATUS_REJECTED';
    end if;

    select count(*)::integer into v_prediction_count
    from jsonb_array_elements(p_payload->'predictions') p
    where (p->>'ticket_event_id')::bigint=v_event.id and (p->>'cutoff_hours')::integer=v_cutoff;
    if v_status='FALLBACK_PREDICTION_READY' and v_prediction_count<>1 then raise exception 'P9_FALLBACK_V2_READY_WITHOUT_SINGLE_PREDICTION'; end if;
    if v_status<>'FALLBACK_PREDICTION_READY' and v_prediction_count<>0 then raise exception 'P9_FALLBACK_V2_NONREADY_WITH_PREDICTION'; end if;

    if v_status='FALLBACK_PREDICTION_READY' then
      if coalesce((v_diag->>'v1_residual_reference_count')::integer,99)>=3 then raise exception 'P9_FALLBACK_V2_V1_ALREADY_SUPPORTED'; end if;
      if v_diag->>'v1_target_incumbent_source_family'<>'d2_long72_forward_predictions_v1' then raise exception 'P9_FALLBACK_V2_SOURCE_POLICY_REJECTED'; end if;
      if v_diag->>'fallback_target_incumbent_source_family'<>'structural_prior_forecasts_v1' then raise exception 'P9_FALLBACK_V2_TARGET_POLICY_REJECTED'; end if;
      if coalesce((v_diag->>'fallback_residual_reference_count')::integer,0)<3 then raise exception 'P9_FALLBACK_V2_SUPPORT_REJECTED'; end if;
    end if;

    insert into private.p9_booking_curve_prospective_fallback_attempts_v2(
      ticket_event_id,cutoff_hours,target_as_of_at,attempted_at,status,
      v1_target_incumbent_source_family,v1_residual_reference_count,
      fallback_target_incumbent_source_family,fallback_residual_reference_count,
      selected_neighbor_event_ids,support_manifest_sha256,source_version,precommit_id,github_sha,production_change
    ) values (
      v_event.id,v_cutoff,v_target_as_of,v_now,v_status,
      nullif(v_diag->>'v1_target_incumbent_source_family',''),
      case when v_diag ? 'v1_residual_reference_count' then (v_diag->>'v1_residual_reference_count')::integer else null end,
      nullif(v_diag->>'fallback_target_incumbent_source_family',''),
      case when v_diag ? 'fallback_residual_reference_count' then (v_diag->>'fallback_residual_reference_count')::integer else null end,
      coalesce(array(select jsonb_array_elements_text(coalesce(v_diag->'selected_neighbor_event_ids','[]'::jsonb))::bigint),'{}'::bigint[]),
      nullif(v_diag->>'support_manifest_sha256',''),p_payload->>'version',p_payload->>'precommit_id',nullif(trim(p_github_sha),''),false
    ) on conflict(ticket_event_id,cutoff_hours) do nothing;
    if found then v_inserted:=v_inserted+1; end if;
  end loop;

  return jsonb_build_object(
    'version','p9-booking-curve-prospective-fallback-attempt-insert-v2',
    'inserted_attempts',v_inserted,
    'attempt_rows_after',(select count(*) from private.p9_booking_curve_prospective_fallback_attempts_v2),
    'target_values_used',false,'production_activation_allowed',false,'live_adjustment',0,'production_change',false
  );
end;$function$;

create or replace function public.insert_p9_booking_curve_prospective_fallback_predictions_v2(
  p_payload jsonb,
  p_github_sha text default null
)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_row jsonb;
  v_now timestamptz:=clock_timestamp();
  v_inserted integer:=0;
  v_event public.ticket_events%rowtype;
  v_cutoff integer;
  v_target_as_of timestamptz;
begin
  if p_payload is null or jsonb_typeof(p_payload)<>'object' then raise exception 'P9_FALLBACK_V2_PAYLOAD_REQUIRED'; end if;
  if p_payload->>'version'<>'p9-booking-curve-prospective-family-fallback-builder-v2' then raise exception 'P9_FALLBACK_V2_VERSION_MISMATCH'; end if;
  if p_payload->>'precommit_id'<>'p9-knn-median-residual-k5-family-fallback-v2' then raise exception 'P9_FALLBACK_V2_PRECOMMIT_MISMATCH'; end if;
  if coalesce((p_payload->>'target_values_used')::boolean,true) then raise exception 'P9_FALLBACK_V2_TARGET_VALUES_USED'; end if;
  if coalesce((p_payload->>'production_activation_allowed')::boolean,true) then raise exception 'P9_FALLBACK_V2_PRODUCTION_ACTIVATION_REJECTED'; end if;
  if coalesce((p_payload->>'live_adjustment')::numeric,1)<>0 then raise exception 'P9_FALLBACK_V2_LIVE_ADJUSTMENT_REJECTED'; end if;
  if coalesce((p_payload->>'production_change')::boolean,true) then raise exception 'P9_FALLBACK_V2_PRODUCTION_CHANGE_REJECTED'; end if;
  if lower(p_payload::text) ~ '"(actual_attendance|target_attendance|target_outcome)"\s*:' then raise exception 'P9_FALLBACK_V2_TARGET_KEY_REJECTED'; end if;
  if jsonb_typeof(p_payload->'predictions')<>'array' then raise exception 'P9_FALLBACK_V2_PREDICTIONS_REQUIRED'; end if;

  for v_row in select value from jsonb_array_elements(p_payload->'predictions') loop
    select * into v_event from public.ticket_events where id=(v_row->>'ticket_event_id')::bigint;
    if not found then raise exception 'P9_FALLBACK_V2_EVENT_NOT_FOUND'; end if;
    v_cutoff:=(v_row->>'cutoff_hours')::integer;
    if v_cutoff not in(24,48) then raise exception 'P9_FALLBACK_V2_CUTOFF_REJECTED'; end if;
    v_target_as_of:=v_event.kickoff_at-make_interval(hours=>v_cutoff);
    if abs(extract(epoch from ((v_row->>'target_as_of_at')::timestamptz-v_target_as_of)))>1 then raise exception 'P9_FALLBACK_V2_TARGET_ASOF_MISMATCH'; end if;
    if v_now<v_target_as_of or v_now>v_target_as_of+interval '90 minutes' then raise exception 'P9_FALLBACK_V2_PERSISTENCE_WINDOW_CLOSED event=% cutoff=%',v_event.id,v_cutoff; end if;
    if v_now>=v_event.kickoff_at then raise exception 'P9_FALLBACK_V2_TARGET_ALREADY_STARTED'; end if;
    if exists(select 1 from public.ticket_event_outcomes o where o.ticket_event_id=v_event.id and o.actual_attendance is not null) then raise exception 'P9_FALLBACK_V2_TARGET_OUTCOME_ALREADY_KNOWN'; end if;
    if v_row->>'fallback_from_family'<>'d2_long72_forward_predictions_v1' then raise exception 'P9_FALLBACK_V2_FROM_POLICY_REJECTED'; end if;
    if v_row->>'incumbent_source'<>'structural_prior_forecasts_v1' then raise exception 'P9_FALLBACK_V2_INCUMBENT_POLICY_REJECTED'; end if;
    if coalesce((v_row->>'v1_residual_reference_count')::integer,99)>=3 then raise exception 'P9_FALLBACK_V2_V1_ALREADY_SUPPORTED'; end if;

    insert into private.p9_booking_curve_prospective_fallback_predictions_v2(
      ticket_event_id,cutoff_hours,target_as_of_at,predicted_at,target_at,stadium_capacity,
      fallback_from_family,v1_residual_reference_count,incumbent_source,incumbent_row_id,
      incumbent_p50,trajectory_residual,challenger_p50,selected_neighbor_event_ids,
      residual_reference_event_ids,reference_incumbent_row_ids,p9a_manifest_sha256,
      support_manifest_sha256,reference_outcomes_sha256,prediction_identity_sha256,
      source_version,github_sha,production_change
    ) values (
      v_event.id,v_cutoff,v_target_as_of,v_now,v_event.kickoff_at,(v_row->>'stadium_capacity')::integer,
      v_row->>'fallback_from_family',(v_row->>'v1_residual_reference_count')::integer,
      v_row->>'incumbent_source',(v_row->>'incumbent_row_id')::bigint,
      (v_row->>'incumbent_p50')::double precision,(v_row->>'trajectory_residual')::double precision,
      (v_row->>'challenger_p50')::double precision,
      array(select jsonb_array_elements_text(v_row->'selected_neighbor_event_ids')::bigint),
      array(select jsonb_array_elements_text(v_row->'residual_reference_event_ids')::bigint),
      array(select jsonb_array_elements_text(v_row->'reference_incumbent_row_ids')::bigint),
      v_row->>'p9a_manifest_sha256',v_row->>'support_manifest_sha256',v_row->>'reference_outcomes_sha256',
      v_row->>'prediction_identity_sha256',v_row->>'source_version',nullif(trim(p_github_sha),''),false
    ) on conflict(ticket_event_id,cutoff_hours) do nothing;
    if found then v_inserted:=v_inserted+1; end if;
  end loop;

  return jsonb_build_object(
    'version','p9-booking-curve-prospective-fallback-insert-v2',
    'inserted_predictions',v_inserted,
    'prediction_rows_after',(select count(*) from private.p9_booking_curve_prospective_fallback_predictions_v2),
    'independent_events_after',(select count(distinct ticket_event_id) from private.p9_booking_curve_prospective_fallback_predictions_v2),
    'target_values_used',false,'production_activation_allowed',false,'live_adjustment',0,'production_change',false
  );
end;$function$;

create or replace function public.score_p9_booking_curve_prospective_fallback_completed_v2()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare v_inserted integer:=0;
begin
  with eligible as (
    select p.id prediction_id,p.ticket_event_id,p.cutoff_hours,p.predicted_at,p.incumbent_p50,p.challenger_p50,o.actual_attendance,o.confirmed_at
    from private.p9_booking_curve_prospective_fallback_predictions_v2 p
    join public.ticket_event_outcomes o on o.ticket_event_id=p.ticket_event_id
      and o.actual_attendance is not null and o.confirmed_at is not null and o.confirmed_at>p.predicted_at
  ), ins as (
    insert into private.p9_booking_curve_prospective_fallback_scores_v2(
      prediction_id,ticket_event_id,cutoff_hours,predicted_at,actual_attendance,attendance_confirmed_at,
      incumbent_abs_error,challenger_abs_error,delta_abs_error,incumbent_bias,challenger_bias,improved,production_change
    )
    select e.prediction_id,e.ticket_event_id,e.cutoff_hours,e.predicted_at,e.actual_attendance,e.confirmed_at,
      abs(e.incumbent_p50-e.actual_attendance),abs(e.challenger_p50-e.actual_attendance),
      abs(e.challenger_p50-e.actual_attendance)-abs(e.incumbent_p50-e.actual_attendance),
      e.incumbent_p50-e.actual_attendance,e.challenger_p50-e.actual_attendance,
      abs(e.challenger_p50-e.actual_attendance)<abs(e.incumbent_p50-e.actual_attendance),false
    from eligible e on conflict(prediction_id) do nothing returning 1
  ) select count(*) into v_inserted from ins;

  return jsonb_build_object(
    'version','p9-booking-curve-prospective-fallback-score-v2',
    'inserted_scores',v_inserted,
    'score_rows_after',(select count(*) from private.p9_booking_curve_prospective_fallback_scores_v2),
    'production_change',false
  );
end;$function$;

create or replace function public.p9_booking_curve_prospective_fallback_summary_v2()
returns jsonb
language sql
stable
set search_path='public','private'
as $function$
with a as (
  select count(*)::int attempt_rows,
         count(distinct ticket_event_id)::int attempt_events,
         count(*) filter(where status='V1_COVERED')::int v1_covered_attempts,
         count(*) filter(where status='FALLBACK_PREDICTION_READY')::int fallback_ready_attempts,
         count(*) filter(where status='FALLBACK_SUPPORT_INSUFFICIENT')::int fallback_support_insufficient_attempts,
         min(attempted_at) first_attempted_at,max(attempted_at) last_attempted_at
  from private.p9_booking_curve_prospective_fallback_attempts_v2
), p as (
  select count(*)::int prediction_rows,count(distinct ticket_event_id)::int prediction_events,
         min(predicted_at) first_predicted_at,max(predicted_at) last_predicted_at
  from private.p9_booking_curve_prospective_fallback_predictions_v2
), event_scores as (
  select ticket_event_id,count(*)::int cutoff_count,
         avg(incumbent_abs_error)::double precision incumbent_event_ae,
         avg(challenger_abs_error)::double precision challenger_event_ae,
         avg(incumbent_bias)::double precision incumbent_event_bias,
         avg(challenger_bias)::double precision challenger_event_bias
  from private.p9_booking_curve_prospective_fallback_scores_v2 group by ticket_event_id
), s as (
  select count(*)::int scored_events,
         avg(incumbent_event_ae)::double precision incumbent_event_balanced_mae,
         avg(challenger_event_ae)::double precision challenger_event_balanced_mae,
         avg(challenger_event_ae-incumbent_event_ae)::double precision delta_event_balanced_mae,
         avg(case when challenger_event_ae<incumbent_event_ae then 1.0 else 0.0 end)::double precision event_improvement_rate,
         max(challenger_event_ae-incumbent_event_ae)::double precision worst_event_degradation
  from event_scores
)
select jsonb_build_object(
  'version','p9-booking-curve-prospective-fallback-summary-v2','checked_at',now(),
  'attempt_rows',(select attempt_rows from a),'attempt_events',(select attempt_events from a),
  'v1_covered_attempts',(select v1_covered_attempts from a),'fallback_ready_attempts',(select fallback_ready_attempts from a),
  'fallback_support_insufficient_attempts',(select fallback_support_insufficient_attempts from a),
  'first_attempted_at',(select first_attempted_at from a),'last_attempted_at',(select last_attempted_at from a),
  'prediction_rows',(select prediction_rows from p),'prediction_events',(select prediction_events from p),
  'first_predicted_at',(select first_predicted_at from p),'last_predicted_at',(select last_predicted_at from p),
  'scored_events',(select scored_events from s),
  'incumbent_event_balanced_mae',(select incumbent_event_balanced_mae from s),
  'challenger_event_balanced_mae',(select challenger_event_balanced_mae from s),
  'delta_event_balanced_mae',(select delta_event_balanced_mae from s),
  'event_improvement_rate',(select event_improvement_rate from s),
  'worst_event_degradation',(select worst_event_degradation from s),
  'production_activation_allowed',false,'live_adjustment',0,'production_change',false
);
$function$;

revoke all on function public.record_p9_booking_curve_prospective_fallback_attempt_v2(jsonb,text) from public,anon,authenticated;
revoke all on function public.insert_p9_booking_curve_prospective_fallback_predictions_v2(jsonb,text) from public,anon,authenticated;
revoke all on function public.score_p9_booking_curve_prospective_fallback_completed_v2() from public,anon,authenticated;
revoke all on function public.p9_booking_curve_prospective_fallback_summary_v2() from public,anon,authenticated;

grant execute on function public.record_p9_booking_curve_prospective_fallback_attempt_v2(jsonb,text) to service_role;
grant execute on function public.insert_p9_booking_curve_prospective_fallback_predictions_v2(jsonb,text) to service_role;
grant execute on function public.score_p9_booking_curve_prospective_fallback_completed_v2() to service_role;
grant execute on function public.p9_booking_curve_prospective_fallback_summary_v2() to service_role;

grant select on private.p9_booking_curve_prospective_fallback_attempts_v2 to service_role;
grant select on private.p9_booking_curve_prospective_fallback_predictions_v2 to service_role;
grant select on private.p9_booking_curve_prospective_fallback_scores_v2 to service_role;

revoke all on private.p9_booking_curve_prospective_fallback_attempts_v2 from anon,authenticated;
revoke all on private.p9_booking_curve_prospective_fallback_predictions_v2 from anon,authenticated;
revoke all on private.p9_booking_curve_prospective_fallback_scores_v2 from anon,authenticated;
