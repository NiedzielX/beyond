-- Additive fresh PERS versus fixed drift24 comparator. READY for controlled
-- deployment/review only; this file does not activate or schedule the lane.
create schema if not exists private;

create table private.rolling72_mvp_paired_drift24_v1_lane (
 lane_id text primary key check(lane_id='rolling72-mvp-paired-drift24-v1'),
 version text not null check(version='rolling72-mvp-paired-drift24-v1'),
 source_lane_id text not null check(source_lane_id='rolling72-mvp-research-v1'),
 manifest_text text not null, manifest_sha256 text not null check(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 sql_sha256 text not null check(sql_sha256 ~ '^[0-9a-f]{64}$'),
 source_manifest_sha256 text not null check(source_manifest_sha256 ~ '^[0-9a-f]{64}$'),
 source_sql_sha256 text not null check(source_sql_sha256 ~ '^[0-9a-f]{64}$'),
 b_sql_sha256 text not null check(b_sql_sha256='c9621bb692ca7de38037a204a9ca204ed3be370657b9ab89dc3aa438575effb4'),
 lad_v5_sql_sha256 text not null check(lad_v5_sql_sha256='c2a3071d7109b74040228fb6b4ee77a6524afccc7174550acb7fa362e9f7afd2'),
 source_family text not null check(source_family='roboticket/roboticket'),
 unit text not null check(unit='available_total_seats'),
 methods text[] not null check(methods=array['PERS','DRIFT24']::text[]),
 horizons_hours integer[] not null check(horizons_hours=array[24,48,72]::integer[]),
 anchor_min_hours integer not null check(anchor_min_hours=24),
 anchor_max_hours integer not null check(anchor_max_hours=30),
 max_issue_latency_seconds integer not null check(max_issue_latency_seconds=90),
 max_source_age_seconds integer not null check(max_source_age_seconds=3600),
 max_target_age_seconds integer not null check(max_target_age_seconds=21600),
 max_issue_batch integer not null check(max_issue_batch=25),
 max_score_batch integer not null check(max_score_batch=100),
 max_fixtures integer not null check(max_fixtures between 1 and 1000),
 activated_at timestamptz not null, issue_until timestamptz not null, scoring_until timestamptz not null,
 check(issue_until>activated_at), check(scoring_until>=issue_until+interval '78 hours')
);

create table private.rolling72_mvp_paired_drift24_v1_runs (
 id uuid primary key, operation text not null check(operation in('ISSUE','SCORE')),
 started_at timestamptz not null, completed_at timestamptz not null,
 status text not null, requested_limit integer not null, processed integer not null check(processed>=0),
 result_counts jsonb not null, check(completed_at>=started_at)
);

create table private.rolling72_mvp_paired_drift24_v1_issue_bundles (
 id bigint generated always as identity primary key,
 seal_id bigint not null unique references private.rolling72_mvp_research_v1_seals(id),
 ticket_event_id bigint not null references private.rolling72_mvp_research_v1_registry(ticket_event_id),
 source_known_at timestamptz not null, source_captured_at timestamptz not null,
 projection_reference_at timestamptz not null, calculation_completed_at timestamptz not null,
 issued_at timestamptz not null, issue_latency_seconds numeric not null check(issue_latency_seconds between 0 and 90),
 source_age_seconds numeric not null check(source_age_seconds between 0 and 3600),
 kickoff_at timestamptz not null, origin_available_total bigint not null check(origin_available_total>=0),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 origin_sector_count integer not null check(origin_sector_count>0), origin_membership jsonb not null,
 origin_membership_sha256 text not null check(origin_membership_sha256 ~ '^[0-9a-f]{64}$'),
 origin_transition_status text not null, origin_transition jsonb not null,
 anchor_seal_id bigint references private.rolling72_mvp_research_v1_seals(id),
 anchor_captured_at timestamptz, anchor_known_at timestamptz,
 anchor_available_total bigint, anchor_sector_count integer, anchor_membership jsonb,
 anchor_membership_sha256 text, anchor_transition_status text, anchor_transition jsonb,
 drift_status text not null check(drift_status in('READY','FALLBACK_PERS')),
 fallback_reason text check(fallback_reason in('NO_24H_ANCHOR','SOURCE_BREAK','SCOPE_MISMATCH')),
 slope24 double precision, age_hours double precision not null,
 history_input_sha256 text not null check(history_input_sha256 ~ '^[0-9a-f]{64}$'),
 check(projection_reference_at>=source_known_at),
 check(source_captured_at<=source_known_at),
 check(calculation_completed_at>=projection_reference_at), check(issued_at>calculation_completed_at),
 check(issued_at>=projection_reference_at),
 check(source_age_seconds=extract(epoch from issued_at-source_captured_at)),
 check(issue_latency_seconds=extract(epoch from issued_at-projection_reference_at)),
 check((drift_status='READY' and fallback_reason is null and anchor_seal_id is not null and slope24 is not null)
    or (drift_status='FALLBACK_PERS' and fallback_reason is not null)),
 unique(id,ticket_event_id)
);

create table private.rolling72_mvp_paired_drift24_v1_predictions (
 id bigint generated always as identity primary key,
 bundle_id bigint not null, ticket_event_id bigint not null,
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 method text not null check(method in('PERS','DRIFT24')),
 issued_at timestamptz not null, target_at timestamptz not null, kickoff_at timestamptz not null,
 status text not null check(status in('READY','FALLBACK_PERS','OUTSIDE_KICKOFF')),
 prediction double precision,
 fallback_reason text check(fallback_reason in('NO_24H_ANCHOR','SOURCE_BREAK','SCOPE_MISMATCH')),
 origin_available_total bigint not null check(origin_available_total>=0),
 source_seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 unique(bundle_id,horizon_hours,method), unique(id,ticket_event_id),
 foreign key(bundle_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_issue_bundles(id,ticket_event_id),
 check(target_at=issued_at+make_interval(hours=>horizon_hours)),
 check((status='OUTSIDE_KICKOFF' and target_at>=kickoff_at and prediction is null and fallback_reason is null)
   or (status in('READY','FALLBACK_PERS') and target_at<kickoff_at and prediction is not null and prediction>=0
      and prediction not in('Infinity'::double precision,'-Infinity'::double precision,'NaN'::double precision)
      and ((status='FALLBACK_PERS' and method='DRIFT24' and prediction=origin_available_total and fallback_reason is not null)
        or (status='READY' and fallback_reason is null))))
);

create table private.rolling72_mvp_paired_drift24_v1_issue_attempts (
 id bigint generated always as identity primary key,
 run_id uuid not null references private.rolling72_mvp_paired_drift24_v1_runs(id) deferrable initially deferred,
 candidate_id bigint not null references private.rolling72_mvp_research_v1_candidates(id),
 ticket_event_id bigint not null, seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 source_candidate_status text not null check(source_candidate_status in('SOURCE_ELIGIBLE','OUTSIDE_KICKOFF')),
 attempted_at timestamptz not null, status text not null check(status in('ISSUED','REFUSED','DEFERRED')),
 reason text, bundle_id bigint, prediction_pers_id bigint, prediction_drift24_id bigint,
 foreign key(bundle_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_issue_bundles(id,ticket_event_id),
 foreign key(prediction_pers_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_predictions(id,ticket_event_id),
 foreign key(prediction_drift24_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_predictions(id,ticket_event_id),
 check((status='ISSUED' and reason is null and bundle_id is not null and prediction_pers_id is not null
        and prediction_drift24_id is not null)
    or (status in('REFUSED','DEFERRED') and reason is not null and prediction_pers_id is null
        and prediction_drift24_id is null))
);

create table private.rolling72_mvp_paired_drift24_v1_labels (
 id bigint generated always as identity primary key, bundle_id bigint not null,
 ticket_event_id bigint not null, horizon_hours integer not null check(horizon_hours in(24,48,72)),
 target_seal_id bigint not null references private.rolling72_mvp_research_v1_seals(id),
 target_attempt_id bigint not null references private.rolling72_mvp_research_v1_attempts(id),
 snapshot_id bigint not null, actual_available_total bigint not null check(actual_available_total>=0),
 source_captured_at timestamptz not null, source_known_at timestamptz not null,
 scored_at timestamptz not null, target_age_seconds numeric not null check(target_age_seconds between 0 and 21600),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 source_status text not null, source_transition_status text not null, source_transition jsonb not null,
 sector_count integer not null check(sector_count>0), membership jsonb not null,
 membership_sha256 text not null check(membership_sha256 ~ '^[0-9a-f]{64}$'),
 origin_membership_changed boolean not null, origin_sector_count_delta integer not null,
 pers_prediction_id bigint not null, drift24_prediction_id bigint not null,
 pers_prediction double precision not null, drift24_prediction double precision not null,
 pers_signed_error double precision not null, drift24_signed_error double precision not null,
 pers_absolute_error double precision not null check(pers_absolute_error>=0),
 drift24_absolute_error double precision not null check(drift24_absolute_error>=0),
 foreign key(bundle_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_issue_bundles(id,ticket_event_id),
 foreign key(pers_prediction_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_predictions(id,ticket_event_id),
 foreign key(drift24_prediction_id,ticket_event_id)
  references private.rolling72_mvp_paired_drift24_v1_predictions(id,ticket_event_id),
 unique(bundle_id,horizon_hours), check(source_known_at<=scored_at),
 check(pers_signed_error=pers_prediction-actual_available_total),
 check(drift24_signed_error=drift24_prediction-actual_available_total),
 check(pers_absolute_error=abs(pers_signed_error)),
 check(drift24_absolute_error=abs(drift24_signed_error))
);

create table private.rolling72_mvp_paired_drift24_v1_score_attempts (
 id bigint generated always as identity primary key,
 run_id uuid not null references private.rolling72_mvp_paired_drift24_v1_runs(id) deferrable initially deferred,
 bundle_id bigint not null references private.rolling72_mvp_paired_drift24_v1_issue_bundles(id),
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 attempted_at timestamptz not null,
 status text not null check(status in('SCORED','WAITING','SOURCE_ORDER_UNKNOWN','SOURCE_INVALID',
  'SOURCE_MISMATCH','SOURCE_STALE','OUTSIDE_KICKOFF','EXPIRED')),
 reason text, selected_attempt_id bigint references private.rolling72_mvp_research_v1_attempts(id),
 selected_snapshot_id bigint, label_id bigint references private.rolling72_mvp_paired_drift24_v1_labels(id)
);

create unique index rolling72_mvp_paired_drift24_v1_terminal_candidate_idx
 on private.rolling72_mvp_paired_drift24_v1_issue_attempts(candidate_id)
 where status in('ISSUED','REFUSED');

create index rolling72_mvp_paired_drift24_v1_issue_attempt_candidate_idx
 on private.rolling72_mvp_paired_drift24_v1_issue_attempts(candidate_id,attempted_at desc,id desc);

create index rolling72_mvp_paired_drift24_v1_predictions_due_idx
 on private.rolling72_mvp_paired_drift24_v1_predictions(target_at,bundle_id,horizon_hours)
 where status in('READY','FALLBACK_PERS');

create function private.rolling72_mvp_paired_drift24_v1_immutable()
returns trigger language plpgsql set search_path='' as $$
begin raise exception 'ROLLING72_MVP_PAIRED_DRIFT24_IMMUTABLE'; end $$;

create function private.rolling72_mvp_paired_drift24_v1_hash(p_value jsonb)
returns text language sql immutable set search_path='' as $$
 select encode(sha256(convert_to(p_value::text,'UTF8')),'hex')
$$;

create function private.rolling72_mvp_paired_drift24_v1_committed(p_xid xid,p_snapshot pg_snapshot)
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

-- Pure checks over the one cached immutable source read. No upstream reread.
create function private.rolling72_mvp_paired_drift24_v1_membership(p_payload jsonb)
returns jsonb language sql immutable set search_path='' as $$
 select jsonb_build_object(
  'sector_ids',coalesce((select jsonb_agg(sk order by sk) from (
    select distinct x->>'sector_source_id' sk
    from jsonb_array_elements(p_payload->'sector_price_area_rows') x) q),'[]'::jsonb),
  'pairs',coalesce((select jsonb_agg(jsonb_build_array(sk,pa) order by sk,pa) from (
    select x->>'sector_source_id' sk,x->>'price_area_id' pa
    from jsonb_array_elements(p_payload->'sector_price_area_rows') x) q),'[]'::jsonb))
$$;

create function private.rolling72_mvp_paired_drift24_v1_valid_seal(s jsonb,a jsonb,r jsonb)
returns boolean language plpgsql immutable set search_path='' set timezone='UTC' as $$
declare p jsonb; sn jsonb; m jsonb;
begin
 if jsonb_typeof(s) is distinct from 'object' or jsonb_typeof(a) is distinct from 'object'
  or jsonb_typeof(r) is distinct from 'object' then return false; end if;
 p:=s->'source_payload'; sn:=p->'snapshot';
 if jsonb_typeof(p) is distinct from 'object'
  or jsonb_typeof(p->'sector_price_area_rows') is distinct from 'array'
  or jsonb_array_length(p->'sector_price_area_rows')=0 then return false; end if;
 m:=private.rolling72_mvp_paired_drift24_v1_membership(p);
 return coalesce(
  p->>'lane_id'='rolling72-mvp-research-v1'
  and p->>'source_family'='roboticket/roboticket' and p->>'unit'='available_total_seats'
  and private.rolling72_mvp_paired_drift24_v1_hash(p)=s->>'source_content_sha256'
  and private.rolling72_mvp_paired_drift24_v1_hash(sn)=s->>'snapshot_sha256'
  and s->>'snapshot_sha256'=a->>'snapshot_sha256'
  and p=a->'raw_source' and s->>'source_content_sha256'=a->>'source_content_sha256'
  and (s->>'attempt_id')::bigint=(a->>'id')::bigint and a->>'status'='READY'
  and (s->>'ticket_event_id')::bigint=(a->>'ticket_event_id')::bigint
  and (s->>'ticket_event_id')::bigint=(r->>'ticket_event_id')::bigint
  and (s->>'snapshot_id')::bigint=(a->>'snapshot_id')::bigint
  and (s->>'snapshot_id')::bigint=(sn->>'id')::bigint
  and (s->>'ticket_event_id')::bigint=(sn->>'ticket_event_id')::bigint
  and (s->>'captured_at')::timestamptz=(a->>'captured_at')::timestamptz
  and (s->>'captured_at')::timestamptz=(sn->>'captured_at')::timestamptz
  and (s->>'known_at')::timestamptz=(a->>'known_at')::timestamptz
  and (s->>'read_started_at')::timestamptz=(a->>'read_started_at')::timestamptz
  and (s->>'read_completed_at')::timestamptz=(a->>'read_completed_at')::timestamptz
  and (s->>'captured_at')::timestamptz<=(s->>'known_at')::timestamptz
  and (s->>'available_total')::bigint=(sn->>'available_total')::bigint
  and (s->>'sector_count')::integer=(sn->>'sector_count')::integer
  and (s->>'sector_count')::integer=jsonb_array_length(m->'sector_ids')
  and not exists(select 1 from jsonb_array_elements(p->'sector_price_area_rows') x
    where coalesce(x->>'sector_source_id','')!~'^[0-9]+$'
      or coalesce(x->>'price_area_id','')!~'^[0-9]+$')
  and not exists(select 1 from jsonb_array_elements(p->'sector_price_area_rows') x
    group by x->>'sector_source_id',x->>'price_area_id' having count(*)>1)
  and r->>'lane_id'='rolling72-mvp-research-v1'
  and private.rolling72_mvp_paired_drift24_v1_hash(r->'binding')=r->>'binding_sha256'
  and private.rolling72_mvp_paired_drift24_v1_hash(p->'admission')=r->>'admission_sha256'
  and (p->'admission'->>'id')::bigint=(r->>'admission_receipt_id')::bigint
  and p->'binding'=r->'binding'
  and (r->'binding'->>'ticket_event_id')::bigint=(r->>'ticket_event_id')::bigint
  and r->'binding'->>'external_event_id'=r->>'external_event_id'
  and r->'binding'->>'club_slug'=r->>'club_slug'
  and (r->'binding'->>'kickoff_at')::timestamptz=(r->>'kickoff_at')::timestamptz
  and private.rolling72_mvp_paired_drift24_v1_hash(a->'binding_payload')=a->>'attempt_binding_sha256'
  and a->'binding_payload'=jsonb_build_object(
   'attempt_id',(a->>'id')::bigint,'run_id',a->>'run_id','lane_id','rolling72-mvp-research-v1',
   'ticket_event_id',(a->>'ticket_event_id')::bigint,'snapshot_id',(a->>'snapshot_id')::bigint,
   'source_content_sha256',a->>'source_content_sha256','read_started_at',a->'read_started_at',
   'read_completed_at',a->'read_completed_at','known_at',a->'known_at','status',a->>'status','reason',a->'reason'),false);
exception when data_exception then return false;
end $$;

create function public.issue_rolling72_mvp_paired_drift24_v1(p_limit integer default 25)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare l private.rolling72_mvp_paired_drift24_v1_lane%rowtype;
 run_id uuid:=gen_random_uuid(); started timestamptz:=clock_timestamp(); entry_snapshot pg_snapshot;
 seal_key record; origin jsonb; origin_xmin xid; source_attempt jsonb; attempt_xmin xid;
 registry jsonb; registry_xmin xid; candidate_rows jsonb; history_rows jsonb; history_attempts jsonb;
 projection_ref timestamptz; calc_done timestamptz; issued timestamptz; latency numeric; source_age numeric;
 event_id bigint; seal_id bigint; origin_known timestamptz; origin_captured timestamptz;
 kickoff timestamptz; available bigint; family text; unit_name text; membership jsonb; membership_hash text;
 anchor jsonb; anchor_id bigint; anchor_capture timestamptz; anchor_known timestamptz;
 anchor_available bigint; anchor_membership jsonb; anchor_membership_hash text; anchor_sector_count integer;
 origin_sector_count integer; origin_transition jsonb; origin_transition_status text;
 anchor_transition jsonb; anchor_transition_status text; elapsed double precision; age double precision;
 slope double precision; estimate double precision; drift_state text; fallback text; break_row jsonb;
 rowj jsonb; attemptj jsonb; cand record; pers_id bigint; drift_id bigint; v_bundle_id bigint;
 h integer; method_name text; target timestamptz; status_name text; prediction_value double precision;
 predictions jsonb; results jsonb:='[]'::jsonb; numeric_count integer:=0; outside_count integer:=0;
 refused_count integer:=0; processed integer:=0; bundles integer:=0; one_result jsonb;
 seal_hash text; source_payload jsonb; source_rows jsonb; source_snapshot jsonb;
 sector_n integer; valid_candidate_count integer;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'PAIRED_DRIFT24_READ_COMMITTED_REQUIRED'; end if;
 if p_limit is null or p_limit not between 1 and 25 then raise exception 'PAIRED_DRIFT24_ISSUE_LIMIT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-paired-drift24-v1:runtime',20261125));
 select * into l from private.rolling72_mvp_paired_drift24_v1_lane;
 if not found then raise exception 'PAIRED_DRIFT24_NOT_ACTIVATED'; end if;
 entry_snapshot:=pg_current_snapshot();
 if clock_timestamp()>=l.issue_until then
  insert into private.rolling72_mvp_paired_drift24_v1_runs values(run_id,'ISSUE',started,clock_timestamp(),
   'ISSUE_WINDOW_CLOSED',p_limit,0,jsonb_build_object('refused',0));
  return jsonb_build_object('schema_version',l.version,'lane_id',l.lane_id,'run_id',run_id,
   'status','ISSUE_WINDOW_CLOSED','processed_source_seals',0,'processed_bundles',0,
   'numeric_forecasts',0,'outside_kickoff',0,'refused_candidates',0,'results','[]'::jsonb);
 end if;
 for seal_key in
  select s.id seal_id,min(s.known_at) known_at
  from private.rolling72_mvp_research_v1_seals s
  join private.rolling72_mvp_research_v1_candidates c on c.seal_id=s.id
  where s.phase='ISSUE_WINDOW' and s.known_at>l.activated_at and s.known_at<l.issue_until
   and not exists(select 1 from private.rolling72_mvp_paired_drift24_v1_issue_bundles b where b.seal_id=s.id)
    and not exists(select 1 from private.rolling72_mvp_paired_drift24_v1_issue_attempts ia
     join private.rolling72_mvp_research_v1_candidates cc on cc.id=ia.candidate_id
     where cc.seal_id=s.id and ia.status in('ISSUED','REFUSED'))
   and exists(select 1 from private.rolling72_mvp_research_v1_candidates cx
      where cx.seal_id=s.id and cx.status='SOURCE_ELIGIBLE')
   and (select count(*) from private.rolling72_mvp_research_v1_candidates cx where cx.seal_id=s.id)=3
  group by s.id order by min(s.known_at),s.id limit p_limit
 loop
  perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-paired-drift24-v1:seal:'||seal_key.seal_id::text,20261125));
  -- One MVCC statement caches the origin, attempt, registry, triplet and all
  -- then-visible history/break attempts before projection_reference_at.
  select to_jsonb(s),s.xmin,to_jsonb(a),a.xmin,to_jsonb(r),r.xmin,
   coalesce((select jsonb_agg(jsonb_build_object('candidate',to_jsonb(c),'xmin',c.xmin::text)
       order by c.horizon_hours)
      from private.rolling72_mvp_research_v1_candidates c where c.seal_id=s.id),'[]'::jsonb),
   coalesce((select jsonb_agg(jsonb_build_object('seal',to_jsonb(hs),'seal_xmin',hs.xmin::text,
       'attempt',to_jsonb(ha),'attempt_xmin',ha.xmin::text) order by hs.captured_at,hs.id)
      from private.rolling72_mvp_research_v1_seals hs
      join private.rolling72_mvp_research_v1_attempts ha on ha.id=hs.attempt_id
      where hs.ticket_event_id=s.ticket_event_id and hs.captured_at<=s.captured_at
       and hs.captured_at>=s.captured_at-interval '30 hours'),'[]'::jsonb),
   coalesce((select jsonb_agg(jsonb_build_object('attempt',to_jsonb(ha),'xmin',ha.xmin::text)
       order by ha.known_at,ha.id)
      from private.rolling72_mvp_research_v1_attempts ha
      where ha.ticket_event_id=s.ticket_event_id and ha.known_at<=clock_timestamp()
       and ha.known_at>=s.captured_at-interval '30 hours'),'[]'::jsonb)
  into origin,origin_xmin,source_attempt,attempt_xmin,registry,registry_xmin,
       candidate_rows,history_rows,history_attempts
  from private.rolling72_mvp_research_v1_seals s
  join private.rolling72_mvp_research_v1_attempts a on a.id=s.attempt_id
  join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=s.ticket_event_id
  where s.id=seal_key.seal_id;
  if origin is null then continue; end if;
  projection_ref:=clock_timestamp();
  -- A row visible to the statement but not committed at RPC entry is deferred,
  -- never turned into a terminal refusal or used as an anchor.
  if not private.rolling72_mvp_paired_drift24_v1_committed(origin_xmin,entry_snapshot)
    or not private.rolling72_mvp_paired_drift24_v1_committed(attempt_xmin,entry_snapshot)
    or not private.rolling72_mvp_paired_drift24_v1_committed(registry_xmin,entry_snapshot)
    or exists(select 1 from jsonb_array_elements(candidate_rows) c
       where not private.rolling72_mvp_paired_drift24_v1_committed((c->>'xmin')::xid,entry_snapshot))
  then
   for cand in select value->'candidate' c from jsonb_array_elements(candidate_rows) order by (value->'candidate'->>'horizon_hours')::integer loop
    insert into private.rolling72_mvp_paired_drift24_v1_issue_attempts(
      run_id,candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(run_id,(cand.c->>'id')::bigint,(cand.c->>'ticket_event_id')::bigint,
      (cand.c->>'seal_id')::bigint,(cand.c->>'horizon_hours')::integer,cand.c->>'status',
      projection_ref,'DEFERRED','SOURCE_NOT_COMMITTED_AT_READ_START');
   end loop;
   results:=results||jsonb_build_array(jsonb_build_object('seal_id',seal_key.seal_id,'status','DEFERRED',
     'reason','SOURCE_NOT_COMMITTED_AT_READ_START','projection_reference_at',projection_ref));
   processed:=processed+1; continue;
  end if;
  event_id:=(origin->>'ticket_event_id')::bigint; seal_id:=(origin->>'id')::bigint;
  origin_known:=(origin->>'known_at')::timestamptz; origin_captured:=(origin->>'captured_at')::timestamptz;
  kickoff:=(registry->>'kickoff_at')::timestamptz;
  available:=(origin->>'available_total')::bigint;
  source_payload:=origin->'source_payload'; seal_hash:=origin->>'source_content_sha256';
  family:=source_payload->>'source_family'; unit_name:=source_payload->>'unit';
  source_rows:=coalesce(source_payload->'sector_price_area_rows','[]'::jsonb);
  origin_sector_count:=(origin->>'sector_count')::integer;
  membership:=case when private.rolling72_mvp_paired_drift24_v1_valid_seal(origin,source_attempt,registry)
    then private.rolling72_mvp_paired_drift24_v1_membership(source_payload)
    else jsonb_build_object('sector_ids','[]'::jsonb,'pairs','[]'::jsonb) end;
  age:=extract(epoch from projection_ref-origin_captured)::double precision/3600.0;
  membership_hash:=private.rolling72_mvp_paired_drift24_v1_hash(membership);
  origin_transition:=coalesce(origin->'transition','{}'::jsonb);
  origin_transition_status:=origin->>'transition_status';
  valid_candidate_count:=jsonb_array_length(candidate_rows);
  fallback:=null; anchor:=null; anchor_id:=null; anchor_membership:=null;
  anchor_membership_hash:=null; anchor_capture:=null; anchor_known:=null;
  anchor_available:=null; anchor_sector_count:=null; anchor_transition:=null; anchor_transition_status:=null;
  slope:=null; drift_state:='FALLBACK_PERS';
  if valid_candidate_count<>3
    or not private.rolling72_mvp_paired_drift24_v1_valid_seal(origin,source_attempt,registry)
    or origin_known>projection_ref or origin->>'phase' is distinct from 'ISSUE_WINDOW'
    or exists(select 1 from jsonb_array_elements(candidate_rows) z
       where (z->'candidate'->>'seal_id')::bigint is distinct from seal_id
        or (z->'candidate'->>'ticket_event_id')::bigint is distinct from event_id
        or (z->'candidate'->>'observation_known_at')::timestamptz is distinct from origin_known
        or z->'candidate'->>'status' is distinct from case
          when (z->'candidate'->>'provisional_target_at')::timestamptz>=kickoff
          then 'OUTSIDE_KICKOFF' else 'SOURCE_ELIGIBLE' end)
  then
   for cand in select value->'candidate' c from jsonb_array_elements(candidate_rows) order by (value->'candidate'->>'horizon_hours')::integer loop
    insert into private.rolling72_mvp_paired_drift24_v1_issue_attempts(
      run_id,candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(run_id,(cand.c->>'id')::bigint,event_id,seal_id,(cand.c->>'horizon_hours')::integer,
      cand.c->>'status',projection_ref,'REFUSED','SOURCE_ORIGIN_BINDING_INVALID');
    refused_count:=refused_count+1;
   end loop;
   results:=results||jsonb_build_array(jsonb_build_object('seal_id',seal_id,'status','REFUSED',
     'reason','SOURCE_ORIGIN_BINDING_INVALID','projection_reference_at',projection_ref));
   processed:=processed+1; continue;
  end if;
  if origin_sector_count is null or origin_sector_count<=0 or jsonb_array_length(membership->'sector_ids')=0 then
   for cand in select value->'candidate' c from jsonb_array_elements(candidate_rows) order by (value->'candidate'->>'horizon_hours')::integer loop
    insert into private.rolling72_mvp_paired_drift24_v1_issue_attempts(
      run_id,candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(run_id,(cand.c->>'id')::bigint,event_id,seal_id,(cand.c->>'horizon_hours')::integer,
      cand.c->>'status',projection_ref,'REFUSED','SOURCE_MEMBERSHIP_INVALID');
    refused_count:=refused_count+1;
   end loop;
   results:=results||jsonb_build_array(jsonb_build_object('seal_id',seal_id,'status','REFUSED',
     'reason','SOURCE_MEMBERSHIP_INVALID','projection_reference_at',projection_ref));
   processed:=processed+1; continue;
  end if;
  if fallback is null then
   -- Deterministic latest seal in the inclusive 24-30 elapsed-hour window.
   for rowj in select value from jsonb_array_elements(history_rows)
     where (value->'seal'->>'ticket_event_id')::bigint=event_id
      and (value->'seal'->>'phase')='ISSUE_WINDOW'
      and (value->'seal'->>'captured_at')::timestamptz<=origin_captured
      and (value->'seal'->>'known_at')::timestamptz<=projection_ref
      and extract(epoch from origin_captured-(value->'seal'->>'captured_at')::timestamptz)
        between 86400 and 108000
     order by (value->'seal'->>'captured_at')::timestamptz desc,
       (value->'seal'->>'id')::bigint desc
   loop
    if not private.rolling72_mvp_paired_drift24_v1_committed((rowj->>'seal_xmin')::xid,entry_snapshot)
      or not private.rolling72_mvp_paired_drift24_v1_committed((rowj->>'attempt_xmin')::xid,entry_snapshot)
    then continue; end if;
    if not private.rolling72_mvp_paired_drift24_v1_valid_seal(rowj->'seal',rowj->'attempt',registry) then
      fallback:='SOURCE_BREAK'; exit;
    end if;
    anchor:=rowj->'seal'; anchor_id:=(anchor->>'id')::bigint; exit;
   end loop;
   if anchor is null then fallback:=coalesce(fallback,'NO_24H_ANCHOR');
   else
    anchor_capture:=(anchor->>'captured_at')::timestamptz; anchor_known:=(anchor->>'known_at')::timestamptz;
    anchor_available:=(anchor->>'available_total')::bigint;
    anchor_transition:=coalesce(anchor->'transition','{}'::jsonb);
    anchor_transition_status:=anchor->>'transition_status';
    anchor_sector_count:=coalesce((anchor->'source_payload'->>'sector_count')::integer,
      (anchor->>'sector_count')::integer);
    anchor_membership:=private.rolling72_mvp_paired_drift24_v1_membership(anchor->'source_payload');
    anchor_membership_hash:=private.rolling72_mvp_paired_drift24_v1_hash(anchor_membership);
    if anchor->'source_payload'->>'source_family' is distinct from family
      or anchor->'source_payload'->>'unit' is distinct from unit_name
    then fallback:='SOURCE_BREAK';
    elsif anchor_membership is distinct from membership then fallback:='SCOPE_MISMATCH';
    end if;
    -- Seals after the selected anchor are segment boundaries when source or
    -- complete stable membership changes; count equality is not sufficient.
    for rowj in select value from jsonb_array_elements(history_rows)
      where (value->'seal'->>'ticket_event_id')::bigint=event_id
       and (value->'seal'->>'captured_at')::timestamptz>anchor_capture
       and (value->'seal'->>'captured_at')::timestamptz<=origin_captured
       and (value->'seal'->>'known_at')::timestamptz<=projection_ref
      order by (value->'seal'->>'captured_at')::timestamptz,(value->'seal'->>'id')::bigint
    loop
     if not private.rolling72_mvp_paired_drift24_v1_committed((rowj->>'seal_xmin')::xid,entry_snapshot)
       or not private.rolling72_mvp_paired_drift24_v1_committed((rowj->>'attempt_xmin')::xid,entry_snapshot) then continue; end if;
     if rowj->'seal'->'source_payload'->>'source_family' is distinct from family
       or rowj->'seal'->'source_payload'->>'unit' is distinct from unit_name then
      fallback:='SOURCE_BREAK'; exit;
     end if;
     if not private.rolling72_mvp_paired_drift24_v1_valid_seal(rowj->'seal',rowj->'attempt',registry) then
      fallback:='SOURCE_BREAK'; exit;
     end if;
     break_row:=private.rolling72_mvp_paired_drift24_v1_membership(rowj->'seal'->'source_payload');
     if break_row is distinct from membership then fallback:='SCOPE_MISMATCH'; exit; end if;
    end loop;
    if fallback is null then
     for attemptj in select value from jsonb_array_elements(history_attempts)
      where value->'attempt'->>'status' in('MISSING_SOURCE','SKIPPED_STALE','INVALID_SOURCE','INTERNAL_ERROR')
       and (value->'attempt'->>'known_at')::timestamptz<=projection_ref
       and private.rolling72_mvp_paired_drift24_v1_committed((value->>'xmin')::xid,entry_snapshot)
       and (((value->'attempt'->>'captured_at') is null
          and (value->'attempt'->>'known_at')::timestamptz>anchor_known)
        or ((value->'attempt'->>'captured_at')::timestamptz>=anchor_capture
          and (value->'attempt'->>'known_at')::timestamptz>anchor_known
          and (value->'attempt'->>'captured_at')::timestamptz<=origin_captured))
     loop fallback:='SOURCE_BREAK'; exit; end loop;
    end if;
    elapsed:=extract(epoch from origin_captured-anchor_capture)/3600.0;
    age:=extract(epoch from projection_ref-origin_captured)/3600.0;
    if fallback is null and elapsed>0 then
      slope:=(available::double precision-anchor_available::double precision)/elapsed;
      if slope is not null and slope not in('Infinity'::double precision,'-Infinity'::double precision,'NaN'::double precision)
      then drift_state:='READY'; else fallback:='NO_24H_ANCHOR'; end if;
    elsif fallback is null then fallback:='NO_24H_ANCHOR'; end if;
   end if;
  end if;
  if fallback is not null then drift_state:='FALLBACK_PERS'; slope:=null; end if;
  -- Calculate all values before taking calculation/issue clocks.
  predictions:='[]'::jsonb;
  for h in select unnest(l.horizons_hours) order by 1 loop
   for method_name in select unnest(l.methods) order by 1 loop
    if method_name='PERS' then prediction_value:=available; status_name:='READY';
    elsif drift_state='FALLBACK_PERS' then prediction_value:=available; status_name:='FALLBACK_PERS';
    else
      estimate:=greatest(0::double precision,
        available::double precision+slope*(h::double precision+age));
      if estimate is null or estimate in('Infinity'::double precision,'-Infinity'::double precision,'NaN'::double precision)
      then raise exception using errcode='22003',message='PAIRED_DRIFT24_FLOAT8_OVERFLOW'; end if;
      prediction_value:=estimate; status_name:='READY';
    end if;
    predictions:=predictions||jsonb_build_array(jsonb_build_object('horizon_hours',h,'method',method_name,
      'status',status_name,'prediction',prediction_value,
      'fallback_reason',case when method_name='DRIFT24' and status_name='FALLBACK_PERS' then fallback else null end));
   end loop;
  end loop;
  calc_done:=clock_timestamp(); issued:=clock_timestamp();
  if issued<=calc_done then
   perform pg_sleep(0.000001); issued:=clock_timestamp();
   if issued<=calc_done then raise exception using errcode='40001',message='PAIRED_DRIFT24_ISSUE_CLOCK_RETRY'; end if;
  end if;
  latency:=extract(epoch from issued-projection_ref); source_age:=extract(epoch from issued-origin_captured);
  if origin_known>issued or issued>=l.issue_until or latency<0 or latency>l.max_issue_latency_seconds
    or source_age<0 or source_age>l.max_source_age_seconds
  then
   for cand in select value->'candidate' c from jsonb_array_elements(candidate_rows) order by (value->'candidate'->>'horizon_hours')::integer loop
    insert into private.rolling72_mvp_paired_drift24_v1_issue_attempts(
      run_id,candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,reason)
    values(run_id,(cand.c->>'id')::bigint,event_id,seal_id,(cand.c->>'horizon_hours')::integer,
      cand.c->>'status',issued,'REFUSED',case when latency>90 then 'ISSUE_LATENCY_EXCEEDED'
      when source_age>3600 then 'SOURCE_STALE_AT_ISSUE' else 'ISSUE_CLOCK_OR_WINDOW_INVALID' end)
;
    refused_count:=refused_count+1;
   end loop;
   processed:=processed+1;
   results:=results||jsonb_build_array(jsonb_build_object('seal_id',seal_id,'status','REFUSED',
     'reason',case when latency>90 then 'ISSUE_LATENCY_EXCEEDED' when source_age>3600 then 'SOURCE_STALE_AT_ISSUE'
       else 'ISSUE_CLOCK_OR_WINDOW_INVALID' end,'projection_reference_at',projection_ref,'issued_at',issued));
   continue;
  end if;
  insert into private.rolling72_mvp_paired_drift24_v1_issue_bundles(
   seal_id,ticket_event_id,source_known_at,source_captured_at,projection_reference_at,calculation_completed_at,
   issued_at,issue_latency_seconds,source_age_seconds,kickoff_at,origin_available_total,source_content_sha256,
   origin_sector_count,origin_membership,origin_membership_sha256,origin_transition_status,origin_transition,
   anchor_seal_id,anchor_captured_at,anchor_known_at,anchor_available_total,anchor_sector_count,
   anchor_membership,anchor_membership_sha256,anchor_transition_status,anchor_transition,
   drift_status,fallback_reason,slope24,age_hours,history_input_sha256)
  values(seal_id,event_id,origin_known,origin_captured,projection_ref,calc_done,issued,latency,source_age,kickoff,
   available,seal_hash,origin_sector_count,membership,membership_hash,origin_transition_status,origin_transition,
   anchor_id,anchor_capture,anchor_known,anchor_available,anchor_sector_count,anchor_membership,
   anchor_membership_hash,anchor_transition_status,anchor_transition,drift_state,fallback,slope,age,
   private.rolling72_mvp_paired_drift24_v1_hash(history_rows||history_attempts)) returning id into v_bundle_id;
  for rowj in select value from jsonb_array_elements(predictions) order by (value->>'horizon_hours')::integer,
        case value->>'method' when 'PERS' then 0 else 1 end loop
   h:=(rowj->>'horizon_hours')::integer; method_name:=rowj->>'method'; target:=issued+make_interval(hours=>h);
   if target>=kickoff then status_name:='OUTSIDE_KICKOFF'; prediction_value:=null; outside_count:=outside_count+1;
   else status_name:=rowj->>'status'; prediction_value:=(rowj->>'prediction')::double precision; numeric_count:=numeric_count+1; end if;
   insert into private.rolling72_mvp_paired_drift24_v1_predictions(
    bundle_id,ticket_event_id,horizon_hours,method,issued_at,target_at,kickoff_at,status,prediction,fallback_reason,
    origin_available_total,source_seal_id,source_content_sha256)
   values(v_bundle_id,event_id,h,method_name,issued,target,kickoff,status_name,prediction_value,
    case when status_name='OUTSIDE_KICKOFF' then null else rowj->>'fallback_reason' end,
    available,seal_id,seal_hash) returning id into pers_id;
  end loop;
  for h in select unnest(l.horizons_hours) order by 1 loop
   select p.id into pers_id from private.rolling72_mvp_paired_drift24_v1_predictions p
    where p.bundle_id=v_bundle_id and p.horizon_hours=h and p.method='PERS';
   select p.id into drift_id from private.rolling72_mvp_paired_drift24_v1_predictions p
    where p.bundle_id=v_bundle_id and p.horizon_hours=h and p.method='DRIFT24';
   insert into private.rolling72_mvp_paired_drift24_v1_issue_attempts(
    run_id,candidate_id,ticket_event_id,seal_id,horizon_hours,source_candidate_status,attempted_at,status,
    bundle_id,prediction_pers_id,prediction_drift24_id)
   select run_id,(z->'candidate'->>'id')::bigint,event_id,seal_id,h,z->'candidate'->>'status',
    issued,'ISSUED',v_bundle_id,pers_id,drift_id
   from jsonb_array_elements(candidate_rows) z where (z->'candidate'->>'horizon_hours')::integer=h;
  end loop;
  bundles:=bundles+1; processed:=processed+1;
  select jsonb_agg(jsonb_build_object('horizon_hours',p.horizon_hours,'method',p.method,
      'target_at',p.target_at,'status',p.status,'prediction',p.prediction,'fallback_reason',p.fallback_reason)
      order by p.horizon_hours,case p.method when 'PERS' then 0 else 1 end)
   into one_result from private.rolling72_mvp_paired_drift24_v1_predictions p where p.bundle_id=v_bundle_id;
  results:=results||jsonb_build_array(jsonb_build_object('seal_id',seal_id,'bundle_id',v_bundle_id,
    'status','ISSUED','projection_reference_at',projection_ref,'calculation_completed_at',calc_done,
    'issued_at',issued,'latency_seconds',latency,'source_age_seconds',source_age,
    'drift_status',drift_state,'fallback_reason',fallback,'predictions',one_result));
 end loop;
 insert into private.rolling72_mvp_paired_drift24_v1_runs values(run_id,'ISSUE',started,clock_timestamp(),
  case when processed=0 then 'EMPTY' else 'COMPLETED' end,p_limit,processed,
  jsonb_build_object('bundles',bundles,'numeric_forecasts',numeric_count,'outside_kickoff',outside_count,
   'refused_candidates',refused_count));
 return jsonb_build_object('schema_version',l.version,'lane_id',l.lane_id,'run_id',run_id,
  'status',case when processed=0 then 'EMPTY' else 'COMPLETED' end,'processed_source_seals',processed,
  'processed_bundles',bundles,'numeric_forecasts',numeric_count,'outside_kickoff',outside_count,
  'refused_candidates',refused_count,'results',results);
end $$;

create function public.activate_rolling72_mvp_paired_drift24_v1(p_manifest_text text,p_manifest_sha256 text)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare j jsonb; src private.rolling72_mvp_research_v1_lane%rowtype;
 old private.rolling72_mvp_paired_drift24_v1_lane%rowtype; t timestamptz;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'PAIRED_DRIFT24_READ_COMMITTED_REQUIRED'; end if;
 if p_manifest_text is null or octet_length(convert_to(p_manifest_text,'UTF8'))>32768
  or p_manifest_sha256 is null or p_manifest_sha256 !~ '^[0-9a-f]{64}$'
  or p_manifest_sha256 is distinct from encode(sha256(convert_to(p_manifest_text,'UTF8')),'hex')
 then raise exception 'PAIRED_DRIFT24_MANIFEST_HASH'; end if;
 j:=p_manifest_text::jsonb;
 if jsonb_typeof(j) is distinct from 'object' or (select count(*) from jsonb_object_keys(j))<>22
  or j->>'lane_id' is distinct from 'rolling72-mvp-paired-drift24-v1'
  or j->>'version' is distinct from 'rolling72-mvp-paired-drift24-v1'
  or j->>'source_lane_id' is distinct from 'rolling72-mvp-research-v1'
  or j->>'source_family' is distinct from 'roboticket/roboticket'
  or j->>'unit' is distinct from 'available_total_seats'
  or j->'methods' is distinct from '["PERS","DRIFT24"]'::jsonb
  or j->'horizons_hours' is distinct from '[24,48,72]'::jsonb
  or j->'anchor_min_hours' is distinct from '24'::jsonb
  or j->'anchor_max_hours' is distinct from '30'::jsonb
  or j->'max_issue_latency_seconds' is distinct from '90'::jsonb
  or j->'max_source_age_seconds' is distinct from '3600'::jsonb
  or j->'max_target_age_seconds' is distinct from '21600'::jsonb
  or j->'max_issue_batch' is distinct from '25'::jsonb
  or j->'max_score_batch' is distinct from '100'::jsonb
  or jsonb_typeof(j->'max_fixtures') is distinct from 'number'
  or coalesce(j->>'max_fixtures','') !~ '^[1-9][0-9]*$'
  or (j->>'max_fixtures')::numeric not between 1 and 1000
  or coalesce(j->>'source_manifest_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'source_sql_sha256','') !~ '^[0-9a-f]{64}$'
  or j->>'b_sql_sha256' is distinct from 'c9621bb692ca7de38037a204a9ca204ed3be370657b9ab89dc3aa438575effb4'
  or j->>'lad_v5_sql_sha256' is distinct from 'c2a3071d7109b74040228fb6b4ee77a6524afccc7174550acb7fa362e9f7afd2'
  or coalesce(j->>'sql_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'issue_until','') !~ '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
  or coalesce(j->>'scoring_until','') !~ '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$'
 then raise exception 'PAIRED_DRIFT24_MANIFEST_CONTRACT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-paired-drift24-v1:runtime',20261125));
 select * into src from private.rolling72_mvp_research_v1_lane where lane_id='rolling72-mvp-research-v1';
 if not found then raise exception 'MVP_SOURCE_LANE_NOT_ACTIVATED'; end if;
 if j->>'source_manifest_sha256' is distinct from src.manifest_sha256
  or j->>'source_sql_sha256' is distinct from src.sql_sha256
  or (j->>'max_fixtures')::integer is distinct from src.max_fixtures
  or (j->>'issue_until')::timestamptz is distinct from src.issue_until
  or (j->>'scoring_until')::timestamptz is distinct from src.scoring_until
 then raise exception 'PAIRED_DRIFT24_SOURCE_BINDING'; end if;
 select * into old from private.rolling72_mvp_paired_drift24_v1_lane;
 if found then
  if old.manifest_text=p_manifest_text and old.manifest_sha256=p_manifest_sha256 then
   return jsonb_build_object('schema_version','rolling72-mvp-paired-drift24-v1','activated',false,
    'idempotent',true,'lane_id',old.lane_id,'activated_at',old.activated_at,
    'issue_until',old.issue_until,'scoring_until',old.scoring_until);
  end if;
  raise exception 'PAIRED_DRIFT24_MANIFEST_ALREADY_FROZEN';
 end if;
 t:=clock_timestamp();
 if t>=src.issue_until or t>=src.scoring_until or src.activated_at>t
  or (j->>'issue_until')::timestamptz<=t
  or not isfinite((j->>'issue_until')::timestamptz)
  or not isfinite((j->>'scoring_until')::timestamptz)
  or (j->>'scoring_until')::timestamptz<(j->>'issue_until')::timestamptz+interval '78 hours'
 then raise exception 'PAIRED_DRIFT24_MANIFEST_DEADLINE'; end if;
 insert into private.rolling72_mvp_paired_drift24_v1_lane(
  lane_id,version,source_lane_id,manifest_text,manifest_sha256,sql_sha256,source_manifest_sha256,
  source_sql_sha256,b_sql_sha256,lad_v5_sql_sha256,source_family,unit,methods,horizons_hours,anchor_min_hours,anchor_max_hours,
  max_issue_latency_seconds,max_source_age_seconds,max_target_age_seconds,max_issue_batch,max_score_batch,
  max_fixtures,activated_at,issue_until,scoring_until)
 values('rolling72-mvp-paired-drift24-v1','rolling72-mvp-paired-drift24-v1','rolling72-mvp-research-v1',
  p_manifest_text,p_manifest_sha256,j->>'sql_sha256',j->>'source_manifest_sha256',j->>'source_sql_sha256',
  j->>'b_sql_sha256',j->>'lad_v5_sql_sha256',
  'roboticket/roboticket','available_total_seats',array['PERS','DRIFT24'],array[24,48,72],24,30,90,3600,21600,25,100,
  (j->>'max_fixtures')::integer,t,(j->>'issue_until')::timestamptz,(j->>'scoring_until')::timestamptz);
 return jsonb_build_object('schema_version','rolling72-mvp-paired-drift24-v1','activated',true,'idempotent',false,
  'lane_id','rolling72-mvp-paired-drift24-v1','activated_at',t,'issue_until',src.issue_until,
  'scoring_until',src.scoring_until,'source_lane_id',src.lane_id,
  'source_manifest_sha256',src.manifest_sha256,'source_sql_sha256',src.sql_sha256);
end $$;

create function public.get_rolling72_mvp_paired_drift24_v1_status()
returns jsonb language sql volatile security definer set search_path='' set timezone='UTC' as $$
with asof as materialized (select clock_timestamp() at_time), cfg as materialized (
 select * from private.rolling72_mvp_paired_drift24_v1_lane
 where lane_id='rolling72-mvp-paired-drift24-v1'
), all_candidates as materialized (
 select c.*,s.known_at
 from private.rolling72_mvp_research_v1_candidates c
 join private.rolling72_mvp_research_v1_seals s on s.id=c.seal_id
), c as materialized (
 select c.* from all_candidates c cross join cfg
 where c.known_at>cfg.activated_at and c.known_at<cfg.issue_until
), latest_issue as materialized (
 select distinct on(a.candidate_id) a.*
 from private.rolling72_mvp_paired_drift24_v1_issue_attempts a
 order by a.candidate_id,a.attempted_at desc,a.id desc
), ch as (
 select c.horizon_hours,count(*) candidates,
  count(*) filter(where c.status='SOURCE_ELIGIBLE') eligible_source_candidates,
  count(*) filter(where c.status='OUTSIDE_KICKOFF') source_outside_candidates,
  count(*) filter(where c.status='SOURCE_ELIGIBLE' and a.id is not null) attempted_eligible,
  count(*) filter(where c.status='SOURCE_ELIGIBLE' and a.status='REFUSED') refused_eligible,
  count(*) filter(where c.status='SOURCE_ELIGIBLE' and a.status='DEFERRED') deferred_eligible,
  count(*) filter(where c.status='SOURCE_ELIGIBLE' and a.id is null) unattempted_eligible
 from c left join latest_issue a on a.candidate_id=c.id group by c.horizon_hours
), p as materialized (
 select p.*,d.status drift_status,d.prediction drift_prediction,d.fallback_reason drift_fallback_reason,
  (p.prediction is not null and d.prediction is not null) numeric_pair
 from private.rolling72_mvp_paired_drift24_v1_predictions p
 join private.rolling72_mvp_paired_drift24_v1_predictions d
  on d.bundle_id=p.bundle_id and d.horizon_hours=p.horizon_hours and d.method='DRIFT24'
 where p.method='PERS'
), pc as (
 select p.horizon_hours,
  count(*) filter(where p.numeric_pair) numeric_pairs,
  count(*) filter(where p.status='OUTSIDE_KICKOFF') outside_targets,
  count(*) filter(where p.numeric_pair and p.target_at>asof.at_time) future_targets,
  count(*) filter(where p.numeric_pair and p.target_at<=asof.at_time) matured_eligible_targets,
  count(*) filter(where p.numeric_pair and p.target_at<=asof.at_time and l.id is null) due_unscored_targets,
  count(l.id) filter(where p.numeric_pair) accepted_common_labels,
  count(*) filter(where p.numeric_pair and p.drift_status='READY') drift_ready_issues,
  count(*) filter(where p.numeric_pair and p.drift_status='FALLBACK_PERS') fallback_issues,
  count(l.id) filter(where p.numeric_pair and p.drift_status='READY') drift_ready_labels,
  count(l.id) filter(where p.numeric_pair and p.drift_status='FALLBACK_PERS') fallback_labels,
  count(l.id) filter(where p.numeric_pair and l.origin_membership_changed) changed_scope_labels
 from p cross join asof
 left join private.rolling72_mvp_paired_drift24_v1_labels l
  on l.bundle_id=p.bundle_id and l.horizon_hours=p.horizon_hours
 group by p.horizon_hours
), per_event as materialized (
 select l.horizon_hours,l.ticket_event_id,r.club_slug,count(*) labels,
  avg(l.pers_absolute_error) pers_mae,avg(l.drift24_absolute_error) drift24_mae,
  avg(l.pers_signed_error) pers_bias,avg(l.drift24_signed_error) drift24_bias
 from private.rolling72_mvp_paired_drift24_v1_labels l
 join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=l.ticket_event_id
 group by l.horizon_hours,l.ticket_event_id,r.club_slug
), scores as (
 select horizon_hours,count(*) fixtures,count(distinct club_slug) clubs,
  avg(pers_mae) pers_mae,avg(drift24_mae) drift24_mae,
  avg(drift24_mae-pers_mae) delta_mae,
  avg(pers_bias) pers_bias,avg(drift24_bias) drift24_bias,
  percentile_cont(0.9) within group(order by pers_mae) pers_p90_event_mae,
  percentile_cont(0.9) within group(order by drift24_mae) drift24_p90_event_mae,
  max(pers_mae) pers_worst_event_mae,max(drift24_mae) drift24_worst_event_mae
 from per_event group by horizon_hours
), stable_event as (
 select l.horizon_hours,l.ticket_event_id,count(*) labels,
  avg(l.pers_absolute_error) pers_mae,avg(l.drift24_absolute_error) drift24_mae
 from private.rolling72_mvp_paired_drift24_v1_labels l
 where not l.origin_membership_changed and l.origin_sector_count_delta=0
 group by l.horizon_hours,l.ticket_event_id
), stable_scores as (
 select horizon_hours,count(*) fixtures,sum(labels) labels,
  avg(pers_mae) pers_mae,avg(drift24_mae) drift24_mae
 from stable_event group by horizon_hours
), ready_event as (
 select l.horizon_hours,l.ticket_event_id,count(*) labels,
  avg(l.pers_absolute_error) pers_mae,avg(l.drift24_absolute_error) drift24_mae
 from private.rolling72_mvp_paired_drift24_v1_labels l
 join private.rolling72_mvp_paired_drift24_v1_issue_bundles b on b.id=l.bundle_id
 where b.drift_status='READY' group by l.horizon_hours,l.ticket_event_id
), ready_scores as (
 select horizon_hours,count(*) fixtures,sum(labels) labels,
  avg(pers_mae) pers_mae,avg(drift24_mae) drift24_mae
 from ready_event group by horizon_hours
), latest_score as (
 select distinct on(a.bundle_id,a.horizon_hours) a.*
 from private.rolling72_mvp_paired_drift24_v1_score_attempts a
 order by a.bundle_id,a.horizon_hours,a.attempted_at desc,a.id desc
)
select jsonb_build_object(
 'schema_version','rolling72-mvp-paired-drift24-v1','lane_id','rolling72-mvp-paired-drift24-v1',
 'activated',exists(select 1 from cfg),'target','public_available_total','unit','available_total_seats',
 'methods',jsonb_build_array('PERS','DRIFT24'),'scope','FULL_PAIRED_LANE',
 'read_watermark',(select at_time from asof),'activated_at',(select activated_at from cfg),
 'issue_until',(select issue_until from cfg),'scoring_until',(select scoring_until from cfg),
 'manifest_sha256',(select manifest_sha256 from cfg),'sql_sha256',(select sql_sha256 from cfg),
 'source_manifest_sha256',(select source_manifest_sha256 from cfg),
 'source_sql_sha256',(select source_sql_sha256 from cfg),
 'candidate_denominator',jsonb_build_object(
  'in_scope_candidates',(select count(*) from c),
  'source_eligible',(select count(*) from c where status='SOURCE_ELIGIBLE'),
  'source_time_outside_kickoff',(select count(*) from c where status='OUTSIDE_KICKOFF'),
  'pre_activation_excluded',(select count(*) from all_candidates cross join cfg where known_at<=cfg.activated_at),
  'after_issue_cutoff_excluded',(select count(*) from all_candidates cross join cfg where known_at>=cfg.issue_until),
  'attempt_records',(select count(*) from private.rolling72_mvp_paired_drift24_v1_issue_attempts),
  'refused_eligible',coalesce((select sum(refused_eligible) from ch),0),
  'deferred_eligible',coalesce((select sum(deferred_eligible) from ch),0),
  'unattempted_eligible',coalesce((select sum(unattempted_eligible) from ch),0),
  'numeric_pairs',coalesce((select sum(numeric_pairs) from pc),0),
  'forecast_coverage',(select sum(pc.numeric_pairs)::numeric/nullif((select count(*) from c where status='SOURCE_ELIGIBLE'),0) from pc),
  'count_unit','one source candidate / bundle-horizon pair; methods are not doubled'),
 'scorecards',(select jsonb_agg(jsonb_build_object(
  'horizon_hours',x.horizon_hours,'status',case when coalesce(pc.accepted_common_labels,0)=0 then 'PENDING' else 'SCORED' end,
  'valid_pre_kickoff_opportunities',coalesce(ch.eligible_source_candidates,0),
  'source_outside_candidates',coalesce(ch.source_outside_candidates,0),
  'attempted_eligible',coalesce(ch.attempted_eligible,0),'refused_eligible',coalesce(ch.refused_eligible,0),
  'deferred_eligible',coalesce(ch.deferred_eligible,0),'unattempted_eligible',coalesce(ch.unattempted_eligible,0),
  'numeric_pairs',coalesce(pc.numeric_pairs,0),'outside_kickoff_targets',coalesce(pc.outside_targets,0),
  'future_targets',coalesce(pc.future_targets,0),'matured_eligible_targets',coalesce(pc.matured_eligible_targets,0),
  'due_unscored_targets',coalesce(pc.due_unscored_targets,0),'accepted_common_labels',coalesce(pc.accepted_common_labels,0),
  'fixtures',coalesce(s.fixtures,0),'clubs',coalesce(s.clubs,0),
  'forecast_coverage',coalesce(pc.numeric_pairs,0)::numeric/nullif(ch.eligible_source_candidates,0),
  'scoring_coverage',coalesce(pc.accepted_common_labels,0)::numeric/nullif(pc.matured_eligible_targets,0),
  'scoring_denominator','actual numeric common targets with target_at <= read_watermark',
  'pers_event_balanced_mae',s.pers_mae,'drift24_event_balanced_mae',s.drift24_mae,'delta_mae',s.delta_mae,
  'pers_event_balanced_bias',s.pers_bias,'drift24_event_balanced_bias',s.drift24_bias,
  'pers_p90_event_mae',s.pers_p90_event_mae,'drift24_p90_event_mae',s.drift24_p90_event_mae,
  'pers_worst_event_mae',s.pers_worst_event_mae,'drift24_worst_event_mae',s.drift24_worst_event_mae,
  'drift_ready_issues',coalesce(pc.drift_ready_issues,0),'fallback_issues',coalesce(pc.fallback_issues,0),
  'drift_ready_labels',coalesce(pc.drift_ready_labels,0),'fallback_labels',coalesce(pc.fallback_labels,0),
  'changed_scope_labels',coalesce(pc.changed_scope_labels,0),
  'stable_scope_sensitivity',jsonb_build_object('fixtures',coalesce(ss.fixtures,0),'labels',coalesce(ss.labels,0),
    'pers_event_balanced_mae',ss.pers_mae,'drift24_event_balanced_mae',ss.drift24_mae),
  'drift_ready_diagnostic',jsonb_build_object('fixtures',coalesce(rs.fixtures,0),'labels',coalesce(rs.labels,0),
    'pers_event_balanced_mae',rs.pers_mae,'drift24_event_balanced_mae',rs.drift24_mae)
 ) order by x.horizon_hours)
 from (values(24),(48),(72)) x(horizon_hours)
 left join ch using(horizon_hours) left join pc using(horizon_hours) left join scores s using(horizon_hours)
 left join stable_scores ss using(horizon_hours) left join ready_scores rs using(horizon_hours)),
 'per_event_scores',(select coalesce(jsonb_agg(to_jsonb(e) order by horizon_hours,ticket_event_id),'[]'::jsonb) from per_event e),
 'latest_score_attempt_statuses',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb)
  from(select status,count(*) n from latest_score group by status) q),
 'decision_status','UNKNOWN','formal_decision','Use fixed event-bootstrap evaluator after 30 new events / 8 clubs; all horizons retained',
 'attendance_or_sales_claim',false,'production_live_adjustment',0)
$$;
create function public.score_rolling72_mvp_paired_drift24_v1(p_limit integer default 100)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare l private.rolling72_mvp_paired_drift24_v1_lane%rowtype;
 run_id uuid:=gen_random_uuid(); started timestamptz:=clock_timestamp(); watermark timestamptz;
 score_clock timestamptz; entry_snapshot pg_snapshot; bundle_row record; h integer;
 unknown_attempt record; latest_attempt record; selected_seal record;
 selected_attempt_id bigint; selected_snapshot_id bigint; label_id bigint;
 score_status text; score_reason text; results jsonb:='[]'::jsonb;
 processed integer:=0; scored integer:=0; waiting integer:=0; refused integer:=0;
 pers_id bigint; drift_id bigint; age_seconds numeric; target_membership jsonb;
 target_membership_hash text; target_sector_count integer; target_payload jsonb;
 linked_ready_attempt jsonb; linked_ready_xmin xid; target_registry jsonb; target_registry_xmin xid;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'PAIRED_DRIFT24_READ_COMMITTED_REQUIRED'; end if;
 if p_limit is null or p_limit not between 1 and 100 then raise exception 'PAIRED_DRIFT24_SCORE_LIMIT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-paired-drift24-v1:runtime',20261125));
 select * into l from private.rolling72_mvp_paired_drift24_v1_lane;
 if not found then raise exception 'PAIRED_DRIFT24_NOT_ACTIVATED'; end if;
 entry_snapshot:=pg_current_snapshot(); watermark:=clock_timestamp();
 if watermark>=l.scoring_until then
  insert into private.rolling72_mvp_paired_drift24_v1_runs values(run_id,'SCORE',started,watermark,
   'SCORING_WINDOW_CLOSED',p_limit,0,jsonb_build_object('labels',0));
  return jsonb_build_object('schema_version',l.version,'lane_id',l.lane_id,'run_id',run_id,
   'status','SCORING_WINDOW_CLOSED','watermark',watermark,'processed',0,'labels',0,'results','[]'::jsonb);
 end if;
 for bundle_row in
  select b.*,p.horizon_hours,p.status prediction_status,p.target_at
  from private.rolling72_mvp_paired_drift24_v1_issue_bundles b
  join private.rolling72_mvp_paired_drift24_v1_predictions p
   on p.bundle_id=b.id and p.method='PERS'
  where p.status in('READY','FALLBACK_PERS','OUTSIDE_KICKOFF') and p.target_at<=watermark
   and not exists(select 1 from private.rolling72_mvp_paired_drift24_v1_labels z
     where z.bundle_id=b.id and z.horizon_hours=p.horizon_hours)
   and not exists(select 1 from private.rolling72_mvp_paired_drift24_v1_score_attempts sa
     where sa.bundle_id=b.id and sa.horizon_hours=p.horizon_hours and sa.status in('OUTSIDE_KICKOFF','EXPIRED'))
  order by p.target_at,b.id,p.horizon_hours limit p_limit
 loop
   h:=bundle_row.horizon_hours;
   score_clock:=null;
   label_id:=null; selected_attempt_id:=null; selected_snapshot_id:=null;
   score_status:=null; score_reason:=null; unknown_attempt:=null; latest_attempt:=null; selected_seal:=null;
   select p.id into pers_id from private.rolling72_mvp_paired_drift24_v1_predictions p
    where p.bundle_id=bundle_row.id and p.horizon_hours=h and p.method='PERS';
   select p.id into drift_id from private.rolling72_mvp_paired_drift24_v1_predictions p
    where p.bundle_id=bundle_row.id and p.horizon_hours=h and p.method='DRIFT24';
   if exists(select 1 from private.rolling72_mvp_paired_drift24_v1_labels z
      where z.bundle_id=bundle_row.id and z.horizon_hours=h) then continue; end if;
   if bundle_row.target_at>watermark then continue; end if;
   if bundle_row.prediction_status='OUTSIDE_KICKOFF' then
    score_status:='OUTSIDE_KICKOFF'; score_reason:='TARGET_NOT_PRE_KICKOFF';
   else
    -- Unknown-capture INTERNAL_ERROR attempts newer than the latest trustworthy
    -- observation are an explicit ordering refusal, never an older label.
    select a.*,a.xmin as tuple_xmin into unknown_attempt
    from private.rolling72_mvp_research_v1_attempts a
    where a.ticket_event_id=bundle_row.ticket_event_id and a.known_at>bundle_row.issued_at
      and a.known_at<=watermark and a.captured_at is null and a.status='INTERNAL_ERROR'
      and private.rolling72_mvp_paired_drift24_v1_committed(a.xmin,entry_snapshot)
    order by a.known_at desc,a.id desc limit 1;
    -- First choose the latest attempt for each snapshot, then choose the newest
    -- captured post-issue snapshot. Validation happens only after this choice.
    with latest_per_snapshot as materialized (
      select distinct on(a.snapshot_id) a.*,a.xmin as tuple_xmin
      from private.rolling72_mvp_research_v1_attempts a
      where a.ticket_event_id=bundle_row.ticket_event_id and a.snapshot_id is not null
        and a.known_at>bundle_row.issued_at and a.known_at<=watermark
        and private.rolling72_mvp_paired_drift24_v1_committed(a.xmin,entry_snapshot)
      order by a.snapshot_id,a.known_at desc,a.id desc
    )
    select q.* into latest_attempt from latest_per_snapshot q
    where q.captured_at>bundle_row.issued_at and q.captured_at<=bundle_row.target_at
    order by q.captured_at desc,q.snapshot_id desc limit 1;
    if latest_attempt.id is not null then
     select s.*,s.xmin as tuple_xmin into selected_seal
      from private.rolling72_mvp_research_v1_seals s
      where s.ticket_event_id=bundle_row.ticket_event_id and s.snapshot_id=latest_attempt.snapshot_id;
    end if;
    score_clock:=clock_timestamp();
    if score_clock>=l.scoring_until then
     score_status:='EXPIRED'; score_reason:='SCORING_WINDOW_CLOSED';
    elsif unknown_attempt.id is not null and
      (latest_attempt.id is null or unknown_attempt.known_at>latest_attempt.known_at
       or (unknown_attempt.known_at=latest_attempt.known_at and unknown_attempt.id>latest_attempt.id)) then
     score_status:='SOURCE_ORDER_UNKNOWN'; score_reason:='UNRESOLVED_CAPTURE_TIME_AFTER_LAST_TRUSTWORTHY_SOURCE';
    elsif latest_attempt.id is null then
     score_status:='WAITING'; score_reason:='NO_OBSERVED_POST_ISSUE_TARGET_SOURCE';
    else
     selected_attempt_id:=latest_attempt.id; selected_snapshot_id:=latest_attempt.snapshot_id;
     if latest_attempt.status not in('READY','NO_NEW_SOURCE') or selected_seal.id is null then
      score_status:='SOURCE_INVALID'; score_reason:=coalesce(latest_attempt.reason,'LATEST_SOURCE_HAS_NO_READY_SEAL');
     elsif latest_attempt.attempt_binding_sha256 !~ '^[0-9a-f]{64}$'
       or latest_attempt.source_content_sha256 is distinct from selected_seal.source_content_sha256
       or latest_attempt.captured_at is distinct from selected_seal.captured_at
       or latest_attempt.raw_source is distinct from selected_seal.source_payload
       or (latest_attempt.status='READY' and selected_seal.attempt_id is distinct from latest_attempt.id)
       or latest_attempt.attempt_binding_sha256 is distinct from
          private.rolling72_mvp_paired_drift24_v1_hash(latest_attempt.binding_payload)
       or latest_attempt.binding_payload is distinct from jsonb_build_object(
         'attempt_id',latest_attempt.id,'run_id',latest_attempt.run_id,'lane_id',l.source_lane_id,
         'ticket_event_id',latest_attempt.ticket_event_id,'snapshot_id',latest_attempt.snapshot_id,
         'source_content_sha256',latest_attempt.source_content_sha256,'read_started_at',latest_attempt.read_started_at,
         'read_completed_at',latest_attempt.read_completed_at,'known_at',latest_attempt.known_at,
         'status',latest_attempt.status,'reason',latest_attempt.reason)
       or not private.rolling72_mvp_paired_drift24_v1_committed(latest_attempt.tuple_xmin,entry_snapshot)
     then score_status:='SOURCE_MISMATCH'; score_reason:='LATEST_SOURCE_HASH_OR_COMMIT_MISMATCH';
     elsif latest_attempt.known_at>score_clock then
      score_status:='SOURCE_INVALID'; score_reason:='SOURCE_KNOWN_AFTER_SCORE_CLOCK';
     elsif selected_seal.source_payload->>'source_family' is distinct from l.source_family
       or selected_seal.source_payload->>'unit' is distinct from l.unit
       or selected_seal.ticket_event_id<>bundle_row.ticket_event_id then
      score_status:='SOURCE_MISMATCH'; score_reason:='SOURCE_EVENT_FAMILY_OR_UNIT_MISMATCH';
     elsif selected_seal.captured_at>score_clock or selected_seal.captured_at>bundle_row.issued_at+
       make_interval(hours=>h) then
      score_status:='SOURCE_INVALID'; score_reason:='SOURCE_AFTER_TARGET_OR_SCORE_CLOCK';
     else
      age_seconds:=extract(epoch from bundle_row.issued_at+make_interval(hours=>h)-selected_seal.captured_at);
      if age_seconds<0 then score_status:='SOURCE_INVALID'; score_reason:='SOURCE_AFTER_TARGET';
      elsif age_seconds>l.max_target_age_seconds then score_status:='SOURCE_STALE'; score_reason:='TARGET_SOURCE_OLDER_THAN_SIX_HOURS';
      else
       select to_jsonb(ra),ra.xmin into linked_ready_attempt,linked_ready_xmin
        from private.rolling72_mvp_research_v1_attempts ra where ra.id=selected_seal.attempt_id;
       select to_jsonb(r),r.xmin into target_registry,target_registry_xmin
        from private.rolling72_mvp_research_v1_registry r where r.ticket_event_id=bundle_row.ticket_event_id;
       if not private.rolling72_mvp_paired_drift24_v1_committed(selected_seal.tuple_xmin,entry_snapshot)
         or not private.rolling72_mvp_paired_drift24_v1_committed(linked_ready_xmin,entry_snapshot)
         or not private.rolling72_mvp_paired_drift24_v1_committed(target_registry_xmin,entry_snapshot)
         or not private.rolling72_mvp_paired_drift24_v1_valid_seal(to_jsonb(selected_seal),linked_ready_attempt,target_registry) then
        score_status:='SOURCE_MISMATCH'; score_reason:='LATEST_SOURCE_SEAL_BINDING_INVALID';
       else
       target_payload:=selected_seal.source_payload;
       target_membership:=private.rolling72_mvp_paired_drift24_v1_membership(target_payload);
       target_sector_count:=jsonb_array_length(target_membership->'sector_ids');
       target_membership_hash:=private.rolling72_mvp_paired_drift24_v1_hash(target_membership);
       if target_membership is null or target_sector_count<=0 then
        score_status:='SOURCE_MISMATCH'; score_reason:='TARGET_MEMBERSHIP_INVALID';
       else
       insert into private.rolling72_mvp_paired_drift24_v1_labels(
        bundle_id,ticket_event_id,horizon_hours,target_seal_id,target_attempt_id,snapshot_id,
        actual_available_total,source_captured_at,source_known_at,scored_at,target_age_seconds,
        source_content_sha256,source_status,source_transition_status,source_transition,sector_count,
        membership,membership_sha256,origin_membership_changed,origin_sector_count_delta,
        pers_prediction_id,drift24_prediction_id,pers_prediction,drift24_prediction,
        pers_signed_error,drift24_signed_error,pers_absolute_error,drift24_absolute_error)
       select bundle_row.id,bundle_row.ticket_event_id,h,selected_seal.id,latest_attempt.id,
        selected_seal.snapshot_id,selected_seal.available_total,selected_seal.captured_at,
        selected_seal.known_at,score_clock,age_seconds,selected_seal.source_content_sha256,
        latest_attempt.status,coalesce(selected_seal.transition_status,'UNKNOWN'),
        coalesce(selected_seal.transition,'{}'::jsonb),target_sector_count,target_membership,
        target_membership_hash,target_membership is distinct from bundle_row.origin_membership,
        target_sector_count-bundle_row.origin_sector_count,pers.id,drift.id,pers.prediction,drift.prediction,
        pers.prediction-selected_seal.available_total,drift.prediction-selected_seal.available_total,
        abs(pers.prediction-selected_seal.available_total),abs(drift.prediction-selected_seal.available_total)
       from private.rolling72_mvp_paired_drift24_v1_predictions pers
       join private.rolling72_mvp_paired_drift24_v1_predictions drift
         on drift.bundle_id=pers.bundle_id and drift.horizon_hours=pers.horizon_hours and drift.method='DRIFT24'
       where pers.bundle_id=bundle_row.id and pers.horizon_hours=h and pers.method='PERS'
        and pers.prediction is not null and drift.prediction is not null
       on conflict(bundle_id,horizon_hours) do nothing returning id into label_id;
       if label_id is null then score_status:='SCORED'; score_reason:='LABEL_ALREADY_ACCEPTED';
       else score_status:='SCORED'; score_reason:=null; scored:=scored+1; end if;
       end if;
       end if;
      end if;
     end if;
    end if;
   end if;
   if score_status='WAITING' then waiting:=waiting+1; end if;
   if score_status not in('SCORED','WAITING') then refused:=refused+1; end if;
   insert into private.rolling72_mvp_paired_drift24_v1_score_attempts(
    run_id,bundle_id,horizon_hours,attempted_at,status,reason,selected_attempt_id,selected_snapshot_id,label_id)
   values(run_id,bundle_row.id,h,coalesce(score_clock,clock_timestamp()),score_status,score_reason,
      selected_attempt_id,selected_snapshot_id,label_id);
   processed:=processed+1;
   results:=results||jsonb_build_array(jsonb_build_object('bundle_id',bundle_row.id,'horizon_hours',h,
     'status',score_status,'reason',score_reason,'label_id',label_id,
     'source_attempt_id',selected_attempt_id,'snapshot_id',selected_snapshot_id));
 end loop;
 insert into private.rolling72_mvp_paired_drift24_v1_runs values(run_id,'SCORE',started,clock_timestamp(),
  case when processed=0 then 'EMPTY' else 'COMPLETED' end,p_limit,processed,
  jsonb_build_object('labels',scored,'waiting',waiting,'refused',refused));
 return jsonb_build_object('schema_version',l.version,'lane_id',l.lane_id,'run_id',run_id,
  'status',case when processed=0 then 'EMPTY' else 'COMPLETED' end,'watermark',watermark,
  'processed',processed,'labels',scored,'waiting',waiting,'refused',refused,'results',results);
end $$;

do $$
declare tab text; f record;
begin
 foreach tab in array array['lane','runs','issue_bundles','predictions','issue_attempts','labels','score_attempts'] loop
  execute format('alter table private.%I enable row level security','rolling72_mvp_paired_drift24_v1_'||tab);
  execute format('revoke all on table private.%I from public,anon,authenticated,service_role','rolling72_mvp_paired_drift24_v1_'||tab);
  execute format('create trigger immutable_rows before update or delete on private.%I for each row execute function private.rolling72_mvp_paired_drift24_v1_immutable()','rolling72_mvp_paired_drift24_v1_'||tab);
  execute format('create trigger immutable_truncate before truncate on private.%I for each statement execute function private.rolling72_mvp_paired_drift24_v1_immutable()','rolling72_mvp_paired_drift24_v1_'||tab);
  if tab in ('issue_bundles','predictions','issue_attempts','labels','score_attempts') then
   execute format('revoke all on sequence private.%I_id_seq from public,anon,authenticated,service_role','rolling72_mvp_paired_drift24_v1_'||tab);
  end if;
 end loop;
 for f in select p.oid::regprocedure sig from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
  where ns.nspname='private' and left(p.proname,length('rolling72_mvp_paired_drift24_v1_'))='rolling72_mvp_paired_drift24_v1_' loop
  execute format('revoke all on function %s from public,anon,authenticated,service_role',f.sig);
 end loop;
end $$;

revoke all on function public.activate_rolling72_mvp_paired_drift24_v1(text,text) from public,anon,authenticated;
revoke all on function public.issue_rolling72_mvp_paired_drift24_v1(integer) from public,anon,authenticated;
revoke all on function public.score_rolling72_mvp_paired_drift24_v1(integer) from public,anon,authenticated;
revoke all on function public.get_rolling72_mvp_paired_drift24_v1_status() from public,anon,authenticated;
grant execute on function public.activate_rolling72_mvp_paired_drift24_v1(text,text) to service_role;
grant execute on function public.issue_rolling72_mvp_paired_drift24_v1(integer) to service_role;
grant execute on function public.score_rolling72_mvp_paired_drift24_v1(integer) to service_role;
grant execute on function public.get_rolling72_mvp_paired_drift24_v1_status() to service_role;
