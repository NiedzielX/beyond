-- Roboticket forward-only admission v2.
-- Local proposal only; do not apply to any hosted database without separate review.
-- It writes only explicit source receipts + ticket-event tracking. It never
-- imports legacy candidate-buffer observations into public snapshots.

create table if not exists private.roboticket_admission_receipts_v2 (
  id bigint generated always as identity primary key,
  club_slug text not null,
  external_event_id text not null,
  ticket_event_id bigint not null references public.ticket_events(id),
  plan_sha256 text not null,
  original_html_sha256 text not null,
  provider_body_sha256 text not null,
  runtime_html_sha256 text not null,
  runtime_provider_sha256 text not null,
  acquisition_index_sha256 text not null,
  source_reference text not null,
  source_retrieved_at_bound timestamptz not null,
  known_at timestamptz not null,
  evidence_payload jsonb not null,
  created_at timestamptz not null default clock_timestamp(),
  constraint roboticket_admission_receipt_identity_v2 unique(club_slug,external_event_id),
  constraint roboticket_admission_receipt_hashes_v2 check (
    plan_sha256 ~ '^[0-9a-f]{64}$' and
    original_html_sha256 ~ '^[0-9a-f]{64}$' and
    provider_body_sha256 ~ '^[0-9a-f]{64}$' and
    runtime_html_sha256 ~ '^[0-9a-f]{64}$' and
    runtime_provider_sha256 ~ '^[0-9a-f]{64}$' and
    acquisition_index_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint roboticket_admission_receipt_payload_object_v2 check(jsonb_typeof(evidence_payload)='object')
);

create index if not exists roboticket_admission_receipts_event_v2_idx
  on private.roboticket_admission_receipts_v2(ticket_event_id);

alter table private.roboticket_admission_receipts_v2 enable row level security;
revoke all on private.roboticket_admission_receipts_v2 from public, anon, authenticated, service_role;

create or replace function private.reject_roboticket_admission_receipt_mutation_v2()
returns trigger
language plpgsql
security definer
set search_path=''
as $function$
begin
  raise exception 'ROBOTICKET_ADMISSION_RECEIPTS_IMMUTABLE';
end;
$function$;

revoke all on function private.reject_roboticket_admission_receipt_mutation_v2() from public, anon, authenticated, service_role;
drop trigger if exists roboticket_admission_receipts_immutable_v2 on private.roboticket_admission_receipts_v2;
create trigger roboticket_admission_receipts_immutable_v2
before update or delete on private.roboticket_admission_receipts_v2
for each row execute function private.reject_roboticket_admission_receipt_mutation_v2();

-- Shared lock helper. The old upsert remains unchanged; this trigger serializes
-- its per-identity writes against the explicit v2 admission RPC.
create or replace function private.lock_roboticket_admission_identity_v2(p_club_slug text,p_external_event_id text)
returns void
language sql
volatile
security definer
set search_path=''
as $function$
  select pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_club_slug || ':' || p_external_event_id, 20261115)
  );
$function$;
revoke all on function private.lock_roboticket_admission_identity_v2(text,text) from public, anon, authenticated, service_role;

create or replace function private.guard_roboticket_verified_schedule_v2()
returns trigger
language plpgsql
volatile
security definer
set search_path=''
as $function$
declare
  v_old_key text;
  v_new_key text;
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise exception 'ROBOTICKET_ADMISSION_REQUIRES_READ_COMMITTED';
  end if;

  if tg_op = 'UPDATE' then
    v_old_key := old.club_slug || ':' || old.external_event_id;
  end if;
  v_new_key := new.club_slug || ':' || new.external_event_id;

  if tg_op = 'UPDATE' and v_old_key <> v_new_key then
    if v_old_key < v_new_key then
      perform private.lock_roboticket_admission_identity_v2(old.club_slug,old.external_event_id);
      perform private.lock_roboticket_admission_identity_v2(new.club_slug,new.external_event_id);
    else
      perform private.lock_roboticket_admission_identity_v2(new.club_slug,new.external_event_id);
      perform private.lock_roboticket_admission_identity_v2(old.club_slug,old.external_event_id);
    end if;
  else
    perform private.lock_roboticket_admission_identity_v2(new.club_slug,new.external_event_id);
  end if;

  if exists (
    select 1 from private.roboticket_admission_receipts_v2 r
    where (r.club_slug=new.club_slug and r.external_event_id=new.external_event_id)
       or (tg_op='UPDATE' and r.club_slug=old.club_slug and r.external_event_id=old.external_event_id)
  ) then
    raise exception 'ROBOTICKET_V1_SCHEDULE_BLOCKED_BY_V2_ADMISSION';
  end if;
  return new;
end;
$function$;
revoke all on function private.guard_roboticket_verified_schedule_v2() from public, anon, authenticated, service_role;
drop trigger if exists roboticket_verified_schedule_v2_admission_guard on private.roboticket_verified_schedule_v1;
create trigger roboticket_verified_schedule_v2_admission_guard
before insert or update on private.roboticket_verified_schedule_v1
for each row execute function private.guard_roboticket_verified_schedule_v2();

create or replace function public.admit_roboticket_explicit_fixtures_v2(p_request jsonb)
returns jsonb
language plpgsql
volatile
security definer
set search_path=''
as $function$
declare
  v_now timestamptz;
  v_item jsonb;
  v_plan jsonb;
  v_runtime jsonb;
  v_lock record;
  v_count integer;
  v_results jsonb := '[]'::jsonb;
  v_club text;
  v_event text;
  v_domain text;
  v_home text;
  v_away text;
  v_home_key text;
  v_away_key text;
  v_competition text;
  v_match_date date;
  v_kickoff timestamptz;
  v_ticket_url text;
  v_provider_event_id text;
  v_plan_sha text;
  v_html_sha text;
  v_provider_sha text;
  v_runtime_html_sha text;
  v_runtime_provider_sha text;
  v_index_sha text;
  v_source_reference text;
  v_source_bound timestamptz;
  v_runtime_at timestamptz;
  v_club_cfg record;
  v_existing private.roboticket_admission_receipts_v2%rowtype;
  v_ticket_event_id bigint;
  v_receipt_id bigint;
  v_inserted boolean;
  v_key text;
  v_lock_keys text[] := array[]::text[];
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise exception 'ROBOTICKET_ADMISSION_REQUIRES_READ_COMMITTED';
  end if;
  if p_request is null or jsonb_typeof(p_request) is distinct from 'object'
     or p_request->>'version' is distinct from 'roboticket-explicit-admission-request-v2'
     or jsonb_typeof(p_request->'fixtures') is distinct from 'array' then
    raise exception 'ROBOTICKET_ADMISSION_INVALID_REQUEST';
  end if;
  v_count := jsonb_array_length(p_request->'fixtures');
  if v_count < 1 or v_count > 20 then raise exception 'ROBOTICKET_ADMISSION_FIXTURE_COUNT'; end if;

  -- Lock all explicit fixture identities in sorted order before processing.
  for v_lock in
    select keys.club_slug,keys.external_event_id
    from (
      select distinct x->>'club_slug' as club_slug,x->>'roboticket_event_id' as external_event_id
      from jsonb_array_elements(p_request->'fixtures') x
    ) keys
    -- Match the exact ordering used by the legacy UPDATE trigger, including
    -- prefix-like slugs (e.g. club / club1), rather than sorting a tuple.
    order by keys.club_slug || ':' || keys.external_event_id
  loop
    if coalesce(v_lock.club_slug,'')='' or coalesce(v_lock.external_event_id,'')='' then
      raise exception 'ROBOTICKET_ADMISSION_IDENTITY_REQUIRED';
    end if;
    v_key := v_lock.club_slug || ':' || v_lock.external_event_id;
    if v_key = any(v_lock_keys) then raise exception 'ROBOTICKET_ADMISSION_DUPLICATE_IDENTITY'; end if;
    v_lock_keys := array_append(v_lock_keys,v_key);
    perform private.lock_roboticket_admission_identity_v2(v_lock.club_slug,v_lock.external_event_id);
  end loop;
  if cardinality(v_lock_keys) <> v_count then raise exception 'ROBOTICKET_ADMISSION_DUPLICATE_IDENTITY'; end if;

  for v_item in select value from jsonb_array_elements(p_request->'fixtures') loop
    v_now := clock_timestamp();
    v_plan := v_item->'plan_evidence';
    v_runtime := v_item->'runtime_recheck';
    if jsonb_typeof(v_plan) is distinct from 'object' or jsonb_typeof(v_runtime) is distinct from 'object' then
      raise exception 'ROBOTICKET_ADMISSION_EVIDENCE_REQUIRED';
    end if;
    if v_plan->>'status' is distinct from 'PREPARATION_REQUIRES_RUNTIME_RECHECK'
       or v_plan->'admitted' is distinct from 'false'::jsonb
       or v_plan->'historical_backfill' is distinct from 'false'::jsonb
       or v_plan->'writes_performed' is distinct from 'false'::jsonb
       or v_plan->'network_requests_performed' is distinct from 'false'::jsonb
       or v_plan->>'collection_readiness' is distinct from 'NOT_ASSESSED' then
      raise exception 'ROBOTICKET_ADMISSION_PREPARATION_PLAN_REQUIRED';
    end if;

    v_club := nullif(v_plan->>'club_slug','');
    v_event := nullif(v_plan->>'roboticket_event_id','');
    v_domain := lower(nullif(v_runtime->>'ticket_source_domain',''));
    v_home := nullif(v_runtime->>'home_team','');
    v_away := nullif(v_runtime->>'away_team','');
    v_home_key := nullif(v_plan->>'canonical_home_club_key','');
    v_away_key := nullif(v_plan->>'canonical_away_club_key','');
    v_competition := nullif(v_plan->>'competition','');
    v_match_date := nullif(v_plan->>'civil_date','')::date;
    v_kickoff := nullif(v_plan->>'kickoff_at','')::timestamptz;
    v_ticket_url := nullif(v_runtime->>'ticket_page_url','');
    v_provider_event_id := nullif(v_plan->>'source_event_id','');
    v_plan_sha := lower(nullif(v_item->>'plan_sha256',''));
    v_html_sha := lower(nullif(v_plan->>'original_html_sha256',''));
    v_provider_sha := lower(nullif(v_plan->>'provider_body_sha256',''));
    v_runtime_html_sha := lower(nullif(v_runtime->>'ticket_html_sha256',''));
    v_runtime_provider_sha := lower(nullif(v_runtime->>'provider_body_sha256',''));
    v_index_sha := lower(nullif(v_plan->>'acquisition_index_sha256',''));
    v_source_reference := nullif(v_plan->>'source_retrieved_at_bound','');
    v_source_bound := nullif(v_source_reference,'')::timestamptz;
    v_source_reference := 'acquisition-index-sha256:' || v_index_sha;
    v_runtime_at := nullif(v_runtime->>'retrieved_at','')::timestamptz;

    if v_item->>'club_slug' is distinct from v_club
       or v_item->>'roboticket_event_id' is distinct from v_event then
      raise exception 'ROBOTICKET_ADMISSION_LOCK_IDENTITY_MISMATCH';
    end if;
    if jsonb_typeof(v_item->'plan_evidence_json') is distinct from 'string'
       or (v_item->>'plan_evidence_json')::jsonb is distinct from v_plan
       or encode(sha256(convert_to(v_item->>'plan_evidence_json','UTF8')),'hex') is distinct from v_plan_sha then
      raise exception 'ROBOTICKET_ADMISSION_PLAN_BYTES_MISMATCH';
    end if;

    -- Exact immutable plan retries return their original result. They are not
    -- new admissions and do not acquire a new source/knowledge clock.
    select * into v_existing from private.roboticket_admission_receipts_v2 r
    where r.club_slug=v_club and r.external_event_id=v_event;
    if found then
      if v_existing.plan_sha256 is distinct from v_plan_sha
         or v_existing.evidence_payload->'plan_evidence' is distinct from v_plan then
        raise exception 'ROBOTICKET_ADMISSION_CONFLICTING_IMMUTABLE_RETRY';
      end if;
      v_results := v_results || jsonb_build_array(jsonb_build_object(
        'club_slug',v_club,'roboticket_event_id',v_event,
        'ticket_event_id',v_existing.ticket_event_id,'receipt_id',v_existing.id,
        'admitted',true,'tracking_created',false,'known_at',v_existing.known_at,
        'backfilled_snapshots',0,'model_activation',false,'live_adjustment',0
      ));
      continue;
    end if;

    if v_club is null or v_event is null or v_home is null or v_away is null
       or v_home_key is null or v_away_key is null or v_provider_event_id is null
       or v_ticket_url is null or v_domain is null or v_kickoff is null or v_match_date is null
       or v_competition is null or v_source_bound is null then
      raise exception 'ROBOTICKET_ADMISSION_IDENTITY_OR_TIME_REQUIRED';
    end if;
    if v_event !~ '^[0-9]+$' or v_provider_event_id !~ '^[0-9]+$'
       or v_home_key=v_away_key or v_competition <> 'Ekstraklasa'
       or v_plan->>'time_zone' is distinct from 'Europe/Warsaw'
       or (v_kickoff at time zone 'Europe/Warsaw')::date <> v_match_date then
      raise exception 'ROBOTICKET_ADMISSION_IDENTITY_OR_DATE_CONFLICT';
    end if;
    if v_kickoff <= v_now then raise exception 'ROBOTICKET_ADMISSION_KICKOFF_NOT_FUTURE'; end if;
    if v_source_bound > v_now or v_runtime_at is null or v_runtime_at > v_now
       or v_runtime_at < v_now - interval '10 minutes' then
      raise exception 'ROBOTICKET_ADMISSION_SOURCE_RECEIPT_NOT_CURRENT';
    end if;
    if coalesce(v_plan_sha,'') !~ '^[0-9a-f]{64}$' or coalesce(v_html_sha,'') !~ '^[0-9a-f]{64}$'
       or coalesce(v_provider_sha,'') !~ '^[0-9a-f]{64}$' or coalesce(v_runtime_html_sha,'') !~ '^[0-9a-f]{64}$'
       or coalesce(v_runtime_provider_sha,'') !~ '^[0-9a-f]{64}$' or coalesce(v_index_sha,'') !~ '^[0-9a-f]{64}$' then
      raise exception 'ROBOTICKET_ADMISSION_HASH_INVALID';
    end if;
    if v_runtime_html_sha is distinct from v_html_sha or v_runtime_provider_sha is distinct from v_provider_sha
       or v_home is distinct from v_plan->>'h1_home_team_text'
       or v_away is distinct from v_plan->>'h1_away_team_text'
       or v_domain is distinct from v_plan->>'ticket_source_domain'
       or v_ticket_url is distinct from v_plan->>'ticket_source_url'
       or v_runtime->>'provider_source_domain' is distinct from 'www.thesportsdb.com'
       or v_runtime->>'provider_source_type' is distinct from 'thesportsdb_league_schedule'
       or v_runtime->>'provider_competition' is distinct from 'Ekstraklasa'
       or v_runtime->>'provider_event_id' is distinct from v_provider_event_id
       or (v_runtime->>'provider_match_date')::date is distinct from v_match_date
       or v_runtime->>'provider_home_club_key' is distinct from v_home_key
       or v_runtime->>'provider_away_club_key' is distinct from v_away_key
       or v_runtime->>'civil_time' is distinct from to_char(v_kickoff at time zone 'Europe/Warsaw','HH24:MI')
       or v_plan->>'civil_time' is distinct from v_runtime->>'civil_time' then
      raise exception 'ROBOTICKET_ADMISSION_PROVIDER_RECEIPT_MISMATCH';
    end if;
    if left(lower(v_ticket_url),8) <> 'https://' or position('@' in split_part(split_part(v_ticket_url,'//',2),'/',1)) > 0
       or lower(split_part(split_part(v_ticket_url,'//',2),'/',1)) <> v_domain
       or position('eventId=' || v_event in v_ticket_url) = 0 then
      raise exception 'ROBOTICKET_ADMISSION_TICKET_URL_MISMATCH';
    end if;

    select c.* into v_club_cfg from public.roboticket_clubs c
    where c.club_slug=v_club and c.active for share;
    if not found or lower(v_club_cfg.source_domain) <> v_domain
       or lower(split_part(split_part(v_club_cfg.base_url,'//',2),'/',1)) <> v_domain then
      raise exception 'ROBOTICKET_ADMISSION_CLUB_CONFIG_MISMATCH';
    end if;
    if v_ticket_url is distinct from rtrim(v_club_cfg.base_url,'/') || '/Stadium/Index?eventId=' || v_event then
      raise exception 'ROBOTICKET_ADMISSION_TICKET_URL_MISMATCH';
    end if;
    if not exists (
      select 1 from private.structural_prior_club_aliases_v1 a
      where a.is_active and a.canonical_name=v_club_cfg.club_name and a.club_key=v_home_key
    ) or exists (
      select 1 from private.structural_prior_club_aliases_v1 a
      where a.is_active and a.canonical_name=v_club_cfg.club_name and a.club_key<>v_home_key
    ) then raise exception 'ROBOTICKET_ADMISSION_SOURCE_CLUB_ALIAS_MISMATCH'; end if;
    if not exists (
      select 1 from public.roboticket_event_candidates c
      where c.club_slug=v_club and c.external_event_id=v_event
        and coalesce(c.metadata->>'candidate_kind','')='match'
        and c.status in ('discovered','mapped','collecting')
      for update
    ) then raise exception 'ROBOTICKET_ADMISSION_CANDIDATE_MISMATCH'; end if;
    if exists (select 1 from private.roboticket_verified_schedule_v1 s
      where s.club_slug=v_club and s.external_event_id=v_event) then
      raise exception 'ROBOTICKET_ADMISSION_V1_SCHEDULE_ALREADY_OWNS_IDENTITY';
    end if;
    if not exists (
      select 1 from private.structural_prior_club_aliases_v1 a
      where a.is_active and a.alias=v_home and a.club_key=v_home_key
    ) or not exists (
      select 1 from private.structural_prior_club_aliases_v1 a
      where a.is_active and a.alias=v_away and a.club_key=v_away_key
    ) then raise exception 'ROBOTICKET_ADMISSION_PARTICIPANT_ALIAS_MISMATCH'; end if;
    if not exists (
      select 1 from private.structural_prior_competition_aliases_v1 a
      where a.is_active and a.alias=v_competition and a.canonical_competition='Ekstraklasa'
    ) then raise exception 'ROBOTICKET_ADMISSION_COMPETITION_ALIAS_MISMATCH'; end if;

      -- Row locks above can wait too; stamp and validate at the write boundary.
      v_now := clock_timestamp();
      if v_kickoff <= v_now then raise exception 'ROBOTICKET_ADMISSION_KICKOFF_NOT_FUTURE'; end if;
      if v_source_bound > v_now or v_runtime_at > v_now or v_runtime_at < v_now - interval '10 minutes' then
        raise exception 'ROBOTICKET_ADMISSION_SOURCE_RECEIPT_NOT_CURRENT';
      end if;
      if exists (
        select 1 from public.ticket_events e
        where e.provider='roboticket'
          and (e.source_domain=v_domain and e.external_event_id=v_event
               or e.club_slug=v_club and e.home_team=v_home and e.away_team=v_away and e.match_date=v_match_date)
      ) then raise exception 'ROBOTICKET_ADMISSION_TICKET_EVENT_DUPLICATE'; end if;

      insert into public.ticket_events(
        provider,external_event_id,home_team,away_team,competition,match_date,kickoff_at,source_url,
        mapping_source,mapping_confidence,club_slug,source_domain,updated_at
      ) values (
        'roboticket',v_event,v_home,v_away,'Ekstraklasa',v_match_date,v_kickoff,v_ticket_url,
        'roboticket-explicit-admission-v2','verified',v_club,v_domain,v_now
      ) returning id into v_ticket_event_id;

      insert into private.roboticket_admission_receipts_v2(
        club_slug,external_event_id,ticket_event_id,plan_sha256,original_html_sha256,provider_body_sha256,
        runtime_html_sha256,runtime_provider_sha256,acquisition_index_sha256,source_reference,
        source_retrieved_at_bound,known_at,evidence_payload
      ) values (
        v_club,v_event,v_ticket_event_id,v_plan_sha,v_html_sha,v_provider_sha,
        v_runtime_html_sha,v_runtime_provider_sha,v_index_sha,v_source_reference,
        v_source_bound,v_now,v_item
      ) returning id into v_receipt_id;
      update public.roboticket_event_candidates c
        set status='collecting',metadata=c.metadata || jsonb_build_object(
          'admission_version','roboticket-explicit-admission-v2',
          'admission_receipt_id',v_receipt_id,
          'promoted_ticket_event_id',v_ticket_event_id
        )
        where c.club_slug=v_club and c.external_event_id=v_event;
      v_inserted := true;
    v_results := v_results || jsonb_build_array(jsonb_build_object(
      'club_slug',v_club,'roboticket_event_id',v_event,'ticket_event_id',v_ticket_event_id,
      'receipt_id',v_receipt_id,'admitted',true,'tracking_created',v_inserted,
      'known_at',case when v_inserted then v_now else v_existing.known_at end,
      'backfilled_snapshots',0,'model_activation',false,'live_adjustment',0
    ));
  end loop;

  return jsonb_build_object(
    'version','roboticket-explicit-admission-v2',
    'fixtures',v_results,
    'tracking_created_count',(select count(*) from jsonb_array_elements(v_results) x where (x->>'tracking_created')::boolean),
    'backfilled_snapshots',0,
    'model_activation',false,
    'live_adjustment',0
  );
end;
$function$;

revoke all on function public.admit_roboticket_explicit_fixtures_v2(jsonb) from public, anon, authenticated;
grant execute on function public.admit_roboticket_explicit_fixtures_v2(jsonb) to service_role;
