-- Resolver contract fix for C1 v8 prospective shadow input.
-- get_structural_prior_v1 exposes feature_contract/generated_at, not artifact_version.

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
            p.feature_contract as structural_prior_feature_contract,
            p.generated_at as structural_prior_generated_at,
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
         and s.captured_at>a.kickoff_at-interval '24 hours'
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
          and r.bucket_6h between 0 and 3
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
                    'feature_contract',a.structural_prior_feature_contract,
                    'generated_at',a.structural_prior_generated_at,
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
