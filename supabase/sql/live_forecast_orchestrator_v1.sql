-- Live Forecast Orchestrator v1
-- Production migration applied to project adchzwqboeekhokapxqi on 2026-10-15.
-- Forward-only, service-role-only orchestration. No model retraining occurs here.

create table if not exists private.live_forecast_orchestrator_runs_v1 (
    id bigserial primary key,
    requested_at timestamptz not null,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    checkpoint_rows_materialized integer not null default 0,
    active_event_count integer not null default 0,
    processed_event_count integer not null default 0,
    missing_prior_count integer not null default 0,
    skipped_event_count integer not null default 0,
    error_event_count integer not null default 0,
    result jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

comment on table private.live_forecast_orchestrator_runs_v1 is
'Forward-only audit log for Live Forecast Orchestrator v1. One row per scheduler invocation; event-level outcomes are stored in result.';

grant usage on schema private to service_role;
grant select, insert, update on private.live_forecast_orchestrator_runs_v1 to service_role;
grant usage, select on sequence private.live_forecast_orchestrator_runs_v1_id_seq to service_role;
grant select, insert, update on private.trajectory_gap_observations_v1 to service_role;
grant usage, select on sequence private.trajectory_gap_observations_v1_id_seq to service_role;
grant select on private.trajectory_gap_reference_pool_v1 to service_role;
grant execute on function private.materialize_due_live_trajectory_checkpoints_v1() to service_role;

create or replace function public.run_live_forecast_orchestrator_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_run_id bigint;
    v_checkpoint_count integer := 0;
    v_active_count integer := 0;
    v_processed_count integer := 0;
    v_missing_prior_count integer := 0;
    v_skipped_count integer := 0;
    v_error_count integer := 0;
    v_results jsonb := '[]'::jsonb;
    v_event record;
    v_prior record;
    v_live record;
    v_gap_id bigint;
    v_forecast_id bigint;
    v_reference_event_count integer := 0;
    v_reference_club_count integer := 0;
    v_expected_progress numeric;
    v_q25 numeric;
    v_q75 numeric;
    v_expected_v24 numeric;
    v_expected_acc numeric;
    v_observed_progress numeric;
    v_observed_acc numeric;
    v_level_gap numeric;
    v_velocity_gap numeric;
    v_acceleration_gap numeric;
    v_status text;
    v_confidence text;
    v_reason text;
    v_reference_horizon text;
    v_observation jsonb;
    v_result jsonb;
begin
    if p_requested_at is null then
        raise exception 'p_requested_at is required';
    end if;
    if abs(extract(epoch from (now() - p_requested_at))) > 900 then
        raise exception 'Live Forecast Orchestrator v1 is forward-only; p_requested_at must be within 15 minutes of now()';
    end if;

    insert into private.live_forecast_orchestrator_runs_v1(requested_at)
    values (p_requested_at)
    returning id into v_run_id;

    begin
        v_checkpoint_count := private.materialize_due_live_trajectory_checkpoints_v1();
    exception when others then
        v_checkpoint_count := 0;
        v_results := v_results || jsonb_build_array(jsonb_build_object(
            'scope','checkpoint_materialization','status','error','error',sqlerrm
        ));
    end;

    for v_event in
        select
            e.id as ticket_event_id,
            e.club_slug,
            e.home_team,
            e.away_team,
            e.competition,
            e.kickoff_at,
            s.id as snapshot_id,
            s.captured_at as snapshot_captured_at
        from public.ticket_events e
        left join lateral (
            select s1.id, s1.captured_at
            from public.snapshots s1
            where s1.ticket_event_id = e.id
              and s1.captured_at <= p_requested_at
            order by s1.captured_at desc, s1.id desc
            limit 1
        ) s on true
        where e.kickoff_at > p_requested_at
          and e.kickoff_at <= p_requested_at + interval '31 days'
        order by e.kickoff_at, e.id
    loop
        v_active_count := v_active_count + 1;
        begin
            if v_event.snapshot_id is null then
                v_skipped_count := v_skipped_count + 1;
                v_results := v_results || jsonb_build_array(jsonb_build_object(
                    'ticket_event_id',v_event.ticket_event_id,
                    'status','missing_snapshot',
                    'kickoff_at',v_event.kickoff_at
                ));
                continue;
            end if;

            select * into v_prior
            from public.get_structural_prior_v1(v_event.ticket_event_id, v_event.snapshot_captured_at)
            limit 1;

            if v_prior.status is distinct from 'ready' then
                if v_prior.status = 'missing_prior' then
                    v_missing_prior_count := v_missing_prior_count + 1;
                else
                    v_skipped_count := v_skipped_count + 1;
                end if;
                v_results := v_results || jsonb_build_array(jsonb_build_object(
                    'ticket_event_id',v_event.ticket_event_id,
                    'status',coalesce(v_prior.status,'prior_unavailable'),
                    'kickoff_at',v_event.kickoff_at,
                    'snapshot_id',v_event.snapshot_id
                ));
                continue;
            end if;

            select * into v_live
            from public.get_live_trajectory_features_v1_1_asof(
                v_event.ticket_event_id,
                v_event.snapshot_captured_at,
                v_prior.stadium_capacity
            )
            limit 1;

            if not found then
                v_skipped_count := v_skipped_count + 1;
                v_results := v_results || jsonb_build_array(jsonb_build_object(
                    'ticket_event_id',v_event.ticket_event_id,
                    'status','live_features_missing',
                    'snapshot_id',v_event.snapshot_id
                ));
                continue;
            end if;

            v_observed_progress := case
                when v_live.available_index is null then null
                else 1.0 - v_live.available_index
            end;
            v_observed_acc := case
                when v_live.velocity_6h_pct_of_first_per_hour is null
                  or v_live.velocity_24h_pct_of_first_per_hour is null then null
                else v_live.velocity_6h_pct_of_first_per_hour - v_live.velocity_24h_pct_of_first_per_hour
            end;
            v_reference_event_count := 0;
            v_reference_club_count := 0;
            v_expected_progress := null;
            v_q25 := null;
            v_q75 := null;
            v_expected_v24 := null;
            v_expected_acc := null;
            v_level_gap := null;
            v_velocity_gap := null;
            v_acceleration_gap := null;
            v_reference_horizon := v_live.checkpoint_label;
            v_status := 'INSUFFICIENT_SIGNAL';
            v_confidence := 'NONE';

            if not coalesce(v_prior.point_in_time_validated,false) then
                v_reason := 'structural_prior_not_pit_validated';
            elsif not coalesce(v_live.point_in_time_validated,false) then
                v_reason := 'live_feature_not_pit_validated';
            elsif v_live.signal_readiness is distinct from 'ready' then
                v_reason := 'live_signal_' || coalesce(v_live.signal_readiness,'unknown');
            elsif not coalesce(v_live.checkpoint_ready,false) or v_live.checkpoint_label is null then
                v_reason := 'outside_reference_checkpoint_window';
            elsif v_live.available_index is null then
                v_reason := 'missing_available_index';
            else
                select
                    count(distinct r.ticket_event_id)::integer,
                    count(distinct r.club_slug)::integer,
                    percentile_cont(0.25) within group(order by (1.0 - r.available_index)),
                    percentile_cont(0.50) within group(order by (1.0 - r.available_index)),
                    percentile_cont(0.75) within group(order by (1.0 - r.available_index)),
                    percentile_cont(0.50) within group(order by r.velocity_24h_pct_of_first_per_hour),
                    percentile_cont(0.50) within group(order by (r.velocity_6h_pct_of_first_per_hour - r.velocity_24h_pct_of_first_per_hour))
                into
                    v_reference_event_count,
                    v_reference_club_count,
                    v_q25,
                    v_expected_progress,
                    v_q75,
                    v_expected_v24,
                    v_expected_acc
                from private.trajectory_gap_reference_pool_v1 r
                where r.ticket_event_id <> v_event.ticket_event_id
                  and r.horizon = v_live.checkpoint_label
                  and r.feature_version = v_live.feature_version
                  and r.training_eligible
                  and r.point_in_time_validated
                  and r.signal_readiness = 'ready'
                  and r.available_index is not null
                  and r.as_of_at <= v_live.as_of_at;

                if coalesce(v_reference_event_count,0) < 3 or coalesce(v_reference_club_count,0) < 2
                   or v_expected_progress is null or v_q25 is null or v_q75 is null then
                    v_reason := 'insufficient_reference_pool';
                else
                    v_level_gap := v_observed_progress - v_expected_progress;
                    if v_live.velocity_24h_pct_of_first_per_hour is not null and v_expected_v24 is not null then
                        v_velocity_gap := v_live.velocity_24h_pct_of_first_per_hour - v_expected_v24;
                    end if;
                    if v_observed_acc is not null and v_expected_acc is not null then
                        v_acceleration_gap := v_observed_acc - v_expected_acc;
                    end if;

                    if v_observed_progress < v_q25 then
                        v_status := 'UNDERPERFORMING';
                        v_reason := 'progress_below_reference_iqr';
                    elsif v_observed_progress > v_q75 then
                        v_status := 'OUTPERFORMING';
                        v_reason := 'progress_above_reference_iqr';
                    else
                        v_status := 'ON_TRACK';
                        v_reason := 'progress_within_reference_iqr';
                    end if;

                    v_confidence := case
                        when v_reference_event_count >= 10 and v_reference_club_count >= 5 then 'HIGH'
                        when v_reference_event_count >= 5 and v_reference_club_count >= 3 then 'MEDIUM'
                        else 'LOW'
                    end;
                end if;
            end if;

            insert into private.trajectory_gap_observations_v1 (
                ticket_event_id,source_prior_id,source_snapshot_id,as_of_at,kickoff_at,
                structural_prior_horizon,reference_horizon,trajectory_gap_version,live_feature_version,
                reference_mode,prior_mapping_mode,structural_prior_p50,
                reference_event_count,reference_club_count,
                observed_progress,expected_progress,expected_progress_q25,expected_progress_q75,level_gap,
                observed_velocity_24h,expected_velocity_24h,velocity_gap,
                observed_acceleration_6h_vs_24h,expected_acceleration_6h_vs_24h,acceleration_gap,
                trajectory_status,confidence,reason_code,signal_readiness,feature_quality,
                point_in_time_validated,metadata
            ) values (
                v_event.ticket_event_id,v_prior.source_prior_id,v_live.snapshot_id,v_live.as_of_at,v_live.kickoff_at,
                v_prior.horizon,v_reference_horizon,'trajectory-gap-v1',v_live.feature_version,
                'empirical_inventory_progress_by_horizon_v1','anchor_only_no_inventory_to_attendance_conversion',v_prior.p50,
                coalesce(v_reference_event_count,0),coalesce(v_reference_club_count,0),
                v_observed_progress,v_expected_progress,v_q25,v_q75,v_level_gap,
                v_live.velocity_24h_pct_of_first_per_hour,v_expected_v24,v_velocity_gap,
                v_observed_acc,v_expected_acc,v_acceleration_gap,
                v_status,v_confidence,v_reason,v_live.signal_readiness,v_live.feature_quality,
                coalesce(v_prior.point_in_time_validated,false) and coalesce(v_live.point_in_time_validated,false),
                jsonb_build_object(
                    'orchestrator_version','live-forecast-orchestrator-v1',
                    'run_id',v_run_id,
                    'requested_at',p_requested_at,
                    'hours_to_kickoff',v_live.hours_to_kickoff,
                    'checkpoint_ready',v_live.checkpoint_ready,
                    'checkpoint_label',v_live.checkpoint_label,
                    'available_total',v_live.available_total,
                    'first_available_total',v_live.first_available_total,
                    'net_removed_since_first',v_live.net_removed_since_first,
                    'raw_snapshot_count',v_live.raw_snapshot_count,
                    'clean_snapshot_count',v_live.clean_snapshot_count,
                    'excluded_anomaly_count',v_live.excluded_anomaly_count,
                    'data_gap_detected',v_live.data_gap_detected,
                    'reference_min_events',3,
                    'reference_min_clubs',2
                )
            )
            on conflict (ticket_event_id,as_of_at,trajectory_gap_version)
            do update set
                source_prior_id=excluded.source_prior_id,
                source_snapshot_id=excluded.source_snapshot_id,
                structural_prior_horizon=excluded.structural_prior_horizon,
                reference_horizon=excluded.reference_horizon,
                live_feature_version=excluded.live_feature_version,
                structural_prior_p50=excluded.structural_prior_p50,
                reference_event_count=excluded.reference_event_count,
                reference_club_count=excluded.reference_club_count,
                observed_progress=excluded.observed_progress,
                expected_progress=excluded.expected_progress,
                expected_progress_q25=excluded.expected_progress_q25,
                expected_progress_q75=excluded.expected_progress_q75,
                level_gap=excluded.level_gap,
                observed_velocity_24h=excluded.observed_velocity_24h,
                expected_velocity_24h=excluded.expected_velocity_24h,
                velocity_gap=excluded.velocity_gap,
                observed_acceleration_6h_vs_24h=excluded.observed_acceleration_6h_vs_24h,
                expected_acceleration_6h_vs_24h=excluded.expected_acceleration_6h_vs_24h,
                acceleration_gap=excluded.acceleration_gap,
                trajectory_status=excluded.trajectory_status,
                confidence=excluded.confidence,
                reason_code=excluded.reason_code,
                signal_readiness=excluded.signal_readiness,
                feature_quality=excluded.feature_quality,
                point_in_time_validated=excluded.point_in_time_validated,
                metadata=excluded.metadata
            returning id into v_gap_id;

            v_observation := jsonb_strip_nulls(jsonb_build_object(
                'ticket_event_id',v_event.ticket_event_id,
                'source_snapshot_id',v_live.snapshot_id,
                'forecast_generated_at',v_live.as_of_at,
                'source_snapshot_captured_at',v_live.snapshot_captured_at,
                'hours_to_kickoff',v_live.hours_to_kickoff,
                'days_to_match',v_live.days_to_kickoff,
                'horizon',v_prior.horizon,
                'model_version','beyond-demand-engine-v1-structural-prior-shadow',
                'historical_model',v_prior.model_spec_id,
                'historical_p50',round(v_prior.p50)::integer,
                'live_adjustment',0,
                'final_p50',round(v_prior.p50)::integer,
                'forecast_status','shadow',
                'correction_status','shadow',
                'signal_readiness',v_live.signal_readiness,
                'live_available_total',v_live.available_total,
                'live_first_available_total',v_live.first_available_total,
                'live_available_index',v_live.available_index,
                'live_net_removed_since_first',v_live.net_removed_since_first,
                'live_net_removed_since_previous',v_live.net_removed_since_previous,
                'live_velocity_since_previous',v_live.velocity_since_previous,
                'live_net_removed_6h',v_live.net_removed_6h,
                'live_velocity_6h',v_live.velocity_6h,
                'live_net_removed_24h',v_live.net_removed_24h,
                'live_velocity_24h',v_live.velocity_24h,
                'live_acceleration_6h_vs_24h',v_live.acceleration_6h_vs_24h,
                'live_raw_snapshot_count',v_live.raw_snapshot_count,
                'live_clean_snapshot_count',v_live.clean_snapshot_count,
                'live_excluded_anomaly_count',v_live.excluded_anomaly_count,
                'payload',jsonb_build_object(
                    'engine',jsonb_build_object(
                        'engine_version','beyond-demand-engine-v1-structural-prior-shadow',
                        'mode','shadow',
                        'orchestrator_version','live-forecast-orchestrator-v1',
                        'orchestrator_run_id',v_run_id,
                        'source_prior_id',v_prior.source_prior_id,
                        'structural_prior_horizon',v_prior.horizon,
                        'historical_model_name',v_prior.model_spec_id,
                        'historical_model_version',v_prior.model_spec_id,
                        'historical_feature_set_version',v_prior.feature_contract,
                        'historical_interval_method','not_yet_calibrated',
                        'live_feature_version',v_live.feature_version,
                        'correction_version','live-correction-noop-v2-trajectory-gap-observed',
                        'correction_reason','No validated live correction promoted; genuine Structural Prior P50 preserved.'
                    ),
                    'trajectory_gap',jsonb_build_object(
                        'source_observation_id',v_gap_id,
                        'version','trajectory-gap-v1',
                        'reference_horizon',v_reference_horizon,
                        'reference_event_count',coalesce(v_reference_event_count,0),
                        'reference_club_count',coalesce(v_reference_club_count,0),
                        'observed_progress',v_observed_progress,
                        'expected_progress',v_expected_progress,
                        'level_gap',v_level_gap,
                        'status',v_status,
                        'confidence',v_confidence,
                        'reason_code',v_reason
                    ),
                    'structural_prior',jsonb_build_object(
                        'source_prior_id',v_prior.source_prior_id,
                        'horizon',v_prior.horizon,
                        'model_spec_id',v_prior.model_spec_id,
                        'feature_contract',v_prior.feature_contract,
                        'p50',v_prior.p50,
                        'stadium_capacity',v_prior.stadium_capacity,
                        'expected_occupancy',v_prior.expected_occupancy,
                        'point_in_time_validated',v_prior.point_in_time_validated
                    ),
                    'live',jsonb_build_object(
                        'feature_version',v_live.feature_version,
                        'inventory_interpretation',v_live.inventory_interpretation,
                        'feature_quality',v_live.feature_quality,
                        'point_in_time_validated',v_live.point_in_time_validated,
                        'checkpoint_label',v_live.checkpoint_label,
                        'checkpoint_ready',v_live.checkpoint_ready,
                        'data_gap_detected',v_live.data_gap_detected
                    )
                )
            ));

            v_forecast_id := public.insert_demand_engine_shadow_forecast_v1(v_observation);
            v_processed_count := v_processed_count + 1;
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event.ticket_event_id,
                'status','processed',
                'snapshot_id',v_live.snapshot_id,
                'prior_id',v_prior.source_prior_id,
                'trajectory_gap_id',v_gap_id,
                'trajectory_status',v_status,
                'trajectory_reason',v_reason,
                'trajectory_confidence',v_confidence,
                'forecast_observation_id',v_forecast_id,
                'p50',round(v_prior.p50)::integer
            ));
        exception when others then
            v_error_count := v_error_count + 1;
            v_results := v_results || jsonb_build_array(jsonb_build_object(
                'ticket_event_id',v_event.ticket_event_id,
                'status','error',
                'error',sqlerrm
            ));
        end;
    end loop;

    v_result := jsonb_build_object(
        'ok',v_error_count = 0,
        'version','live-forecast-orchestrator-v1',
        'run_id',v_run_id,
        'requested_at',p_requested_at,
        'checkpoint_rows_materialized',v_checkpoint_count,
        'active_event_count',v_active_count,
        'processed_event_count',v_processed_count,
        'missing_prior_count',v_missing_prior_count,
        'skipped_event_count',v_skipped_count,
        'error_event_count',v_error_count,
        'events',v_results
    );

    update private.live_forecast_orchestrator_runs_v1
    set completed_at=now(),
        checkpoint_rows_materialized=v_checkpoint_count,
        active_event_count=v_active_count,
        processed_event_count=v_processed_count,
        missing_prior_count=v_missing_prior_count,
        skipped_event_count=v_skipped_count,
        error_event_count=v_error_count,
        result=v_result
    where id=v_run_id;

    return v_result;
exception when others then
    if v_run_id is not null then
        update private.live_forecast_orchestrator_runs_v1
        set completed_at=now(),
            error_event_count=error_event_count+1,
            result=jsonb_build_object(
                'ok',false,
                'version','live-forecast-orchestrator-v1',
                'run_id',v_run_id,
                'fatal_error',sqlerrm
            )
        where id=v_run_id;
    end if;
    raise;
end;
$function$;

revoke all on function public.run_live_forecast_orchestrator_v1(timestamptz) from public;
revoke all on function public.run_live_forecast_orchestrator_v1(timestamptz) from anon;
revoke all on function public.run_live_forecast_orchestrator_v1(timestamptz) from authenticated;
grant execute on function public.run_live_forecast_orchestrator_v1(timestamptz) to service_role;

comment on function public.run_live_forecast_orchestrator_v1(timestamptz) is
'Forward-only, idempotent Live Forecast Orchestrator v1. Materializes due canonical checkpoints, resolves genuine Structural Prior, computes live-trajectory-v1.1 and trajectory-gap-v1, persists shadow revisions, and fails closed on missing prior/signal.';
