-- d2 Long72 Forward Score Quality v1
--
-- Preserve the two manual bootstrap predictions as immutable audit evidence,
-- but exclude them from the official prospective scorecard. Only rows produced
-- by the reproducible frozen forward pipeline are scoreable.

begin;

create or replace function public.score_d2_long72_forward_completed_events_v1(
    p_requested_at timestamptz default now()
)
returns jsonb
language plpgsql
security invoker
set search_path = public, private
as $function$
declare
    v_package constant text := 'd2-long72-stage2-p2-observation-maturity-2026-10-21-v1';
    v_inserted integer := 0;
    v_event_count integer := 0;
    v_anchor_mae numeric;
    v_p2_mae numeric;
    v_p2_bias numeric;
    v_improvement_rate numeric;
    v_worst_degradation numeric;
    v_anchor_24_48 numeric;
    v_p2_24_48 numeric;
    v_anchor_48_72 numeric;
    v_p2_48_72 numeric;
begin
    if p_requested_at is null
       or abs(extract(epoch from (now()-p_requested_at)))>900 then
        raise exception 'Long72 scorer requested_at must be within 15 minutes of now()';
    end if;

    with joined as (
        select
            p.*,
            o.actual_attendance,
            o.confirmed_at as outcome_confirmed_at,
            coalesce(o.updated_at,o.confirmed_at,o.created_at) as outcome_version_at,
            row_number() over (
                partition by p.ticket_event_id,p.package_id,p.bucket_6h
                order by p.as_of_at desc,p.id desc
            ) as bucket_rn
        from private.d2_long72_forward_predictions_v1 p
        join public.ticket_event_outcomes o
          on o.ticket_event_id=p.ticket_event_id
         and o.actual_attendance is not null
        where p.package_id=v_package
          and coalesce((p.metadata->>'manual_first_checkpoint')::boolean,false)=false
    ), representative as (
        select *
        from joined
        where bucket_rn=1
    ), event_agg as (
        select
            ticket_event_id,
            package_id,
            actual_attendance,
            max(outcome_confirmed_at) as outcome_confirmed_at,
            max(outcome_version_at) as outcome_version_at,
            count(*)::integer as representative_bucket_count,
            avg(abs(anchor_p50-actual_attendance)) as anchor_mae,
            avg(abs(stage1_inventory_p50-actual_attendance)) as stage1_mae,
            avg(abs(final_p50-actual_attendance)) as p2_mae,
            avg(final_p50-actual_attendance) as p2_bias,
            avg(abs(final_p50-actual_attendance))
              filter (where hours_to_kickoff>24 and hours_to_kickoff<=48) as mae_24_48h,
            avg(abs(anchor_p50-actual_attendance))
              filter (where hours_to_kickoff>24 and hours_to_kickoff<=48) as anchor_mae_24_48h,
            avg(abs(final_p50-actual_attendance))
              filter (where hours_to_kickoff>48 and hours_to_kickoff<=72) as mae_48_72h,
            avg(abs(anchor_p50-actual_attendance))
              filter (where hours_to_kickoff>48 and hours_to_kickoff<=72) as anchor_mae_48_72h,
            max(greatest(
                0,
                abs(final_p50-actual_attendance)-abs(anchor_p50-actual_attendance)
            )) as worst_row_degradation
        from representative
        group by ticket_event_id,package_id,actual_attendance
    ), inserted as (
        insert into private.d2_long72_forward_event_scores_v1(
            ticket_event_id,package_id,actual_attendance,outcome_confirmed_at,outcome_version_at,
            representative_bucket_count,anchor_mae,stage1_mae,p2_mae,p2_bias,
            mae_24_48h,anchor_mae_24_48h,mae_48_72h,anchor_mae_48_72h,
            event_improves_anchor,worst_row_degradation,metadata
        )
        select
            a.ticket_event_id,a.package_id,a.actual_attendance,a.outcome_confirmed_at,a.outcome_version_at,
            a.representative_bucket_count,a.anchor_mae,a.stage1_mae,a.p2_mae,a.p2_bias,
            a.mae_24_48h,a.anchor_mae_24_48h,a.mae_48_72h,a.anchor_mae_48_72h,
            a.p2_mae<a.anchor_mae,a.worst_row_degradation,
            jsonb_build_object(
                'scoring_version','d2-long72-forward-scoring-v1',
                'scoring_requested_at',p_requested_at,
                'representative_rule','latest reproducible pre-outcome forecast per event x 6h bucket',
                'manual_bootstrap_rows_excluded',true,
                'prospective_only',true
            )
        from event_agg a
        on conflict(ticket_event_id,package_id,outcome_version_at) do nothing
        returning id
    )
    select count(*)::integer into v_inserted from inserted;

    with latest_scores as (
        select distinct on (ticket_event_id,package_id)
            *
        from private.d2_long72_forward_event_scores_v1
        where package_id=v_package
        order by ticket_event_id,package_id,outcome_version_at desc,id desc
    )
    select
        count(*)::integer,
        avg(anchor_mae),
        avg(p2_mae),
        avg(p2_bias),
        avg(case when event_improves_anchor then 1.0 else 0.0 end),
        max(greatest(0,p2_mae-anchor_mae)),
        avg(anchor_mae_24_48h) filter (where anchor_mae_24_48h is not null),
        avg(mae_24_48h) filter (where mae_24_48h is not null),
        avg(anchor_mae_48_72h) filter (where anchor_mae_48_72h is not null),
        avg(mae_48_72h) filter (where mae_48_72h is not null)
    into
        v_event_count,v_anchor_mae,v_p2_mae,v_p2_bias,v_improvement_rate,v_worst_degradation,
        v_anchor_24_48,v_p2_24_48,v_anchor_48_72,v_p2_48_72
    from latest_scores;

    return jsonb_build_object(
        'version','d2-long72-forward-scoring-v1',
        'package_id',v_package,
        'inserted_score_count',v_inserted,
        'prospective_scored_event_count',coalesce(v_event_count,0),
        'quality_rule',jsonb_build_object(
            'manual_bootstrap_rows_scoreable',false,
            'representative_rule','latest reproducible pre-outcome forecast per event x 6h bucket'
        ),
        'overall_24_72h',jsonb_build_object(
            'anchor_event_balanced_mae',v_anchor_mae,
            'package_event_balanced_mae',v_p2_mae,
            'mae_improvement',case when v_anchor_mae is null or v_p2_mae is null then null else v_anchor_mae-v_p2_mae end,
            'relative_mae_improvement',case when coalesce(v_anchor_mae,0)>0 then (v_anchor_mae-v_p2_mae)/v_anchor_mae else null end,
            'event_balanced_bias',v_p2_bias,
            'event_improvement_rate',v_improvement_rate,
            'worst_event_degradation',v_worst_degradation
        ),
        'band_24_48h',jsonb_build_object(
            'anchor_mae',v_anchor_24_48,
            'package_mae',v_p2_24_48,
            'mae_improvement',case when v_anchor_24_48 is null or v_p2_24_48 is null then null else v_anchor_24_48-v_p2_24_48 end
        ),
        'band_48_72h',jsonb_build_object(
            'anchor_mae',v_anchor_48_72,
            'package_mae',v_p2_48_72,
            'mae_improvement',case when v_anchor_48_72 is null or v_p2_48_72 is null then null else v_anchor_48_72-v_p2_48_72 end
        ),
        'production_change',false
    );
end;
$function$;

revoke all on function public.score_d2_long72_forward_completed_events_v1(timestamptz)
    from public, anon, authenticated;
grant execute on function public.score_d2_long72_forward_completed_events_v1(timestamptz)
    to service_role;

commit;
