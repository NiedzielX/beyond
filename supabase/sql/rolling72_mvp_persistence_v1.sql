-- Rolling72 P0-4c: forward-only PERS issuance and due scoring.
-- Additive private objects only. P0-4b is a read-only source dependency.
create schema if not exists private;

create table private.rolling72_mvp_persistence_v1_lane (
 lane_id text primary key check(lane_id='rolling72-mvp-persistence-v1'),
 version text not null check(version='rolling72-mvp-persistence-v1'),
 source_lane_id text not null check(source_lane_id='rolling72-mvp-research-v1'),
 manifest_text text not null,
 manifest_sha256 text not null check(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 sql_sha256 text not null check(sql_sha256 ~ '^[0-9a-f]{64}$'),
 source_manifest_sha256 text not null check(source_manifest_sha256 ~ '^[0-9a-f]{64}$'),
 source_sql_sha256 text not null check(source_sql_sha256 ~ '^[0-9a-f]{64}$'),
 source_family text not null check(source_family='roboticket/roboticket'),
 unit text not null check(unit='available_total_seats'),
 method text not null check(method='PERS'),
 horizons_hours integer[] not null check(horizons_hours=array[24,48,72]::integer[]),
 max_source_age_seconds integer not null check(max_source_age_seconds=3600),
 max_issue_batch integer not null check(max_issue_batch=25),
 max_score_batch integer not null check(max_score_batch=100),
 max_fixtures integer not null check(max_fixtures between 1 and 1000),
 activated_at timestamptz not null,
 issue_until timestamptz not null,
 scoring_until timestamptz not null,
 check(issue_until>activated_at),
 check(scoring_until>=issue_until+interval '78 hours')
);

create table private.rolling72_mvp_persistence_v1_runs (
 id uuid primary key,
 operation text not null check(operation in('ISSUE','SCORE')),
 started_at timestamptz not null,
 completed_at timestamptz not null,
 status text not null,
 requested_limit integer not null,
 processed integer not null check(processed>=0),
 result_counts jsonb not null,
 check(completed_at>=started_at)
);

create table private.rolling72_mvp_persistence_v1_issue_bundles (
 id bigint generated always as identity primary key,
 seal_id bigint not null unique references private.rolling72_mvp_research_v1_seals(id),
 ticket_event_id bigint not null references private.rolling72_mvp_research_v1_registry(ticket_event_id),
 source_known_at timestamptz not null,
 source_captured_at timestamptz not null,
 source_read_completed_at timestamptz not null,
 source_age_seconds numeric not null check(source_age_seconds between 0 and 3600),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 input_available_total bigint not null check(input_available_total>=0),
 scope_status text not null check(scope_status in('NO_PRIOR','COMPLETE','GAPPED','UNKNOWN')),
 sector_count integer not null check(sector_count>0),
 prior_sector_count integer,
 sector_count_delta integer,
 membership_change_count integer,
 transition jsonb not null,
 calculation_completed_at timestamptz not null,
 read_completed_at timestamptz not null,
 issued_at timestamptz not null,
 kickoff_at timestamptz not null,
 check(source_read_completed_at<=read_completed_at),
 check(read_completed_at<=calculation_completed_at),
 check(calculation_completed_at<issued_at),
 check(source_known_at<=issued_at),
 check(source_captured_at<=issued_at),
 check(source_age_seconds=extract(epoch from issued_at-source_captured_at)),
 unique(id,ticket_event_id)
);

create table private.rolling72_mvp_persistence_v1_predictions (
 id bigint generated always as identity primary key,
 bundle_id bigint not null,
 candidate_id bigint not null unique references private.rolling72_mvp_research_v1_candidates(id),
 ticket_event_id bigint not null,
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 issued_at timestamptz not null,
 target_at timestamptz not null,
 kickoff_at timestamptz not null,
 source_candidate_status text not null check(source_candidate_status in('SOURCE_ELIGIBLE','OUTSIDE_KICKOFF')),
 status text not null check(status in('ISSUED','OUTSIDE_KICKOFF')),
 prediction bigint,
 origin_available_total bigint not null check(origin_available_total>=0),
 source_seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 source_scope_status text not null check(source_scope_status in('NO_PRIOR','COMPLETE','GAPPED','UNKNOWN')),
 source_sector_count integer not null check(source_sector_count>0),
 source_prior_sector_count integer,
 source_sector_count_delta integer,
 source_membership_change_count integer,
 source_transition jsonb not null,
 unique(bundle_id,horizon_hours),
 unique(id,ticket_event_id),
 foreign key(bundle_id,ticket_event_id)
  references private.rolling72_mvp_persistence_v1_issue_bundles(id,ticket_event_id),
 check(target_at=issued_at+make_interval(hours=>horizon_hours)),
 check((target_at<kickoff_at and status='ISSUED' and prediction=origin_available_total)
    or (target_at>=kickoff_at and status='OUTSIDE_KICKOFF' and prediction is null))
);

create table private.rolling72_mvp_persistence_v1_issue_attempts (
 id bigint generated always as identity primary key,
 candidate_id bigint not null unique references private.rolling72_mvp_research_v1_candidates(id),
 ticket_event_id bigint not null,
 seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 source_candidate_status text not null check(source_candidate_status in('SOURCE_ELIGIBLE','OUTSIDE_KICKOFF')),
 attempted_at timestamptz not null,
 status text not null check(status in('ISSUED','REFUSED')),
 reason text,
 bundle_id bigint,
 prediction_id bigint,
 foreign key(prediction_id,ticket_event_id)
  references private.rolling72_mvp_persistence_v1_predictions(id,ticket_event_id),
 foreign key(bundle_id,ticket_event_id)
  references private.rolling72_mvp_persistence_v1_issue_bundles(id,ticket_event_id),
 check((status='ISSUED' and reason is null and bundle_id is not null and prediction_id is not null)
    or (status='REFUSED' and reason is not null and prediction_id is null))
);

create table private.rolling72_mvp_persistence_v1_labels (
 id bigint generated always as identity primary key,
 prediction_id bigint not null unique,
 ticket_event_id bigint not null,
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 source_seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 source_attempt_id bigint not null references private.rolling72_mvp_research_v1_attempts(id),
 snapshot_id bigint not null,
 actual_available_total bigint not null check(actual_available_total>=0),
 source_captured_at timestamptz not null,
 source_known_at timestamptz not null,
 scored_at timestamptz not null,
 target_age_seconds numeric not null check(target_age_seconds between 0 and 21600),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 source_scope_status text not null check(source_scope_status in('NO_PRIOR','COMPLETE','GAPPED','UNKNOWN')),
 source_sector_count integer not null check(source_sector_count>0),
 source_prior_sector_count integer,
 source_sector_count_delta integer,
 source_membership_change_count integer,
 source_transition jsonb not null,
 prediction bigint not null,
 signed_error bigint not null,
 absolute_error bigint not null check(absolute_error>=0),
 foreign key(prediction_id,ticket_event_id)
  references private.rolling72_mvp_persistence_v1_predictions(id,ticket_event_id),
 check(source_known_at<=scored_at),
 check(signed_error=prediction-actual_available_total),
 check(absolute_error=abs(signed_error))
);

create table private.rolling72_mvp_persistence_v1_score_attempts (
 id bigint generated always as identity primary key,
 run_id uuid not null references private.rolling72_mvp_persistence_v1_runs(id) deferrable initially deferred,
 prediction_id bigint not null references private.rolling72_mvp_persistence_v1_predictions(id),
 attempted_at timestamptz not null,
 status text not null check(status in('SCORED','WAITING','NO_ELIGIBLE_SOURCE','SOURCE_ORDER_UNKNOWN',
  'SOURCE_INVALID','SOURCE_MISMATCH','SOURCE_STALE','OUTSIDE_KICKOFF','EXPIRED')),
 reason text,
 selected_source_attempt_id bigint references private.rolling72_mvp_research_v1_attempts(id),
 selected_snapshot_id bigint,
 label_id bigint references private.rolling72_mvp_persistence_v1_labels(id)
);

create index rolling72_mvp_persistence_v1_predictions_due_idx
 on private.rolling72_mvp_persistence_v1_predictions(target_at,id)
 where status='ISSUED' and prediction is not null;

create function private.rolling72_mvp_persistence_v1_immutable()
returns trigger language plpgsql set search_path='' as $$
begin raise exception 'ROLLING72_MVP_PERSISTENCE_IMMUTABLE'; end $$;

create function private.rolling72_mvp_persistence_v1_hash(p_value jsonb)
returns text language sql immutable set search_path='' as $$
 select encode(sha256(convert_to(p_value::text,'UTF8')),'hex')
$$;

-- Check both the read snapshot and transaction status. Unknown/old XIDs fail closed.
create function private.rolling72_mvp_persistence_v1_committed(p_xid xid,p_snapshot pg_snapshot)
returns boolean language plpgsql volatile set search_path='' as $$
declare cur numeric; full_xid numeric;
begin
 if p_xid is null or p_xid::text in('0','1') then return false; end if;
 if p_xid::text='2' then return true; end if;
 cur:=pg_catalog.pg_current_xact_id()::text::numeric;
 full_xid:=floor(cur/4294967296)*4294967296+p_xid::text::numeric;
 if full_xid>cur then full_xid:=full_xid-4294967296; end if;
 if full_xid<3 then return false; end if;
 return coalesce(pg_catalog.pg_visible_in_snapshot(full_xid::text::xid8,p_snapshot)
   and pg_catalog.pg_xact_status(full_xid::text::xid8)='committed',false);
exception when others then return false;
end $$;

create function public.activate_rolling72_mvp_persistence_v1(p_manifest_text text,p_manifest_sha256 text)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 j jsonb; src private.rolling72_mvp_research_v1_lane%rowtype;
 old private.rolling72_mvp_persistence_v1_lane%rowtype; t timestamptz;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_PERSISTENCE_READ_COMMITTED_REQUIRED'; end if;
 if p_manifest_text is null or octet_length(convert_to(p_manifest_text,'UTF8'))>32768
  or p_manifest_sha256 is null or p_manifest_sha256 !~ '^[0-9a-f]{64}$'
  or p_manifest_sha256 is distinct from encode(sha256(convert_to(p_manifest_text,'UTF8')),'hex')
 then raise exception 'MVP_PERSISTENCE_MANIFEST_HASH'; end if;
 j:=p_manifest_text::jsonb;
 if jsonb_typeof(j) is distinct from 'object' or (select count(*) from jsonb_object_keys(j))<>16
  or j->>'lane_id' is distinct from 'rolling72-mvp-persistence-v1'
  or j->>'version' is distinct from 'rolling72-mvp-persistence-v1'
  or j->>'source_lane_id' is distinct from 'rolling72-mvp-research-v1'
  or j->>'source_family' is distinct from 'roboticket/roboticket'
  or j->>'unit' is distinct from 'available_total_seats'
  or j->>'method' is distinct from 'PERS'
  or j->'horizons_hours' is distinct from '[24,48,72]'::jsonb
  or j->'max_source_age_seconds' is distinct from '3600'::jsonb
  or j->'max_issue_batch' is distinct from '25'::jsonb
  or j->'max_score_batch' is distinct from '100'::jsonb
  or jsonb_typeof(j->'max_fixtures') is distinct from 'number'
  or coalesce(j->>'max_fixtures','') !~ '^[1-9][0-9]*$'
  or (j->>'max_fixtures')::numeric not between 1 and 1000
  or coalesce(j->>'source_manifest_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'source_sql_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'sql_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'issue_until','') !~ '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
  or coalesce(j->>'scoring_until','') !~ '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
 then raise exception 'MVP_PERSISTENCE_MANIFEST_CONTRACT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-persistence-v1:runtime',20261123));
 select * into src from private.rolling72_mvp_research_v1_lane where lane_id='rolling72-mvp-research-v1';
 if not found then raise exception 'MVP_SOURCE_LANE_NOT_ACTIVATED'; end if;
 if j->>'source_manifest_sha256' is distinct from src.manifest_sha256
  or j->>'source_sql_sha256' is distinct from src.sql_sha256
  or (j->>'max_fixtures')::integer is distinct from src.max_fixtures
  or (j->>'issue_until')::timestamptz is distinct from src.issue_until
  or (j->>'scoring_until')::timestamptz is distinct from src.scoring_until
 then raise exception 'MVP_PERSISTENCE_SOURCE_BINDING'; end if;
 select * into old from private.rolling72_mvp_persistence_v1_lane;
 if found then
  if old.manifest_text=p_manifest_text and old.manifest_sha256=p_manifest_sha256 then
   return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','activated',false,
    'idempotent',true,'lane_id',old.lane_id,'activated_at',old.activated_at,
    'issue_until',old.issue_until,'scoring_until',old.scoring_until);
  end if;
  raise exception 'MVP_PERSISTENCE_MANIFEST_ALREADY_FROZEN';
 end if;
 t:=clock_timestamp();
 if t>=src.issue_until or t>=src.scoring_until or src.activated_at>t
  or (j->>'issue_until')::timestamptz<=t
  or not isfinite((j->>'issue_until')::timestamptz)
  or not isfinite((j->>'scoring_until')::timestamptz)
  or (j->>'scoring_until')::timestamptz<(j->>'issue_until')::timestamptz+interval '78 hours'
 then raise exception 'MVP_PERSISTENCE_MANIFEST_DEADLINE'; end if;
 insert into private.rolling72_mvp_persistence_v1_lane(
  lane_id,version,source_lane_id,manifest_text,manifest_sha256,sql_sha256,
  source_manifest_sha256,source_sql_sha256,source_family,unit,method,horizons_hours,
  max_source_age_seconds,max_issue_batch,max_score_batch,max_fixtures,activated_at,issue_until,scoring_until)
 values('rolling72-mvp-persistence-v1','rolling72-mvp-persistence-v1','rolling72-mvp-research-v1',
  p_manifest_text,p_manifest_sha256,j->>'sql_sha256',j->>'source_manifest_sha256',j->>'source_sql_sha256',
  'roboticket/roboticket','available_total_seats','PERS',array[24,48,72],3600,25,100,
  (j->>'max_fixtures')::integer,t,(j->>'issue_until')::timestamptz,(j->>'scoring_until')::timestamptz);
 return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','activated',true,
  'idempotent',false,'lane_id','rolling72-mvp-persistence-v1','activated_at',t,
  'issue_until',src.issue_until,'scoring_until',src.scoring_until,
  'source_lane_id',src.lane_id,'source_manifest_sha256',src.manifest_sha256,'source_sql_sha256',src.sql_sha256);
end $$;

create function public.issue_rolling72_mvp_persistence_v1(p_limit integer default 25)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 l private.rolling72_mvp_persistence_v1_lane%rowtype; run_id uuid:=gen_random_uuid();
 started timestamptz:=clock_timestamp(); entry_snapshot pg_snapshot; seal_row record;
 bundle_check record; src private.rolling72_mvp_research_v1_seals%rowtype;
 att private.rolling72_mvp_research_v1_attempts%rowtype;
 reg private.rolling72_mvp_research_v1_registry%rowtype;
 cand record; candidate_rows jsonb; source_bundle jsonb; source_attempt jsonb; source_registry jsonb;
 src_tuple_xmin xid; att_tuple_xmin xid; reg_tuple_xmin xid; candidate_rows_committed boolean;
 v_bundle_id bigint; pred_id bigint; issued timestamptz;
 read_done timestamptz; calc_done timestamptz; attempted timestamptz; src_age numeric;
 h integer; val bigint; p_status text; p_value bigint; scope_stat text;
 attempt_status text; refusal text; count_seals integer:=0; count_numeric integer:=0;
 count_outside integer:=0; count_refused integer:=0; count_processed integer:=0; count_bad_candidates integer:=0;
 count_bundles integer:=0;
 result_rows jsonb:='[]'::jsonb; one_result jsonb; raw_ok boolean;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_PERSISTENCE_READ_COMMITTED_REQUIRED'; end if;
 if p_limit is null or p_limit not between 1 and 25 then raise exception 'MVP_PERSISTENCE_ISSUE_LIMIT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-persistence-v1:runtime',20261123));
 select * into l from private.rolling72_mvp_persistence_v1_lane;
 if not found then raise exception 'MVP_PERSISTENCE_NOT_ACTIVATED'; end if;
 entry_snapshot:=pg_current_snapshot();
 if clock_timestamp()>=l.issue_until then
  insert into private.rolling72_mvp_persistence_v1_runs values(run_id,'ISSUE',started,clock_timestamp(),
   'ISSUE_WINDOW_CLOSED',p_limit,0,jsonb_build_object('reason','ISSUE_WINDOW_CLOSED'));
  return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','lane_id',l.lane_id,
   'run_id',run_id,'status','ISSUE_WINDOW_CLOSED','processed',0,'numeric_forecasts',0,
   'outside_kickoff',0,'refused',0,'unattempted_remain_visible',true,'results','[]'::jsonb);
 end if;
 for seal_row in
  select s.id seal_id,min(s.known_at) known_at
  from private.rolling72_mvp_research_v1_seals s
  join private.rolling72_mvp_research_v1_candidates cand_src on cand_src.seal_id=s.id
  where s.known_at>=l.activated_at and s.known_at<l.issue_until
   and s.phase='ISSUE_WINDOW'
   and not exists(select 1 from private.rolling72_mvp_persistence_v1_issue_bundles b where b.seal_id=s.id)
   and exists(select 1 from private.rolling72_mvp_research_v1_candidates c24 where c24.seal_id=s.id and c24.horizon_hours=24)
   and exists(select 1 from private.rolling72_mvp_research_v1_candidates c48 where c48.seal_id=s.id and c48.horizon_hours=48)
   and exists(select 1 from private.rolling72_mvp_research_v1_candidates c72 where c72.seal_id=s.id and c72.horizon_hours=72)
   and not exists(select 1 from private.rolling72_mvp_persistence_v1_issue_attempts ia
     join private.rolling72_mvp_research_v1_candidates cc on cc.id=ia.candidate_id where cc.seal_id=s.id)
  group by s.id order by min(s.known_at),s.id limit p_limit
 loop
  -- One lane lock serializes bundle creation; candidate row locks document the ownership boundary.
  perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-persistence-v1:seal:'||seal_row.seal_id::text,20261123));
  -- Cache the complete immutable source bundle under one READ COMMITTED statement snapshot.
  select to_jsonb(s),s.xmin,to_jsonb(a),a.xmin,to_jsonb(r),r.xmin,
   coalesce(jsonb_agg(to_jsonb(cc) order by cc.horizon_hours) filter(where cc.id is not null),'[]'::jsonb),
   coalesce(bool_and(private.rolling72_mvp_persistence_v1_committed(cc.xmin,entry_snapshot))
    filter(where cc.id is not null),true)
  into source_bundle,src_tuple_xmin,source_attempt,att_tuple_xmin,source_registry,reg_tuple_xmin,
   candidate_rows,candidate_rows_committed
  from private.rolling72_mvp_research_v1_seals s
  join private.rolling72_mvp_research_v1_attempts a on a.id=s.attempt_id
  join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=s.ticket_event_id
  left join private.rolling72_mvp_research_v1_candidates cc on cc.seal_id=s.id
  where s.id=seal_row.seal_id
  group by s.id,a.id,r.ticket_event_id;
  src:=jsonb_populate_record(null::private.rolling72_mvp_research_v1_seals,source_bundle);
  att:=jsonb_populate_record(null::private.rolling72_mvp_research_v1_attempts,source_attempt);
  reg:=jsonb_populate_record(null::private.rolling72_mvp_research_v1_registry,source_registry);
  select * into bundle_check from private.rolling72_mvp_persistence_v1_issue_bundles where seal_id=src.id;
  if found then continue; end if;
  if not private.rolling72_mvp_persistence_v1_committed(src_tuple_xmin,entry_snapshot)
   or not private.rolling72_mvp_persistence_v1_committed(att_tuple_xmin,entry_snapshot)
   or not private.rolling72_mvp_persistence_v1_committed(reg_tuple_xmin,entry_snapshot)
   or not candidate_rows_committed
  then continue; end if;
  count_processed:=jsonb_array_length(candidate_rows);
  count_bad_candidates:=0;
  for cand in select * from jsonb_populate_recordset(null::private.rolling72_mvp_research_v1_candidates,candidate_rows)
  loop
   if cand.ticket_event_id<>src.ticket_event_id or cand.observation_known_at<>src.known_at
    or cand.provisional_target_at<>src.known_at+make_interval(hours=>cand.horizon_hours)
    or cand.status is distinct from (case when cand.provisional_target_at<reg.kickoff_at then 'SOURCE_ELIGIBLE' else 'OUTSIDE_KICKOFF' end)
   then count_bad_candidates:=count_bad_candidates+1; end if;
  end loop;
  if count_processed<>3 then
   refusal:='CANDIDATE_TRIPLET_INVALID';
  elsif count_bad_candidates>0 then
   refusal:='CANDIDATE_BINDING_INVALID';
  elsif src.ticket_event_id is null or reg.ticket_event_id is null or att.id is null
   or src.phase<>'ISSUE_WINDOW' or src.known_at<l.activated_at or src.known_at>=l.issue_until
   or src.attempt_id<>att.id or att.ticket_event_id<>src.ticket_event_id
   or att.snapshot_id<>src.snapshot_id or att.status<>'READY'
   or att.known_at<>src.known_at or att.captured_at<>src.captured_at
   or att.source_content_sha256<>src.source_content_sha256
  or att.raw_source is distinct from src.source_payload
  or att.attempt_binding_sha256<>private.rolling72_mvp_persistence_v1_hash(att.binding_payload)
  or att.binding_payload is distinct from jsonb_build_object('attempt_id',att.id,'run_id',att.run_id,
   'lane_id',l.source_lane_id,'ticket_event_id',att.ticket_event_id,'snapshot_id',att.snapshot_id,
   'source_content_sha256',att.source_content_sha256,'read_started_at',att.read_started_at,
   'read_completed_at',att.read_completed_at,'known_at',att.known_at,'status',att.status,'reason',att.reason)
   or private.rolling72_mvp_persistence_v1_hash(src.source_payload)<>src.source_content_sha256
   or not private.rolling72_mvp_persistence_v1_committed(src_tuple_xmin,entry_snapshot)
   or not private.rolling72_mvp_persistence_v1_committed(att_tuple_xmin,entry_snapshot)
   or not private.rolling72_mvp_persistence_v1_committed(reg_tuple_xmin,entry_snapshot)
  then refusal:='SOURCE_SEAL_INVALID';
  elsif (src.source_payload->>'source_family') is distinct from l.source_family
   or (src.source_payload->>'unit') is distinct from l.unit
   or src.ticket_event_id<>reg.ticket_event_id
  then refusal:='SOURCE_BINDING_MISMATCH';
  else refusal:=null;
  end if;
  if refusal is not null then
   for cand in select * from jsonb_populate_recordset(null::private.rolling72_mvp_research_v1_candidates,candidate_rows) order by horizon_hours loop
    insert into private.rolling72_mvp_persistence_v1_issue_attempts(
     candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(cand.id,cand.ticket_event_id,cand.seal_id,cand.horizon_hours,cand.status,clock_timestamp(),'REFUSED',refusal)
    on conflict(candidate_id) do nothing;
    count_refused:=count_refused+1;
   end loop;
   result_rows:=result_rows||jsonb_build_array(jsonb_build_object('seal_id',src.id,'status','REFUSED','reason',refusal));
   count_seals:=count_seals+1;
   continue;
  end if;
  -- Read-completion and computation clocks precede the actual issue clock.
  read_done:=clock_timestamp();
  val:=src.available_total;
  scope_stat:=case when src.transition_status in('NO_PRIOR','COMPLETE','GAPPED') then src.transition_status else 'UNKNOWN' end;
  calc_done:=clock_timestamp();
  issued:=clock_timestamp();
  src_age:=extract(epoch from issued-src.captured_at);
  if issued>=l.issue_until then refusal:='ISSUE_WINDOW_CLOSED';
  elsif src.known_at>issued then refusal:='SOURCE_KNOWN_AFTER_ISSUE';
  elsif src_age<0 then refusal:='SOURCE_CAPTURE_AFTER_ISSUE';
  elsif src_age>l.max_source_age_seconds then refusal:='SOURCE_STALE_AT_ISSUE';
  else refusal:=null; end if;
  if refusal is not null then
   for cand in select * from jsonb_populate_recordset(null::private.rolling72_mvp_research_v1_candidates,candidate_rows) order by horizon_hours loop
    insert into private.rolling72_mvp_persistence_v1_issue_attempts(
     candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(cand.id,cand.ticket_event_id,cand.seal_id,cand.horizon_hours,cand.status,issued,'REFUSED',refusal)
    on conflict(candidate_id) do nothing;
    count_refused:=count_refused+1;
   end loop;
   result_rows:=result_rows||jsonb_build_array(jsonb_build_object('seal_id',src.id,'status','REFUSED','reason',refusal,
    'issued_at',issued,'source_age_seconds',src_age));
   count_seals:=count_seals+1;
   continue;
  end if;
  insert into private.rolling72_mvp_persistence_v1_issue_bundles(
   seal_id,ticket_event_id,source_known_at,source_captured_at,source_read_completed_at,source_age_seconds,
   source_content_sha256,input_available_total,scope_status,sector_count,prior_sector_count,sector_count_delta,
   membership_change_count,transition,calculation_completed_at,read_completed_at,issued_at,kickoff_at)
  values(src.id,src.ticket_event_id,src.known_at,src.captured_at,src.read_completed_at,src_age,
   src.source_content_sha256,val,scope_stat,src.sector_count,
   (src.transition->>'prior_sector_count')::integer,(src.transition->>'sector_count_delta')::integer,
   (src.transition->>'price_area_membership_change_count')::integer,src.transition,calc_done,read_done,issued,reg.kickoff_at)
  returning id into v_bundle_id;
  for cand in select * from jsonb_populate_recordset(null::private.rolling72_mvp_research_v1_candidates,candidate_rows) order by horizon_hours loop
   if issued+make_interval(hours=>cand.horizon_hours)<reg.kickoff_at then
    p_status:='ISSUED'; p_value:=val; count_numeric:=count_numeric+1;
   else
    p_status:='OUTSIDE_KICKOFF'; p_value:=null; count_outside:=count_outside+1;
   end if;
   insert into private.rolling72_mvp_persistence_v1_predictions(
   bundle_id,candidate_id,ticket_event_id,horizon_hours,issued_at,target_at,kickoff_at,
    source_candidate_status,status,prediction,origin_available_total,source_seal_id,source_content_sha256,
    source_scope_status,source_sector_count,source_prior_sector_count,source_sector_count_delta,
    source_membership_change_count,source_transition)
   values(v_bundle_id,cand.id,src.ticket_event_id,cand.horizon_hours,issued,
    issued+make_interval(hours=>cand.horizon_hours),reg.kickoff_at,cand.status,p_status,p_value,val,
    src.id,src.source_content_sha256,scope_stat,src.sector_count,
    (src.transition->>'prior_sector_count')::integer,(src.transition->>'sector_count_delta')::integer,
    (src.transition->>'price_area_membership_change_count')::integer,src.transition)
   returning id into pred_id;
   insert into private.rolling72_mvp_persistence_v1_issue_attempts(
    candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,
    bundle_id,prediction_id)
   values(cand.id,cand.ticket_event_id,cand.seal_id,cand.horizon_hours,cand.status,issued,'ISSUED',v_bundle_id,pred_id)
   on conflict(candidate_id) do nothing;
  end loop;
  count_bundles:=count_bundles+1;
  count_seals:=count_seals+1;
  result_rows:=result_rows||jsonb_build_array(jsonb_build_object('seal_id',src.id,'bundle_id',v_bundle_id,
   'status','ISSUED','issued_at',issued,'source_age_seconds',src_age,'predictions',
   (select jsonb_agg(jsonb_build_object('prediction_id',p.id,'horizon_hours',p.horizon_hours,
      'target_at',p.target_at,'status',p.status,'prediction',p.prediction) order by p.horizon_hours)
    from private.rolling72_mvp_persistence_v1_predictions p where p.bundle_id=v_bundle_id)));
 end loop;
 insert into private.rolling72_mvp_persistence_v1_runs values(run_id,'ISSUE',started,clock_timestamp(),
  case when count_seals=0 then 'EMPTY' else 'COMPLETED' end,p_limit,count_seals,
  jsonb_build_object('processed_source_seals',count_seals,'bundles',count_bundles,
   'numeric_forecasts',count_numeric,'outside_kickoff',count_outside,'refused_candidates',count_refused));
 return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','lane_id',l.lane_id,
  'run_id',run_id,'status',case when count_seals=0 then 'EMPTY' else 'COMPLETED' end,
  'processed_source_seals',count_seals,'processed_bundles',count_bundles,
  'numeric_forecasts',count_numeric,'outside_kickoff',count_outside,
  'refused_candidates',count_refused,'results',result_rows);
end $$;

create function public.score_rolling72_mvp_persistence_v1(p_limit integer default 100)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 l private.rolling72_mvp_persistence_v1_lane%rowtype; run_id uuid:=gen_random_uuid();
 started timestamptz:=clock_timestamp(); watermark timestamptz; score_clock timestamptz; entry_snapshot pg_snapshot;
 p record; unknown_attempt record; selected_seal record;
 selected_source_attempt_id bigint; selected_snapshot_id bigint;
 latest_by_snapshot record; label_id bigint; score_status text; score_reason text;
 n_processed integer:=0; n_scored integer:=0; n_waiting integer:=0; n_refused integer:=0;
 results jsonb:='[]'::jsonb; latest_attempt_known timestamptz; latest_trustworthy_known timestamptz;
 hash_ok boolean;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_PERSISTENCE_READ_COMMITTED_REQUIRED'; end if;
 if p_limit is null or p_limit not between 1 and 100 then raise exception 'MVP_PERSISTENCE_SCORE_LIMIT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-persistence-v1:runtime',20261123));
 select * into l from private.rolling72_mvp_persistence_v1_lane;
 if not found then raise exception 'MVP_PERSISTENCE_NOT_ACTIVATED'; end if;
 entry_snapshot:=pg_current_snapshot();
 watermark:=clock_timestamp();
 if watermark>=l.scoring_until then
  insert into private.rolling72_mvp_persistence_v1_runs values(run_id,'SCORE',started,watermark,
   'SCORING_WINDOW_CLOSED',p_limit,0,jsonb_build_object('reason','SCORING_WINDOW_CLOSED'));
  return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','lane_id',l.lane_id,
   'run_id',run_id,'status','SCORING_WINDOW_CLOSED','watermark',watermark,'processed',0,'labels',0,'results','[]'::jsonb);
 end if;
 for p in
  select pr.*,b.kickoff_at bundle_kickoff,b.issued_at bundle_issued_at,b.id bundle_key
  from private.rolling72_mvp_persistence_v1_predictions pr
  join private.rolling72_mvp_persistence_v1_issue_bundles b on b.id=pr.bundle_id
  where pr.status='ISSUED' and pr.prediction is not null and pr.target_at<=watermark
   and not exists(select 1 from private.rolling72_mvp_persistence_v1_labels z where z.prediction_id=pr.id)
  order by pr.target_at,pr.id limit p_limit
 loop
  score_status:=null; score_reason:=null; selected_seal:=null; label_id:=null; score_clock:=null;
  selected_source_attempt_id:=null; selected_snapshot_id:=null;
  if p.target_at>=p.bundle_kickoff then
   score_status:='OUTSIDE_KICKOFF'; score_reason:='TARGET_NOT_PRE_KICKOFF';
  else
   -- Per snapshot, use the newest source attempt known at this exact scoring watermark.
   -- Select the newest captured observation first; validate it second, with no older fallback.
   select a.* into unknown_attempt
   from private.rolling72_mvp_research_v1_attempts a
   where a.ticket_event_id=p.ticket_event_id and a.known_at>p.issued_at and a.known_at<=watermark
    and a.captured_at is null and a.status='INTERNAL_ERROR'
   order by a.known_at desc,a.id desc limit 1;
   with latest_per_snapshot as materialized(
    select distinct on(a.snapshot_id) a.*,a.xmin as tuple_xmin
    from private.rolling72_mvp_research_v1_attempts a
    where a.ticket_event_id=p.ticket_event_id and a.snapshot_id is not null
     and a.known_at>p.issued_at and a.known_at<=watermark
    order by a.snapshot_id,a.known_at desc,a.id desc
   )
   select q.* into latest_by_snapshot from latest_per_snapshot q
   where q.captured_at>p.issued_at and q.captured_at<=p.target_at
   order by q.captured_at desc,q.snapshot_id desc limit 1;
   if latest_by_snapshot.id is not null then
    select s.*,s.xmin as tuple_xmin into selected_seal from private.rolling72_mvp_research_v1_seals s
     where s.ticket_event_id=p.ticket_event_id and s.snapshot_id=latest_by_snapshot.snapshot_id;
   end if;
   score_clock:=clock_timestamp();
   if score_clock>=l.scoring_until then
    score_status:='EXPIRED'; score_reason:='SCORING_WINDOW_CLOSED';
   elsif unknown_attempt.id is not null and
      (latest_by_snapshot.id is null or unknown_attempt.known_at>latest_by_snapshot.known_at) then
    score_status:='SOURCE_ORDER_UNKNOWN'; score_reason:='UNRESOLVED_CAPTURE_TIME_AFTER_LAST_TRUSTWORTHY_SOURCE';
   elsif latest_by_snapshot.id is null then
    score_status:='WAITING'; score_reason:='NO_OBSERVED_POST_ISSUE_TARGET_SOURCE';
   else
    selected_source_attempt_id:=latest_by_snapshot.id;
    selected_snapshot_id:=latest_by_snapshot.snapshot_id;
    if latest_by_snapshot.status not in('READY','NO_NEW_SOURCE') or selected_seal.id is null then
     score_status:='SOURCE_INVALID'; score_reason:=coalesce(latest_by_snapshot.reason,'LATEST_SOURCE_HAS_NO_READY_SEAL');
    elsif latest_by_snapshot.attempt_binding_sha256 !~ '^[0-9a-f]{64}$'
      or latest_by_snapshot.source_content_sha256<>selected_seal.source_content_sha256
      or latest_by_snapshot.captured_at<>selected_seal.captured_at
      or latest_by_snapshot.raw_source is distinct from selected_seal.source_payload
      or private.rolling72_mvp_persistence_v1_hash(selected_seal.source_payload)<>selected_seal.source_content_sha256
      or (latest_by_snapshot.status='READY' and selected_seal.attempt_id<>latest_by_snapshot.id)
      or latest_by_snapshot.attempt_binding_sha256<>private.rolling72_mvp_persistence_v1_hash(latest_by_snapshot.binding_payload)
      or latest_by_snapshot.binding_payload is distinct from jsonb_build_object('attempt_id',latest_by_snapshot.id,
       'run_id',latest_by_snapshot.run_id,'lane_id',l.source_lane_id,
       'ticket_event_id',latest_by_snapshot.ticket_event_id,'snapshot_id',latest_by_snapshot.snapshot_id,
       'source_content_sha256',latest_by_snapshot.source_content_sha256,
       'read_started_at',latest_by_snapshot.read_started_at,'read_completed_at',latest_by_snapshot.read_completed_at,
       'known_at',latest_by_snapshot.known_at,'status',latest_by_snapshot.status,'reason',latest_by_snapshot.reason)
      or not private.rolling72_mvp_persistence_v1_committed(latest_by_snapshot.tuple_xmin,entry_snapshot)
      or not private.rolling72_mvp_persistence_v1_committed(selected_seal.tuple_xmin,entry_snapshot)
    then score_status:='SOURCE_MISMATCH'; score_reason:='LATEST_SOURCE_HASH_OR_COMMIT_MISMATCH';
    elsif latest_by_snapshot.known_at>score_clock then
     score_status:='SOURCE_INVALID'; score_reason:='SOURCE_KNOWN_AFTER_SCORE_CLOCK';
    elsif selected_seal.source_payload->>'source_family' is distinct from l.source_family
      or selected_seal.source_payload->>'unit' is distinct from l.unit
      or selected_seal.ticket_event_id<>p.ticket_event_id
    then score_status:='SOURCE_MISMATCH'; score_reason:='SOURCE_EVENT_FAMILY_OR_UNIT_MISMATCH';
    elsif p.target_at-selected_seal.captured_at>interval '6 hours' then
     score_status:='SOURCE_STALE'; score_reason:='TARGET_SOURCE_OLDER_THAN_SIX_HOURS';
    elsif p.target_at-selected_seal.captured_at<interval '0 seconds' then
     score_status:='SOURCE_INVALID'; score_reason:='SOURCE_AFTER_TARGET';
    else
     insert into private.rolling72_mvp_persistence_v1_labels(
      prediction_id,ticket_event_id,horizon_hours,source_seal_id,source_attempt_id,snapshot_id,
      actual_available_total,source_captured_at,source_known_at,scored_at,target_age_seconds,
      source_content_sha256,source_scope_status,source_sector_count,source_prior_sector_count,
      source_sector_count_delta,source_membership_change_count,source_transition,
      prediction,signed_error,absolute_error)
     values(p.id,p.ticket_event_id,p.horizon_hours,selected_seal.id,latest_by_snapshot.id,selected_seal.snapshot_id,
      selected_seal.available_total,selected_seal.captured_at,selected_seal.known_at,score_clock,
      extract(epoch from p.target_at-selected_seal.captured_at),selected_seal.source_content_sha256,
      case when selected_seal.transition_status in('NO_PRIOR','COMPLETE','GAPPED') then selected_seal.transition_status else 'UNKNOWN' end,
      selected_seal.sector_count,(selected_seal.transition->>'prior_sector_count')::integer,
      (selected_seal.transition->>'sector_count_delta')::integer,
      (selected_seal.transition->>'price_area_membership_change_count')::integer,
      selected_seal.transition,p.prediction,p.prediction-selected_seal.available_total,
      abs(p.prediction-selected_seal.available_total))
     on conflict(prediction_id) do nothing returning id into label_id;
     if label_id is not null then score_status:='SCORED'; score_reason:=null; n_scored:=n_scored+1;
     else score_status:='SCORED'; score_reason:='LABEL_ALREADY_ACCEPTED'; end if;
    end if;
   end if;
  end if;
  insert into private.rolling72_mvp_persistence_v1_score_attempts(
   run_id,prediction_id,attempted_at,status,reason,selected_source_attempt_id,selected_snapshot_id,label_id)
  values(run_id,p.id,coalesce(score_clock,clock_timestamp()),score_status,score_reason,
   selected_source_attempt_id,selected_snapshot_id,label_id);
  n_processed:=n_processed+1;
  if score_status='WAITING' then n_waiting:=n_waiting+1; end if;
  if score_status not in('SCORED','WAITING') then n_refused:=n_refused+1; end if;
  results:=results||jsonb_build_array(jsonb_build_object('prediction_id',p.id,'horizon_hours',p.horizon_hours,
   'status',score_status,'reason',score_reason,'label_id',label_id,
   'source_attempt_id',selected_source_attempt_id,'snapshot_id',selected_snapshot_id));
 end loop;
 insert into private.rolling72_mvp_persistence_v1_runs values(run_id,'SCORE',started,clock_timestamp(),
  case when n_processed=0 then 'EMPTY' else 'COMPLETED' end,p_limit,n_processed,
  jsonb_build_object('labels',n_scored,'waiting',n_waiting,'refused',n_refused));
 return jsonb_build_object('schema_version','rolling72-mvp-persistence-v1','lane_id',l.lane_id,
  'run_id',run_id,'status',case when n_processed=0 then 'EMPTY' else 'COMPLETED' end,
  'watermark',watermark,'processed',n_processed,'labels',n_scored,'waiting',n_waiting,
  'refused',n_refused,'results',results);
end $$;

create function public.get_rolling72_mvp_persistence_v1_status()
returns jsonb language sql stable security definer set search_path='' set timezone='UTC' as $$
with cfg as (
 select * from private.rolling72_mvp_persistence_v1_lane where lane_id='rolling72-mvp-persistence-v1'
), c as (
 select c.id,c.status,c.seal_id,c.horizon_hours,c.ticket_event_id,s.known_at
 from private.rolling72_mvp_research_v1_candidates c
 join private.rolling72_mvp_research_v1_seals s on s.id=c.seal_id
 cross join cfg
 where s.known_at>=cfg.activated_at
), p as (
 select p.*,r.club_slug
 from private.rolling72_mvp_persistence_v1_predictions p
 join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=p.ticket_event_id
), h as (
 select horizon_hours,count(*) filter(where status='SOURCE_ELIGIBLE') eligible_source_candidates,
  count(*) filter(where status='OUTSIDE_KICKOFF') source_outside_candidates,
  count(*) filter(where status='SOURCE_ELIGIBLE' and exists(select 1 from private.rolling72_mvp_persistence_v1_issue_attempts ia where ia.candidate_id=c.id and ia.status='REFUSED')) refused_eligible,
  count(*) filter(where status='SOURCE_ELIGIBLE' and not exists(select 1 from private.rolling72_mvp_persistence_v1_issue_attempts ia where ia.candidate_id=c.id)) unattempted_eligible
 from c group by horizon_hours
), per_event as (
 select p.horizon_hours,p.ticket_event_id,p.club_slug,
  avg(l.absolute_error::numeric) event_mae,avg(l.signed_error::numeric) event_bias,count(l.id) labels
 from p left join private.rolling72_mvp_persistence_v1_labels l on l.prediction_id=p.id
 where p.status='ISSUED' and p.prediction is not null
 group by p.horizon_hours,p.ticket_event_id,p.club_slug
), scores as (
 select horizon_hours,count(*) filter(where labels>0) fixtures,
  count(distinct club_slug) filter(where labels>0) clubs,
  avg(event_mae) filter(where labels>0) event_balanced_mae,
  avg(event_bias) filter(where labels>0) event_balanced_bias
 from per_event group by horizon_hours
), pred_counts as (
 select horizon_hours,count(*) filter(where status='ISSUED' and prediction is not null) numeric_forecasts,
  count(*) filter(where status='OUTSIDE_KICKOFF') actual_outside_kickoff,
  count(*) filter(where status='ISSUED' and prediction is not null and target_at<=clock_timestamp()
    and not exists(select 1 from private.rolling72_mvp_persistence_v1_labels l where l.prediction_id=p.id)) due_unscored,
  count(*) filter(where status='ISSUED' and prediction is not null and target_at>clock_timestamp()) future_targets,
  count(*) filter(where status='ISSUED' and prediction is not null and exists(select 1 from private.rolling72_mvp_persistence_v1_labels l where l.prediction_id=p.id)) accepted_labels,
  count(distinct ticket_event_id) filter(where status='ISSUED' and prediction is not null) issued_fixtures
 from p group by horizon_hours
)
select jsonb_build_object(
 'schema_version','rolling72-mvp-persistence-v1',
 'lane_id','rolling72-mvp-persistence-v1',
 'method','PERS','target','public_available_total','scope','FULL_P0_4C_LANE',
 'activated_at',(select activated_at from cfg),'issue_until',(select issue_until from cfg),
 'scoring_until',(select scoring_until from cfg),'read_watermark',clock_timestamp(),
 'source_lane_id',(select source_lane_id from cfg),
 'source_manifest_sha256',(select source_manifest_sha256 from cfg),
 'source_sql_sha256',(select source_sql_sha256 from cfg),
 'candidate_denominator',jsonb_build_object(
  'in_scope_candidates',(select count(*) from c),
  'source_eligible',(select count(*) from c where status='SOURCE_ELIGIBLE'),
  'source_time_outside_kickoff',(select count(*) from c where status='OUTSIDE_KICKOFF'),
  'pre_activation_excluded',(select count(*) from private.rolling72_mvp_research_v1_candidates c0
    join private.rolling72_mvp_research_v1_seals s0 on s0.id=c0.seal_id cross join cfg where s0.known_at<cfg.activated_at),
  'refused',(select count(*) from private.rolling72_mvp_persistence_v1_issue_attempts where status='REFUSED'),
  'issued_candidate_attempts',(select count(*) from private.rolling72_mvp_persistence_v1_issue_attempts where status='ISSUED'),
  'unattempted',(select count(*) from c where not exists(select 1 from private.rolling72_mvp_persistence_v1_issue_attempts ia where ia.candidate_id=c.id)),
  'numeric_forecasts',(select count(*) from private.rolling72_mvp_persistence_v1_predictions where status='ISSUED' and prediction is not null),
  'outside_actual_targets',(select count(*) from private.rolling72_mvp_persistence_v1_predictions where status='OUTSIDE_KICKOFF'),
  'forecast_coverage',case when (select count(*) from c where status='SOURCE_ELIGIBLE')=0 then null
   else (select count(*)::numeric from private.rolling72_mvp_persistence_v1_predictions p0 where p0.status='ISSUED' and p0.prediction is not null)
     /(select count(*)::numeric from c where status='SOURCE_ELIGIBLE') end,
  'per_horizon',(select coalesce(jsonb_agg(jsonb_build_object('horizon_hours',h.horizon_hours,
    'eligible_source_candidates',h.eligible_source_candidates,'source_outside_candidates',h.source_outside_candidates,
    'refused_eligible',h.refused_eligible,'unattempted_eligible',h.unattempted_eligible) order by h.horizon_hours),'[]'::jsonb) from h)),
 'scorecards',(select coalesce(jsonb_agg(jsonb_build_object(
   'lane_id','rolling72-mvp-persistence-v1','target','public_available_total','method','PERS',
   'horizon_hours',x.horizon_hours,'status',case when coalesce(s.fixtures,0)=0 then 'PENDING' else 'SCORED' end,
   'issues',coalesce(pc.numeric_forecasts,0),'labels',coalesce(pc.accepted_labels,0),
   'fixtures',coalesce(s.fixtures,0),'clubs',coalesce(s.clubs,0),
   'forecast_coverage',case when coalesce(h.eligible_source_candidates,0)=0 then null else coalesce(pc.numeric_forecasts,0)::numeric/h.eligible_source_candidates end,
   'scoring_coverage',case when coalesce(pc.numeric_forecasts,0)=0 then null else coalesce(pc.accepted_labels,0)::numeric/pc.numeric_forecasts end,
   'valid_pre_kickoff_opportunities',coalesce(h.eligible_source_candidates,0),
   'numeric_forecasts',coalesce(pc.numeric_forecasts,0),
   'matured_eligible_targets',coalesce(pc.accepted_labels,0)+coalesce(pc.due_unscored,0),
   'accepted_labels',coalesce(pc.accepted_labels,0),'future_targets',coalesce(pc.future_targets,0),
   'due_unscored_targets',coalesce(pc.due_unscored,0),'outside_kickoff_targets',coalesce(pc.actual_outside_kickoff,0),
   'event_balanced_mae',s.event_balanced_mae,'event_balanced_bias',s.event_balanced_bias,
   'fallback_issues',0) order by x.horizon_hours),'[]'::jsonb)
  from (values(24),(48),(72)) x(horizon_hours)
  left join h on h.horizon_hours=x.horizon_hours
  left join pred_counts pc on pc.horizon_hours=x.horizon_hours
  left join scores s on s.horizon_hours=x.horizon_hours),
 'latest_score_attempt_statuses',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb)
   from(select status,count(*) n from private.rolling72_mvp_persistence_v1_score_attempts group by status) q),
 'production_live_adjustment',0)
$$;

do $$
declare tab text; f record;
begin
 foreach tab in array array['lane','runs','issue_bundles','predictions','issue_attempts','labels','score_attempts'] loop
  execute format('alter table private.%I enable row level security','rolling72_mvp_persistence_v1_'||tab);
  execute format('revoke all on table private.%I from public,anon,authenticated,service_role','rolling72_mvp_persistence_v1_'||tab);
  execute format('create trigger immutable_rows before update or delete on private.%I for each row execute function private.rolling72_mvp_persistence_v1_immutable()','rolling72_mvp_persistence_v1_'||tab);
  execute format('create trigger immutable_truncate before truncate on private.%I for each statement execute function private.rolling72_mvp_persistence_v1_immutable()','rolling72_mvp_persistence_v1_'||tab);
  if tab in ('issue_bundles','predictions','issue_attempts','labels','score_attempts') then
   execute format('revoke all on sequence private.%I_id_seq from public,anon,authenticated,service_role','rolling72_mvp_persistence_v1_'||tab);
  end if;
 end loop;
 for f in select p.oid::regprocedure sig from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
  where ns.nspname='private' and left(p.proname,length('rolling72_mvp_persistence_v1_'))='rolling72_mvp_persistence_v1_' loop
  execute format('revoke all on function %s from public,anon,authenticated,service_role',f.sig);
 end loop;
end $$;

revoke all on function public.activate_rolling72_mvp_persistence_v1(text,text) from public,anon,authenticated;
revoke all on function public.issue_rolling72_mvp_persistence_v1(integer) from public,anon,authenticated;
revoke all on function public.score_rolling72_mvp_persistence_v1(integer) from public,anon,authenticated;
revoke all on function public.get_rolling72_mvp_persistence_v1_status() from public,anon,authenticated;
grant execute on function public.activate_rolling72_mvp_persistence_v1(text,text) to service_role;
grant execute on function public.issue_rolling72_mvp_persistence_v1(integer) to service_role;
grant execute on function public.score_rolling72_mvp_persistence_v1(integer) to service_role;
grant execute on function public.get_rolling72_mvp_persistence_v1_status() to service_role;
