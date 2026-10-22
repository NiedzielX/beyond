-- D2 Long72 Next-Opponent Attractiveness v1
--
-- Research-only PIT-safe context layer for the P4 fixture-cannibalization
-- hypothesis. It estimates historical attendance uplift for the NEXT HOME
-- opponent known in the immutable schedule state at the forecast cutoff.
--
-- Two independent knowledge gates apply:
-- 1. the next home opponent must exist in a schedule batch observed no later
--    than the forecast as_of_at;
-- 2. attendance outcomes used for attractiveness must have kickoff and
--    created/updated/confirmed timestamps no later than that same as_of_at.
--
-- No production forecast is changed.

begin;

create or replace function public.opponent_attractiveness_as_known_v1(
    p_ticket_event_id bigint,
    p_opponent_canonical text,
    p_as_of_at timestamptz
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private'
as $function$
declare
    v_event public.ticket_events%rowtype;
    v_opponent text;
    v_competition_key text;
    v_club_count integer;
    v_opponent_count integer;
    v_club_median numeric;
    v_opponent_median numeric;
    v_uplift numeric;
    v_status text;
begin
    if p_ticket_event_id is null or p_as_of_at is null then
        raise exception 'ticket_event_id and as_of_at are required';
    end if;
    if p_as_of_at > now() + interval '5 minutes' then
        raise exception 'as_of_at cannot be in the future';
    end if;

    select * into v_event from public.ticket_events where id=p_ticket_event_id;
    if v_event.id is null then
        return jsonb_build_object(
            'version','opponent-attractiveness-as-known-v1',
            'status','TICKET_EVENT_NOT_FOUND',
            'ticket_event_id',p_ticket_event_id,
            'as_of_at',p_as_of_at,
            'production_change',false
        );
    end if;

    v_opponent := nullif(public.sporting_canonical_team_v1(p_opponent_canonical),'');
    if v_opponent is null then
        return jsonb_build_object(
            'version','opponent-attractiveness-as-known-v1',
            'status','NO_OPPONENT',
            'ticket_event_id',p_ticket_event_id,
            'as_of_at',p_as_of_at,
            'production_change',false
        );
    end if;

    v_competition_key := public.match_competition_key_v1(v_event.competition);

    with history as (
        select
            h.id,
            public.sporting_canonical_team_v1(h.away_team) as away_team_canonical,
            o.actual_attendance
        from public.ticket_events h
        join public.ticket_event_outcomes o on o.ticket_event_id=h.id
        where h.club_slug=v_event.club_slug
          and public.match_competition_key_v1(h.competition)=v_competition_key
          and h.kickoff_at < p_as_of_at
          and h.kickoff_at >= p_as_of_at - interval '730 days'
          and o.actual_attendance is not null
          and o.created_at <= p_as_of_at
          and coalesce(o.updated_at,o.created_at) <= p_as_of_at
          and coalesce(o.confirmed_at,o.created_at) <= p_as_of_at
    )
    select
        count(*)::integer,
        count(*) filter (where away_team_canonical=v_opponent)::integer,
        percentile_cont(0.5) within group (order by actual_attendance)::numeric,
        percentile_cont(0.5) within group (order by actual_attendance)
            filter (where away_team_canonical=v_opponent)::numeric
    into v_club_count,v_opponent_count,v_club_median,v_opponent_median
    from history;

    v_status := case
        when v_club_count < 8 then 'INSUFFICIENT_CLUB_HISTORY'
        when v_opponent_count < 3 then 'INSUFFICIENT_OPPONENT_HISTORY'
        when v_club_median is null or v_club_median <= 0 then 'INVALID_CLUB_BASELINE'
        else 'READY'
    end;

    if v_status='READY' then
        v_uplift := round(((v_opponent_median/v_club_median)-1.0)*100.0,2);
    end if;

    return jsonb_build_object(
        'version','opponent-attractiveness-as-known-v1',
        'status',v_status,
        'ticket_event_id',p_ticket_event_id,
        'as_of_at',p_as_of_at,
        'club_slug',v_event.club_slug,
        'competition_key',v_competition_key,
        'opponent_canonical',v_opponent,
        'club_history_count',v_club_count,
        'opponent_history_count',v_opponent_count,
        'club_median_attendance',v_club_median,
        'opponent_median_attendance',v_opponent_median,
        'opponent_uplift_pct',v_uplift,
        'lookback_days',730,
        'club_history_gate',8,
        'opponent_history_gate',3,
        'outcome_knowledge_rule','kickoff, outcome created/updated/confirmed all no later than as_of_at',
        'evidence_class','point_in_time_system_known',
        'production_change',false
    );
end;
$function$;

create or replace function public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private'
as $function$
declare
    v_fixture jsonb;
    v_opponent text;
    v_attr jsonb;
begin
    v_fixture := public.fixture_context_for_ticket_event_as_known_v1(p_ticket_event_id,p_as_of_at);

    if coalesce(v_fixture->>'status','') <> 'READY' then
        return jsonb_build_object(
            'version','next-home-opponent-attractiveness-v1',
            'status','FIXTURE_CONTEXT_' || coalesce(v_fixture->>'status','UNKNOWN'),
            'ticket_event_id',p_ticket_event_id,
            'as_of_at',p_as_of_at,
            'fixture_context',v_fixture,
            'production_change',false
        );
    end if;

    v_opponent := nullif(v_fixture->>'next_home_opponent_canonical','');
    if v_opponent is null then
        return jsonb_build_object(
            'version','next-home-opponent-attractiveness-v1',
            'status','NO_NEXT_HOME_MATCH_IN_SCHEDULE_STATE',
            'ticket_event_id',p_ticket_event_id,
            'as_of_at',p_as_of_at,
            'schedule_batch_id',v_fixture->>'schedule_batch_id',
            'fixture_context',v_fixture,
            'production_change',false
        );
    end if;

    v_attr := public.opponent_attractiveness_as_known_v1(
        p_ticket_event_id,v_opponent,p_as_of_at
    );

    return v_attr || jsonb_build_object(
        'version','next-home-opponent-attractiveness-v1',
        'next_home_opponent_canonical',v_opponent,
        'next_home_match_days',v_fixture->'next_home_match_days',
        'schedule_batch_id',v_fixture->'schedule_batch_id',
        'schedule_observed_at',v_fixture->'schedule_observed_at',
        'fixture_context_status',v_fixture->>'status'
    );
end;
$function$;

create table if not exists private.d2_long72_next_opponent_attractiveness_v1 (
    id bigserial primary key,
    forward_prediction_id bigint not null unique references private.d2_long72_forward_predictions_v1(id),
    ticket_event_id bigint not null references public.ticket_events(id),
    forecast_as_of_at timestamptz not null,
    status text not null,
    schedule_batch_id bigint references private.fixture_schedule_batches_v1(id),
    next_home_opponent_canonical text,
    next_home_match_days numeric,
    club_history_count integer,
    opponent_history_count integer,
    opponent_uplift_pct numeric,
    payload jsonb not null,
    evidence_class text not null default 'point_in_time_system_known',
    captured_at timestamptz not null default now()
);

create index if not exists d2_long72_next_opponent_attr_event_idx
    on private.d2_long72_next_opponent_attractiveness_v1(ticket_event_id,forecast_as_of_at);

create or replace function private.reject_d2_long72_next_opponent_attr_mutation_v1()
returns trigger
language plpgsql
set search_path=private,public
as $function$
begin
    raise exception 'Long72 next-opponent attractiveness evidence is append-only; % is not allowed',tg_op;
end;
$function$;

drop trigger if exists d2_long72_next_opponent_attr_immutable_v1
    on private.d2_long72_next_opponent_attractiveness_v1;
create trigger d2_long72_next_opponent_attr_immutable_v1
before update or delete on private.d2_long72_next_opponent_attractiveness_v1
for each row execute function private.reject_d2_long72_next_opponent_attr_mutation_v1();

create or replace function public.capture_d2_long72_next_opponent_attractiveness_v1(
    p_limit integer default 1000
)
returns jsonb
language plpgsql
set search_path to 'public','private'
as $function$
declare
    v_prediction record;
    v_payload jsonb;
    v_inserted integer := 0;
    v_ready integer := 0;
    v_nonready integer := 0;
begin
    if p_limit is null or p_limit < 1 or p_limit > 10000 then
        raise exception 'p_limit must be between 1 and 10000';
    end if;

    for v_prediction in
        select p.id,p.ticket_event_id,p.as_of_at
        from private.d2_long72_forward_predictions_v1 p
        left join private.d2_long72_next_opponent_attractiveness_v1 a
          on a.forward_prediction_id=p.id
        where a.id is null
          and coalesce((p.metadata->>'manual_first_checkpoint')::boolean,false)=false
        order by p.as_of_at,p.id
        limit p_limit
    loop
        v_payload := public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(
            v_prediction.ticket_event_id,v_prediction.as_of_at
        );

        insert into private.d2_long72_next_opponent_attractiveness_v1(
            forward_prediction_id,ticket_event_id,forecast_as_of_at,status,
            schedule_batch_id,next_home_opponent_canonical,next_home_match_days,
            club_history_count,opponent_history_count,opponent_uplift_pct,payload,evidence_class
        ) values (
            v_prediction.id,v_prediction.ticket_event_id,v_prediction.as_of_at,
            coalesce(v_payload->>'status','UNKNOWN'),
            nullif(v_payload->>'schedule_batch_id','')::bigint,
            nullif(v_payload->>'next_home_opponent_canonical',''),
            nullif(v_payload->>'next_home_match_days','')::numeric,
            nullif(v_payload->>'club_history_count','')::integer,
            nullif(v_payload->>'opponent_history_count','')::integer,
            nullif(v_payload->>'opponent_uplift_pct','')::numeric,
            v_payload,
            'point_in_time_system_known'
        )
        on conflict (forward_prediction_id) do nothing;

        if found then
            v_inserted:=v_inserted+1;
            if coalesce(v_payload->>'status','')='READY' then
                v_ready:=v_ready+1;
            else
                v_nonready:=v_nonready+1;
            end if;
        end if;
    end loop;

    return jsonb_build_object(
        'version','d2-long72-next-opponent-attractiveness-sidecar-v1',
        'inserted_rows',v_inserted,
        'ready_rows',v_ready,
        'nonready_rows',v_nonready,
        'production_change',false
    );
end;
$function$;

revoke all on function public.opponent_attractiveness_as_known_v1(bigint,text,timestamptz) from public,anon,authenticated;
revoke all on function public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(bigint,timestamptz) from public,anon,authenticated;
revoke all on function public.capture_d2_long72_next_opponent_attractiveness_v1(integer) from public,anon,authenticated;
grant execute on function public.opponent_attractiveness_as_known_v1(bigint,text,timestamptz) to service_role;
grant execute on function public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(bigint,timestamptz) to service_role;
grant execute on function public.capture_d2_long72_next_opponent_attractiveness_v1(integer) to service_role;

revoke all on private.d2_long72_next_opponent_attractiveness_v1 from public,anon,authenticated;
grant select,insert on private.d2_long72_next_opponent_attractiveness_v1 to service_role;
grant usage,select on sequence private.d2_long72_next_opponent_attractiveness_v1_id_seq to service_role;

do $block$
begin
    if not exists (
        select 1 from cron.job
        where jobname='d2_long72_next_opponent_attractiveness_v1_15m'
    ) then
        perform cron.schedule(
            'd2_long72_next_opponent_attractiveness_v1_15m',
            '9,24,39,54 * * * *',
            'select public.capture_d2_long72_next_opponent_attractiveness_v1();'
        );
    end if;
end;
$block$;

commit;
