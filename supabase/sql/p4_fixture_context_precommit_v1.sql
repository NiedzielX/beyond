-- P4a fixture-context research precommit v1
--
-- Independent unit: ticket_event.
-- Input selection: first READY fixture-context row per reproducible Long72 event.
-- Primary feature: previous_home_match_days.
-- Research start: >=9 labeled events AND >=3 distinct labeled spacing values.
-- Inputs and labels are exported separately so identities/features can be frozen
-- before target values are opened.

begin;

create or replace function public.p4_fixture_context_readiness_v1()
returns jsonb
language sql
stable
set search_path to 'public','private'
as $$
with ready_rows as (
    select
        c.ticket_event_id,
        c.forward_prediction_id,
        c.forecast_as_of_at,
        c.context_payload,
        row_number() over (
            partition by c.ticket_event_id
            order by c.forecast_as_of_at asc, c.id asc
        ) as ready_rank
    from private.d2_long72_fixture_context_v1 c
    join private.d2_long72_forward_predictions_v1 p on p.id=c.forward_prediction_id
    where c.context_status='READY'
      and coalesce((p.metadata->>'manual_first_checkpoint')::boolean,false)=false
), first_ready as (
    select
        r.*,
        nullif(r.context_payload->>'previous_home_match_days','')::numeric as previous_home_match_days,
        nullif(r.context_payload->>'next_home_match_days','')::numeric as next_home_match_days,
        nullif(r.context_payload->>'team_fixture_density_next_7d','')::numeric as team_density_7d,
        nullif(r.context_payload->>'team_fixture_density_next_14d','')::numeric as team_density_14d,
        nullif(r.context_payload->>'team_fixture_density_next_30d','')::numeric as team_density_30d,
        nullif(r.context_payload->>'home_fixture_density_next_7d','')::numeric as home_density_7d,
        nullif(r.context_payload->>'home_fixture_density_next_14d','')::numeric as home_density_14d,
        nullif(r.context_payload->>'home_fixture_density_next_30d','')::numeric as home_density_30d,
        exists(select 1 from private.d2_long72_forward_event_scores_v1 s where s.ticket_event_id=r.ticket_event_id) as has_genuine_label
    from ready_rows r where r.ready_rank=1
), agg as (
    select
        count(*)::integer as ready_events,
        count(*) filter(where has_genuine_label)::integer as labeled_ready_events,
        count(*) filter(where previous_home_match_days is not null)::integer as prev_nonnull_events,
        count(distinct previous_home_match_days)::integer as prev_distinct_values,
        count(*) filter(where has_genuine_label and previous_home_match_days is not null)::integer as prev_labeled_events,
        count(distinct previous_home_match_days) filter(where has_genuine_label and previous_home_match_days is not null)::integer as prev_labeled_distinct_values,
        min(previous_home_match_days) as prev_min_days,
        max(previous_home_match_days) as prev_max_days,
        count(*) filter(where next_home_match_days is not null)::integer as next_nonnull_events,
        count(distinct next_home_match_days)::integer as next_distinct_values,
        count(*) filter(where has_genuine_label and next_home_match_days is not null)::integer as next_labeled_events,
        count(distinct team_density_7d)::integer as team_7d_distinct_values,
        count(distinct team_density_14d)::integer as team_14d_distinct_values,
        count(distinct team_density_30d)::integer as team_30d_distinct_values,
        count(distinct home_density_7d)::integer as home_7d_distinct_values,
        count(distinct home_density_14d)::integer as home_14d_distinct_values,
        count(distinct home_density_30d)::integer as home_30d_distinct_values,
        coalesce(jsonb_agg(ticket_event_id order by ticket_event_id),'[]'::jsonb) as ready_event_ids
    from first_ready
)
select jsonb_build_object(
    'version','p4-fixture-context-readiness-v1',
    'checked_at',now(),
    'production_change',false,
    'independent_unit','ticket_event',
    'event_selection','first READY fixture-context row per reproducible Long72 event',
    'ready_events',a.ready_events,
    'labeled_ready_events',a.labeled_ready_events,
    'ready_event_ids',a.ready_event_ids,
    'previous_home_spacing',jsonb_build_object(
        'feature','previous_home_match_days',
        'status','PRECOMMITTED_PRIMARY_P4A_V1',
        'nonnull_ready_events',a.prev_nonnull_events,
        'distinct_values_ready',a.prev_distinct_values,
        'min_days_ready',a.prev_min_days,
        'max_days_ready',a.prev_max_days,
        'labeled_nonnull_events',a.prev_labeled_events,
        'distinct_values_labeled',a.prev_labeled_distinct_values,
        'research_start_threshold_events',9,
        'minimum_distinct_values',3,
        'threshold_source','existing frozen d2 Stage-1 development event count; start threshold only',
        'research_start_trigger',(a.prev_labeled_events>=9 and a.prev_labeled_distinct_values>=3)
    ),
    'next_home_spacing',jsonb_build_object(
        'feature','next_home_match_days',
        'status','SEPARATE_SPARSE_FEATURE_NOT_IN_P4A_V1',
        'nonnull_ready_events',a.next_nonnull_events,
        'distinct_values_ready',a.next_distinct_values,
        'labeled_nonnull_events',a.next_labeled_events,
        'missing_is_zero',false
    ),
    'fixture_density',jsonb_build_object(
        'status','INACTIVE_UNTIL_REAL_VARIANCE',
        'team_7d_distinct_values',a.team_7d_distinct_values,
        'team_14d_distinct_values',a.team_14d_distinct_values,
        'team_30d_distinct_values',a.team_30d_distinct_values,
        'home_7d_distinct_values',a.home_7d_distinct_values,
        'home_14d_distinct_values',a.home_14d_distinct_values,
        'home_30d_distinct_values',a.home_30d_distinct_values,
        'minimum_distinct_values_to_activate',2
    ),
    'model_results_opened',false,
    'target_values_used_for_feature_selection',false
) from agg a;
$$;

create or replace function public.export_p4_fixture_context_inputs_v1()
returns jsonb
language sql
stable
set search_path to 'public','private'
as $$
with ranked as (
    select
        c.id as context_id,c.ticket_event_id,c.forward_prediction_id,c.forecast_as_of_at,c.schedule_batch_id,c.context_payload,
        p.source_prior_id,p.kickoff_at,p.stadium_capacity,p.structural_t3_p50,p.b2_prior_home_matches,
        p.b2_ewma_residual_fraction,p.b2_correction_seats,p.anchor_p50,
        row_number() over(partition by c.ticket_event_id order by c.forecast_as_of_at asc,c.id asc) as ready_rank
    from private.d2_long72_fixture_context_v1 c
    join private.d2_long72_forward_predictions_v1 p on p.id=c.forward_prediction_id
    where c.context_status='READY'
      and coalesce((p.metadata->>'manual_first_checkpoint')::boolean,false)=false
), first_ready as (select * from ranked where ready_rank=1), rows as (
    select jsonb_build_object(
        'ticket_event_id',ticket_event_id,'context_id',context_id,'forward_prediction_id',forward_prediction_id,
        'source_prior_id',source_prior_id,'forecast_as_of_at',forecast_as_of_at,'kickoff_at',kickoff_at,
        'schedule_batch_id',schedule_batch_id,'stadium_capacity',stadium_capacity,'structural_t3_p50',structural_t3_p50,
        'b2_prior_home_matches',b2_prior_home_matches,'b2_ewma_residual_fraction',b2_ewma_residual_fraction,
        'b2_correction_seats',b2_correction_seats,'anchor_p50',anchor_p50,
        'home_team_canonical',context_payload->>'home_team_canonical','away_team_canonical',context_payload->>'away_team_canonical',
        'previous_home_match_days',nullif(context_payload->>'previous_home_match_days','')::numeric,
        'previous_home_opponent_canonical',context_payload->>'previous_home_opponent_canonical',
        'next_home_match_days',nullif(context_payload->>'next_home_match_days','')::numeric,
        'next_home_opponent_canonical',context_payload->>'next_home_opponent_canonical',
        'team_fixture_density_next_7d',nullif(context_payload->>'team_fixture_density_next_7d','')::numeric,
        'team_fixture_density_next_14d',nullif(context_payload->>'team_fixture_density_next_14d','')::numeric,
        'team_fixture_density_next_30d',nullif(context_payload->>'team_fixture_density_next_30d','')::numeric,
        'home_fixture_density_next_7d',nullif(context_payload->>'home_fixture_density_next_7d','')::numeric,
        'home_fixture_density_next_14d',nullif(context_payload->>'home_fixture_density_next_14d','')::numeric,
        'home_fixture_density_next_30d',nullif(context_payload->>'home_fixture_density_next_30d','')::numeric
    ) row from first_ready
)
select jsonb_build_object(
    'version','p4-fixture-context-inputs-v1','independentUnit','ticket_event',
    'selectionRule','first READY fixture-context row per reproducible Long72 event',
    'anchorDefinition','frozen Long72 pre-live T3 Structural Prior plus frozen B2 current-season correction',
    'primaryFeature','previous_home_match_days',
    'inactiveFeatures',jsonb_build_array('next_home_match_days','team_fixture_density_next_7d','team_fixture_density_next_14d','team_fixture_density_next_30d','home_fixture_density_next_7d','home_fixture_density_next_14d','home_fixture_density_next_30d'),
    'targetFieldsIncluded',false,'labelsIncluded',false,
    'eventCount',(select count(*) from first_ready),
    'events',coalesce((select jsonb_agg(row order by (row->>'ticket_event_id')::bigint) from rows),'[]'::jsonb)
);
$$;

create or replace function public.export_p4_fixture_context_labels_v1()
returns jsonb language sql stable set search_path to 'public','private' as $$
with labels as (
    select ticket_event_id,actual_attendance,outcome_confirmed_at,outcome_version_at,scored_at,package_id
    from private.d2_long72_forward_event_scores_v1
    where package_id='d2-long72-stage2-p2-observation-maturity-2026-10-21-v1'
)
select jsonb_build_object(
    'version','p4-fixture-context-labels-v1','independentUnit','ticket_event','eventCount',(select count(*) from labels),
    'labels',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',ticket_event_id,'actual_attendance',actual_attendance,
        'outcome_confirmed_at',outcome_confirmed_at,'outcome_version_at',outcome_version_at,
        'scored_at',scored_at,'package_id',package_id
    ) order by ticket_event_id) from labels),'[]'::jsonb)
);
$$;

revoke all on function public.p4_fixture_context_readiness_v1() from public,anon,authenticated;
revoke all on function public.export_p4_fixture_context_inputs_v1() from public,anon,authenticated;
revoke all on function public.export_p4_fixture_context_labels_v1() from public,anon,authenticated;
grant execute on function public.p4_fixture_context_readiness_v1() to service_role;
grant execute on function public.export_p4_fixture_context_inputs_v1() to service_role;
grant execute on function public.export_p4_fixture_context_labels_v1() to service_role;

commit;
