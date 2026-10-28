-- Beyond Ticketing — Daily Trajectory Prospective Evidence v1
-- Applied live on 2026-10-28 via Supabase migrations:
--   daily_trajectory_prospective_ledger_v1
--   daily_trajectory_attempt_snapshot_index_v1
--   daily_trajectory_scoring_v1
--
-- Purpose:
--   immutable daily P-N attempt/prediction evidence plus post-outcome scoring.
--
-- Production boundary:
--   research only; production_change is hard-checked false.

create table if not exists private.daily_trajectory_attempts_v1 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  days_to_event integer not null check (days_to_event between 1 and 60),
  target_as_of_at timestamptz not null,
  attempted_at timestamptz not null default clock_timestamp(),
  model_version text not null check (btrim(model_version) <> ''),
  precommit_id text not null check (btrim(precommit_id) <> ''),
  dataset_version text not null check (btrim(dataset_version) <> ''),
  dataset_manifest_sha256 text not null check (dataset_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  github_sha text,
  status text not null check (status in (
    'PREDICTION_READY',
    'NO_USABLE_TRAJECTORY',
    'NO_INCUMBENT',
    'DATA_QUALITY_BLOCKED',
    'MODEL_INPUT_INSUFFICIENT'
  )),
  status_reason text,
  source_snapshot_id bigint references public.snapshots(id),
  source_snapshot_captured_at timestamptz,
  observed_prefix_start_at timestamptz,
  observed_prefix_end_at timestamptz,
  incumbent_source text,
  incumbent_row_id bigint,
  incumbent_p50 double precision,
  input_payload jsonb not null default '{}'::jsonb,
  target_values_used boolean not null default false check (target_values_used = false),
  production_change boolean not null default false check (production_change = false),
  constraint daily_trajectory_attempt_prefix_order_v1 check (
    observed_prefix_start_at is null
    or observed_prefix_end_at is null
    or observed_prefix_start_at <= observed_prefix_end_at
  ),
  constraint daily_trajectory_attempt_prefix_cutoff_v1 check (
    observed_prefix_end_at is null or observed_prefix_end_at <= target_as_of_at
  ),
  constraint daily_trajectory_attempt_snapshot_lineage_v1 check (
    (source_snapshot_id is null and source_snapshot_captured_at is null)
    or (source_snapshot_id is not null and source_snapshot_captured_at is not null)
  ),
  constraint daily_trajectory_attempt_ready_inputs_v1 check (
    status <> 'PREDICTION_READY'
    or (source_snapshot_id is not null and incumbent_source is not null and incumbent_p50 is not null)
  ),
  unique(ticket_event_id, days_to_event, model_version)
);

create index if not exists daily_trajectory_attempts_v1_attempted_at_idx
  on private.daily_trajectory_attempts_v1(attempted_at);
create index if not exists daily_trajectory_attempts_v1_status_idx
  on private.daily_trajectory_attempts_v1(status);
create index if not exists daily_trajectory_attempts_v1_event_idx
  on private.daily_trajectory_attempts_v1(ticket_event_id, days_to_event);
create index if not exists daily_trajectory_attempts_v1_source_snapshot_idx
  on private.daily_trajectory_attempts_v1(source_snapshot_id)
  where source_snapshot_id is not null;

create table if not exists private.daily_trajectory_predictions_v1 (
  id bigint generated always as identity primary key,
  attempt_id bigint not null unique references private.daily_trajectory_attempts_v1(id),
  ticket_event_id bigint not null references public.ticket_events(id),
  days_to_event integer not null check (days_to_event between 1 and 60),
  target_as_of_at timestamptz not null,
  predicted_at timestamptz not null default clock_timestamp(),
  target_at timestamptz not null,
  model_version text not null check (btrim(model_version) <> ''),
  precommit_id text not null check (btrim(precommit_id) <> ''),
  dataset_version text not null check (btrim(dataset_version) <> ''),
  dataset_manifest_sha256 text not null check (dataset_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  prediction_identity_sha256 text not null check (prediction_identity_sha256 ~ '^[0-9a-f]{64}$'),
  github_sha text,
  incumbent_source text not null,
  incumbent_row_id bigint,
  incumbent_p50 double precision not null check (incumbent_p50 >= 0),
  trajectory_residual double precision not null,
  challenger_p10 double precision,
  challenger_p50 double precision not null check (challenger_p50 >= 0),
  challenger_p90 double precision,
  stadium_capacity integer check (stadium_capacity is null or stadium_capacity > 0),
  prediction_payload jsonb not null default '{}'::jsonb,
  target_values_used boolean not null default false check (target_values_used = false),
  production_change boolean not null default false check (production_change = false),
  constraint daily_trajectory_prediction_interval_v1 check (
    (challenger_p10 is null or challenger_p10 <= challenger_p50)
    and (challenger_p90 is null or challenger_p50 <= challenger_p90)
  ),
  constraint daily_trajectory_prediction_capacity_v1 check (
    stadium_capacity is null or challenger_p50 <= stadium_capacity
  ),
  unique(ticket_event_id, days_to_event, model_version)
);

create index if not exists daily_trajectory_predictions_v1_predicted_at_idx
  on private.daily_trajectory_predictions_v1(predicted_at);
create index if not exists daily_trajectory_predictions_v1_event_idx
  on private.daily_trajectory_predictions_v1(ticket_event_id, days_to_event);

create or replace function private.reject_daily_trajectory_mutation_v1()
returns trigger
language plpgsql
set search_path = public, private
as $$
begin
  raise exception 'DAILY_TRAJECTORY_PROSPECTIVE_IMMUTABLE';
end;
$$;

drop trigger if exists daily_trajectory_attempts_immutable_v1 on private.daily_trajectory_attempts_v1;
create trigger daily_trajectory_attempts_immutable_v1
before update or delete on private.daily_trajectory_attempts_v1
for each row execute function private.reject_daily_trajectory_mutation_v1();

drop trigger if exists daily_trajectory_predictions_immutable_v1 on private.daily_trajectory_predictions_v1;
create trigger daily_trajectory_predictions_immutable_v1
before update or delete on private.daily_trajectory_predictions_v1
for each row execute function private.reject_daily_trajectory_mutation_v1();

create or replace function public.record_daily_trajectory_attempt_v1(
  p_payload jsonb,
  p_github_sha text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public, private
as $$
declare
  v_event public.ticket_events%rowtype;
  v_days integer;
  v_target_as_of timestamptz;
  v_now timestamptz := clock_timestamp();
  v_status text;
  v_snapshot public.snapshots%rowtype;
  v_inserted_id bigint;
begin
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_PAYLOAD_REQUIRED';
  end if;
  if p_payload->>'version' <> 'daily-trajectory-attempt-v1' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_VERSION_MISMATCH';
  end if;
  if coalesce((p_payload->>'target_values_used')::boolean, true) then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_TARGET_VALUES_USED';
  end if;
  if coalesce((p_payload->>'production_change')::boolean, true) then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_PRODUCTION_CHANGE_REJECTED';
  end if;
  if coalesce((p_payload->>'live_adjustment')::numeric, 1) <> 0 then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_LIVE_ADJUSTMENT_REJECTED';
  end if;
  if lower(p_payload::text) ~ '\"(actual_attendance|target_attendance|target_outcome)\"\s*:' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_TARGET_KEY_REJECTED';
  end if;
  if coalesce(p_payload->>'dataset_manifest_sha256','') !~ '^[0-9a-f]{64}$' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_MANIFEST_SHA_REJECTED';
  end if;
  if coalesce(btrim(p_payload->>'model_version'),'') = ''
     or coalesce(btrim(p_payload->>'precommit_id'),'') = ''
     or coalesce(btrim(p_payload->>'dataset_version'),'') = '' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_IDENTITY_REQUIRED';
  end if;

  v_days := (p_payload->>'days_to_event')::integer;
  if v_days not between 1 and 60 then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_HORIZON_REJECTED';
  end if;

  select * into v_event
  from public.ticket_events
  where id = (p_payload->>'ticket_event_id')::bigint;
  if not found or v_event.kickoff_at is null then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_EVENT_NOT_FOUND';
  end if;

  v_target_as_of := v_event.kickoff_at - make_interval(days => v_days);
  if abs(extract(epoch from ((p_payload->>'target_as_of_at')::timestamptz - v_target_as_of))) > 1 then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_TARGET_ASOF_MISMATCH';
  end if;
  if v_now < v_target_as_of or v_now > v_target_as_of + interval '90 minutes' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_OUTSIDE_IMMUTABLE_WINDOW event=% p-%', v_event.id, v_days;
  end if;
  if v_now >= v_event.kickoff_at then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_TARGET_ALREADY_STARTED';
  end if;
  if exists (
    select 1 from public.ticket_event_outcomes o
    where o.ticket_event_id = v_event.id and o.actual_attendance is not null
  ) then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_TARGET_OUTCOME_ALREADY_PRESENT';
  end if;

  v_status := p_payload->>'status';
  if v_status not in (
    'PREDICTION_READY','NO_USABLE_TRAJECTORY','NO_INCUMBENT',
    'DATA_QUALITY_BLOCKED','MODEL_INPUT_INSUFFICIENT'
  ) then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_STATUS_REJECTED';
  end if;

  if p_payload ? 'source_snapshot_id' and (p_payload->>'source_snapshot_id') is not null then
    select * into v_snapshot
    from public.snapshots
    where id = (p_payload->>'source_snapshot_id')::bigint
      and ticket_event_id = v_event.id;
    if not found then
      raise exception 'DAILY_TRAJECTORY_ATTEMPT_SNAPSHOT_NOT_FOUND';
    end if;
    if v_snapshot.captured_at > v_target_as_of then
      raise exception 'DAILY_TRAJECTORY_ATTEMPT_FUTURE_SNAPSHOT_REJECTED';
    end if;
    if p_payload ? 'source_snapshot_captured_at'
       and abs(extract(epoch from ((p_payload->>'source_snapshot_captured_at')::timestamptz - v_snapshot.captured_at))) > 1 then
      raise exception 'DAILY_TRAJECTORY_ATTEMPT_SNAPSHOT_TIME_MISMATCH';
    end if;
  elsif v_status = 'PREDICTION_READY' then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_READY_WITHOUT_SNAPSHOT';
  end if;

  if v_status = 'PREDICTION_READY'
     and (coalesce(btrim(p_payload->>'incumbent_source'),'') = '' or not (p_payload ? 'incumbent_p50')) then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_READY_WITHOUT_INCUMBENT';
  end if;

  if p_payload ? 'observed_prefix_end_at'
     and (p_payload->>'observed_prefix_end_at')::timestamptz > v_target_as_of then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_FUTURE_PREFIX_REJECTED';
  end if;
  if p_payload ? 'observed_prefix_start_at' and p_payload ? 'observed_prefix_end_at'
     and (p_payload->>'observed_prefix_start_at')::timestamptz > (p_payload->>'observed_prefix_end_at')::timestamptz then
    raise exception 'DAILY_TRAJECTORY_ATTEMPT_PREFIX_ORDER_REJECTED';
  end if;

  insert into private.daily_trajectory_attempts_v1(
    ticket_event_id, days_to_event, target_as_of_at, attempted_at,
    model_version, precommit_id, dataset_version, dataset_manifest_sha256,
    github_sha, status, status_reason, source_snapshot_id,
    source_snapshot_captured_at, observed_prefix_start_at, observed_prefix_end_at,
    incumbent_source, incumbent_row_id, incumbent_p50, input_payload,
    target_values_used, production_change
  ) values (
    v_event.id, v_days, v_target_as_of, v_now,
    p_payload->>'model_version', p_payload->>'precommit_id', p_payload->>'dataset_version', p_payload->>'dataset_manifest_sha256',
    nullif(btrim(p_github_sha),''), v_status, nullif(p_payload->>'status_reason',''),
    case when p_payload ? 'source_snapshot_id' then (p_payload->>'source_snapshot_id')::bigint else null end,
    case when p_payload ? 'source_snapshot_id' then v_snapshot.captured_at else null end,
    case when p_payload ? 'observed_prefix_start_at' then (p_payload->>'observed_prefix_start_at')::timestamptz else null end,
    case when p_payload ? 'observed_prefix_end_at' then (p_payload->>'observed_prefix_end_at')::timestamptz else null end,
    nullif(p_payload->>'incumbent_source',''),
    case when p_payload ? 'incumbent_row_id' then (p_payload->>'incumbent_row_id')::bigint else null end,
    case when p_payload ? 'incumbent_p50' then (p_payload->>'incumbent_p50')::double precision else null end,
    coalesce(p_payload->'input_payload','{}'::jsonb), false, false
  )
  on conflict(ticket_event_id, days_to_event, model_version) do nothing
  returning id into v_inserted_id;

  return jsonb_build_object(
    'version','daily-trajectory-attempt-registry-v1',
    'inserted',v_inserted_id is not null,
    'attempt_id',v_inserted_id,
    'ticket_event_id',v_event.id,
    'days_to_event',v_days,
    'target_values_used',false,
    'production_change',false
  );
end;
$$;

create or replace function public.insert_daily_trajectory_prediction_v1(
  p_payload jsonb,
  p_github_sha text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public, private
as $$
declare
  v_attempt private.daily_trajectory_attempts_v1%rowtype;
  v_event public.ticket_events%rowtype;
  v_now timestamptz := clock_timestamp();
  v_inserted_id bigint;
  v_p10 double precision;
  v_p50 double precision;
  v_p90 double precision;
  v_capacity integer;
begin
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_PAYLOAD_REQUIRED';
  end if;
  if p_payload->>'version' <> 'daily-trajectory-prediction-v1' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_VERSION_MISMATCH';
  end if;
  if coalesce((p_payload->>'target_values_used')::boolean, true) then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_TARGET_VALUES_USED';
  end if;
  if coalesce((p_payload->>'production_change')::boolean, true) then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_PRODUCTION_CHANGE_REJECTED';
  end if;
  if lower(p_payload::text) ~ '\"(actual_attendance|target_attendance|target_outcome)\"\s*:' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_TARGET_KEY_REJECTED';
  end if;
  if coalesce(p_payload->>'prediction_identity_sha256','') !~ '^[0-9a-f]{64}$'
     or coalesce(p_payload->>'dataset_manifest_sha256','') !~ '^[0-9a-f]{64}$' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_SHA_REJECTED';
  end if;

  select * into v_attempt
  from private.daily_trajectory_attempts_v1
  where id=(p_payload->>'attempt_id')::bigint;
  if not found then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_ATTEMPT_NOT_FOUND';
  end if;
  if v_attempt.status <> 'PREDICTION_READY' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_ATTEMPT_NOT_READY';
  end if;
  if p_payload->>'model_version' <> v_attempt.model_version
     or p_payload->>'precommit_id' <> v_attempt.precommit_id
     or p_payload->>'dataset_version' <> v_attempt.dataset_version
     or p_payload->>'dataset_manifest_sha256' <> v_attempt.dataset_manifest_sha256 then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_IDENTITY_MISMATCH';
  end if;

  select * into v_event from public.ticket_events where id=v_attempt.ticket_event_id;
  if not found or v_event.kickoff_at is null then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_EVENT_NOT_FOUND';
  end if;
  if v_now < v_attempt.target_as_of_at or v_now > v_attempt.target_as_of_at + interval '90 minutes' then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_OUTSIDE_IMMUTABLE_WINDOW';
  end if;
  if v_now >= v_event.kickoff_at then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_TARGET_ALREADY_STARTED';
  end if;
  if exists (
    select 1 from public.ticket_event_outcomes o
    where o.ticket_event_id=v_event.id and o.actual_attendance is not null
  ) then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_TARGET_OUTCOME_ALREADY_PRESENT';
  end if;

  v_p50 := (p_payload->>'challenger_p50')::double precision;
  v_p10 := case when p_payload ? 'challenger_p10' then (p_payload->>'challenger_p10')::double precision else null end;
  v_p90 := case when p_payload ? 'challenger_p90' then (p_payload->>'challenger_p90')::double precision else null end;
  v_capacity := case when p_payload ? 'stadium_capacity' then (p_payload->>'stadium_capacity')::integer else null end;
  if v_p50 < 0 or (v_p10 is not null and v_p10 > v_p50) or (v_p90 is not null and v_p50 > v_p90) then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_INTERVAL_REJECTED';
  end if;
  if v_capacity is not null and (v_capacity <= 0 or v_p50 > v_capacity) then
    raise exception 'DAILY_TRAJECTORY_PREDICTION_CAPACITY_REJECTED';
  end if;

  insert into private.daily_trajectory_predictions_v1(
    attempt_id,ticket_event_id,days_to_event,target_as_of_at,predicted_at,target_at,
    model_version,precommit_id,dataset_version,dataset_manifest_sha256,
    prediction_identity_sha256,github_sha,incumbent_source,incumbent_row_id,
    incumbent_p50,trajectory_residual,challenger_p10,challenger_p50,challenger_p90,
    stadium_capacity,prediction_payload,target_values_used,production_change
  ) values (
    v_attempt.id,v_attempt.ticket_event_id,v_attempt.days_to_event,v_attempt.target_as_of_at,v_now,v_event.kickoff_at,
    v_attempt.model_version,v_attempt.precommit_id,v_attempt.dataset_version,v_attempt.dataset_manifest_sha256,
    p_payload->>'prediction_identity_sha256',nullif(btrim(p_github_sha),''),v_attempt.incumbent_source,v_attempt.incumbent_row_id,
    v_attempt.incumbent_p50,(p_payload->>'trajectory_residual')::double precision,v_p10,v_p50,v_p90,
    v_capacity,coalesce(p_payload->'prediction_payload','{}'::jsonb),false,false
  )
  on conflict(attempt_id) do nothing
  returning id into v_inserted_id;

  return jsonb_build_object(
    'version','daily-trajectory-prediction-registry-v1',
    'inserted',v_inserted_id is not null,
    'prediction_id',v_inserted_id,
    'attempt_id',v_attempt.id,
    'target_values_used',false,
    'production_change',false
  );
end;
$$;

create table if not exists private.daily_trajectory_scores_v1 (
  id bigint generated always as identity primary key,
  prediction_id bigint not null unique references private.daily_trajectory_predictions_v1(id),
  ticket_event_id bigint not null references public.ticket_events(id),
  days_to_event integer not null check (days_to_event between 1 and 60),
  model_version text not null,
  predicted_at timestamptz not null,
  attendance_confirmed_at timestamptz not null,
  scored_at timestamptz not null default clock_timestamp(),
  actual_attendance integer not null check (actual_attendance >= 0),
  incumbent_p50 double precision not null,
  challenger_p50 double precision not null,
  incumbent_abs_error double precision not null check (incumbent_abs_error >= 0),
  challenger_abs_error double precision not null check (challenger_abs_error >= 0),
  delta_abs_error double precision not null,
  production_change boolean not null default false check (production_change = false)
);

create index if not exists daily_trajectory_scores_v1_event_idx
  on private.daily_trajectory_scores_v1(ticket_event_id, days_to_event);
create index if not exists daily_trajectory_scores_v1_model_horizon_idx
  on private.daily_trajectory_scores_v1(model_version, days_to_event);

drop trigger if exists daily_trajectory_scores_immutable_v1 on private.daily_trajectory_scores_v1;
create trigger daily_trajectory_scores_immutable_v1
before update or delete on private.daily_trajectory_scores_v1
for each row execute function private.reject_daily_trajectory_mutation_v1();

create or replace function public.score_daily_trajectory_completed_v1()
returns jsonb
language plpgsql
security definer
set search_path = public, private
as $$
declare
  v_inserted integer := 0;
begin
  insert into private.daily_trajectory_scores_v1(
    prediction_id,ticket_event_id,days_to_event,model_version,predicted_at,
    attendance_confirmed_at,actual_attendance,incumbent_p50,challenger_p50,
    incumbent_abs_error,challenger_abs_error,delta_abs_error,production_change
  )
  select
    p.id,p.ticket_event_id,p.days_to_event,p.model_version,p.predicted_at,
    o.confirmed_at,o.actual_attendance,p.incumbent_p50,p.challenger_p50,
    abs(p.incumbent_p50-o.actual_attendance::double precision),
    abs(p.challenger_p50-o.actual_attendance::double precision),
    abs(p.challenger_p50-o.actual_attendance::double precision)-abs(p.incumbent_p50-o.actual_attendance::double precision),
    false
  from private.daily_trajectory_predictions_v1 p
  join public.ticket_events e on e.id=p.ticket_event_id
  join public.ticket_event_outcomes o on o.ticket_event_id=p.ticket_event_id
  left join private.daily_trajectory_scores_v1 s on s.prediction_id=p.id
  where s.id is null
    and e.kickoff_at < clock_timestamp()
    and o.actual_attendance is not null
    and o.confirmed_at is not null
    and o.confirmed_at > p.predicted_at
    and p.production_change=false;

  get diagnostics v_inserted = row_count;
  return jsonb_build_object(
    'version','daily-trajectory-scoring-v1',
    'inserted_scores',v_inserted,
    'score_rows_after',(select count(*) from private.daily_trajectory_scores_v1),
    'independent_events_after',(select count(distinct ticket_event_id) from private.daily_trajectory_scores_v1),
    'production_change',false
  );
end;
$$;

create or replace function public.daily_trajectory_mae_by_horizon_v1()
returns table(
  model_version text,
  days_to_event integer,
  event_count bigint,
  club_count bigint,
  incumbent_mae double precision,
  challenger_mae double precision,
  delta_mae double precision,
  event_improvement_rate double precision,
  median_challenger_ae double precision,
  p90_challenger_ae double precision,
  worst_event_degradation double precision
)
language sql
security definer
set search_path = public, private
as $$
  select
    s.model_version,
    s.days_to_event,
    count(distinct s.ticket_event_id)::bigint,
    count(distinct e.club_slug)::bigint,
    avg(s.incumbent_abs_error)::double precision,
    avg(s.challenger_abs_error)::double precision,
    (avg(s.challenger_abs_error)-avg(s.incumbent_abs_error))::double precision,
    avg(case when s.challenger_abs_error < s.incumbent_abs_error then 1.0 else 0.0 end)::double precision,
    percentile_cont(0.5) within group (order by s.challenger_abs_error)::double precision,
    percentile_cont(0.9) within group (order by s.challenger_abs_error)::double precision,
    max(s.delta_abs_error)::double precision
  from private.daily_trajectory_scores_v1 s
  join public.ticket_events e on e.id=s.ticket_event_id
  group by s.model_version,s.days_to_event
  order by s.model_version,s.days_to_event desc;
$$;

revoke all on private.daily_trajectory_attempts_v1 from public, anon, authenticated, service_role;
revoke all on private.daily_trajectory_predictions_v1 from public, anon, authenticated, service_role;
revoke all on private.daily_trajectory_scores_v1 from public, anon, authenticated, service_role;
grant select on private.daily_trajectory_attempts_v1 to service_role;
grant select on private.daily_trajectory_predictions_v1 to service_role;
grant select on private.daily_trajectory_scores_v1 to service_role;

revoke all on function public.record_daily_trajectory_attempt_v1(jsonb,text) from public, anon, authenticated;
revoke all on function public.insert_daily_trajectory_prediction_v1(jsonb,text) from public, anon, authenticated;
revoke all on function public.score_daily_trajectory_completed_v1() from public, anon, authenticated;
revoke all on function public.daily_trajectory_mae_by_horizon_v1() from public, anon, authenticated;
grant execute on function public.record_daily_trajectory_attempt_v1(jsonb,text) to service_role;
grant execute on function public.insert_daily_trajectory_prediction_v1(jsonb,text) to service_role;
grant execute on function public.score_daily_trajectory_completed_v1() to service_role;
grant execute on function public.daily_trajectory_mae_by_horizon_v1() to service_role;
