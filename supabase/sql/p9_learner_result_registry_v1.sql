-- Immutable P9 learner result registry v1.
-- A result can be stored only after both fixed T-48 and T-24 support freezes
-- have been registered. The registry never activates production.

create table if not exists private.p9_learner_result_registry_v1 (
  result_sha256 text primary key,
  precommit_id text not null,
  evaluated_at timestamptz not null default clock_timestamp(),
  github_sha text,
  independent_event_count integer not null,
  row_count integer not null,
  anchor_event_balanced_mae double precision,
  challenger_event_balanced_mae double precision,
  delta_event_balanced_mae double precision,
  relative_point_improvement double precision,
  evidence_status text not null,
  result_payload jsonb not null,
  production_activation_allowed boolean not null default false,
  live_adjustment numeric not null default 0,
  production_change boolean not null default false,
  constraint p9_result_sha check (result_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_result_precommit check (precommit_id='p9-knn-median-residual-k5-v1'),
  constraint p9_result_count check (independent_event_count>0 and row_count>0),
  constraint p9_result_evidence check (evidence_status in ('NO_RESEARCH_GAIN','POINT_GAIN_UNCERTAINTY_LIMITED','ROBUST_RESEARCH_ADVANCE')),
  constraint p9_result_prod check (production_activation_allowed=false and live_adjustment=0 and production_change=false)
);

create or replace function private.reject_p9_learner_result_mutation_v1()
returns trigger
language plpgsql
security definer
set search_path='public','private'
as $function$
begin
  raise exception 'P9_LEARNER_RESULT_REGISTRY_IMMUTABLE';
end;
$function$;

drop trigger if exists p9_learner_result_registry_immutable_v1 on private.p9_learner_result_registry_v1;
create trigger p9_learner_result_registry_immutable_v1
before update or delete on private.p9_learner_result_registry_v1
for each row execute function private.reject_p9_learner_result_mutation_v1();

create or replace function public.register_p9_learner_result_v1(p_result jsonb,p_github_sha text default null)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_sha text;
  v_primary jsonb;
  v_events integer;
  v_rows integer;
  v_evidence text;
begin
  if p_result is null or jsonb_typeof(p_result)<>'object' then raise exception 'P9_RESULT_OBJECT_REQUIRED'; end if;
  if p_result->>'version'<>'p9-booking-curve-learner-v1' then raise exception 'P9_RESULT_VERSION_REJECTED'; end if;
  if p_result->>'precommit_id'<>'p9-knn-median-residual-k5-v1' then raise exception 'P9_RESULT_PRECOMMIT_MISMATCH'; end if;
  if coalesce((p_result->>'production_activation_allowed')::boolean,true) then raise exception 'P9_RESULT_PRODUCTION_ACTIVATION_REJECTED'; end if;
  if coalesce((p_result->>'production_change')::boolean,true) then raise exception 'P9_RESULT_PRODUCTION_CHANGE_REJECTED'; end if;
  if coalesce((p_result->>'live_adjustment')::numeric,1)<>0 then raise exception 'P9_RESULT_LIVE_ADJUSTMENT_REJECTED'; end if;
  if not exists(select 1 from private.p9_learner_support_freeze_registry_v1 where cutoff_hours=24)
     or not exists(select 1 from private.p9_learner_support_freeze_registry_v1 where cutoff_hours=48) then
    raise exception 'P9_RESULT_SUPPORT_FREEZES_MISSING';
  end if;

  v_sha:=p_result->>'result_sha256';
  if v_sha is null or v_sha !~ '^[0-9a-f]{64}$' then raise exception 'P9_RESULT_SHA_REJECTED'; end if;
  v_primary:=coalesce(p_result->'primary','{}'::jsonb);
  v_events:=coalesce((p_result->>'independent_event_count')::integer,0);
  v_rows:=coalesce((p_result->>'row_count')::integer,0);
  v_evidence:=p_result->>'evidence_status';
  if v_events<=0 or v_rows<=0 then raise exception 'P9_RESULT_EMPTY'; end if;
  if v_evidence='ROBUST_RESEARCH_ADVANCE' and coalesce((p_result->>'business_minimum_meaningful_delta_approved')::boolean,false)=false then
    raise exception 'P9_RESULT_ROBUST_WITHOUT_BUSINESS_THRESHOLD';
  end if;

  insert into private.p9_learner_result_registry_v1(
    result_sha256,precommit_id,github_sha,independent_event_count,row_count,
    anchor_event_balanced_mae,challenger_event_balanced_mae,delta_event_balanced_mae,
    relative_point_improvement,evidence_status,result_payload,
    production_activation_allowed,live_adjustment,production_change
  ) values(
    v_sha,p_result->>'precommit_id',nullif(trim(p_github_sha),''),v_events,v_rows,
    nullif(v_primary->>'anchor_event_balanced_mae','')::double precision,
    nullif(v_primary->>'challenger_event_balanced_mae','')::double precision,
    nullif(v_primary->>'delta_event_balanced_mae','')::double precision,
    nullif(v_primary->>'relative_point_improvement','')::double precision,
    v_evidence,p_result,false,0,false
  ) on conflict(result_sha256) do nothing;

  return jsonb_build_object(
    'version','p9-learner-result-registry-v1',
    'registered',true,
    'result_sha256',v_sha,
    'independent_event_count',v_events,
    'row_count',v_rows,
    'evidence_status',v_evidence,
    'production_activation_allowed',false,
    'live_adjustment',0,
    'production_change',false
  );
end;
$function$;

create or replace function public.p9_learner_result_status_v1()
returns jsonb
language sql
stable
security invoker
set search_path='public','private'
as $function$
select jsonb_build_object(
  'version','p9-learner-result-status-v1',
  'result_count',(select count(*) from private.p9_learner_result_registry_v1),
  'results',coalesce((select jsonb_agg(jsonb_build_object(
    'result_sha256',r.result_sha256,'evaluated_at',r.evaluated_at,'github_sha',r.github_sha,
    'independent_event_count',r.independent_event_count,'row_count',r.row_count,
    'anchor_event_balanced_mae',r.anchor_event_balanced_mae,
    'challenger_event_balanced_mae',r.challenger_event_balanced_mae,
    'delta_event_balanced_mae',r.delta_event_balanced_mae,
    'relative_point_improvement',r.relative_point_improvement,
    'evidence_status',r.evidence_status
  ) order by r.evaluated_at) from private.p9_learner_result_registry_v1 r),'[]'::jsonb),
  'production_activation_allowed',false,
  'live_adjustment',0,
  'production_change',false
);
$function$;

revoke all on private.p9_learner_result_registry_v1 from public,anon,authenticated;
revoke all on function public.register_p9_learner_result_v1(jsonb,text) from public,anon,authenticated;
grant execute on function public.register_p9_learner_result_v1(jsonb,text) to service_role;
grant execute on function public.p9_learner_result_status_v1() to service_role;
