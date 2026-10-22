-- D2 Long72 Fixture Context Sidecar v1
--
-- Append-only PIT-safe context evidence aligned to immutable Long72 forward
-- predictions. This never changes the forecast itself.
--
-- For each reproducible Long72 prediction, context is reconstructed only from
-- an immutable schedule batch with observed_at <= prediction.as_of_at.
-- If no such schedule state existed, the sidecar permanently records the
-- fail-closed status rather than filling the row from later knowledge.

begin;

create table if not exists private.d2_long72_fixture_context_v1 (
    id bigserial primary key,
    forward_prediction_id bigint not null unique references private.d2_long72_forward_predictions_v1(id),
    ticket_event_id bigint not null references public.ticket_events(id),
    forecast_as_of_at timestamptz not null,
    context_status text not null,
    schedule_batch_id bigint references private.fixture_schedule_batches_v1(id),
    context_payload jsonb not null,
    evidence_class text not null default 'forward_schedule_as_known',
    metadata jsonb not null default '{}'::jsonb,
    captured_at timestamptz not null default now()
);

create index if not exists d2_long72_fixture_context_event_idx
    on private.d2_long72_fixture_context_v1(ticket_event_id, forecast_as_of_at);

create index if not exists d2_long72_fixture_context_status_idx
    on private.d2_long72_fixture_context_v1(context_status, forecast_as_of_at);

create or replace function private.reject_d2_long72_fixture_context_mutation_v1()
returns trigger
language plpgsql
set search_path = private, public
as $function$
begin
    raise exception 'Long72 fixture-context sidecar is append-only; % is not allowed', tg_op;
end;
$function$;

drop trigger if exists d2_long72_fixture_context_immutable_v1
    on private.d2_long72_fixture_context_v1;
create trigger d2_long72_fixture_context_immutable_v1
before update or delete on private.d2_long72_fixture_context_v1
for each row execute function private.reject_d2_long72_fixture_context_mutation_v1();

create or replace function public.capture_d2_long72_fixture_context_v1(
    p_limit integer default 1000
)
returns jsonb
language plpgsql
set search_path to 'public','private'
as $function$
declare
    v_prediction record;
    v_context jsonb;
    v_inserted integer := 0;
    v_ready integer := 0;
    v_unavailable integer := 0;
    v_status text;
    v_schedule_batch_id bigint;
begin
    if p_limit is null or p_limit < 1 or p_limit > 10000 then
        raise exception 'p_limit must be between 1 and 10000';
    end if;

    for v_prediction in
        select p.id, p.ticket_event_id, p.as_of_at, p.package_id
        from private.d2_long72_forward_predictions_v1 p
        left join private.d2_long72_fixture_context_v1 c
          on c.forward_prediction_id = p.id
        where c.id is null
          and coalesce((p.metadata->>'manual_first_checkpoint')::boolean,false)=false
        order by p.as_of_at, p.id
        limit p_limit
    loop
        v_context := public.fixture_context_for_ticket_event_as_known_v1(
            v_prediction.ticket_event_id,
            v_prediction.as_of_at
        );
        v_status := coalesce(v_context->>'status','UNKNOWN');
        v_schedule_batch_id := nullif(v_context->>'schedule_batch_id','')::bigint;

        insert into private.d2_long72_fixture_context_v1(
            forward_prediction_id,
            ticket_event_id,
            forecast_as_of_at,
            context_status,
            schedule_batch_id,
            context_payload,
            evidence_class,
            metadata
        ) values (
            v_prediction.id,
            v_prediction.ticket_event_id,
            v_prediction.as_of_at,
            v_status,
            v_schedule_batch_id,
            v_context,
            'forward_schedule_as_known',
            jsonb_build_object(
                'package_id',v_prediction.package_id,
                'source_prediction_table','private.d2_long72_forward_predictions_v1',
                'fixture_context_version','fixture-context-as-known-v1',
                'historical_backfill_from_later_schedule_allowed',false,
                'production_change',false
            )
        )
        on conflict (forward_prediction_id) do nothing;

        if found then
            v_inserted := v_inserted + 1;
            if v_status = 'READY' then
                v_ready := v_ready + 1;
            else
                v_unavailable := v_unavailable + 1;
            end if;
        end if;
    end loop;

    return jsonb_build_object(
        'version','d2-long72-fixture-context-sidecar-v1',
        'inserted_rows',v_inserted,
        'ready_rows',v_ready,
        'unavailable_rows',v_unavailable,
        'evidence_class','forward_schedule_as_known',
        'production_change',false
    );
end;
$function$;

revoke all on private.d2_long72_fixture_context_v1 from public, anon, authenticated;
grant select, insert on private.d2_long72_fixture_context_v1 to service_role;
grant usage, select on sequence private.d2_long72_fixture_context_v1_id_seq to service_role;

revoke all on function public.capture_d2_long72_fixture_context_v1(integer) from public, anon, authenticated;
grant execute on function public.capture_d2_long72_fixture_context_v1(integer) to service_role;

-- Long72 prediction materialization starts at :17 each hour. This low-cost
-- catch-up job checks four times per hour and inserts only missing sidecar rows.
do $block$
begin
    if not exists (
        select 1 from cron.job
        where jobname='d2_long72_fixture_context_sidecar_v1_15m'
    ) then
        perform cron.schedule(
            'd2_long72_fixture_context_sidecar_v1_15m',
            '7,22,37,52 * * * *',
            'select public.capture_d2_long72_fixture_context_v1();'
        );
    end if;
end;
$block$;

commit;
