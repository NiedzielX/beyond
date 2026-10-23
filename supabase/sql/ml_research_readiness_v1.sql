-- Canonical ML research readiness snapshot v1
--
-- Objective pre-outcome / pre-model-selection triggers for remaining data-bound loops.
--
-- Hard triggers:
--   P7 Long168 research start: 9 independent events with >72h observations.
--   Long72 prospective review: first genuine scored event.
--   P4a previous-home-spacing research start: >=9 labeled READY events and >=3 distinct spacing values.
--   P4 next-opponent inspection: first READY attractiveness row.
--
-- This function changes no forecast and performs no model selection.

begin;

create or replace function public.ml_research_readiness_v1()
returns jsonb
language plpgsql
stable
set search_path to 'public','private'
as $function$
declare
    v_long168 jsonb;
    v_p4_fixture_research jsonb;
    v_events_gt_72 integer := 0;
    v_rows_gt_72 integer := 0;
    v_long72_predictions integer := 0;
    v_long72_scored integer := 0;
    v_fixture_rows integer := 0;
    v_fixture_ready integer := 0;
    v_opponent_rows integer := 0;
    v_opponent_ready integer := 0;
    v_latest_as_of timestamptz;
    v_p4_prev_start boolean := false;
begin
    select public.export_d2_long_horizon_168_rows_v1() into v_long168;
    select public.p4_fixture_context_readiness_v1() into v_p4_fixture_research;

    with rows as (
        select jsonb_array_elements(coalesce(v_long168->'liveRows','[]'::jsonb)) as r
    )
    select
        count(distinct (r->>'ticket_event_id')) filter (
            where (r->>'hours_to_kickoff')::numeric > 72
        )::integer,
        count(*) filter (
            where (r->>'hours_to_kickoff')::numeric > 72
        )::integer
    into v_events_gt_72, v_rows_gt_72
    from rows;

    select count(*)::integer, max(as_of_at)
    into v_long72_predictions, v_latest_as_of
    from private.d2_long72_forward_predictions_v1
    where coalesce((metadata->>'manual_first_checkpoint')::boolean,false)=false;

    select count(*)::integer into v_long72_scored
    from private.d2_long72_forward_event_scores_v1;

    select
        count(*)::integer,
        count(*) filter (where context_status='READY')::integer
    into v_fixture_rows, v_fixture_ready
    from private.d2_long72_fixture_context_v1;

    select
        count(*)::integer,
        count(*) filter (where status='READY')::integer
    into v_opponent_rows, v_opponent_ready
    from private.d2_long72_next_opponent_attractiveness_v1;

    v_p4_prev_start := coalesce(
        (v_p4_fixture_research#>>'{previous_home_spacing,research_start_trigger}')::boolean,
        false
    );

    return jsonb_build_object(
        'version','ml-research-readiness-v1',
        'checked_at',now(),
        'production_change',false,
        'long72',jsonb_build_object(
            'reproducible_prediction_rows',v_long72_predictions,
            'scored_genuine_events',v_long72_scored,
            'latest_as_of_at',v_latest_as_of,
            'first_scored_event_trigger',v_long72_scored >= 1
        ),
        'p4_fixture_context',jsonb_build_object(
            'sidecar_rows',v_fixture_rows,
            'ready_rows',v_fixture_ready,
            'first_ready_trigger',v_fixture_ready >= 1
        ),
        'p4_fixture_context_research',v_p4_fixture_research,
        'p4_next_opponent',jsonb_build_object(
            'sidecar_rows',v_opponent_rows,
            'ready_rows',v_opponent_ready,
            'first_ready_trigger',v_opponent_ready >= 1
        ),
        'p7_long168',jsonb_build_object(
            'independent_events_gt_72h',v_events_gt_72,
            'rows_gt_72h',v_rows_gt_72,
            'research_start_threshold',9,
            'research_start_trigger',v_events_gt_72 >= 9
        ),
        'next_actions',jsonb_build_array(
            jsonb_build_object(
                'gate','P7_LONG168_START',
                'ready',v_events_gt_72 >= 9,
                'action','freeze exact event/as_of identities before any Long168 model selection'
            ),
            jsonb_build_object(
                'gate','LONG72_FIRST_GENUINE_SCORE',
                'ready',v_long72_scored >= 1,
                'action','inspect first prospective score; do not retune frozen package'
            ),
            jsonb_build_object(
                'gate','P4_PREVIOUS_HOME_SPACING_START',
                'ready',v_p4_prev_start,
                'action','run precommitted event-level previous-home-spacing ablation against Long72 pre-live T3+B2 anchor'
            ),
            jsonb_build_object(
                'gate','P4_NEXT_OPPONENT_FIRST_READY',
                'ready',v_opponent_ready >= 1,
                'action','inspect feature availability/variance before predeclaring separate sparse-feature ablation'
            )
        )
    );
end;
$function$;

revoke all on function public.ml_research_readiness_v1() from public,anon,authenticated;
grant execute on function public.ml_research_readiness_v1() to service_role;

commit;
