-- P9a booking-curve freeze/export v1
--
-- Purpose:
--   * provide a target-free T-24/T-48 representation export;
--   * make post-cutoff target snapshots impossible to receive in target payloads;
--   * export one flat historical reference catalog instead of duplicating full
--     trajectories for every target;
--   * let the freeze harness construct strict prior-only reference pools using
--     `reference kickoff < target_as_of_at` and self-event exclusion;
--   * expose only genuinely persisted-before-cutoff incumbent rows for lineage audit;
--   * keep attendance labels in a separate RPC opened only after freeze.
--
-- This file does not train/select a model and does not change production.

begin;

create or replace function public.export_p9a_booking_curve_inputs_v1(
    p_cutoff_hours integer default 24
)
returns jsonb
language plpgsql
stable
security invoker
set search_path to 'public','private'
as $function$
declare
    v_cutoff integer := p_cutoff_hours;
begin
    if v_cutoff not in (24,48) then
        raise exception 'P9a v1 cutoff must be 24 or 48 hours';
    end if;

    return (
        with candidate_targets as (
            select
                e.id as ticket_event_id,
                e.club_slug,
                e.home_team,
                e.away_team,
                e.competition,
                e.kickoff_at,
                e.kickoff_at - make_interval(hours => v_cutoff) as target_as_of_at
            from public.ticket_events e
            where e.kickoff_at < now()
              and exists (
                  select 1
                  from public.snapshots s
                  where s.ticket_event_id=e.id
                    and s.available_total is not null
                    and s.available_total >= 0
                    and s.captured_at < e.kickoff_at
                    and s.captured_at <= e.kickoff_at - make_interval(hours => v_cutoff)
              )
        ), target_payload as (
            select
                t.*,
                coalesce((
                    select jsonb_agg(jsonb_build_object(
                        'snapshot_id',s.id,
                        'captured_at',s.captured_at,
                        'available_total',s.available_total
                    ) order by s.captured_at,s.id)
                    from public.snapshots s
                    where s.ticket_event_id=t.ticket_event_id
                      and s.available_total is not null
                      and s.available_total >= 0
                      and s.captured_at < t.kickoff_at
                      and s.captured_at <= t.target_as_of_at
                ),'[]'::jsonb) as target_snapshots,
                coalesce((
                    select jsonb_agg(row_data order by (row_data->>'source')::text,(row_data->>'as_of_at')::timestamptz)
                    from (
                        select jsonb_build_object(
                            'source','structural_prior_forecasts_v1',
                            'row_id',sp.id,
                            'as_of_at',sp.target_as_of_at,
                            'persisted_at',sp.created_at,
                            'p50',sp.p50,
                            'model_spec_id',sp.model_spec_id,
                            'point_in_time_validated',sp.point_in_time_validated
                        ) as row_data
                        from private.structural_prior_forecasts_v1 sp
                        where sp.ticket_event_id=t.ticket_event_id
                          and sp.target_as_of_at <= t.target_as_of_at
                          and sp.created_at <= t.target_as_of_at
                        union all
                        select jsonb_build_object(
                            'source','d2_long72_forward_predictions_v1',
                            'row_id',d.id,
                            'as_of_at',d.as_of_at,
                            'persisted_at',d.created_at,
                            'p50',d.anchor_p50,
                            'model_spec_id',d.package_id,
                            'point_in_time_validated',true
                        ) as row_data
                        from private.d2_long72_forward_predictions_v1 d
                        where d.ticket_event_id=t.ticket_event_id
                          and d.as_of_at <= t.target_as_of_at
                          and d.created_at <= t.target_as_of_at
                    ) incumbents
                ),'[]'::jsonb) as persisted_incumbents
            from candidate_targets t
        ), reference_catalog as (
            select
                r.id as ticket_event_id,
                r.club_slug,
                r.home_team,
                r.away_team,
                r.kickoff_at,
                coalesce((
                    select jsonb_agg(jsonb_build_object(
                        'snapshot_id',rs.id,
                        'captured_at',rs.captured_at,
                        'available_total',rs.available_total
                    ) order by rs.captured_at,rs.id)
                    from public.snapshots rs
                    where rs.ticket_event_id=r.id
                      and rs.available_total is not null
                      and rs.available_total >= 0
                      and rs.captured_at < r.kickoff_at
                ),'[]'::jsonb) as snapshots
            from public.ticket_events r
            where r.kickoff_at < now()
              and exists (
                  select 1
                  from public.snapshots rs0
                  where rs0.ticket_event_id=r.id
                    and rs0.available_total is not null
                    and rs0.available_total >= 0
                    and rs0.captured_at < r.kickoff_at
              )
        )
        select jsonb_build_object(
            'version','p9a-booking-curve-inputs-v1',
            'generated_at',now(),
            'cutoff_hours',v_cutoff,
            'canonical_hours',jsonb_build_array(168,144,120,96,72,60,48,36,24,18,12,6),
            'max_interpolation_gap_hours',12,
            'minimum_overlap_points',3,
            'inventory_interpretation','demand_proxy_not_confirmed_sales',
            'independent_unit','ticket_event',
            'target_values_used',false,
            'post_cutoff_target_snapshots_exported',false,
            'reference_catalog_semantics','catalog may contain events after an individual target cutoff; freeze harness must use only reference kickoff < target_as_of_at and exclude self',
            'incumbent_rule','only rows persisted at or before target_as_of_at are exposed',
            'production_change',false,
            'targets',coalesce((
                select jsonb_agg(jsonb_build_object(
                    'ticket_event_id',p.ticket_event_id,
                    'club_slug',p.club_slug,
                    'home_team',p.home_team,
                    'away_team',p.away_team,
                    'competition',p.competition,
                    'kickoff_at',p.kickoff_at,
                    'target_as_of_at',p.target_as_of_at,
                    'target_snapshots',p.target_snapshots,
                    'persisted_incumbents',p.persisted_incumbents
                ) order by p.kickoff_at,p.ticket_event_id)
                from target_payload p
            ),'[]'::jsonb),
            'reference_catalog',coalesce((
                select jsonb_agg(jsonb_build_object(
                    'ticket_event_id',r.ticket_event_id,
                    'club_slug',r.club_slug,
                    'home_team',r.home_team,
                    'away_team',r.away_team,
                    'kickoff_at',r.kickoff_at,
                    'snapshots',r.snapshots
                ) order by r.kickoff_at,r.ticket_event_id)
                from reference_catalog r
            ),'[]'::jsonb)
        )
    );
end;
$function$;

revoke all on function public.export_p9a_booking_curve_inputs_v1(integer) from public,anon,authenticated;
grant execute on function public.export_p9a_booking_curve_inputs_v1(integer) to service_role;

create or replace function public.export_p9a_booking_curve_labels_v1(
    p_ticket_event_ids bigint[]
)
returns jsonb
language sql
stable
security invoker
set search_path to 'public'
as $function$
select jsonb_build_object(
    'version','p9a-booking-curve-labels-v1',
    'generated_at',now(),
    'production_change',false,
    'labels',coalesce((
        select jsonb_agg(jsonb_build_object(
            'ticket_event_id',o.ticket_event_id,
            'actual_attendance',o.actual_attendance,
            'attendance_definition',o.attendance_definition,
            'source_name',o.source_name,
            'confirmed_at',o.confirmed_at
        ) order by o.ticket_event_id)
        from public.ticket_event_outcomes o
        where o.ticket_event_id=any(p_ticket_event_ids)
          and o.actual_attendance is not null
    ),'[]'::jsonb)
);
$function$;

revoke all on function public.export_p9a_booking_curve_labels_v1(bigint[]) from public,anon,authenticated;
grant execute on function public.export_p9a_booking_curve_labels_v1(bigint[]) to service_role;

commit;
