-- Separate prospective candidate sidecar. Frozen v3a rows/functions are read-only.
create table private.rolling72_lad_lane_v5 (
 lane_id text primary key check(lane_id='rolling72-lad-shadow-v5'),
 model_sha256 text not null check(model_sha256 ~ '^[0-9a-f]{64}$'), model_text text not null,
 model jsonb not null, manifest_sha256 text not null, manifest_text text not null,
 activated_at timestamptz not null, issue_until timestamptz not null, scoring_until timestamptz not null,
 check(model_text::jsonb=model),
 check(encode(extensions.digest(convert_to(model_text,'UTF8'),'sha256'),'hex')=model_sha256),
 check(encode(extensions.digest(convert_to(manifest_text,'UTF8'),'sha256'),'hex')=manifest_sha256)
);
create table private.rolling72_lad_predictions_v5 (
 id bigint generated always as identity primary key,
 lane_id text not null references private.rolling72_lad_lane_v5(lane_id),
 ticket_event_id bigint not null, receipt_id bigint not null references private.rolling72_managed_receipts_v3a(id),
 issued_at timestamptz not null, horizon_hours integer not null check(horizon_hours in(24,48,72)),
 target_at timestamptz not null, status text not null check(status in('LEARNED','FALLBACK_UNSEEN_SOURCE_FAMILY','FALLBACK_MATURITY_SUPPORT','FALLBACK_NO_HISTORY_ANCHOR','INVALID_SOURCE','OUTSIDE_KICKOFF')), baseline integer, candidate double precision,
 features jsonb not null, created_at timestamptz not null default clock_timestamp(),
 unique(receipt_id,horizon_hours),
 check((baseline is null and candidate is null) or (baseline is not null and candidate is not null and baseline>=0 and candidate>=0 and candidate<'Infinity'::float8))
);
create table private.rolling72_lad_labels_v5 (
 prediction_id bigint primary key references private.rolling72_lad_predictions_v5(id),
 scored_at timestamptz not null, label_receipt_id bigint not null references private.rolling72_managed_receipts_v3a(id),
 actual_available_total integer not null check(actual_available_total>=0),
 candidate_absolute_error double precision not null check(candidate_absolute_error>=0),
 persistence_absolute_error double precision not null check(persistence_absolute_error>=0)
);
create table private.rolling72_lad_attempts_v5 (
 id bigint generated always as identity primary key,
 prediction_id bigint not null references private.rolling72_lad_predictions_v5(id),
 attempted_at timestamptz not null, status text not null
);
create table private.rolling72_lad_failures_v5 (
 id bigint generated always as identity primary key, receipt_id bigint,
 failed_at timestamptz not null default clock_timestamp(), sqlstate text not null
);
create index rolling72_lad_due_v5 on private.rolling72_lad_predictions_v5(target_at);

alter table private.rolling72_lad_lane_v5 enable row level security;
alter table private.rolling72_lad_predictions_v5 enable row level security;
alter table private.rolling72_lad_labels_v5 enable row level security;
alter table private.rolling72_lad_attempts_v5 enable row level security;
alter table private.rolling72_lad_failures_v5 enable row level security;
revoke all on private.rolling72_lad_lane_v5,private.rolling72_lad_predictions_v5,
 private.rolling72_lad_labels_v5,private.rolling72_lad_attempts_v5,private.rolling72_lad_failures_v5
 from public,anon,authenticated,service_role;

create function private.rolling72_lad_immutable_v5() returns trigger
language plpgsql security definer set search_path='' as $$
begin raise exception 'ROLLING72_LAD_IMMUTABLE'; end $$;
create trigger rolling72_lad_lane_immutable_v5 before update or delete on private.rolling72_lad_lane_v5 for each row execute function private.rolling72_lad_immutable_v5();
create trigger rolling72_lad_prediction_immutable_v5 before update or delete on private.rolling72_lad_predictions_v5 for each row execute function private.rolling72_lad_immutable_v5();
create trigger rolling72_lad_label_immutable_v5 before update or delete on private.rolling72_lad_labels_v5 for each row execute function private.rolling72_lad_immutable_v5();
create trigger rolling72_lad_attempt_immutable_v5 before update or delete on private.rolling72_lad_attempts_v5 for each row execute function private.rolling72_lad_immutable_v5();
create trigger rolling72_lad_failure_immutable_v5 before update or delete on private.rolling72_lad_failures_v5 for each row execute function private.rolling72_lad_immutable_v5();

create function private.rolling72_lad_vector_v5(p_last float8,p_first float8,p_span float8,p_age float8,p_maturity float8,p_h integer,p_slopes float8[],p_family text)
returns float8[] language plpgsql immutable set search_path='' as $$
declare a float8; b float8; c float8; n float8;
begin
 if p_last is null or p_first is null or p_span is null or p_age is null or p_maturity is null
    or p_last<0 or p_first<0 or p_span<0 or p_age<0 or p_maturity<=0
    or p_h is null or p_h not in(24,48,72) or array_length(p_slopes,1) is distinct from 3
    or p_family is null or p_family not in('roboticket/roboticket','stellis/stellis_visible_available')
    or greatest(p_last,p_first,p_span,p_age,p_maturity)>='Infinity'::float8 then
  raise exception 'ROLLING72_LAD_BAD_VECTOR'; end if;
 a:=coalesce(p_slopes[1],0)*(p_h+p_age); b:=coalesce(p_slopes[2],0)*(p_h+p_age); c:=coalesce(p_slopes[3],0)*(p_h+p_age);
 n:=1/(1+p_maturity/24);
 return array[p_last,p_last-p_first,ln(1+p_span),ln(1+p_maturity),a,b,c,
   (p_slopes[1] is null)::integer::float8,(p_slopes[2] is null)::integer::float8,(p_slopes[3] is null)::integer::float8,
   a*n,b*n,c*n,(p_family='stellis/stellis_visible_available')::integer::float8];
end $$;

create function private.rolling72_lad_delta_v5(p_model jsonb,p_vector float8[])
returns float8 language plpgsql immutable set search_path='' as $$
declare v float8; s float8; c float8; i integer;
begin
 if jsonb_typeof(p_model->'intercept') is distinct from 'number'
    or array_length(p_vector,1) is distinct from 14 or jsonb_array_length(p_model->'coefficients') is distinct from 14
    or jsonb_array_length(p_model->'scale') is distinct from 14 then raise exception 'ROLLING72_LAD_BAD_MODEL_SHAPE'; end if;
 v:=(p_model->>'intercept')::float8;
 for i in 1..14 loop
  s:=(p_model->'scale'->>(i-1))::float8; c:=(p_model->'coefficients'->>(i-1))::float8;
  if jsonb_typeof(p_model->'scale'->(i-1)) is distinct from 'number' or jsonb_typeof(p_model->'coefficients'->(i-1)) is distinct from 'number'
    or s is null or s<1 or s>='Infinity'::float8 or c is null or abs(c)>='Infinity'::float8 or p_vector[i] is null or abs(p_vector[i])>='Infinity'::float8 then raise exception 'ROLLING72_LAD_NONFINITE'; end if;
  v:=v+c*(p_vector[i]/s);
 end loop;
 if v is null or abs(v)>='Infinity'::float8 then raise exception 'ROLLING72_LAD_NONFINITE'; end if;
 return v;
end $$;

create function private.rolling72_lad_capture_v5(p_receipt_id bigint)
returns void language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare r private.rolling72_managed_receipts_v3a%rowtype; l private.rolling72_lad_lane_v5%rowtype;
 f private.rolling72_managed_fixtures_v3a%rowtype; e public.ticket_events%rowtype;
 v_now timestamptz; v_started timestamptz; v_break timestamptz; v_first record; v_anchor record;
 v_h integer; v_w integer; v_target timestamptz; v_family text; v_maturity float8; v_age float8;
 v_span float8; v_slopes float8[]; v_anchors bigint[]; v_vec float8[]; v_model jsonb; v_status text; v_candidate float8; v_baseline integer; v_prefix_sha text;
begin
 select * into r from private.rolling72_managed_receipts_v3a where id=p_receipt_id;
 if not found then return; end if;
 select * into l from private.rolling72_lad_lane_v5;
 if not found or not (l.manifest_text::jsonb->'fixture_ids' @> to_jsonb(array[r.ticket_event_id])) then return; end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-lad-shadow-v5:'||r.ticket_event_id::text,20261117));
 v_now:=clock_timestamp(); v_started:=v_now;
 if v_now>l.issue_until or exists(select 1 from private.rolling72_lad_predictions_v5 where receipt_id=r.id) then return; end if;
 select * into f from private.rolling72_managed_fixtures_v3a where ticket_event_id=r.ticket_event_id;
 select * into e from public.ticket_events where id=r.ticket_event_id;
 v_family:=e.provider||'/'||(r.source_payload->>'source');
 v_maturity:=extract(epoch from(f.kickoff_at-v_now))/3600; v_age:=extract(epoch from(v_now-r.captured_at))/3600;
 v_status:='VALID';
 select null::bigint as id,null::float8 as available_total,null::timestamptz as captured_at into v_first;
 if r.receipt_status<>'VALID' or r.known_at>v_now or r.captured_at>v_now or r.captured_at<v_now-interval '1 hour'
    or r.available_total is null or r.available_total<0 or r.sector_count is null or r.sector_count<=0
    or e.provider<>'roboticket' or r.source_payload->>'source'<>'roboticket'
    or e.kickoff_at is distinct from f.kickoff_at or e.club_slug is distinct from f.club_slug
    or e.competition is distinct from f.competition or e.match_date is distinct from f.match_date
    or e.external_event_id is distinct from f.external_event_id or e.source_domain is distinct from f.source_domain
    or e.home_team is distinct from f.home_team or e.away_team is distinct from f.away_team
    or not exists(select 1 from public.snapshots z where z.id=r.snapshot_id and to_jsonb(z)=r.source_payload)
    or encode(extensions.digest(convert_to(r.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from r.source_payload_sha256 then v_status:='INVALID_SOURCE'; end if;
 if v_status='VALID' then
  select max(x.captured_at) into v_break from private.rolling72_managed_receipts_v3a x
  where x.ticket_event_id=r.ticket_event_id and x.known_at<=v_now and x.captured_at<=r.captured_at and x.id<=r.id
    and (x.receipt_status<>'VALID' or x.sector_count is distinct from r.sector_count or x.source_payload->>'source' is distinct from r.source_payload->>'source');
  if v_break=r.captured_at then v_status:='INVALID_SOURCE'; end if;
  if exists(select 1 from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=r.ticket_event_id
    and x.known_at<=v_now and x.captured_at<=r.captured_at and x.id<=r.id and (v_break is null or x.captured_at>v_break)
    and (not exists(select 1 from public.snapshots z where z.id=x.snapshot_id and to_jsonb(z)=x.source_payload)
      or encode(extensions.digest(convert_to(x.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from x.source_payload_sha256)) then v_status:='INVALID_SOURCE'; end if;
 end if;
 if v_status='VALID' then
  select x.id,x.available_total,x.captured_at into v_first from private.rolling72_managed_receipts_v3a x
  where x.ticket_event_id=r.ticket_event_id and x.known_at<=v_now and x.captured_at<=r.captured_at and x.id<=r.id
    and x.receipt_status='VALID' and (v_break is null or x.captured_at>v_break)
  order by x.captured_at,x.id desc limit 1;
  v_span:=extract(epoch from(r.captured_at-v_first.captured_at))/3600;
  select encode(extensions.digest(convert_to(coalesce(jsonb_agg(jsonb_build_array(x.id,x.source_payload_sha256) order by x.captured_at,x.id),'[]'::jsonb)::text,'UTF8'),'sha256'),'hex') into v_prefix_sha
   from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=r.ticket_event_id and x.known_at<=v_now
    and x.captured_at<=r.captured_at and x.id<=r.id and x.receipt_status='VALID' and (v_break is null or x.captured_at>v_break);
  v_slopes:=array[]::float8[]; v_anchors:=array[]::bigint[];
  foreach v_w in array array[6,24,72] loop
   select x.id,x.available_total,x.captured_at into v_anchor from private.rolling72_managed_receipts_v3a x
   where x.ticket_event_id=r.ticket_event_id and x.known_at<=v_now and x.id<=r.id and x.receipt_status='VALID'
    and x.captured_at<=r.captured_at-make_interval(hours=>v_w)
    and x.captured_at>=r.captured_at-make_interval(hours=>v_w+6)
    and (v_break is null or x.captured_at>v_break)
   order by x.captured_at desc,x.id desc limit 1;
   if found then v_slopes:=array_append(v_slopes,(r.available_total-v_anchor.available_total)::float8/(extract(epoch from(r.captured_at-v_anchor.captured_at))/3600)); v_anchors:=array_append(v_anchors,v_anchor.id);
   else v_slopes:=array_append(v_slopes,null::float8); v_anchors:=array_append(v_anchors,null::bigint); end if;
  end loop;
 end if;
 foreach v_h in array array[24,48,72] loop
  v_target:=v_now+make_interval(hours=>v_h); v_baseline:=null; v_candidate:=null; v_vec:=null;
  if v_status<>'VALID' then v_status:='INVALID_SOURCE';
  elsif v_target>=f.kickoff_at then v_status:='OUTSIDE_KICKOFF';
  else
   v_baseline:=r.available_total; v_candidate:=v_baseline;
   v_model:=l.model->'models'->v_h::text;
   v_vec:=private.rolling72_lad_vector_v5(r.available_total,v_first.available_total,v_span,v_age,v_maturity,v_h,v_slopes,v_family);
   if not (v_model->'source_families' @> to_jsonb(array[v_family])) then v_status:='FALLBACK_UNSEEN_SOURCE_FAMILY';
   elsif v_maturity<(v_model->>'maturity_min')::float8 or v_maturity>(v_model->>'maturity_max')::float8 then v_status:='FALLBACK_MATURITY_SUPPORT';
   elsif v_slopes[1] is null and v_slopes[2] is null and v_slopes[3] is null then v_status:='FALLBACK_NO_HISTORY_ANCHOR';
   else v_candidate:=greatest(0::float8,r.available_total+private.rolling72_lad_delta_v5(v_model,v_vec)); v_status:='LEARNED'; end if;
  end if;
  insert into private.rolling72_lad_predictions_v5(lane_id,ticket_event_id,receipt_id,issued_at,horizon_hours,target_at,status,baseline,candidate,features)
  values(l.lane_id,r.ticket_event_id,r.id,v_now,v_h,v_target,v_status,v_baseline,v_candidate,
   jsonb_build_object('vector',v_vec,'slopes',v_slopes,'anchor_receipt_ids',v_anchors,'first_receipt_id',v_first.id,
    'prefix_sha256',v_prefix_sha,'first_capture_at',v_first.captured_at,'prefix_span_hours',v_span,'source_age_hours',v_age,'hours_to_kickoff',v_maturity));
  -- Restore validity for the next horizon; fallback/outside are horizon-specific.
  if v_status<>'INVALID_SOURCE' then v_status:='VALID'; end if;
 end loop;
 if clock_timestamp()-v_started>interval '90 seconds' then raise exception 'ROLLING72_LAD_WRITE_ALLOWANCE'; end if;
end $$;

create function private.rolling72_lad_on_receipt_v5() returns trigger
language plpgsql security definer set search_path='' set timezone='UTC' as $$
begin
 begin
  perform pg_catalog.pg_advisory_xact_lock_shared(pg_catalog.hashtextextended('rolling72-lad-shadow-v5:activation',20261117));
  perform private.rolling72_lad_capture_v5(new.id);
 exception when others then
  begin insert into private.rolling72_lad_failures_v5(receipt_id,sqlstate) values(new.id,SQLSTATE);
  exception when others then null; end;
 end;
 return new;
end $$;
create trigger rolling72_lad_receipt_v5 after insert on private.rolling72_managed_receipts_v3a
 for each row execute function private.rolling72_lad_on_receipt_v5();

create function public.activate_rolling72_lad_shadow_v5(p_model_text text,p_model_sha text,p_manifest_text text,p_manifest_sha text)
returns jsonb language plpgsql security definer set search_path='' set timezone='UTC' as $$
declare m jsonb; j jsonb; h text; v jsonb; x jsonb; v_now timestamptz; v_until timestamptz; rid bigint;
begin
 if p_model_text is null or length(p_model_text)>262144 or p_model_sha is null
 or encode(extensions.digest(convert_to(p_model_text,'UTF8'),'sha256'),'hex') is distinct from p_model_sha
 or p_manifest_text is null or length(p_manifest_text)>65536 or p_manifest_sha is null
 or encode(extensions.digest(convert_to(p_manifest_text,'UTF8'),'sha256'),'hex') is distinct from p_manifest_sha then raise exception 'ROLLING72_LAD_HASH_MISMATCH'; end if;
 m:=p_model_text::jsonb; j:=p_manifest_text::jsonb;
 if m->>'version' is distinct from 'rolling72-final-lad-v5' or j->>'version' is distinct from 'rolling72-lad-shadow-v5'
 or j->>'model_sha256' is distinct from p_model_sha
 or j->'fixture_ids' is distinct from '[24374,24375,24376,24377,24378]'::jsonb then raise exception 'ROLLING72_LAD_CONTRACT'; end if;
 -- Parent verifies the exact final precommit/export before this service-only
 -- call. The immutable manifest binds that external provenance to these bytes.
 if j->>'final_precommit_sha256' is null or j->>'final_precommit_sha256' !~ '^[0-9a-f]{64}$'
  or j->>'final_precommit_sha256' is distinct from m->>'precommit_sha256'
  or j->>'artifact_sha256' is null or j->>'artifact_sha256' !~ '^[0-9a-f]{64}$'
  or j->>'artifact_sha256' is distinct from m->>'artifact_sha256'
  or j->>'sql_sha256' is null or j->>'sql_sha256' !~ '^[0-9a-f]{64}$'
  or j->>'base_manifest_sha256' is distinct from '86ace465e4391429f0fb475f0b33a151a44dce6317b49b95bed31bf354e6f464'
  or not exists(select 1 from private.rolling72_managed_lane_v3a where manifest_sha256=j->>'base_manifest_sha256')
 then raise exception 'ROLLING72_LAD_PROVENANCE'; end if;
 foreach h in array array['24','48','72'] loop
  v:=m->'models'->h;
  if v is null or jsonb_typeof(v->'source_families') is distinct from 'array' or jsonb_array_length(v->'source_families')<1
   or jsonb_typeof(v->'maturity_min') is distinct from 'number' or jsonb_typeof(v->'maturity_max') is distinct from 'number'
   or (v->>'maturity_min')::float8<=0 or (v->>'maturity_max')::float8>='Infinity'::float8
   or (v->>'maturity_max')::float8<(v->>'maturity_min')::float8 then raise exception 'ROLLING72_LAD_MODEL_SUPPORT'; end if;
  perform private.rolling72_lad_delta_v5(v,array_fill(0::float8,array[14]));
 end loop;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-lad-shadow-v5:activation',20261117));
 v_now:=clock_timestamp();
 if exists(select 1 from private.rolling72_lad_lane_v5) then raise exception 'ROLLING72_LAD_ALREADY_FROZEN'; end if;
 if (select count(*) from private.rolling72_managed_fixtures_v3a f where f.ticket_event_id in(24374,24375,24376,24377,24378) and f.kickoff_at>v_now)<>5 then raise exception 'ROLLING72_LAD_FIXTURE_SCOPE'; end if;
 select max(kickoff_at) into v_until from private.rolling72_managed_fixtures_v3a where ticket_event_id in(24374,24375,24376,24377,24378);
 insert into private.rolling72_lad_lane_v5 values('rolling72-lad-shadow-v5',p_model_sha,p_model_text,m,p_manifest_sha,p_manifest_text,v_now,v_until,v_until+interval '6 hours');
 for rid in select distinct on(ticket_event_id) id from private.rolling72_managed_receipts_v3a
  where ticket_event_id in(24374,24375,24376,24377,24378) and known_at<=v_now and captured_at<=v_now and captured_at>=v_now-interval '1 hour'
  order by ticket_event_id,captured_at desc,id desc loop
  perform private.rolling72_lad_capture_v5(rid);
 end loop;
 return jsonb_build_object('activated_at',v_now,'issue_until',v_until,'model_sha256',p_model_sha,
  'predictions',(select count(*) from private.rolling72_lad_predictions_v5));
end $$;

create function public.score_rolling72_lad_shadow_v5() returns jsonb
language plpgsql security definer set search_path='' set timezone='UTC' as $$
declare p record; r private.rolling72_managed_receipts_v3a%rowtype; s private.rolling72_managed_receipts_v3a%rowtype;
 f private.rolling72_managed_fixtures_v3a%rowtype; e public.ticket_events%rowtype; v_now timestamptz; v_status text; v_count integer:=0;
begin
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('rolling72-lad-shadow-v5:scoring',20261117));
 v_now:=clock_timestamp();
 if not exists(select 1 from private.rolling72_lad_lane_v5 where scoring_until>=v_now) then
  return jsonb_build_object('scored_at',v_now,'new_labels',0,'expired_or_inactive',true); end if;
 for p in select z.* from private.rolling72_lad_predictions_v5 z where z.target_at<=v_now and z.candidate is not null
  and not exists(select 1 from private.rolling72_lad_labels_v5 q where q.prediction_id=z.id) order by z.target_at,z.id loop
  select * into s from private.rolling72_managed_receipts_v3a where id=p.receipt_id;
  select * into f from private.rolling72_managed_fixtures_v3a where ticket_event_id=p.ticket_event_id;
  select * into e from public.ticket_events where id=p.ticket_event_id;
  select * into r from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=p.ticket_event_id and x.known_at<=v_now
   and x.captured_at<=p.target_at and x.captured_at>p.issued_at order by x.captured_at desc,x.id desc limit 1;
  v_status:='SCORED';
  if not found or r.captured_at<p.target_at-interval '6 hours' then v_status:='UNMATCHED';
  elsif r.receipt_status<>'VALID' or r.available_total is null or r.available_total<0 then v_status:='INVALID_TARGET';
  elsif r.sector_count is distinct from s.sector_count then v_status:='SECTOR_COUNT_CHANGED';
  elsif e.kickoff_at is distinct from f.kickoff_at or e.club_slug is distinct from f.club_slug
    or e.competition is distinct from f.competition or e.match_date is distinct from f.match_date
    or e.provider<>'roboticket' or e.external_event_id is distinct from f.external_event_id or e.source_domain is distinct from f.source_domain
    or e.home_team is distinct from f.home_team or e.away_team is distinct from f.away_team then v_status:='METADATA_CHANGED';
  elsif exists(select 1 from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=p.ticket_event_id and x.known_at<=v_now
   and x.captured_at>=s.captured_at and x.captured_at<=p.target_at and x.id<>s.id
   and (x.receipt_status<>'VALID' or x.sector_count is distinct from s.sector_count or x.source_payload->>'source' is distinct from s.source_payload->>'source')) then v_status:='INVALID_INTERVENING';
  elsif exists(select 1 from private.rolling72_managed_receipts_v3a x where x.ticket_event_id=p.ticket_event_id
   and x.known_at<=v_now and ((x.captured_at>=s.captured_at and x.captured_at<=p.target_at) or x.id=s.id)
   and (not exists(select 1 from public.snapshots z where z.id=x.snapshot_id and to_jsonb(z)=x.source_payload)
    or encode(extensions.digest(convert_to(x.source_payload::text,'UTF8'),'sha256'),'hex') is distinct from x.source_payload_sha256)) then v_status:='SOURCE_MUTATED'; end if;
  insert into private.rolling72_lad_attempts_v5(prediction_id,attempted_at,status) values(p.id,v_now,v_status);
  if v_status='SCORED' then
   insert into private.rolling72_lad_labels_v5 values(p.id,v_now,r.id,r.available_total,abs(p.candidate-r.available_total),abs(p.baseline-r.available_total));
   v_count:=v_count+1;
  end if;
 end loop;
 return jsonb_build_object('scored_at',v_now,'new_labels',v_count);
end $$;

create function public.get_rolling72_lad_shadow_v5_status() returns jsonb
language sql stable security definer set search_path='' set timezone='UTC' as $$
 select jsonb_build_object('lane',(select to_jsonb(l)-'model_text'-'model'-'manifest_text' from private.rolling72_lad_lane_v5 l),
 'prediction_statuses',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb) from(select status,count(*) n from private.rolling72_lad_predictions_v5 group by status)x),
 'horizons',(select jsonb_agg(jsonb_build_object('horizon_hours',h,'predictions',(select count(*) from private.rolling72_lad_predictions_v5 where horizon_hours=h),
  'labels',(select count(*) from private.rolling72_lad_labels_v5 q join private.rolling72_lad_predictions_v5 p on p.id=q.prediction_id where p.horizon_hours=h),
  'mae',(select avg(cm) from(select p.ticket_event_id,avg(q.candidate_absolute_error) cm from private.rolling72_lad_labels_v5 q join private.rolling72_lad_predictions_v5 p on p.id=q.prediction_id where p.horizon_hours=h group by p.ticket_event_id)a),
  'persistence_mae',(select avg(pm) from(select p.ticket_event_id,avg(q.persistence_absolute_error) pm from private.rolling72_lad_labels_v5 q join private.rolling72_lad_predictions_v5 p on p.id=q.prediction_id where p.horizon_hours=h group by p.ticket_event_id)a),
  'learned_only_mae',(select avg(cm) from(select p.ticket_event_id,avg(q.candidate_absolute_error) cm from private.rolling72_lad_labels_v5 q join private.rolling72_lad_predictions_v5 p on p.id=q.prediction_id where p.horizon_hours=h and p.status='LEARNED' group by p.ticket_event_id)a))) from unnest(array[24,48,72]) h),
 'failures',(select count(*) from private.rolling72_lad_failures_v5),'eligible_new_review_fixtures',0,'pool_semantics','UNKNOWN','live_adjustment',0);
$$;

revoke all on function private.rolling72_lad_immutable_v5(),private.rolling72_lad_vector_v5(float8,float8,float8,float8,float8,integer,float8[],text),
 private.rolling72_lad_delta_v5(jsonb,float8[]),private.rolling72_lad_capture_v5(bigint),private.rolling72_lad_on_receipt_v5() from public,anon,authenticated,service_role;
revoke all on function public.activate_rolling72_lad_shadow_v5(text,text,text,text),public.score_rolling72_lad_shadow_v5(),public.get_rolling72_lad_shadow_v5_status() from public,anon,authenticated;
grant execute on function public.activate_rolling72_lad_shadow_v5(text,text,text,text),public.score_rolling72_lad_shadow_v5(),public.get_rolling72_lad_shadow_v5_status() to service_role;
