-- Fixture Schedule As-Known v1
--
-- Forward-only, append-only schedule state used by P4 fixture-context research.
-- Historical backfill from today's final schedule is intentionally forbidden.
-- Production forecast behavior is unchanged.

begin;

create table if not exists private.fixture_schedule_batches_v1 (
    id bigserial primary key,
    observed_at timestamptz not null,
    source_max_fetched_at timestamptz not null,
    source_row_count integer not null check (source_row_count >= 0),
    state_fingerprint_md5 text not null unique,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists fixture_schedule_batches_observed_idx
    on private.fixture_schedule_batches_v1(observed_at desc);

create table if not exists private.fixture_schedule_rows_v1 (
    id bigserial primary key,
    batch_id bigint not null references private.fixture_schedule_batches_v1(id),
    source_event_id text not null,
    league_id text not null,
    season text not null,
    round_number integer not null,
    event_date date,
    home_team text not null,
    away_team text not null,
    home_team_canonical text not null,
    away_team_canonical text not null,
    home_score integer,
    away_score integer,
    match_status text,
    completed boolean not null,
    source_name text not null,
    source_fetched_at timestamptz not null,
    metadata jsonb not null default '{}'::jsonb,
    unique(batch_id, source_event_id)
);

create index if not exists fixture_schedule_rows_home_date_idx
    on private.fixture_schedule_rows_v1(batch_id, home_team_canonical, event_date);

create or replace function private.reject_fixture_schedule_mutation_v1()
returns trigger
language plpgsql
set search_path = private, public
as $function$
begin
    raise exception 'fixture schedule as-known evidence is append-only; % is not allowed', tg_op;
end;
$function$;

drop trigger if exists fixture_schedule_batches_immutable_v1
    on private.fixture_schedule_batches_v1;
create trigger fixture_schedule_batches_immutable_v1
before update or delete on private.fixture_schedule_batches_v1
for each row execute function private.reject_fixture_schedule_mutation_v1();

drop trigger if exists fixture_schedule_rows_immutable_v1
    on private.fixture_schedule_rows_v1;
create trigger fixture_schedule_rows_immutable_v1
before update or delete on private.fixture_schedule_rows_v1
for each row execute function private.reject_fixture_schedule_mutation_v1();

create or replace function public.capture_fixture_schedule_as_known_v1(
    p_observed_at timestamptz default now()
)
returns jsonb
language plpgsql
set search_path to 'public','private'
as $function$
declare
    v_source_max timestamptz;
    v_count integer;
    v_fingerprint text;
    v_batch_id bigint;
    v_inserted_rows integer := 0;
begin
    if p_observed_at is null
       or abs(extract(epoch from (now() - p_observed_at))) > 900 then
        raise exception 'schedule capture is forward-only; observed_at must be within 15 minutes of now()';
    end if;

    select
        max(fetched_at),
        count(*)::integer,
        md5(coalesce(string_agg(
            concat_ws('|',
                source_event_id,
                league_id,
                season,
                round_number::text,
                coalesce(event_date::text,''),
                home_team,
                away_team,
                coalesce(home_score::text,''),
                coalesce(away_score::text,''),
                coalesce(match_status,''),
                completed::text,
                source_name,
                fetched_at::text
            ),
            E'\n' order by source_event_id
        ),''))
    into v_source_max,v_count,v_fingerprint
    from public.sporting_league_matches_shadow
    where fetched_at <= p_observed_at;

    if v_count = 0 or v_source_max is null then
        return jsonb_build_object(
            'version','fixture-schedule-as-known-v1',
            'status','NO_SOURCE_ROWS',
            'observed_at',p_observed_at,
            'inserted_batch',false,
            'production_change',false
        );
    end if;

    select id into v_batch_id
    from private.fixture_schedule_batches_v1
    where state_fingerprint_md5=v_fingerprint;

    if v_batch_id is not null then
        return jsonb_build_object(
            'version','fixture-schedule-as-known-v1',
            'status','UNCHANGED',
            'observed_at',p_observed_at,
            'batch_id',v_batch_id,
            'source_max_fetched_at',v_source_max,
            'source_row_count',v_count,
            'inserted_batch',false,
            'production_change',false
        );
    end if;

    insert into private.fixture_schedule_batches_v1(
        observed_at,source_max_fetched_at,source_row_count,state_fingerprint_md5,metadata
    ) values (
        p_observed_at,v_source_max,v_count,v_fingerprint,
        jsonb_build_object(
            'source_table','public.sporting_league_matches_shadow',
            'evidence_class','forward_schedule_as_known',
            'historical_backfill_allowed',false
        )
    ) returning id into v_batch_id;

    insert into private.fixture_schedule_rows_v1(
        batch_id,source_event_id,league_id,season,round_number,event_date,
        home_team,away_team,home_team_canonical,away_team_canonical,
        home_score,away_score,match_status,completed,source_name,source_fetched_at,metadata
    )
    select
        v_batch_id,s.source_event_id,s.league_id,s.season,s.round_number,s.event_date,
        s.home_team,s.away_team,
        public.sporting_canonical_team_v1(s.home_team),
        public.sporting_canonical_team_v1(s.away_team),
        s.home_score,s.away_score,s.match_status,s.completed,s.source_name,s.fetched_at,s.metadata
    from public.sporting_league_matches_shadow s
    where s.fetched_at <= p_observed_at;
    get diagnostics v_inserted_rows = row_count;

    return jsonb_build_object(
        'version','fixture-schedule-as-known-v1',
        'status','CAPTURED',
        'observed_at',p_observed_at,
        'batch_id',v_batch_id,
        'source_max_fetched_at',v_source_max,
        'source_row_count',v_count,
        'inserted_rows',v_inserted_rows,
        'inserted_batch',true,
        'production_change',false
    );
end;
$function$;

revoke all on private.fixture_schedule_batches_v1 from public, anon, authenticated;
revoke all on private.fixture_schedule_rows_v1 from public, anon, authenticated;
grant select, insert on private.fixture_schedule_batches_v1 to service_role;
grant select, insert on private.fixture_schedule_rows_v1 to service_role;
grant usage, select on sequence private.fixture_schedule_batches_v1_id_seq to service_role;
grant usage, select on sequence private.fixture_schedule_rows_v1_id_seq to service_role;

revoke all on function public.capture_fixture_schedule_as_known_v1(timestamptz) from public, anon, authenticated;
grant execute on function public.capture_fixture_schedule_as_known_v1(timestamptz) to service_role;

-- Runtime cadence currently used in Supabase:
--   14 */6 * * *
--   select public.capture_fixture_schedule_as_known_v1();
-- Keep scheduler creation outside this idempotent source file to avoid duplicate cron jobs.

commit;
