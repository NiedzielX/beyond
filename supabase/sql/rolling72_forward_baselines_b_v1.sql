-- Forward-only public-availability persistence/drift benchmarks; no v5 edits.
create table private.rolling72_forward_baselines_b_lane_v1 (
 lane_id text primary key check(lane_id='rolling72-forward-baselines-b-v1'),
 manifest_text text not null, manifest_sha256 text not null check(manifest_sha256~'^[0-9a-f]{64}$'),
 sql_sha256 text not null check(sql_sha256~'^[0-9a-f]{64}$'),
 fixture_ids bigint[] not null, activated_at timestamptz not null,
 issue_until timestamptz not null, scoring_until timestamptz not null,
 check(scoring_until>=issue_until)
);
create table private.rolling72_forward_baselines_b_bundles_v1 (
 id bigint generated always as identity primary key,
 lane_id text not null references private.rolling72_forward_baselines_b_lane_v1(lane_id),
 ticket_event_id bigint not null, receipt_id bigint not null unique references private.rolling72_managed_receipts_v3a(id),
 parent_issued_at timestamptz not null, parent_created_at timestamptz not null,
 issued_at timestamptz not null, prefix_sha256 text,
 parent_slopes float8[], source_snapshot_id bigint references public.snapshots(id),
 source_family text, source_unit text, source_captured_at timestamptz,
 source_known_at timestamptz, source_available_total integer,
 source_sector_count integer, source_payload_sha256 text,
 source_status text not null check(source_status in('VALID','INVALID_SOURCE')),
 created_at timestamptz not null default clock_timestamp(),
 unique(ticket_event_id,receipt_id),
 unique(id,lane_id,ticket_event_id,receipt_id,issued_at),
 check(parent_slopes is null or array_length(parent_slopes,1)=3)
);
create table private.rolling72_forward_baselines_b_predictions_v1 (
 id bigint generated always as identity primary key,
 bundle_id bigint not null references private.rolling72_forward_baselines_b_bundles_v1(id),
 lane_id text not null references private.rolling72_forward_baselines_b_lane_v1(lane_id),
 ticket_event_id bigint not null, receipt_id bigint not null references private.rolling72_managed_receipts_v3a(id),
 issued_at timestamptz not null, horizon_hours integer not null check(horizon_hours in(24,48,72)),
 target_at timestamptz not null, source_status text not null check(source_status in('VALID','INVALID_SOURCE')),
 persistence_prediction float8, drift6_prediction float8, drift24_prediction float8,
 persistence_status text not null check(persistence_status in('PERSISTENCE','INVALID_SOURCE','OUTSIDE_KICKOFF')),
 drift6_status text not null check(drift6_status in('DRIFT6','FALLBACK_MISSING_SLOPE','INVALID_SOURCE','OUTSIDE_KICKOFF')),
 drift24_status text not null check(drift24_status in('DRIFT24','FALLBACK_MISSING_SLOPE','INVALID_SOURCE','OUTSIDE_KICKOFF')),
 features jsonb not null, created_at timestamptz not null default clock_timestamp(),
 unique(bundle_id,horizon_hours), unique(receipt_id,horizon_hours),
 foreign key(bundle_id,lane_id,ticket_event_id,receipt_id,issued_at)
  references private.rolling72_forward_baselines_b_bundles_v1(id,lane_id,ticket_event_id,receipt_id,issued_at),
 check(target_at=issued_at+make_interval(hours=>horizon_hours)),
 check((persistence_prediction is null)=(drift6_prediction is null)
   and (persistence_prediction is null)=(drift24_prediction is null)),
 check((persistence_prediction is null or (persistence_prediction>=0 and persistence_prediction<'Infinity'::float8))
   and (drift6_prediction is null or (drift6_prediction>=0 and drift6_prediction<'Infinity'::float8))
   and (drift24_prediction is null or (drift24_prediction>=0 and drift24_prediction<'Infinity'::float8)))
);
create index rolling72_forward_b_due_v1 on private.rolling72_forward_baselines_b_predictions_v1(target_at) where source_status='VALID';
create table private.rolling72_forward_baselines_b_labels_v1 (
 prediction_id bigint primary key references private.rolling72_forward_baselines_b_predictions_v1(id),
 scored_at timestamptz not null, label_receipt_id bigint not null references private.rolling72_managed_receipts_v3a(id),
 label_snapshot_id bigint not null references public.snapshots(id), actual_available_total integer not null check(actual_available_total>=0),
 label_captured_at timestamptz not null, label_known_at timestamptz not null,
 label_age_seconds float8 not null check(label_age_seconds>=0),
 label_source_family text not null, label_source_unit text not null,
 origin_sector_count integer not null, target_sector_count integer not null,
 sector_count_delta integer not null, continuity text not null check(continuity='UNKNOWN'),
 persistence_absolute_error float8 not null check(persistence_absolute_error>=0),
 drift6_absolute_error float8 not null check(drift6_absolute_error>=0),
 drift24_absolute_error float8 not null check(drift24_absolute_error>=0)
);
create table private.rolling72_forward_baselines_b_attempts_v1 (
 id bigint generated always as identity primary key,
 prediction_id bigint not null references private.rolling72_forward_baselines_b_predictions_v1(id),
 attempted_at timestamptz not null, status text not null, selected_receipt_id bigint references private.rolling72_managed_receipts_v3a(id)
);
create index rolling72_forward_b_latest_attempt_v1 on private.rolling72_forward_baselines_b_attempts_v1(prediction_id,id desc);
create table private.rolling72_forward_baselines_b_failures_v1 (
 id bigint generated always as identity primary key, parent_prediction_id bigint,
 receipt_id bigint, failed_at timestamptz not null default clock_timestamp(), sqlstate text not null
);

-- Private tables are service-only via fixed SECURITY DEFINER APIs.
alter table private.rolling72_forward_baselines_b_lane_v1 enable row level security;
alter table private.rolling72_forward_baselines_b_bundles_v1 enable row level security;
alter table private.rolling72_forward_baselines_b_predictions_v1 enable row level security;
alter table private.rolling72_forward_baselines_b_labels_v1 enable row level security;
alter table private.rolling72_forward_baselines_b_attempts_v1 enable row level security;
alter table private.rolling72_forward_baselines_b_failures_v1 enable row level security;
revoke all on private.rolling72_forward_baselines_b_lane_v1,private.rolling72_forward_baselines_b_bundles_v1,
 private.rolling72_forward_baselines_b_predictions_v1,private.rolling72_forward_baselines_b_labels_v1,
 private.rolling72_forward_baselines_b_attempts_v1,private.rolling72_forward_baselines_b_failures_v1
 from public,anon,authenticated,service_role;

create function private.rolling72_forward_baselines_b_immutable_v1() returns trigger
language plpgsql security definer set search_path='' as $$ begin raise exception 'ROLLING72_FORWARD_B_IMMUTABLE'; end $$;
revoke all on function private.rolling72_forward_baselines_b_immutable_v1() from public,anon,authenticated,service_role;
create trigger rolling72_forward_b_lane_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_lane_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();
create trigger rolling72_forward_b_bundle_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_bundles_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();
create trigger rolling72_forward_b_prediction_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_predictions_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();
create trigger rolling72_forward_b_label_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_labels_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();
create trigger rolling72_forward_b_attempt_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_attempts_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();
create trigger rolling72_forward_b_failure_immutable_v1 before update or delete on private.rolling72_forward_baselines_b_failures_v1 for each row execute function private.rolling72_forward_baselines_b_immutable_v1();

create function private.rolling72_forward_baselines_b_slope_v1(p_features jsonb,p_index integer) returns float8
language plpgsql immutable set search_path='' as $$
declare x jsonb; v float8;
begin
 if jsonb_typeof(p_features->'slopes') is distinct from 'array' then return null; end if;
 if jsonb_array_length(p_features->'slopes')<>3 then return null; end if;
 x:=p_features->'slopes'->(p_index-1);
 if jsonb_typeof(x) is distinct from 'number' then return null; end if;
 begin v:=x::text::float8; exception when others then return null; end;
 if v is null or v>='Infinity'::float8 or v<='-Infinity'::float8 then return null; end if;
 return v;
end $$;
revoke all on function private.rolling72_forward_baselines_b_slope_v1(jsonb,integer) from public,anon,authenticated,service_role;

create function private.rolling72_forward_baselines_b_issue_v1(p_parent_id bigint) returns void
language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare p private.rolling72_lad_predictions_v5%rowtype; r private.rolling72_managed_receipts_v3a%rowtype;
 l private.rolling72_forward_baselines_b_lane_v1%rowtype; f private.rolling72_managed_fixtures_v3a%rowtype;
 e public.ticket_events%rowtype; s public.snapshots%rowtype; old private.rolling72_forward_baselines_b_bundles_v1%rowtype;
 v_now timestamptz; v_issue timestamptz; v_target timestamptz; v_h integer; v_age float8; v_family text; v_unit text;
 v_prefix text; v_slopes float8[]; v_status text; v_source_status text; v_p float8; v_d6 float8; v_d24 float8; v_slope float8;
begin
 select * into p from private.rolling72_lad_predictions_v5 where id=p_parent_id;
 if not found then return; end if;
 v_prefix:=p.features->>'prefix_sha256';
 v_slopes:=array[private.rolling72_forward_baselines_b_slope_v1(p.features,1),
  private.rolling72_forward_baselines_b_slope_v1(p.features,2),private.rolling72_forward_baselines_b_slope_v1(p.features,3)];
 select * into l from private.rolling72_forward_baselines_b_lane_v1 where lane_id='rolling72-forward-baselines-b-v1';
 if not found or p.ticket_event_id<>all(l.fixture_ids) or p.issued_at<l.activated_at or p.created_at<l.activated_at
   or p.issued_at>l.issue_until or clock_timestamp()-p.created_at>interval '90 seconds' then return; end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-forward-b:'||p.receipt_id::text,20261119));
 select * into old from private.rolling72_forward_baselines_b_bundles_v1 where receipt_id=p.receipt_id;
 if found then
  if old.ticket_event_id<>p.ticket_event_id or old.parent_issued_at<>p.issued_at
    or old.prefix_sha256 is distinct from v_prefix
    or old.parent_slopes is distinct from v_slopes then raise exception 'ROLLING72_FORWARD_B_PARENT_PREFIX_MISMATCH'; end if;
  return;
 end if;
 select * into r from private.rolling72_managed_receipts_v3a where id=p.receipt_id;
 select * into f from private.rolling72_managed_fixtures_v3a where ticket_event_id=p.ticket_event_id;
 select * into e from public.ticket_events where id=p.ticket_event_id;
 select * into s from public.snapshots where id=r.snapshot_id;
 v_now:=clock_timestamp(); v_family:=e.provider||'/'||coalesce(r.source_payload->>'source','UNKNOWN');
 v_unit:=coalesce(r.source_payload->>'unit','available_total_seats');
 v_source_status:='VALID';
 if r.id is null or r.ticket_event_id<>p.ticket_event_id or r.known_at>p.issued_at or r.captured_at is null
  or r.captured_at>p.issued_at or p.issued_at-v_now>interval '0 seconds'
  or r.receipt_status<>'VALID' or r.available_total is null or r.available_total<0
  or r.sector_count is null or r.sector_count<=0 or p.features is null
  or v_prefix is null or v_prefix !~ '^[0-9a-f]{64}$'
  or e.id is null or f.ticket_event_id is null or e.provider is distinct from f.provider
  or e.external_event_id is distinct from f.external_event_id or e.club_slug is distinct from f.club_slug
  or e.source_domain is distinct from f.source_domain or e.home_team is distinct from f.home_team
  or e.away_team is distinct from f.away_team or e.competition is distinct from f.competition
  or e.match_date is distinct from f.match_date or e.kickoff_at is distinct from f.kickoff_at
  or s.id is null or r.source_payload is distinct from to_jsonb(s)
  or encode(extensions.digest(convert_to(r.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from r.source_payload_sha256
  or s.ticket_event_id is distinct from p.ticket_event_id or s.event_id::text is distinct from f.external_event_id
  or s.source is distinct from r.source_payload->>'source' or s.event_kickoff_at_capture is distinct from f.kickoff_at
  or s.event_match_date_at_capture is distinct from f.match_date then v_source_status:='INVALID_SOURCE'; end if;
 v_issue:=clock_timestamp();
 if v_issue>l.issue_until then return; end if;
 if v_source_status='VALID' and (r.known_at>v_issue or v_issue-r.captured_at>interval '1 hour') then v_source_status:='INVALID_SOURCE'; end if;
 if v_source_status='VALID' and (v_issue<p.issued_at or v_issue-p.issued_at>interval '90 seconds') then v_source_status:='INVALID_SOURCE'; end if;
 insert into private.rolling72_forward_baselines_b_bundles_v1(lane_id,ticket_event_id,receipt_id,parent_issued_at,parent_created_at,
  issued_at,prefix_sha256,parent_slopes,source_snapshot_id,source_family,source_unit,source_captured_at,source_known_at,
  source_available_total,source_sector_count,source_payload_sha256,source_status)
 values(l.lane_id,p.ticket_event_id,p.receipt_id,p.issued_at,p.created_at,v_issue,v_prefix,v_slopes,r.snapshot_id,
  v_family,v_unit,r.captured_at,r.known_at,r.available_total,r.sector_count,r.source_payload_sha256,v_source_status) returning * into old;
 foreach v_h in array array[24,48,72] loop
  v_target:=v_issue+make_interval(hours=>v_h); v_p:=null; v_d6:=null; v_d24:=null;
  v_status:=v_source_status;
  if v_source_status<>'VALID' then v_status:='INVALID_SOURCE';
  elsif v_target>=f.kickoff_at then v_status:='OUTSIDE_KICKOFF';
  else
   v_p:=r.available_total::float8; v_d6:=v_p; v_d24:=v_p; v_status:='VALID';
   v_age:=extract(epoch from(v_issue-r.captured_at))/3600.0;
   v_slope:=v_slopes[1];
   if v_slope is not null and v_slope<'Infinity'::float8 and v_slope>'-Infinity'::float8 then v_d6:=greatest(0::float8,v_p+v_slope*(v_h+v_age)); end if;
   v_slope:=v_slopes[2];
   if v_slope is not null and v_slope<'Infinity'::float8 and v_slope>'-Infinity'::float8 then v_d24:=greatest(0::float8,v_p+v_slope*(v_h+v_age)); end if;
  end if;
  insert into private.rolling72_forward_baselines_b_predictions_v1(bundle_id,lane_id,ticket_event_id,receipt_id,issued_at,horizon_hours,target_at,
   source_status,persistence_prediction,drift6_prediction,drift24_prediction,persistence_status,drift6_status,drift24_status,features)
  values(old.id,l.lane_id,p.ticket_event_id,p.receipt_id,v_issue,v_h,v_target,v_source_status,v_p,v_d6,v_d24,
   case when v_p is null then v_status else 'PERSISTENCE' end,
   case when v_p is null then v_status when v_slopes[1] is null or v_slopes[1]>='Infinity'::float8 or v_slopes[1]<='-Infinity'::float8 then 'FALLBACK_MISSING_SLOPE' else 'DRIFT6' end,
   case when v_p is null then v_status when v_slopes[2] is null or v_slopes[2]>='Infinity'::float8 or v_slopes[2]<='-Infinity'::float8 then 'FALLBACK_MISSING_SLOPE' else 'DRIFT24' end,
   jsonb_build_object('origin_receipt_id',r.id,'origin_snapshot_id',r.snapshot_id,'origin_payload_sha256',r.source_payload_sha256,
    'parent_prefix_sha256',v_prefix,'parent_slopes',v_slopes,'source_age_hours',case when r.captured_at is null then null else extract(epoch from(v_issue-r.captured_at))/3600.0 end,
    'source_family',v_family,'source_unit',v_unit,'sector_count',r.sector_count,'continuity','UNKNOWN'));
 end loop;
end $$;
revoke all on function private.rolling72_forward_baselines_b_issue_v1(bigint) from public,anon,authenticated,service_role;

create function private.rolling72_forward_baselines_b_on_parent_v1() returns trigger
language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
begin
 begin
  perform pg_catalog.pg_advisory_xact_lock_shared(pg_catalog.hashtextextended('rolling72-forward-b:activation',20261119));
  perform private.rolling72_forward_baselines_b_issue_v1(new.id);
 exception when others then
  begin insert into private.rolling72_forward_baselines_b_failures_v1(parent_prediction_id,receipt_id,sqlstate)
   values(new.id,new.receipt_id,SQLSTATE);
  exception when others then null; end;
 end;
 return new;
end $$;
revoke all on function private.rolling72_forward_baselines_b_on_parent_v1() from public,anon,authenticated,service_role;
create trigger rolling72_forward_baselines_b_parent_v1 after insert on private.rolling72_lad_predictions_v5
 for each row execute function private.rolling72_forward_baselines_b_on_parent_v1();

create function public.activate_rolling72_forward_baselines_b_v1(p_manifest_text text,p_manifest_sha256 text)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare j jsonb; old private.rolling72_forward_baselines_b_lane_v1%rowtype; v5 private.rolling72_lad_lane_v5%rowtype;
 v_now timestamptz; v_freeze timestamptz; ids bigint[];
begin
 if p_manifest_text is null or length(p_manifest_text)>32768 or p_manifest_sha256 !~ '^[0-9a-f]{64}$'
  or encode(extensions.digest(convert_to(p_manifest_text,'UTF8'),'sha256'),'hex') is distinct from p_manifest_sha256 then raise exception 'ROLLING72_FORWARD_B_MANIFEST_HASH'; end if;
 j:=p_manifest_text::jsonb;
 if jsonb_typeof(j) is distinct from 'object' or (select count(*) from jsonb_object_keys(j))<>13
  or j->>'version' is distinct from 'rolling72-forward-baselines-b-v1'
  or j->>'lane_id' is distinct from 'rolling72-forward-baselines-b-v1'
  or j->'fixture_ids' is distinct from '[24374,24375,24376,24377,24378]'::jsonb
  or j->'methods' is distinct from '["persistence","drift6","drift24"]'::jsonb
  or j->'horizons' is distinct from '[24,48,72]'::jsonb
  or j->>'scope' is distinct from 'public_available_total_with_scope_events_v1'
  or j->>'continuity' is distinct from 'UNKNOWN' or j->>'unit' is distinct from 'available_total_seats'
  or (j->>'parent_max_age_seconds')::integer is distinct from 90
  or (j->>'issue_source_max_age_seconds')::integer is distinct from 3600
  or (j->>'target_source_max_age_seconds')::integer is distinct from 21600
  or coalesce(j->>'sql_sha256','') !~ '^[0-9a-f]{64}$'
  or coalesce(j->>'frozen_at','')='' then raise exception 'ROLLING72_FORWARD_B_MANIFEST_CONTRACT'; end if;
 v_freeze:=(j->>'frozen_at')::timestamptz;
 if v_freeze is null then raise exception 'ROLLING72_FORWARD_B_FREEZE_TIME'; end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-forward-b:activation',20261119));
 v_now:=clock_timestamp();
 select * into old from private.rolling72_forward_baselines_b_lane_v1 where lane_id='rolling72-forward-baselines-b-v1';
 if found then
  if old.manifest_sha256=p_manifest_sha256 and old.manifest_text=p_manifest_text then return jsonb_build_object('activated',false,'idempotent',true,'activated_at',old.activated_at,'issue_until',old.issue_until,'scoring_until',old.scoring_until); end if;
  raise exception 'ROLLING72_FORWARD_B_ALREADY_FROZEN';
 end if;
 if v_freeze>v_now or v_freeze<v_now-interval '7 days' then raise exception 'ROLLING72_FORWARD_B_FREEZE_TIME'; end if;
 select * into v5 from private.rolling72_lad_lane_v5 where lane_id='rolling72-lad-shadow-v5';
 if not found or v5.manifest_text::jsonb->'fixture_ids' is distinct from j->'fixture_ids'
  or v5.issue_until<=v_now or v5.scoring_until<v_now then raise exception 'ROLLING72_FORWARD_B_PARENT_LANE'; end if;
 ids:=array(select jsonb_array_elements_text(j->'fixture_ids')::bigint order by 1);
 if (select count(*) from private.rolling72_managed_fixtures_v3a f join public.ticket_events e on e.id=f.ticket_event_id
   where f.ticket_event_id=any(ids) and f.lane_id='rolling72-managed-persistence-shadow-v3a'
    and f.kickoff_at>v_now and e.kickoff_at=f.kickoff_at and e.club_slug=f.club_slug
    and e.provider=f.provider and e.external_event_id=f.external_event_id and e.source_domain=f.source_domain
    and e.home_team=f.home_team and e.away_team=f.away_team and e.competition is not distinct from f.competition
    and e.match_date=f.match_date)=5 then null; else raise exception 'ROLLING72_FORWARD_B_FIXTURE_SCOPE'; end if;
 insert into private.rolling72_forward_baselines_b_lane_v1(lane_id,manifest_text,manifest_sha256,sql_sha256,fixture_ids,activated_at,issue_until,scoring_until)
 values('rolling72-forward-baselines-b-v1',p_manifest_text,p_manifest_sha256,j->>'sql_sha256',ids,v_now,v5.issue_until,v5.scoring_until);
 return jsonb_build_object('activated',true,'lane_id','rolling72-forward-baselines-b-v1','activated_at',v_now,
  'issue_until',v5.issue_until,'scoring_until',v5.scoring_until,'sql_sha256',j->>'sql_sha256','initial_parent_replay',false);
end $$;

create function public.score_rolling72_forward_baselines_b_v1() returns jsonb
language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare p record; b private.rolling72_forward_baselines_b_bundles_v1%rowtype; r private.rolling72_managed_receipts_v3a%rowtype;
 origin private.rolling72_managed_receipts_v3a%rowtype; s public.snapshots%rowtype; os public.snapshots%rowtype;
 f private.rolling72_managed_fixtures_v3a%rowtype; e public.ticket_events%rowtype; v_now timestamptz; v_status text; v_n integer:=0;
 v_family text; v_unit text; v_origin_family text; v_origin_unit text; v_age float8;
begin
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-forward-b:scorer',20261119));
 v_now:=clock_timestamp();
 if not exists(select 1 from private.rolling72_forward_baselines_b_lane_v1 where scoring_until>=v_now) then
  return jsonb_build_object('scored_at',v_now,'new_labels',0,'expired_or_inactive',true); end if;
 for p in select x.* from private.rolling72_forward_baselines_b_predictions_v1 x
  where x.target_at<=v_now and not exists(select 1 from private.rolling72_forward_baselines_b_labels_v1 q where q.prediction_id=x.id)
  order by x.target_at,x.id loop
  v_status:='UNMATCHED'; r:=null; select * into b from private.rolling72_forward_baselines_b_bundles_v1 where id=p.bundle_id;
  if p.source_status<>'VALID' then v_status:=p.source_status;
  elsif p.persistence_prediction is null then v_status:='OUTSIDE_KICKOFF';
  else
   select * into r from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=p.ticket_event_id and x.known_at<=v_now
    and x.captured_at>p.issued_at and x.captured_at<=p.target_at and x.captured_at>=p.target_at-interval '6 hours'
    and x.receipt_status='VALID' and x.available_total is not null and x.available_total>=0
    order by x.captured_at desc,x.id desc limit 1;
   if found then
    select * into origin from private.rolling72_managed_receipts_v3a where id=b.receipt_id;
    select * into s from public.snapshots where id=r.snapshot_id; select * into os from public.snapshots where id=origin.snapshot_id;
    select * into f from private.rolling72_managed_fixtures_v3a where ticket_event_id=p.ticket_event_id;
    select * into e from public.ticket_events where id=p.ticket_event_id;
    v_family:=e.provider||'/'||coalesce(r.source_payload->>'source','UNKNOWN'); v_unit:=coalesce(r.source_payload->>'unit','available_total_seats');
    v_origin_family:=b.source_family; v_origin_unit:=b.source_unit;
    v_age:=extract(epoch from(p.target_at-r.captured_at));
    if r.receipt_status<>'VALID' or r.available_total is null or r.available_total<0 or r.sector_count is null or r.sector_count<=0 then v_status:='INVALID_TARGET';
    elsif v_family is distinct from v_origin_family or v_unit is distinct from v_origin_unit then v_status:='SOURCE_MISMATCH';
    elsif e.id is null or f.ticket_event_id is null or e.provider is distinct from f.provider or e.external_event_id is distinct from f.external_event_id
      or e.club_slug is distinct from f.club_slug or e.source_domain is distinct from f.source_domain
      or e.home_team is distinct from f.home_team or e.away_team is distinct from f.away_team
      or e.competition is distinct from f.competition or e.match_date is distinct from f.match_date or e.kickoff_at is distinct from f.kickoff_at then v_status:='METADATA_MISMATCH';
    elsif s.id is null or r.source_payload is distinct from to_jsonb(s)
      or encode(extensions.digest(convert_to(r.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from r.source_payload_sha256
      or os.id is null or origin.source_payload is distinct from to_jsonb(os)
      or encode(extensions.digest(convert_to(origin.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from origin.source_payload_sha256
      or s.event_id::text is distinct from f.external_event_id or os.event_id::text is distinct from f.external_event_id
      or s.ticket_event_id is distinct from p.ticket_event_id or os.ticket_event_id is distinct from p.ticket_event_id
      or s.event_kickoff_at_capture is distinct from f.kickoff_at or os.event_kickoff_at_capture is distinct from f.kickoff_at
      or s.event_match_date_at_capture is distinct from f.match_date or os.event_match_date_at_capture is distinct from f.match_date then v_status:='SOURCE_MUTATED';
    else
     v_status:='SCORED';
     insert into private.rolling72_forward_baselines_b_labels_v1(prediction_id,scored_at,label_receipt_id,label_snapshot_id,
      actual_available_total,label_captured_at,label_known_at,label_age_seconds,label_source_family,label_source_unit,
      origin_sector_count,target_sector_count,sector_count_delta,continuity,
      persistence_absolute_error,drift6_absolute_error,drift24_absolute_error)
     values(p.id,v_now,r.id,r.snapshot_id,r.available_total,r.captured_at,r.known_at,v_age,v_family,v_unit,
      origin.sector_count,r.sector_count,r.sector_count-origin.sector_count,'UNKNOWN',
      abs(p.persistence_prediction-r.available_total),abs(p.drift6_prediction-r.available_total),abs(p.drift24_prediction-r.available_total))
     on conflict(prediction_id) do nothing;
     if found then v_n:=v_n+1; end if;
    end if;
   end if;
  end if;
  insert into private.rolling72_forward_baselines_b_attempts_v1(prediction_id,attempted_at,status,selected_receipt_id)
  values(p.id,v_now,v_status,case when r.id is null then null else r.id end);
 end loop;
 return jsonb_build_object('scored_at',v_now,'new_labels',v_n,'expired_or_inactive',false);
end $$;

create function public.get_rolling72_forward_baselines_b_v1_status() returns jsonb
language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare l private.rolling72_forward_baselines_b_lane_v1%rowtype; v_now timestamptz;
begin
 v_now:=clock_timestamp(); select * into l from private.rolling72_forward_baselines_b_lane_v1 where lane_id='rolling72-forward-baselines-b-v1';
 if not found then return jsonb_build_object('lane_id','rolling72-forward-baselines-b-v1','activated',false); end if;
 return jsonb_build_object('lane_id',l.lane_id,'activated',true,'activated_at',l.activated_at,'issue_until',l.issue_until,
  'scoring_until',l.scoring_until,'manifest_sha256',l.manifest_sha256,'sql_sha256',l.sql_sha256,
  'prediction_statuses',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb) from (select source_status status,count(*) n from private.rolling72_forward_baselines_b_predictions_v1 group by source_status) q),
  'horizons',(select coalesce(jsonb_agg(jsonb_build_object('horizon_hours',h,'predictions',c.predictions,'labels',c.labels,
   'labeled_fixtures',c.labeled_fixtures,'within_1h_labeled_fixtures',c.fast_fixtures,
   'pending_future',c.pending_future,'pending_due',c.pending_due,'latest_attempt_statuses',c.attempts,
   'method_statuses',c.method_statuses,'scope_count_changed_labels',c.scope_changes,
   'policy_mae',c.mae,'within_1h_policy_mae',c.fast_mae) order by h),'[]'::jsonb)
   from (values(24),(48),(72)) z(h) cross join lateral (
    select (select count(*) from private.rolling72_forward_baselines_b_predictions_v1 p where p.horizon_hours=h) predictions,
     (select count(*) from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id where p.horizon_hours=h) labels,
     (select count(distinct p.ticket_event_id) from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id where p.horizon_hours=h) labeled_fixtures,
     (select count(distinct p.ticket_event_id) from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id where p.horizon_hours=h and q.label_age_seconds<=3600) fast_fixtures,
     (select count(*) from private.rolling72_forward_baselines_b_predictions_v1 p where p.horizon_hours=h and p.target_at>v_now and p.persistence_prediction is not null) pending_future,
     (select count(*) from private.rolling72_forward_baselines_b_predictions_v1 p where p.horizon_hours=h and p.target_at<=v_now and p.persistence_prediction is not null and not exists(select 1 from private.rolling72_forward_baselines_b_labels_v1 q where q.prediction_id=p.id)) pending_due,
     (select coalesce(jsonb_object_agg(status,n),'{}'::jsonb) from(select status,count(*) n from(
      select distinct on(a.prediction_id) a.status from private.rolling72_forward_baselines_b_attempts_v1 a
      join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=a.prediction_id
      where p.horizon_hours=h order by a.prediction_id,a.id desc) latest group by status) q) attempts,
     (select jsonb_build_object(
       'persistence',(select coalesce(jsonb_object_agg(persistence_status,n),'{}'::jsonb) from(select persistence_status,count(*) n from private.rolling72_forward_baselines_b_predictions_v1 where horizon_hours=h group by persistence_status) x),
       'drift6',(select coalesce(jsonb_object_agg(drift6_status,n),'{}'::jsonb) from(select drift6_status,count(*) n from private.rolling72_forward_baselines_b_predictions_v1 where horizon_hours=h group by drift6_status) x),
       'drift24',(select coalesce(jsonb_object_agg(drift24_status,n),'{}'::jsonb) from(select drift24_status,count(*) n from private.rolling72_forward_baselines_b_predictions_v1 where horizon_hours=h group by drift24_status) x))) method_statuses,
     (select count(*) from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id
       where p.horizon_hours=h and q.sector_count_delta<>0) scope_changes,
     (select jsonb_build_object('persistence',avg(event_p)::float8,'drift6',avg(event_6)::float8,'drift24',avg(event_24)::float8) from(
      select p.ticket_event_id,avg(q.persistence_absolute_error) event_p,avg(q.drift6_absolute_error) event_6,avg(q.drift24_absolute_error) event_24
      from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id
      where p.horizon_hours=h group by p.ticket_event_id) e) mae,
     (select jsonb_build_object('persistence',avg(event_p)::float8,'drift6',avg(event_6)::float8,'drift24',avg(event_24)::float8) from(
      select p.ticket_event_id,avg(q.persistence_absolute_error) event_p,avg(q.drift6_absolute_error) event_6,avg(q.drift24_absolute_error) event_24
      from private.rolling72_forward_baselines_b_labels_v1 q join private.rolling72_forward_baselines_b_predictions_v1 p on p.id=q.prediction_id
      where p.horizon_hours=h and q.label_age_seconds<=3600 group by p.ticket_event_id) e) fast_mae
   ) c)
 );
end $$;

revoke all on function public.activate_rolling72_forward_baselines_b_v1(text,text),
 public.score_rolling72_forward_baselines_b_v1(),public.get_rolling72_forward_baselines_b_v1_status() from public,anon,authenticated;
grant execute on function public.activate_rolling72_forward_baselines_b_v1(text,text),
 public.score_rolling72_forward_baselines_b_v1(),public.get_rolling72_forward_baselines_b_v1_status() to service_role;
-- The parent registers a dedicated 10-minute pg_cron after review/activation; no old jobs are touched here.
