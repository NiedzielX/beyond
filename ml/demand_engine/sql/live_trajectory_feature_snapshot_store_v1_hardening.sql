-- Hardening for live_trajectory_feature_snapshot_store_v1.sql.
-- Keep the materializer safe when no point-in-time feature row exists.

create or replace function private.materialize_live_trajectory_feature_snapshot_v1(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz,
    p_horizon text default 'continuous',
    p_stadium_capacity integer default null
)
returns bigint
language plpgsql
security definer
set search_path=private,public
as $function$
declare
    v_row record;
    v_id bigint;
begin
    select * into v_row
    from public.get_live_trajectory_features_v1_1_asof(
        p_ticket_event_id,p_as_of_at,p_stadium_capacity
    );

    if not found then
        return null;
    end if;
    if v_row.snapshot_id is null then
        return null;
    end if;
    if v_row.snapshot_captured_at > p_as_of_at then
        raise exception 'point-in-time violation: source snapshot % is after as_of %',
            v_row.snapshot_captured_at,p_as_of_at;
    end if;
    if p_as_of_at >= v_row.kickoff_at then
        raise exception 'as_of_at must be before kickoff';
    end if;

    insert into private.live_trajectory_feature_snapshots_v1(
        ticket_event_id,horizon,as_of_at,kickoff_at,feature_version,
        source_snapshot_id,source_snapshot_captured_at,signal_readiness,
        feature_quality,point_in_time_validated,features,source_metadata
    ) values (
        p_ticket_event_id,p_horizon,p_as_of_at,v_row.kickoff_at,v_row.feature_version,
        v_row.snapshot_id,v_row.snapshot_captured_at,v_row.signal_readiness,
        v_row.feature_quality,v_row.point_in_time_validated,to_jsonb(v_row),
        jsonb_build_object(
            'generator','get_live_trajectory_features_v1_1_asof',
            'stadium_capacity_input',p_stadium_capacity,
            'materialization_contract','live-feature-snapshot-store-v1'
        )
    )
    on conflict(ticket_event_id,horizon,as_of_at,feature_version,source_snapshot_id)
    do nothing
    returning id into v_id;

    if v_id is null then
        select id into v_id
        from private.live_trajectory_feature_snapshots_v1
        where ticket_event_id=p_ticket_event_id
          and horizon=p_horizon
          and as_of_at=p_as_of_at
          and feature_version=v_row.feature_version
          and source_snapshot_id=v_row.snapshot_id;
    end if;

    return v_id;
end;
$function$;
