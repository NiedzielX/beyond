-- C1 v8 Prospective Shadow Evidence v1
--
-- Forward-only evidence path for the frozen v2+v8 package.
-- Production forecasts are not modified. Rows are append-only and may only be
-- inserted before an event outcome is known.

begin;

create table if not exists private.c1_shadow_v8_predictions_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    source_prior_id bigint not null,
    source_snapshot_id bigint not null references public.snapshots(id),
    as_of_at timestamptz not null,
    run_requested_at timestamptz not null,
    kickoff_at timestamptz not null,
    hours_to_kickoff numeric not null,
    stadium_capacity integer not null check (stadium_capacity > 0),
    structural_prior_p50 numeric not null,
    v2_live_p50 numeric not null,
    abs_disagreement_occupancy numeric not null check (abs_disagreement_occupancy >= 0),
    live_observation_count_to_date integer not null check (live_observation_count_to_date >= 1 and live_observation_count_to_date <= 4),
    live_slope_occupancy_per_hour_to_date numeric,
    selected_expert text not null check (selected_expert in ('PRIOR','LIVE')),
    policy_prediction numeric not null,
    reason_code text not null,
    package_version text not null,
    live_model_id text not null,
    policy_id text not null,
    artifact_sha256 text not null,
    feature_contract text not null,
    point_in_time_validated boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique(ticket_event_id, as_of_at, package_version)
);

comment on table private.c1_shadow_v8_predictions_v1 is
'Append-only pre-outcome EXPERIMENTAL_SHADOW decisions from frozen C1 v2+v8 package. Never rewrites production forecasts.';

create index if not exists c1_shadow_v8_predictions_event_idx
    on private.c1_shadow_v8_predictions_v1(ticket_event_id, as_of_at);

revoke all on private.c1_shadow_v8_predictions_v1 from public, anon, authenticated;
grant select, insert on private.c1_shadow_v8_predictions_v1 to service_role;
grant usage, select on sequence private.c1_shadow_v8_predictions_v1_id_seq to service_role;

create or replace function public.get_c1_shadow_v8_inputs_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_payload jsonb;
begin
    if p_requested_at is null then
        raise exception 'p_requested_at is required';
    end if;
    if abs(extract(epoch from (now() - p_requested_at))) > 900 then
        raise exception 'C1 v8 shadow input is forward-only; p_requested_at must be within 15 minutes of now()';
    end if;

    with active as (
        select
            e.id as ticket_event_id,
            e.club_slug,
            e.home_team,
            e.away_team,
            e.kickoff_at,
            s.id as current_snapshot_id,
            s.captured_at as current_snapshot_captured_at
        from public.ticket_events e
        join lateral (
            select s1.id, s1.captured_at
            from public.snapshots s1
            where s1.ticket_event_id=e.id
              and s1.captured_at<=p_requested_at
            order by s1.captured_at desc, s1.id desc
            limit 1
        ) s on true
        where e.kickoff_at>p_requested_at
          and e.kickoff_at<=p_requested_at+interval '24 hours'
    ), anchored as (
        select
            a.*,
            p.status as prior_status,
            p.horizon as prior_horizon,
            p.source_prior_id,
            p.p50 as structural_prior_p50,
            p.stadium_capacity,
            p.model_spec_id as structural_prior_model_spec_id,
            p.artifact_version as structural_prior_artifact_version,
            p.point_in_time_validated as prior_point_in_time_validated
        from active a
        cross join lateral public.get_structural_prior_v1(
            a.ticket_event_id,
            a.current_snapshot_captured_at
        ) p
        where p.status='ready'
          and p.horizon='T-1'
          and coalesce(p.point_in_time_validated,false)
    ), representative_candidates as (
        select
            a.ticket_event_id,
            a.stadium_capacity,
            s.id as requested_snapshot_id,
            s.captured_at as requested_as_of_at,
            floor(extract(epoch from (a.kickoff_at-s.captured_at))/21600.0)::integer as bucket_6h,
            row_number() over (
                partition by a.ticket_event_id,
                    floor(extract(epoch from (a.kickoff_at-s.captured_at))/21600.0)::integer
                order by s.captured_at desc, s.id desc
            ) as rn
        from anchored a
        join public.snapshots s
          on s.ticket_event_id=a.ticket_event_id
         and s.captured_at<a.kickoff_at
         and s.captured_at>=a.kickoff_at-interval '24 hours'
         and s.captured_at<=p_requested_at
    ), representative_rows as (
        select
            r.ticket_event_id,
            r.bucket_6h,
            r.requested_snapshot_id,
            r.requested_as_of_at,
            to_jsonb(f) as features
        from representative_candidates r
        cross join lateral public.get_live_trajectory_features_v1_1_asof(
            r.ticket_event_id,
            r.requested_as_of_at,
            r.stadium_capacity
        ) f
        where r.rn=1
          and coalesce(f.point_in_time_validated,false)
          and f.snapshot_id is not null
    ), representative_json as (
        select
            ticket_event_id,
            jsonb_agg(
                jsonb_build_object(
                    'bucket_6h',bucket_6h,
                    'requested_snapshot_id',requested_snapshot_id,
                    'requested_as_of_at',requested_as_of_at,
                    'features',features
                ) order by requested_as_of_at
            ) as representatives
        from representative_rows
        group by ticket_event_id
    ), candidate_json as (
        select coalesce(jsonb_agg(
            jsonb_build_object(
                'ticket_event_id',a.ticket_event_id,
                'club_slug',a.club_slug,
                'home_team',a.home_team,
                'away_team',a.away_team,
                'kickoff_at',a.kickoff_at,
                'prior',jsonb_build_object(
                    'source_prior_id',a.source_prior_id,
                    'horizon',a.prior_horizon,
                    'p50',a.structural_prior_p50,
                    'stadium_capacity',a.stadium_capacity,
                    'model_spec_id',a.structural_prior_model_spec_id,
                    'artifact_version',a.structural_prior_artifact_version,
                    'point_in_time_validated',a.prior_point_in_time_validated
                ),
                'representatives',r.representatives
            ) order by a.kickoff_at,a.ticket_event_id
        ),'[]'::jsonb) as value
        from anchored a
        join representative_json r on r.ticket_event_id=a.ticket_event_id
    )
    select jsonb_build_object(
        'version','c1-shadow-v8-inputs-v1',
        'requested_at',p_requested_at,
        'status','EXPERIMENTAL_SHADOW',
        'package_version','c1-shadow-v8-frozen-2026-10-16-n9',
        'candidates',(select value from candidate_json),
        'candidate_count',jsonb_array_length((select value from candidate_json))
    ) into v_payload;

    return v_payload;
end;
$function$;

revoke all on function public.get_c1_shadow_v8_inputs_v1(timestamptz) from public, anon, authenticated;
grant execute on function public.get_c1_shadow_v8_inputs_v1(timestamptz) to service_role;

create or replace function public.insert_c1_shadow_v8_predictions_v1(
    p_rows jsonb,
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_row jsonb;
    v_event_id bigint;
    v_snapshot_id bigint;
    v_as_of timestamptz;
    v_kickoff timestamptz;
    v_snapshot_captured timestamptz;
    v_existing_outcome boolean;
    v_prior record;
    v_inserted_id bigint;
    v_inserted integer := 0;
    v_duplicates integer := 0;
    v_results jsonb := '[]'::jsonb;
begin
    if p_rows is null or jsonb_typeof(p_rows) <> 'array' then
        raise exception 'p_rows must be a JSON array';
    end if;
    if p_requested_at is null or abs(extract(epoch from (now()-p_requested_at))) > 900 then
        raise exception 'C1 v8 shadow write is forward-only; p_requested_at must be within 15 minutes of now()';
    end if;

    for v_row in select value from jsonb_array_elements(p_rows)
    loop
        v_event_id := (v_row->>'ticket_event_id')::bigint;
        v_snapshot_id := (v_row->>'source_snapshot_id')::bigint;
        v_as_of := (v_row->>'as_of_at')::timestamptz;

        if v_row->>'package_version' <> 'c1-shadow-v8-frozen-2026-10-16-n9' then
            raise exception 'unexpected C1 shadow package version for event %', v_event_id;
        end if;
        if v_row->>'policy_id' <> 'c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single' then
            raise exception 'unexpected C1 shadow policy id for event %', v_event_id;
        end if;
        if v_row->>'selected_expert' not in ('PRIOR','LIVE') then
            raise exception 'invalid selected expert for event %', v_event_id;
        end if;

        select kickoff_at into v_kickoff
        from public.ticket_events
        where id=v_event_id;
        if v_kickoff is null then
            raise exception 'unknown ticket event %', v_event_id;
        end if;
        if v_as_of>=v_kickoff or v_as_of>p_requested_at then
            raise exception 'non-PIT shadow row for event %', v_event_id;
        end if;

        select captured_at into v_snapshot_captured
        from public.snapshots
        where id=v_snapshot_id and ticket_event_id=v_event_id;
        if v_snapshot_captured is null or v_snapshot_captured<>v_as_of then
            raise exception 'snapshot/as_of mismatch for event %', v_event_id;
        end if;

        select exists(
            select 1 from public.ticket_event_outcomes o
            where o.ticket_event_id=v_event_id and o.actual_attendance is not null
        ) into v_existing_outcome;
        if v_existing_outcome then
            raise exception 'prospective C1 shadow row rejected because outcome already exists for event %', v_event_id;
        end if;

        select * into v_prior
        from public.get_structural_prior_v1(v_event_id,v_as_of)
        limit 1;
        if v_prior.status is distinct from 'ready'
           or v_prior.horizon is distinct from 'T-1'
           or not coalesce(v_prior.point_in_time_validated,false)
           or v_prior.source_prior_id is distinct from (v_row->>'source_prior_id')::bigint
           or abs(v_prior.p50-(v_row->>'structural_prior_p50')::numeric)>0.01
           or v_prior.stadium_capacity is distinct from (v_row->>'stadium_capacity')::integer then
            raise exception 'Structural Prior verification failed for event %', v_event_id;
        end if;

        if v_row->>'selected_expert'='PRIOR'
           and abs((v_row->>'policy_prediction')::numeric-(v_row->>'structural_prior_p50')::numeric)>0.01 then
            raise exception 'PRIOR policy prediction mismatch for event %',v_event_id;
        end if;
        if v_row->>'selected_expert'='LIVE'
           and abs((v_row->>'policy_prediction')::numeric-(v_row->>'v2_live_p50')::numeric)>0.01 then
            raise exception 'LIVE policy prediction mismatch for event %',v_event_id;
        end if;

        v_inserted_id := null;
        insert into private.c1_shadow_v8_predictions_v1(
            ticket_event_id,source_prior_id,source_snapshot_id,as_of_at,run_requested_at,
            kickoff_at,hours_to_kickoff,stadium_capacity,structural_prior_p50,v2_live_p50,
            abs_disagreement_occupancy,live_observation_count_to_date,
            live_slope_occupancy_per_hour_to_date,selected_expert,policy_prediction,reason_code,
            package_version,live_model_id,policy_id,artifact_sha256,feature_contract,
            point_in_time_validated,metadata
        ) values (
            v_event_id,(v_row->>'source_prior_id')::bigint,v_snapshot_id,v_as_of,p_requested_at,
            v_kickoff,(v_row->>'hours_to_kickoff')::numeric,(v_row->>'stadium_capacity')::integer,
            (v_row->>'structural_prior_p50')::numeric,(v_row->>'v2_live_p50')::numeric,
            (v_row->>'abs_disagreement_occupancy')::numeric,(v_row->>'live_observation_count_to_date')::integer,
            nullif(v_row->>'live_slope_occupancy_per_hour_to_date','')::numeric,
            v_row->>'selected_expert',(v_row->>'policy_prediction')::numeric,v_row->>'reason_code',
            v_row->>'package_version',v_row->>'live_model_id',v_row->>'policy_id',
            v_row->>'artifact_sha256',v_row->>'feature_contract',true,
            coalesce(v_row->'metadata','{}'::jsonb)
        )
        on conflict(ticket_event_id,as_of_at,package_version) do nothing
        returning id into v_inserted_id;

        if v_inserted_id is null then
            v_duplicates := v_duplicates+1;
            select id into v_inserted_id
            from private.c1_shadow_v8_predictions_v1
            where ticket_event_id=v_event_id and as_of_at=v_as_of
              and package_version=v_row->>'package_version';
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event_id,'status','duplicate','prediction_id',v_inserted_id
            ));
        else
            v_inserted := v_inserted+1;
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event_id,'status','inserted','prediction_id',v_inserted_id
            ));
        end if;
    end loop;

    return jsonb_build_object(
        'version','c1-shadow-v8-write-v1',
        'requested_at',p_requested_at,
        'inserted_count',v_inserted,
        'duplicate_count',v_duplicates,
        'results',v_results
    );
end;
$function$;

revoke all on function public.insert_c1_shadow_v8_predictions_v1(jsonb,timestamptz) from public, anon, authenticated;
grant execute on function public.insert_c1_shadow_v8_predictions_v1(jsonb,timestamptz) to service_role;

commit;
