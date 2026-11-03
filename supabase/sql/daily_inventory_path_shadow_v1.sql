-- PREPARED, NOT APPLIED. Independent research lane; no attendance-lane changes.
-- Run only with the project migration role. Runtime access is service_role-only.
begin;
create schema if not exists private;

create table if not exists private.daily_inventory_path_models_v1 (
  model_version text primary key,
  model_sha256 text not null unique check(model_sha256 ~ '^[0-9a-f]{64}$'),
  trained_through timestamptz not null,
  fitted_at timestamptz not null,
  training_event_ids bigint[] not null,
  registered_at timestamptz not null default clock_timestamp(),
  check(trained_through <= fitted_at)
);
insert into private.daily_inventory_path_models_v1
  (model_version,model_sha256,trained_through,fitted_at,training_event_ids)
values ('daily-inventory-direct-median-v1',
 '1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525',
 '2026-11-03T00:00:00Z','2026-11-03T16:37:09.890554Z',
 array[1,3,4,5,6,7,10,11,15,16,18,19,20,21,22,23]::bigint[])
on conflict do nothing;

create table if not exists private.daily_inventory_path_attempts_v1 (
 id bigint generated always as identity primary key,
 ticket_event_id bigint not null references public.ticket_events(id),
 issued_as_of_at timestamptz not null,
 kickoff_at timestamptz not null,
 model_version text not null references private.daily_inventory_path_models_v1(model_version),
 model_sha256 text not null,
 received_at timestamptz not null default clock_timestamp(),
 github_sha text not null,
 status text not null,
 input_manifest_sha256 text not null check(input_manifest_sha256 ~ '^[0-9a-f]{64}$'),
 payload jsonb not null,
 production_change boolean not null default false check(production_change=false),
 unique(ticket_event_id,issued_as_of_at,model_version)
);
create table if not exists private.daily_inventory_path_points_v1 (
 id bigint generated always as identity primary key,
 attempt_id bigint not null references private.daily_inventory_path_attempts_v1(id),
 target_at timestamptz not null,
 lead_days integer not null check(lead_days between 1 and 59),
 predicted_available_total double precision not null check(predicted_available_total>=0 and predicted_available_total<'Infinity'::double precision),
 baseline_available_total double precision not null check(baseline_available_total>=0 and baseline_available_total<'Infinity'::double precision),
 measurement_key text not null,
 unique(attempt_id,target_at), unique(attempt_id,lead_days)
);
create table if not exists private.daily_inventory_path_scores_v1 (
 point_id bigint primary key references private.daily_inventory_path_points_v1(id),
 target_snapshot_id bigint not null references public.snapshots(id),
 target_captured_at timestamptz not null,
 actual_available_total double precision not null check(actual_available_total>=0 and actual_available_total<'Infinity'::double precision),
 candidate_abs_error double precision not null,
 baseline_abs_error double precision not null,
 scored_at timestamptz not null default clock_timestamp()
);
create or replace function private.daily_inventory_path_no_mutation_v1()
returns trigger language plpgsql set search_path=pg_catalog as $$
begin raise exception 'DAILY_INVENTORY_PATH_IMMUTABLE'; end; $$;
create trigger daily_inventory_models_immutable_v1 before update or delete on private.daily_inventory_path_models_v1
for each row execute function private.daily_inventory_path_no_mutation_v1();
create trigger daily_inventory_attempts_immutable_v1 before update or delete on private.daily_inventory_path_attempts_v1
for each row execute function private.daily_inventory_path_no_mutation_v1();
create trigger daily_inventory_points_immutable_v1 before update or delete on private.daily_inventory_path_points_v1
for each row execute function private.daily_inventory_path_no_mutation_v1();
create trigger daily_inventory_scores_immutable_v1 before update or delete on private.daily_inventory_path_scores_v1
for each row execute function private.daily_inventory_path_no_mutation_v1();

create or replace function public.record_daily_inventory_path_v1(p_attempt jsonb,p_github_sha text)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public,private set timezone='UTC' as $$
declare
 i jsonb:=p_attempt->'issue'; a jsonb:=p_attempt->'artifact'; points jsonb:=p_attempt->'points';
 event_row public.ticket_events%rowtype; m private.daily_inventory_path_models_v1%rowtype;
 issue_at timestamptz; n integer; now_at timestamptz:=clock_timestamp(); attempt_id bigint;
 old private.daily_inventory_path_attempts_v1%rowtype; point jsonb; lead integer;
 ids bigint[]; expected_ids bigint[]; total integer; first_at timestamptz; last_at timestamptz;
 last_available double precision; measurement text;
begin
 if jsonb_typeof(p_attempt) is distinct from 'object'
 or jsonb_typeof(points) is distinct from 'array'
 or coalesce((p_attempt->>'production_change')::boolean,true)
 or coalesce((i->>'production_change')::boolean,true)
 or coalesce((i->>'target_values_used')::boolean,true)
 or coalesce((a->>'production_change')::boolean,true)
 or coalesce((a->>'live_adjustment')::numeric,1)<>0
 or coalesce(p_github_sha,'') !~ '^[0-9a-f]{40}$'
 then raise exception 'INVALID_DAILY_PATH_CONTRACT'; end if;
 select * into event_row from public.ticket_events where id=(i->>'ticket_event_id')::bigint;
 if not found or event_row.kickoff_at is distinct from (i->>'kickoff_at')::timestamptz
 then raise exception 'EVENT_IDENTITY_MISMATCH'; end if;
 select * into m from private.daily_inventory_path_models_v1 where model_version=a->>'model_version';
 if not found or m.model_sha256 is distinct from a->>'model_sha256'
 or m.trained_through is distinct from (a->>'trained_through')::timestamptz
 or m.fitted_at is distinct from (a->>'fitted_at')::timestamptz
 or event_row.id=any(m.training_event_ids)
 then raise exception 'FROZEN_MODEL_IDENTITY_MISMATCH'; end if;
 issue_at:=(i->>'issued_as_of_at')::timestamptz; n:=(i->>'days_to_event')::integer;
 if n not between 1 and 60 or issue_at is distinct from event_row.kickoff_at-make_interval(days=>n)
 or issue_at<m.fitted_at
 or now_at<issue_at or now_at>issue_at+interval '90 minutes'
 or coalesce(i->>'input_manifest_sha256','') !~ '^[0-9a-f]{64}$'
 then raise exception 'DAILY_PATH_WINDOW_OR_MANIFEST_REJECTED'; end if;

 -- Serializes retries for one model/event/issue; no conflicting overwrite.
 perform pg_advisory_xact_lock(hashtextextended(event_row.id::text||'/'||issue_at::text||'/'||m.model_version,0));
 select * into old from private.daily_inventory_path_attempts_v1
 where ticket_event_id=event_row.id and issued_as_of_at=issue_at and model_version=m.model_version;
 if found then
  if old.payload is distinct from p_attempt then raise exception 'CONFLICTING_IMMUTABLE_DAILY_PATH_RETRY'; end if;
  return jsonb_build_object('attempt_id',old.id,'inserted',false,'production_change',false);
 end if;

 if i->>'status'='READY' then
  if jsonb_typeof(i->'observed_prefix') is distinct from 'array'
  then raise exception 'PREFIX_REQUIRED'; end if;
  select array_agg((x.value->>'snapshot_id')::bigint order by x.ord),count(*)
  into ids,total from jsonb_array_elements(i->'observed_prefix') with ordinality x(value,ord);
  select array_agg(q.id order by q.captured_at,q.id),min(q.captured_at),max(q.captured_at)
  into expected_ids,first_at,last_at from (
   select distinct on(date_trunc('hour',s.captured_at)) s.id,s.captured_at
   from public.snapshots s where s.ticket_event_id=event_row.id
    and s.captured_at between event_row.kickoff_at-interval '60 days' and issue_at
   order by date_trunc('hour',s.captured_at),s.captured_at desc,s.id desc
  ) q;
  if total<4 or ids is distinct from expected_ids or last_at-first_at<interval '24 hours'
  or issue_at-last_at>interval '6 hours' then raise exception 'PREFIX_COVERAGE_MISMATCH'; end if;
  measurement:=i->>'measurement_key';
  if exists(select 1 from public.snapshots s
    where s.ticket_event_id=event_row.id and s.captured_at between event_row.kickoff_at-interval '60 days' and issue_at
    and (s.available_total is null or s.available_total<0 or s.source is null
      or event_row.provider||'/'||s.source is distinct from measurement))
  then raise exception 'SOURCE_MEASUREMENT_INVALID'; end if;
  if exists(select 1 from jsonb_array_elements(i->'observed_prefix') x
    left join public.snapshots s on s.id=(x->>'snapshot_id')::bigint
    where s.id is null or s.ticket_event_id<>event_row.id
     or s.captured_at is distinct from (x->>'captured_at')::timestamptz
     or s.available_total::double precision is distinct from (x->>'available_total')::double precision
     or x->>'measurement_key' is distinct from measurement
     or x->>'source_active'='false' or x->>'source_visible'='false')
  then raise exception 'PREFIX_LINEAGE_MISMATCH'; end if;
  select s.available_total into last_available from public.snapshots s where s.id=ids[total];
  if jsonb_array_length(points)<>n-1 then raise exception 'INCOMPLETE_DAILY_PATH'; end if;
 else
  if coalesce(i->>'status','')='' or jsonb_array_length(points)<>0
  then raise exception 'INVALID_FAILED_ATTEMPT'; end if;
 end if;

 insert into private.daily_inventory_path_attempts_v1
 (ticket_event_id,issued_as_of_at,kickoff_at,model_version,model_sha256,github_sha,status,input_manifest_sha256,payload)
 values(event_row.id,issue_at,event_row.kickoff_at,m.model_version,m.model_sha256,p_github_sha,
 i->>'status',i->>'input_manifest_sha256',p_attempt) returning id into attempt_id;
 for point in select value from jsonb_array_elements(points) loop
  lead:=(point->>'lead_days')::integer;
  if lead not between 1 and n-1
  or (point->>'target_at')::timestamptz is distinct from issue_at+make_interval(days=>lead)
  or (point->>'issued_as_of_at')::timestamptz is distinct from issue_at
  or (point->>'ticket_event_id')::bigint is distinct from event_row.id
  or point->>'model_sha256' is distinct from m.model_sha256
  or point->>'model_version' is distinct from m.model_version
  or point->>'measurement_key' is distinct from measurement
  or point->>'input_manifest_sha256' is distinct from i->>'input_manifest_sha256'
  or coalesce((point->>'production_change')::boolean,true)
  or (point->>'baseline_available_total')::double precision is distinct from last_available
  then raise exception 'POINT_IDENTITY_MISMATCH'; end if;
  insert into private.daily_inventory_path_points_v1
  (attempt_id,target_at,lead_days,predicted_available_total,baseline_available_total,measurement_key)
  values(attempt_id,(point->>'target_at')::timestamptz,lead,
   (point->>'predicted_available_total')::double precision,last_available,measurement);
 end loop;
 return jsonb_build_object('attempt_id',attempt_id,'inserted',true,'point_count',jsonb_array_length(points),'production_change',false);
end; $$;

create or replace function public.score_daily_inventory_path_v1()
returns jsonb language plpgsql security definer set search_path=pg_catalog,public,private set timezone='UTC' as $$
declare n integer;
begin
 insert into private.daily_inventory_path_scores_v1
 (point_id,target_snapshot_id,target_captured_at,actual_available_total,candidate_abs_error,baseline_abs_error)
 select p.id,s.id,s.captured_at,s.available_total,
  abs(p.predicted_available_total-s.available_total),abs(p.baseline_available_total-s.available_total)
 from private.daily_inventory_path_points_v1 p
 join private.daily_inventory_path_attempts_v1 a on a.id=p.attempt_id
 join public.ticket_events e on e.id=a.ticket_event_id and e.kickoff_at=a.kickoff_at
 cross join lateral(select x.id,x.captured_at,x.available_total,x.source from public.snapshots x
  where x.ticket_event_id=a.ticket_event_id and x.captured_at between p.target_at-interval '6 hours' and p.target_at
  order by x.captured_at desc,x.id desc limit 1) s
 where p.target_at<=clock_timestamp() and s.available_total>=0
  and e.provider||'/'||s.source=p.measurement_key
 on conflict(point_id) do nothing;
 get diagnostics n=row_count;
 return jsonb_build_object('inserted_scores',n,'production_change',false);
end; $$;

create or replace function public.daily_inventory_path_feed_v1()
returns jsonb language sql security definer set search_path=pg_catalog,public,private set timezone='UTC' as $$
 select jsonb_build_object('version','daily-inventory-path-preview-v1','generated_at',clock_timestamp(),
  'evidence_kind','research_preview_not_prospective','production_change',false,'events',coalesce((
   select jsonb_agg(jsonb_build_object(
    'ticket_event_id',a.ticket_event_id,'club_slug',a.payload->'issue'->>'club_slug',
    'kickoff_at',a.kickoff_at,'issued_as_of_at',a.issued_as_of_at,'status',a.status,
    'measurement_key',a.payload->'issue'->'measurement_key',
    'model_version',a.model_version,'model_sha256',a.model_sha256,
    'observations',case when a.status='READY' then a.payload->'issue'->'observed_prefix' else '[]'::jsonb end,
    'points',coalesce((select jsonb_agg(jsonb_build_object(
     'ticket_event_id',a.ticket_event_id,'issued_as_of_at',a.issued_as_of_at,'target_at',p.target_at,
     'lead_days',p.lead_days,'model_version',a.model_version,'model_sha256',a.model_sha256,
     'predicted_available_total',p.predicted_available_total,'baseline_available_total',p.baseline_available_total,
     'measurement_key',p.measurement_key,'input_manifest_sha256',a.input_manifest_sha256,
     'evidence_kind','research_preview_not_prospective',
     'score',case when s.point_id is null then null else jsonb_build_object(
      'target_snapshot_id',s.target_snapshot_id,'target_captured_at',s.target_captured_at,
      'target_available_total',s.actual_available_total,'candidate_abs_error',s.candidate_abs_error,
      'baseline_abs_error',s.baseline_abs_error,'scored_at',s.scored_at,'measurement_key',p.measurement_key) end
    ) order by p.target_at) from private.daily_inventory_path_points_v1 p
     left join private.daily_inventory_path_scores_v1 s on s.point_id=p.id where p.attempt_id=a.id),'[]'::jsonb)
   ) order by a.issued_as_of_at,a.ticket_event_id) from private.daily_inventory_path_attempts_v1 a),'[]'::jsonb));
$$;

alter table private.daily_inventory_path_models_v1 enable row level security;
alter table private.daily_inventory_path_attempts_v1 enable row level security;
alter table private.daily_inventory_path_points_v1 enable row level security;
alter table private.daily_inventory_path_scores_v1 enable row level security;
revoke all on private.daily_inventory_path_models_v1,private.daily_inventory_path_attempts_v1,
 private.daily_inventory_path_points_v1,private.daily_inventory_path_scores_v1 from public,anon,authenticated,service_role;
revoke all on function private.daily_inventory_path_no_mutation_v1() from public,anon,authenticated,service_role;
revoke all on function public.record_daily_inventory_path_v1(jsonb,text) from public,anon,authenticated;
revoke all on function public.score_daily_inventory_path_v1() from public,anon,authenticated;
revoke all on function public.daily_inventory_path_feed_v1() from public,anon,authenticated;
grant execute on function public.record_daily_inventory_path_v1(jsonb,text) to service_role;
grant execute on function public.score_daily_inventory_path_v1() to service_role;
grant execute on function public.daily_inventory_path_feed_v1() to service_role;
commit;
