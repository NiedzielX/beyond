-- Independent forward-only source runtime. No forecast, score or cron is added.
-- Existing admission and source tables are read-only dependencies.
create schema if not exists private;

create table private.rolling72_mvp_research_v1_lane (
 lane_id text primary key check(lane_id='rolling72-mvp-research-v1'),
 manifest_text text not null, manifest_sha256 text not null check(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 sql_sha256 text not null check(sql_sha256 ~ '^[0-9a-f]{64}$'),
 activated_at timestamptz not null, issue_until timestamptz not null,
 scoring_until timestamptz not null, max_fixtures integer not null check(max_fixtures between 1 and 1000),
 check(issue_until>activated_at), check(scoring_until>=issue_until+interval '78 hours')
);
create table private.rolling72_mvp_research_v1_registry (
 ticket_event_id bigint primary key references public.ticket_events(id),
 admission_receipt_id bigint not null unique references private.roboticket_admission_receipts_v2(id),
 lane_id text not null references private.rolling72_mvp_research_v1_lane,
 club_slug text not null, external_event_id text not null, kickoff_at timestamptz not null,
 admission_known_at timestamptz not null, registered_at timestamptz not null,
 admission_sha256 text not null check(admission_sha256 ~ '^[0-9a-f]{64}$'),
 binding_sha256 text not null check(binding_sha256 ~ '^[0-9a-f]{64}$'), binding jsonb not null,
 unique(club_slug,external_event_id), check(registered_at>=admission_known_at)
);
create table private.rolling72_mvp_research_v1_registration_attempts (
 id bigint generated always as identity primary key, admission_receipt_id bigint not null,
 attempted_at timestamptz not null, ticket_event_id bigint, status text not null, reason text
);
create table private.rolling72_mvp_research_v1_runs (
 id uuid primary key, started_at timestamptz not null, completed_at timestamptz not null,
 status text not null, attempted_snapshots integer not null check(attempted_snapshots between 0 and 25),
 registered_fixtures integer not null, check(completed_at>=started_at)
);
create table private.rolling72_mvp_research_v1_attempts (
 id bigint generated always as identity primary key,
 run_id uuid not null references private.rolling72_mvp_research_v1_runs deferrable initially deferred,
 ticket_event_id bigint not null references private.rolling72_mvp_research_v1_registry,
 snapshot_id bigint, read_started_at timestamptz not null, read_completed_at timestamptz not null,
 known_at timestamptz not null, captured_at timestamptz, status text not null, reason text,
 source_content_sha256 text not null, snapshot_sha256 text, attempt_binding_sha256 text not null,
 raw_source jsonb not null, binding_payload jsonb not null,
 unique(id,ticket_event_id,snapshot_id,known_at),
 check(read_started_at<=read_completed_at and read_completed_at<=known_at),
 check(source_content_sha256 ~ '^[0-9a-f]{64}$' and attempt_binding_sha256 ~ '^[0-9a-f]{64}$')
);
create table private.rolling72_mvp_research_v1_seals (
 id bigint generated always as identity primary key,
 ticket_event_id bigint not null references private.rolling72_mvp_research_v1_registry,
 snapshot_id bigint not null references public.snapshots(id),
 attempt_id bigint not null unique references private.rolling72_mvp_research_v1_attempts,
 captured_at timestamptz not null, read_started_at timestamptz not null,
 read_completed_at timestamptz not null, known_at timestamptz not null,
 available_total bigint not null check(available_total>=0), sector_count integer not null check(sector_count>0),
 source_content_sha256 text not null check(source_content_sha256 ~ '^[0-9a-f]{64}$'),
 snapshot_sha256 text not null check(snapshot_sha256 ~ '^[0-9a-f]{64}$'), source_payload jsonb not null,
 phase text not null check(phase in('ISSUE_WINDOW','LABEL_ONLY')),
 prior_seal_id bigint references private.rolling72_mvp_research_v1_seals,
 prior_status text not null check(prior_status in('NO_PRIOR','READY_PRIOR')),
 transition_status text not null check(transition_status in('NO_PRIOR','COMPLETE','GAPPED')),
 elapsed_capture_seconds numeric, total_delta bigint, common_sector_delta bigint,
 added_available bigint, removed_available bigint, added_sector_count integer, removed_sector_count integer,
 price_area_membership_change_count integer, gap_count integer not null check(gap_count>=0),
 transition jsonb not null,
 unique(ticket_event_id,snapshot_id),
 unique(id,ticket_event_id), unique(id,ticket_event_id,known_at),
 foreign key(attempt_id,ticket_event_id,snapshot_id,known_at)
  references private.rolling72_mvp_research_v1_attempts(id,ticket_event_id,snapshot_id,known_at),
 foreign key(prior_seal_id,ticket_event_id)
  references private.rolling72_mvp_research_v1_seals(id,ticket_event_id),
 check(read_started_at<=read_completed_at and read_completed_at<=known_at and captured_at<=known_at),
 check((prior_seal_id is null and prior_status='NO_PRIOR' and transition_status='NO_PRIOR'
    and elapsed_capture_seconds is null and total_delta is null and common_sector_delta is null
    and added_available is null and removed_available is null and gap_count=0)
  or (prior_seal_id is not null and prior_status='READY_PRIOR' and transition_status in('COMPLETE','GAPPED')
    and elapsed_capture_seconds>=0 and total_delta=common_sector_delta+added_available-removed_available
    and added_available>=0 and removed_available>=0))
);
create table private.rolling72_mvp_research_v1_candidates (
 id bigint generated always as identity primary key,
 seal_id bigint not null references private.rolling72_mvp_research_v1_seals,
 ticket_event_id bigint not null references private.rolling72_mvp_research_v1_registry,
 horizon_hours integer not null check(horizon_hours in(24,48,72)),
 observation_known_at timestamptz not null, provisional_target_at timestamptz not null,
 status text not null check(status in('SOURCE_ELIGIBLE','OUTSIDE_KICKOFF')),
 unique(seal_id,horizon_hours),
 foreign key(seal_id,ticket_event_id,observation_known_at)
  references private.rolling72_mvp_research_v1_seals(id,ticket_event_id,known_at),
 check(provisional_target_at=observation_known_at+make_interval(hours=>horizon_hours))
);
create index rolling72_mvp_attempt_snapshot_idx on private.rolling72_mvp_research_v1_attempts(ticket_event_id,snapshot_id,id desc);
create index rolling72_mvp_seal_capture_idx on private.rolling72_mvp_research_v1_seals(ticket_event_id,captured_at desc,snapshot_id desc);

create function private.rolling72_mvp_research_v1_immutable() returns trigger
language plpgsql set search_path='' as $$ begin raise exception 'ROLLING72_MVP_IMMUTABLE'; end $$;
create function private.rolling72_mvp_research_v1_hash(j jsonb) returns text
language sql immutable set search_path='' as $$ select encode(sha256(convert_to(j::text,'UTF8')),'hex') $$;

-- Reconstruct the most recent past full XID from a tuple's 32-bit xmin.
-- CLOG status rejects own top-level/subtransaction writes; entry snapshot also
-- rejects transactions that committed only after this RPC's read boundary.
-- Old/truncated/unknown transaction status fails closed, never proves knowledge.
create function private.rolling72_mvp_research_v1_committed(x xid,snap pg_snapshot)
returns boolean language plpgsql volatile set search_path='' as $$
declare cur numeric; full_xid numeric;
begin
 if x is null then return false; end if;
 if x::text='2' then return true; end if;
 if x::text in('0','1') then return false; end if;
 cur:=pg_catalog.pg_current_xact_id()::text::numeric;
 full_xid:=floor(cur/4294967296)*4294967296+x::text::numeric;
 if full_xid>cur then full_xid:=full_xid-4294967296; end if;
 if full_xid<3 then return false; end if;
 return coalesce(pg_catalog.pg_visible_in_snapshot(full_xid::text::xid8,snap)
   and pg_catalog.pg_xact_status(full_xid::text::xid8)='committed',false);
exception when others then return false;
end $$;

create function private.rolling72_mvp_research_v1_capture_one(
 p_event_id bigint,p_snapshot_id bigint,p_run uuid,p_entry_snapshot pg_snapshot)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 l private.rolling72_mvp_research_v1_lane%rowtype; r private.rolling72_mvp_research_v1_registry%rowtype;
 old private.rolling72_mvp_research_v1_seals%rowtype; prior private.rolling72_mvp_research_v1_seals%rowtype;
 a jsonb; e jsonb; c jsonb; s jsonb; pa jsonb:='[]'::jsonb; inv jsonb:='[]'::jsonb; raw jsonb;
 committed boolean; had_source boolean; b jsonb; content_hash text; header_hash text; prior_header text;
 started timestamptz:=clock_timestamp(); completed timestamptz; known timestamptz; captured timestamptz;
 st text:='READY'; reason text; phase text; aid bigint; sid bigint; candidate_ids jsonb:='[]'::jsonb;
 attempt_payload jsonb; attempt_hash text; transition jsonb; h integer; intermediate jsonb:='[]'::jsonb;
 pa_total bigint; inv_total bigint; n_sectors integer; total bigint;
 common_delta bigint; added bigint; removed bigint; n_added integer; n_removed integer; n_memberships integer;
 gaps integer:=0; gap_ids jsonb:='[]'::jsonb; elapsed numeric; prior_status text:='NO_PRIOR';
 transition_status text:='NO_PRIOR';
begin
 select * into l from private.rolling72_mvp_research_v1_lane;
 select * into r from private.rolling72_mvp_research_v1_registry where ticket_event_id=p_event_id;
 if not found then raise exception 'MVP_EVENT_NOT_REGISTERED'; end if;
 if clock_timestamp()>=l.scoring_until then
  st:='EXPIRED'; reason:='CAPTURE_EXPIRED'; completed:=clock_timestamp(); raw:='{}'::jsonb;
 else
  select * into prior from private.rolling72_mvp_research_v1_seals
   where ticket_event_id=p_event_id order by captured_at desc,snapshot_id desc limit 1;
  -- Exactly one statement reads the whole current source bundle.
  -- All validation/hashing below uses these cached values.
  select to_jsonb(ar),to_jsonb(ev),to_jsonb(cl),to_jsonb(ss),
   coalesce((select jsonb_agg(to_jsonb(x) order by x.sector_source_id,x.sector,x.price_area_id,x.id)
    from public.sector_price_area_observations_v1 x where x.snapshot_id=ss.id),'[]'::jsonb),
   coalesce((select jsonb_agg(to_jsonb(x) order by x.sector,x.available,to_jsonb(x)::text)
    from public.sector_inventory x where x.snapshot_id=ss.id),'[]'::jsonb),
   coalesce((select jsonb_agg(jsonb_build_object('snapshot_id',z.id,'captured_at',z.captured_at) order by z.captured_at,z.id)
    from public.snapshots z where z.ticket_event_id=rr.ticket_event_id
     and prior.id is not null and (z.captured_at,z.id)>(prior.captured_at,prior.snapshot_id)
     and (z.captured_at,z.id)<(ss.captured_at,ss.id)
     and private.rolling72_mvp_research_v1_committed(z.xmin,p_entry_snapshot)
     and not exists(select 1 from private.rolling72_mvp_research_v1_seals zz where zz.snapshot_id=z.id)),'[]'::jsonb),
   exists(select 1 from public.snapshots q where q.ticket_event_id=rr.ticket_event_id
    and private.rolling72_mvp_research_v1_committed(q.xmin,p_entry_snapshot)),
   private.rolling72_mvp_research_v1_committed(ar.xmin,p_entry_snapshot)
    and private.rolling72_mvp_research_v1_committed(ev.xmin,p_entry_snapshot)
    and private.rolling72_mvp_research_v1_committed(cl.xmin,p_entry_snapshot)
    and private.rolling72_mvp_research_v1_committed(ss.xmin,p_entry_snapshot)
    and coalesce((select bool_and(private.rolling72_mvp_research_v1_committed(x.xmin,p_entry_snapshot))
      from public.sector_price_area_observations_v1 x where x.snapshot_id=ss.id),true)
    and coalesce((select bool_and(private.rolling72_mvp_research_v1_committed(x.xmin,p_entry_snapshot))
      from public.sector_inventory x where x.snapshot_id=ss.id),true)
  into a,e,c,s,pa,inv,intermediate,had_source,committed
  from private.rolling72_mvp_research_v1_registry rr
  join private.roboticket_admission_receipts_v2 ar on ar.id=rr.admission_receipt_id
  join public.ticket_events ev on ev.id=rr.ticket_event_id
  join public.roboticket_clubs cl on cl.club_slug=rr.club_slug
  left join public.snapshots ss on ss.id=p_snapshot_id and ss.ticket_event_id=rr.ticket_event_id
  where rr.ticket_event_id=p_event_id;
  completed:=clock_timestamp();
  b:=private.rolling72_mvp_research_v1_binding(a,e,c);
  raw:=jsonb_build_object('lane_id',l.lane_id,'source_family','roboticket/roboticket','unit','available_total_seats',
   'admission',a,'binding',b,'snapshot',s,'sector_price_area_rows',pa,'sector_inventory_rows',inv);
  header_hash:=case when s is null then null else private.rolling72_mvp_research_v1_hash(s) end;
  select * into old from private.rolling72_mvp_research_v1_seals
   where ticket_event_id=p_event_id and snapshot_id=p_snapshot_id;
  begin
   if s is not null then captured:=(s->>'captured_at')::timestamptz; end if;
   if a is null or e is null or c is null then st:='INVALID_SOURCE'; reason:='MISSING_ADMISSION_OR_EVENT';
   elsif a is not null and (private.rolling72_mvp_research_v1_hash(a)<>r.admission_sha256 or b is distinct from r.binding)
    then st:='INVALID_SOURCE'; reason:='ADMISSION_BINDING_CHANGED';
   elsif r.kickoff_at<=completed then st:='OUTSIDE_KICKOFF'; reason:='KICKOFF_REACHED';
   elsif s is null and p_snapshot_id is null and had_source
    then st:='NO_NEW_SOURCE'; reason:='NO_POST_ACTIVATION_SOURCE';
   elsif s is null then st:='MISSING_SOURCE'; reason:='MISSING_SOURCE';
   elsif not coalesce(committed,false) then st:='INVALID_SOURCE'; reason:='UNCOMMITTED_SOURCE';
   elsif captured is null or captured>completed or (a->>'known_at')::timestamptz>started
    then st:='INVALID_SOURCE'; reason:='SOURCE_CLOCK';
   elsif old.id is not null then
    if private.rolling72_mvp_research_v1_hash(raw)=old.source_content_sha256 then
     st:='NO_NEW_SOURCE'; reason:=null;
    else st:='INVALID_SOURCE'; reason:='SOURCE_ROW_MUTATED'; end if;
   elsif captured<l.activated_at then st:='INVALID_SOURCE'; reason:='PRE_ACTIVATION_SOURCE';
   elsif completed-captured>interval '1 hour' then st:='SKIPPED_STALE'; reason:='SOURCE_STALE';
   elsif r.kickoff_at<=completed then st:='OUTSIDE_KICKOFF'; reason:='KICKOFF_REACHED';
   elsif s->>'source' is distinct from 'roboticket'
    or s->>'event_id' is distinct from r.external_event_id
    or (s->>'ticket_event_id')::bigint is distinct from r.ticket_event_id
    or (s->>'event_kickoff_at_capture')::timestamptz is distinct from r.kickoff_at
    or (s->>'event_match_date_at_capture')::date is distinct from (r.binding->>'match_date')::date
    or (s ? 'unit' and s->>'unit' is distinct from 'available_total_seats')
    then st:='INVALID_SOURCE'; reason:='SNAPSHOT_IDENTITY';
   elsif jsonb_array_length(pa)=0 or jsonb_array_length(inv)=0 then st:='INVALID_SOURCE'; reason:='MISSING_CHILD_ROWS';
   elsif coalesce(s->>'available_total','') !~ '^[0-9]+$' or coalesce(s->>'sector_count','') !~ '^[1-9][0-9]*$'
    then st:='INVALID_SOURCE'; reason:='INVALID_SNAPSHOT_COUNTS';
   else
    total:=(s->>'available_total')::bigint;
    select coalesce(sum(case when coalesce(x->>'available','') ~ '^[0-9]+$' then (x->>'available')::bigint else 0 end),0),
     count(distinct x->>'sector') into pa_total,n_sectors from jsonb_array_elements(pa) x;
    select coalesce(sum(case when coalesce(x->>'available','') ~ '^[0-9]+$' then (x->>'available')::bigint else 0 end),0)
     into inv_total from jsonb_array_elements(inv) x;
    if exists(select 1 from jsonb_array_elements(pa) x where coalesce(x->>'sector','')=''
      or coalesce(x->>'sector_source_id','') !~ '^[0-9]+$' or coalesce(x->>'price_area_id','') !~ '^[0-9]+$'
      or coalesce(x->>'available','') !~ '^[0-9]+$' or x->>'source' is distinct from 'roboticket'
      or (x->>'snapshot_id')::bigint is distinct from p_snapshot_id
      or (x->>'ticket_event_id')::bigint is distinct from p_event_id
      or (x->>'captured_at')::timestamptz is distinct from captured)
     or exists(select 1 from jsonb_array_elements(inv) x where coalesce(x->>'sector','')=''
      or coalesce(x->>'available','') !~ '^[0-9]+$'
      or (x->>'snapshot_id')::bigint is distinct from p_snapshot_id
      or (x->>'event_id' is not null and x->>'event_id' is distinct from r.external_event_id))
     or exists(select 1 from jsonb_array_elements(pa) x group by x->>'sector_source_id',x->>'price_area_id' having count(*)>1)
     or exists(select 1 from jsonb_array_elements(pa) x group by x->>'sector_source_id' having count(distinct x->>'sector')<>1)
     or exists(select 1 from jsonb_array_elements(pa) x group by x->>'sector' having count(distinct x->>'sector_source_id')<>1)
     or exists(select 1 from jsonb_array_elements(inv) x group by x->>'sector' having count(*)>1)
     then st:='INVALID_SOURCE'; reason:='INVALID_CHILD_COUNTS_OR_MAPPING';
    elsif total<>pa_total or total<>inv_total or n_sectors<>(s->>'sector_count')::integer
     or n_sectors<>jsonb_array_length(inv) or exists(
      select 1 from (select x->>'sector' sector,sum((x->>'available')::bigint) available from jsonb_array_elements(pa) x group by 1) a
      full join (select x->>'sector' sector,(x->>'available')::bigint available from jsonb_array_elements(inv) x) i using(sector)
      where a.available is distinct from i.available)
     then st:='INVALID_SOURCE'; reason:='INCOMPLETE_CHILD_ROWS';
    end if;
   end if;
   -- Partial-child retries may complete, but an already observed header cannot change.
   select at.snapshot_sha256 into prior_header from private.rolling72_mvp_research_v1_attempts at
    where at.ticket_event_id=p_event_id and at.snapshot_id=p_snapshot_id and at.snapshot_sha256 is not null
    order by at.id limit 1;
   if prior_header is not null and prior_header is distinct from header_hash then
    st:='INVALID_SOURCE'; reason:='SOURCE_ROW_MUTATED';
   end if;
   if st='READY' then
    select * into prior from private.rolling72_mvp_research_v1_seals
     where ticket_event_id=p_event_id order by captured_at desc,snapshot_id desc limit 1;
    if prior.id is not null and (captured,p_snapshot_id)<=(prior.captured_at,prior.snapshot_id) then
     st:='INVALID_SOURCE'; reason:='NON_ADVANCING_CAPTURE';
    end if;
   end if;
  exception when data_exception then st:='INVALID_SOURCE'; reason:='INVALID_SOURCE_DATA';
  end;
 end if;
 content_hash:=private.rolling72_mvp_research_v1_hash(raw);
 -- Stamp knowledge only after complete reads, validation and stable content digest.
 known:=clock_timestamp();
 if known>=l.scoring_until then st:='EXPIRED'; reason:='CAPTURE_EXPIRED'; end if;
 if st='READY' and r.kickoff_at<=known then st:='OUTSIDE_KICKOFF'; reason:='KICKOFF_REACHED'; end if;
 phase:=case when known<l.issue_until then 'ISSUE_WINDOW' else 'LABEL_ONLY' end;
 aid:=nextval(pg_get_serial_sequence('private.rolling72_mvp_research_v1_attempts','id')::regclass);
 attempt_payload:=jsonb_build_object('attempt_id',aid,'run_id',p_run,'lane_id',l.lane_id,
  'ticket_event_id',p_event_id,'snapshot_id',p_snapshot_id,'source_content_sha256',content_hash,
  'read_started_at',started,'read_completed_at',completed,'known_at',known,'status',st,'reason',reason);
 attempt_hash:=private.rolling72_mvp_research_v1_hash(attempt_payload);
 insert into private.rolling72_mvp_research_v1_attempts(
  id,run_id,ticket_event_id,snapshot_id,read_started_at,read_completed_at,known_at,captured_at,status,reason,
  source_content_sha256,snapshot_sha256,attempt_binding_sha256,raw_source,binding_payload)
 overriding system value values(aid,p_run,p_event_id,p_snapshot_id,started,completed,known,captured,st,reason,
  content_hash,header_hash,attempt_hash,raw,attempt_payload);
 if st='READY' then
  if prior.id is not null then
   prior_status:='READY_PRIOR'; elapsed:=extract(epoch from captured-prior.captured_at);
   with curr as(select x->>'sector_source_id' key,sum((x->>'available')::bigint)::bigint n
      from jsonb_array_elements(pa) x group by 1),
    prev as(select x->>'sector_source_id' key,sum((x->>'available')::bigint)::bigint n
      from jsonb_array_elements(prior.source_payload->'sector_price_area_rows') x group by 1)
   select coalesce(sum(c.n-p.n) filter(where c.key is not null and p.key is not null),0)::bigint,
    coalesce(sum(c.n) filter(where p.key is null),0)::bigint,
    coalesce(sum(p.n) filter(where c.key is null),0)::bigint,
    count(*) filter(where p.key is null)::integer,count(*) filter(where c.key is null)::integer
    into common_delta,added,removed,n_added,n_removed from curr c full join prev p using(key);
   with curr as(select distinct x->>'sector_source_id' sk,x->>'price_area_id' ak from jsonb_array_elements(pa) x),
    prev as(select distinct x->>'sector_source_id' sk,x->>'price_area_id' ak
     from jsonb_array_elements(prior.source_payload->'sector_price_area_rows') x)
   select count(*)::integer into n_memberships from curr c full join prev p using(sk,ak) where c.sk is null or p.sk is null;
   select coalesce(jsonb_agg(z.snapshot_id order by z.snapshot_id),'[]'::jsonb),count(*)::integer into gap_ids,gaps
   from(select distinct at.snapshot_id from private.rolling72_mvp_research_v1_attempts at
    where at.ticket_event_id=p_event_id and (at.captured_at,at.snapshot_id)>(prior.captured_at,prior.snapshot_id)
     and (at.captured_at,at.snapshot_id)<(captured,p_snapshot_id)
     and at.status in('INVALID_SOURCE','SKIPPED_STALE','MISSING_SOURCE')
     and not exists(select 1 from private.rolling72_mvp_research_v1_seals ss where ss.snapshot_id=at.snapshot_id)
    union select (x->>'snapshot_id')::bigint from jsonb_array_elements(intermediate) x) z;
   transition_status:=case when gaps>0 then 'GAPPED' else 'COMPLETE' end;
  end if;
  transition:=jsonb_build_object('prior_seal_id',prior.id,'prior_status',prior_status,'transition_status',transition_status,
   'prior_source_content_sha256',prior.source_content_sha256,'elapsed_capture_seconds',elapsed,
   'total_delta',case when prior.id is null then null else total-prior.available_total end,
   'common_sector_delta',common_delta,'added_available',added,'removed_available',removed,
   'added_sector_count',n_added,'removed_sector_count',n_removed,'price_area_membership_change_count',n_memberships,
   'gap_count',gaps,'gap_snapshot_ids',gap_ids,'unsealed_intermediate_sources',intermediate,
   'transition_known_at',clock_timestamp(),'unobserved_continuity','UNKNOWN',
   'measurement_order_status',case when elapsed=0 then 'TIED_CAPTURE_TIME' when elapsed>0 then 'ORDERED_CAPTURE_TIME' else 'NO_PRIOR' end,
   'rate_status',case when elapsed=0 then 'UNAVAILABLE_ZERO_ELAPSED' else 'NOT_COMPUTED' end);
  insert into private.rolling72_mvp_research_v1_seals(
   ticket_event_id,snapshot_id,attempt_id,captured_at,read_started_at,read_completed_at,known_at,available_total,sector_count,
   source_content_sha256,snapshot_sha256,source_payload,phase,prior_seal_id,prior_status,transition_status,
   elapsed_capture_seconds,total_delta,common_sector_delta,added_available,removed_available,added_sector_count,
   removed_sector_count,price_area_membership_change_count,gap_count,transition)
  values(p_event_id,p_snapshot_id,aid,captured,started,completed,known,total,n_sectors,content_hash,header_hash,raw,phase,
   prior.id,prior_status,transition_status,elapsed,case when prior.id is null then null else total-prior.available_total end,
   common_delta,added,removed,n_added,n_removed,n_memberships,gaps,transition) returning id into sid;
  if phase='ISSUE_WINDOW' then
   foreach h in array array[24,48,72] loop
    insert into private.rolling72_mvp_research_v1_candidates(
     seal_id,ticket_event_id,horizon_hours,observation_known_at,provisional_target_at,status)
    values(sid,p_event_id,h,known,known+make_interval(hours=>h),
     case when known+make_interval(hours=>h)<r.kickoff_at then 'SOURCE_ELIGIBLE' else 'OUTSIDE_KICKOFF' end);
   end loop;
  end if;
 elsif st='NO_NEW_SOURCE' then sid:=old.id;
 end if;
 if sid is not null then
  select coalesce(jsonb_agg(id order by horizon_hours),'[]'::jsonb) into candidate_ids
   from private.rolling72_mvp_research_v1_candidates where seal_id=sid;
 end if;
 return jsonb_build_object('ticket_event_id',p_event_id,'snapshot_id',p_snapshot_id,'attempt_id',aid,
  'status',st,'reason',reason,'seal_id',sid,'candidate_ids',candidate_ids);
end $$;

create function private.rolling72_mvp_research_v1_binding(a jsonb,e jsonb,c jsonb)
returns jsonb language sql immutable set search_path='' as $$
 select jsonb_build_object(
 'ticket_event_id',e->'id','provider',e->'provider','external_event_id',e->'external_event_id',
 'club_slug',e->'club_slug','source_domain',e->'source_domain','home_team',e->'home_team',
 'away_team',e->'away_team','competition',e->'competition','match_date',e->'match_date',
 'kickoff_at',e->'kickoff_at','source_url',e->'source_url',
 'mapping_source',e->'mapping_source','mapping_confidence',e->'mapping_confidence',
 'canonical_home_club_key',a#>'{evidence_payload,plan_evidence,canonical_home_club_key}',
 'canonical_away_club_key',a#>'{evidence_payload,plan_evidence,canonical_away_club_key}',
 'source_event_id',a#>'{evidence_payload,plan_evidence,source_event_id}',
 'club_config',jsonb_build_object('club_slug',c->'club_slug','club_name',c->'club_name',
   'source_domain',c->'source_domain','base_url',c->'base_url','active',c->'active'))
$$;

create function public.activate_rolling72_mvp_research_v1(p_manifest_text text,p_manifest_sha256 text)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare j jsonb; l private.rolling72_mvp_research_v1_lane%rowtype; t timestamptz;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_READ_COMMITTED_REQUIRED'; end if;
 if p_manifest_text is null or length(p_manifest_text)>32768 or p_manifest_sha256 !~ '^[0-9a-f]{64}$'
  or p_manifest_sha256 is distinct from encode(sha256(convert_to(p_manifest_text,'UTF8')),'hex') then raise exception 'MVP_MANIFEST_HASH'; end if;
 j:=p_manifest_text::jsonb;
 if jsonb_typeof(j) is distinct from 'object' or (select count(*) from jsonb_object_keys(j))<>10
  or j->>'lane_id' is distinct from 'rolling72-mvp-research-v1'
  or j->>'version' is distinct from 'rolling72-mvp-research-v1'
  or j->>'source_family' is distinct from 'roboticket/roboticket'
  or j->>'unit' is distinct from 'available_total_seats'
  or j->'max_source_age_seconds' is distinct from '3600'::jsonb
  or j->'max_batch' is distinct from '25'::jsonb
  or jsonb_typeof(j->'max_fixtures') is distinct from 'number'
  or coalesce(j->>'max_fixtures','') !~ '^[1-9][0-9]*$'
  or (j->>'max_fixtures')::numeric not between 1 and 1000
  or coalesce(j->>'sql_sha256','') !~ '^[0-9a-f]{64}$'
  then raise exception 'MVP_MANIFEST_CONTRACT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-research-v1:runtime',20261123));
 select * into l from private.rolling72_mvp_research_v1_lane;
 if found then
  if l.manifest_text=p_manifest_text and l.manifest_sha256=p_manifest_sha256 then
   return jsonb_build_object('activated',false,'idempotent',true,'activated_at',l.activated_at);
  end if;
  raise exception 'MVP_MANIFEST_ALREADY_FROZEN';
 end if;
 t:=clock_timestamp();
 if (j->>'issue_until')::timestamptz<=t
  or not isfinite((j->>'issue_until')::timestamptz) or not isfinite((j->>'scoring_until')::timestamptz)
  or (j->>'scoring_until')::timestamptz<(j->>'issue_until')::timestamptz+interval '78 hours'
  or (j->>'scoring_until')::timestamptz>(j->>'issue_until')::timestamptz+interval '7 days'
  or j->>'issue_until' is null or j->>'scoring_until' is null then raise exception 'MVP_MANIFEST_DEADLINE'; end if;
 insert into private.rolling72_mvp_research_v1_lane values(
  'rolling72-mvp-research-v1',p_manifest_text,p_manifest_sha256,j->>'sql_sha256',t,
  (j->>'issue_until')::timestamptz,(j->>'scoring_until')::timestamptz,(j->>'max_fixtures')::integer);
 return jsonb_build_object('activated',true,'idempotent',false,'activated_at',t);
end $$;

create function public.register_rolling72_mvp_research_v1(p_admission_receipt_ids bigint[])
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 l private.rolling72_mvp_research_v1_lane%rowtype; old private.rolling72_mvp_research_v1_registry%rowtype;
 rid bigint; k record; a jsonb; e jsonb; c jsonb; p jsonb; rt jsonb; b jsonb;
 t timestamptz; started timestamptz; snap pg_snapshot; committed boolean; ah text; reason text; st text;
 rows jsonb:='[]'::jsonb; n integer;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_READ_COMMITTED_REQUIRED'; end if;
 if p_admission_receipt_ids is null or cardinality(p_admission_receipt_ids) not between 1 and 20
  or exists(select 1 from unnest(p_admission_receipt_ids) x where x is null or x<=0)
  or (select count(distinct x) from unnest(p_admission_receipt_ids) x)<>cardinality(p_admission_receipt_ids)
  then raise exception 'MVP_REGISTRATION_IDS'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-research-v1:runtime',20261123));
 snap:=pg_current_snapshot(); started:=clock_timestamp();
 select * into l from private.rolling72_mvp_research_v1_lane;
 if not found then raise exception 'MVP_NOT_ACTIVATED'; end if;
 -- Same lexical identity order/key/seed as the admission writer; no frozen lane lock.
 for k in select r.club_slug,r.external_event_id from private.roboticket_admission_receipts_v2 r
   where r.id=any(p_admission_receipt_ids) order by r.club_slug||':'||r.external_event_id loop
  perform pg_advisory_xact_lock(hashtextextended(k.club_slug||':'||k.external_event_id,20261115));
 end loop;
 foreach rid in array (select array_agg(x order by x) from unnest(p_admission_receipt_ids) x) loop
  a:=null; e:=null; c:=null; reason:=null; st:='REJECTED'; b:=null;
  begin
   select to_jsonb(ar),to_jsonb(ev),to_jsonb(cl),
    private.rolling72_mvp_research_v1_committed(ar.xmin,snap)
     and private.rolling72_mvp_research_v1_committed(ev.xmin,snap)
     and private.rolling72_mvp_research_v1_committed(cl.xmin,snap)
   into a,e,c,committed
   from private.roboticket_admission_receipts_v2 ar
   join public.ticket_events ev on ev.id=ar.ticket_event_id
   join public.roboticket_clubs cl on cl.club_slug=ar.club_slug where ar.id=rid;
   t:=clock_timestamp();
   p:=a#>'{evidence_payload,plan_evidence}'; rt:=a#>'{evidence_payload,runtime_recheck}';
   if t>=l.issue_until then reason:='REGISTRATION_EXPIRED';
   elsif a is null then reason:='MISSING_ADMISSION';
   elsif not coalesce(committed,false) then reason:='UNCOMMITTED_ADMISSION';
   elsif (a->>'known_at')::timestamptz>started or (a->>'source_retrieved_at_bound')::timestamptz>(a->>'known_at')::timestamptz
    then reason:='ADMISSION_CLOCK';
   elsif e->>'provider' is distinct from 'roboticket' or e->>'external_event_id' is distinct from a->>'external_event_id'
    or e->>'mapping_source' is distinct from 'roboticket-explicit-admission-v2'
    or e->>'mapping_confidence' is distinct from 'verified'
    or e->>'club_slug' is distinct from a->>'club_slug' or c->'active' is distinct from 'true'::jsonb
    or e->>'source_domain' is distinct from c->>'source_domain'
    or e->>'source_domain' is distinct from rt->>'ticket_source_domain'
    or e->>'home_team' is distinct from rt->>'home_team' or e->>'away_team' is distinct from rt->>'away_team'
    or e->>'competition' is distinct from 'Ekstraklasa' or e->>'source_url' is distinct from rt->>'ticket_page_url'
    or e->>'match_date' is distinct from p->>'civil_date'
    or (e->>'kickoff_at')::timestamptz is distinct from (p->>'kickoff_at')::timestamptz
    or p->>'club_slug' is distinct from a->>'club_slug' or p->>'roboticket_event_id' is distinct from a->>'external_event_id'
    then reason:='ADMISSION_IDENTITY_MISMATCH';
   elsif jsonb_typeof(p) is distinct from 'object' or jsonb_typeof(rt) is distinct from 'object'
    or p->>'status' is distinct from 'PREPARATION_REQUIRES_RUNTIME_RECHECK'
    or p->'admitted' is distinct from 'false'::jsonb or p->'historical_backfill' is distinct from 'false'::jsonb
    or p->'writes_performed' is distinct from 'false'::jsonb or p->'network_requests_performed' is distinct from 'false'::jsonb
    or p->>'collection_readiness' is distinct from 'NOT_ASSESSED'
    or coalesce(p->>'canonical_home_club_key','')='' or coalesce(p->>'canonical_away_club_key','')=''
    or coalesce(p->>'source_event_id','')=''
    or jsonb_typeof(a#>'{evidence_payload,plan_evidence_json}') is distinct from 'string'
    or (a#>>'{evidence_payload,plan_evidence_json}')::jsonb is distinct from p
    or encode(sha256(convert_to(a#>>'{evidence_payload,plan_evidence_json}','UTF8')),'hex') is distinct from a->>'plan_sha256'
    or a#>>'{evidence_payload,plan_sha256}' is distinct from a->>'plan_sha256'
    or p->>'original_html_sha256' is distinct from a->>'original_html_sha256'
    or p->>'provider_body_sha256' is distinct from a->>'provider_body_sha256'
    or p->>'acquisition_index_sha256' is distinct from a->>'acquisition_index_sha256'
    or rt->>'ticket_html_sha256' is distinct from a->>'runtime_html_sha256'
    or rt->>'provider_body_sha256' is distinct from a->>'runtime_provider_sha256'
    or a->>'source_reference' is distinct from 'acquisition-index-sha256:'||(a->>'acquisition_index_sha256')
    then reason:='ADMISSION_EVIDENCE_MISMATCH';
   elsif (e->>'kickoff_at')::timestamptz<=t then reason:='KICKOFF_NOT_FUTURE';
   end if;
   if reason is null then
    b:=private.rolling72_mvp_research_v1_binding(a,e,c); ah:=private.rolling72_mvp_research_v1_hash(a);
    select * into old from private.rolling72_mvp_research_v1_registry where ticket_event_id=(e->>'id')::bigint;
    if found then
     if old.admission_receipt_id=rid and old.admission_sha256=ah
      and old.binding=b then st:='IDEMPOTENT'; else reason:='REGISTRY_BINDING_CONFLICT'; end if;
    elsif (select count(*) from private.rolling72_mvp_research_v1_registry)>=l.max_fixtures then reason:='REGISTRY_CAP';
    else
     t:=clock_timestamp();
     if t>=l.issue_until or (e->>'kickoff_at')::timestamptz<=t then reason:='REGISTRATION_EXPIRED';
     else
      insert into private.rolling72_mvp_research_v1_registry values(
       (e->>'id')::bigint,rid,l.lane_id,a->>'club_slug',a->>'external_event_id',(e->>'kickoff_at')::timestamptz,
       (a->>'known_at')::timestamptz,t,ah,private.rolling72_mvp_research_v1_hash(b),b);
      st:='REGISTERED';
     end if;
    end if;
   end if;
  exception when data_exception then reason:='INVALID_ADMISSION_DATA';
  end;
  insert into private.rolling72_mvp_research_v1_registration_attempts(admission_receipt_id,attempted_at,ticket_event_id,status,reason)
  values(rid,clock_timestamp(),(e->>'id')::bigint,st,reason);
  rows:=rows||jsonb_build_array(jsonb_build_object('admission_receipt_id',rid,'ticket_event_id',e->'id','status',st,'reason',reason));
 end loop;
 return jsonb_build_object('lane_id',l.lane_id,'results',rows);
end $$;

create function public.capture_rolling72_mvp_research_v1(p_limit integer default 25)
returns jsonb language plpgsql volatile security definer set search_path='' set timezone='UTC' as $$
declare
 l private.rolling72_mvp_research_v1_lane%rowtype; started timestamptz:=clock_timestamp();
 entry_snapshot pg_snapshot; run uuid:=gen_random_uuid(); queue jsonb; item jsonb; result jsonb;
 results jsonb:='[]'::jsonb; k record; checked integer:=0; registered integer; n_ready integer; n_first integer;
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'MVP_READ_COMMITTED_REQUIRED'; end if;
 if p_limit is null or p_limit not between 1 and 25 then raise exception 'MVP_CAPTURE_LIMIT'; end if;
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-research-v1:runtime',20261123));
 entry_snapshot:=pg_current_snapshot();
 select * into l from private.rolling72_mvp_research_v1_lane;
 if not found then raise exception 'MVP_NOT_ACTIVATED'; end if;
 select count(*) into registered from private.rolling72_mvp_research_v1_registry;
 with pending as materialized(
  select r.ticket_event_id,s.id snapshot_id,s.captured_at order_at,0 priority
  from private.rolling72_mvp_research_v1_registry r join public.snapshots s on s.ticket_event_id=r.ticket_event_id
  where clock_timestamp()<l.scoring_until and s.captured_at>=l.activated_at
   and not exists(select 1 from private.rolling72_mvp_research_v1_seals z where z.ticket_event_id=r.ticket_event_id and z.snapshot_id=s.id)
   and not exists(select 1 from private.rolling72_mvp_research_v1_attempts a
    where a.ticket_event_id=r.ticket_event_id and a.snapshot_id=s.id
     and a.reason is not null and a.reason not in('MISSING_CHILD_ROWS','INCOMPLETE_CHILD_ROWS','UNCOMMITTED_SOURCE'))
 ), fallback as(
  select r.ticket_event_id,
   (select z.snapshot_id from private.rolling72_mvp_research_v1_seals z where z.ticket_event_id=r.ticket_event_id
    order by z.captured_at desc,z.snapshot_id desc limit 1) snapshot_id,
   coalesce((select max(a.known_at) from private.rolling72_mvp_research_v1_attempts a
    where a.ticket_event_id=r.ticket_event_id),'-infinity'::timestamptz) order_at,1 priority
  from private.rolling72_mvp_research_v1_registry r
  where not exists(select 1 from pending p where p.ticket_event_id=r.ticket_event_id)
 ), limited as(
  select * from(select * from pending union all select * from fallback) x
  order by priority,order_at,snapshot_id nulls last,ticket_event_id limit p_limit
 )
 select coalesce(jsonb_agg(to_jsonb(x) order by priority,order_at,snapshot_id nulls last,ticket_event_id),'[]'::jsonb)
  into queue from limited x;
 -- Acquire multi-fixture locks in admission's lexical order before reading.
 for k in select r.club_slug,r.external_event_id from private.rolling72_mvp_research_v1_registry r
  where r.ticket_event_id in(select (v->>'ticket_event_id')::bigint from jsonb_array_elements(queue) v)
  order by r.club_slug||':'||r.external_event_id loop
  perform pg_advisory_xact_lock(hashtextextended(k.club_slug||':'||k.external_event_id,20261115));
 end loop;
 for item in select value from jsonb_array_elements(queue) loop
  -- A corrupt fixture may fail without aborting already-valid fixtures.
  begin
   result:=private.rolling72_mvp_research_v1_capture_one(
    (item->>'ticket_event_id')::bigint,(item->>'snapshot_id')::bigint,run,entry_snapshot);
  exception when others then
   -- Keep the fault visible. No source body or throwable message is returned.
   declare aid bigint; t timestamptz:=clock_timestamp(); payload jsonb; sh text;
   begin
    aid:=nextval(pg_get_serial_sequence('private.rolling72_mvp_research_v1_attempts','id')::regclass);
    sh:=private.rolling72_mvp_research_v1_hash('{}'::jsonb);
    payload:=jsonb_build_object('attempt_id',aid,'run_id',run,'lane_id',l.lane_id,
     'ticket_event_id',item->'ticket_event_id','snapshot_id',item->'snapshot_id',
     'source_content_sha256',sh,'read_started_at',t,'read_completed_at',t,'known_at',t,
     'status','INTERNAL_ERROR','reason','CAPTURE_ERROR_'||sqlstate);
    insert into private.rolling72_mvp_research_v1_attempts(
     id,run_id,ticket_event_id,snapshot_id,read_started_at,read_completed_at,known_at,status,reason,
     source_content_sha256,attempt_binding_sha256,raw_source,binding_payload)
    overriding system value values(aid,run,(item->>'ticket_event_id')::bigint,(item->>'snapshot_id')::bigint,
     t,t,t,'INTERNAL_ERROR','CAPTURE_ERROR_'||sqlstate,sh,private.rolling72_mvp_research_v1_hash(payload),'{}'::jsonb,payload);
    result:=jsonb_build_object('ticket_event_id',item->'ticket_event_id','snapshot_id',item->'snapshot_id',
     'attempt_id',aid,'status','INTERNAL_ERROR','reason','CAPTURE_ERROR_'||sqlstate,'seal_id',null,'candidate_ids','[]'::jsonb);
   end;
  end;
  results:=results||jsonb_build_array(result); checked:=checked+1;
 end loop;
 select count(*) filter(where value->>'status'='READY') into n_ready from jsonb_array_elements(results);
 select count(*) into n_first from private.rolling72_mvp_research_v1_seals s
  join private.rolling72_mvp_research_v1_attempts a on a.id=s.attempt_id where a.run_id=run and s.prior_status='NO_PRIOR';
 insert into private.rolling72_mvp_research_v1_runs values(run,started,clock_timestamp(),
  case when clock_timestamp()>=l.scoring_until then 'EXPIRED' when checked=0 then 'EMPTY' else 'COMPLETED' end,checked,registered);
 return jsonb_build_object('schema_version','rolling72-mvp-source-runtime-v1','lane_id',l.lane_id,
  'run_id',run,'registered_fixtures',registered,'attempted_snapshots',checked,'new_ready_receipts',n_ready,
  'first_point_receipts',n_first,'results',results,'forecasts_created',0,'forecast_coverage',null,
  'scope','SOURCE_HORIZON_CANDIDATES_ONLY');
end $$;

-- Operator-only counts, intentionally separate from the per-poll write path.
create function public.get_rolling72_mvp_research_v1_status()
returns jsonb language sql stable security definer set search_path='' set timezone='UTC' as $$
 select jsonb_build_object('lane_id','rolling72-mvp-research-v1',
  'registered_fixtures',(select count(*) from private.rolling72_mvp_research_v1_registry),
  'registered_clubs',(select count(distinct club_slug) from private.rolling72_mvp_research_v1_registry),
  'collection_calls',(select count(*) from private.rolling72_mvp_research_v1_runs),
  'collection_attempts',(select count(*) from private.rolling72_mvp_research_v1_attempts),
  'valid_receipts',(select count(*) from private.rolling72_mvp_research_v1_seals),
  'first_points',(select count(*) from private.rolling72_mvp_research_v1_seals where prior_status='NO_PRIOR'),
  'source_horizon_candidates',(select count(*) from private.rolling72_mvp_research_v1_candidates),
  'source_time_eligible_candidates',(select count(*) from private.rolling72_mvp_research_v1_candidates where status='SOURCE_ELIGIBLE'),
  'outside_kickoff_candidates',(select count(*) from private.rolling72_mvp_research_v1_candidates where status='OUTSIDE_KICKOFF'),
  'attempt_status_counts',(select coalesce(jsonb_object_agg(status,n),'{}'::jsonb)
   from(select status,count(*) n from private.rolling72_mvp_research_v1_attempts group by status) q),
  'forecasts_created',0,'forecast_coverage',null,'production_live_adjustment',0)
$$;

do $$
declare n text; f record;
begin
 foreach n in array array['lane','registry','registration_attempts','runs','attempts','seals','candidates'] loop
  execute format('alter table private.%I enable row level security','rolling72_mvp_research_v1_'||n);
  execute format('revoke all on table private.%I from public,anon,authenticated,service_role','rolling72_mvp_research_v1_'||n);
  execute format('create trigger immutable_rows before update or delete on private.%I for each row execute function private.rolling72_mvp_research_v1_immutable()','rolling72_mvp_research_v1_'||n);
  execute format('create trigger immutable_truncate before truncate on private.%I for each statement execute function private.rolling72_mvp_research_v1_immutable()','rolling72_mvp_research_v1_'||n);
 end loop;
 for f in select p.oid::regprocedure sig from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
  where ns.nspname='private' and left(p.proname,length('rolling72_mvp_research_v1_'))='rolling72_mvp_research_v1_' loop
  execute format('revoke all on function %s from public,anon,authenticated,service_role',f.sig);
 end loop;
end $$;
revoke all on function public.activate_rolling72_mvp_research_v1(text,text),
 public.register_rolling72_mvp_research_v1(bigint[]),public.capture_rolling72_mvp_research_v1(integer),
 public.get_rolling72_mvp_research_v1_status() from public,anon,authenticated;
grant execute on function public.activate_rolling72_mvp_research_v1(text,text),
 public.register_rolling72_mvp_research_v1(bigint[]),public.capture_rolling72_mvp_research_v1(integer),
 public.get_rolling72_mvp_research_v1_status() to service_role;
