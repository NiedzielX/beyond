-- P9 booking-curve / trajectory-shape readiness v1
--
-- Reports completed independent ticket events whose raw public-inventory path
-- has enough PIT coverage to support canonical curve interpolation without
-- crossing the existing 12h live-trajectory data-gap ceiling.
--
-- This is a data-readiness function only. It does not fit/select a model and
-- does not alter production forecasts.

begin;

create or replace function public.p9_booking_curve_readiness_v1()
returns jsonb
language sql
stable
set search_path to 'public','private'
as $$
with horizons(h) as (
    values (24.0::numeric),(48.0::numeric),(72.0::numeric),(168.0::numeric)
), base as (
    select
        s.ticket_event_id,
        e.club_slug,
        e.kickoff_at,
        s.id as snapshot_id,
        s.captured_at,
        extract(epoch from (e.kickoff_at-s.captured_at))/3600.0 as lead_h
    from public.snapshots s
    join public.ticket_events e on e.id=s.ticket_event_id
    join public.ticket_event_outcomes o on o.ticket_event_id=e.id
    where o.actual_attendance is not null
      and s.available_total is not null
      and s.available_total >= 0
      and s.captured_at < e.kickoff_at
), coverage as (
    select
        ticket_event_id,
        max(lead_h) as max_lead_h,
        min(lead_h) as min_lead_h
    from base
    group by ticket_event_id
), window_rows as (
    select
        b.ticket_event_id,
        b.club_slug,
        h.h,
        b.captured_at,
        b.lead_h,
        lag(b.captured_at) over (
            partition by b.ticket_event_id,h.h
            order by b.captured_at
        ) as prev_at
    from base b
    cross join horizons h
    where b.lead_h between 6.0 and h.h
), window_agg as (
    select
        ticket_event_id,
        min(club_slug) as club_slug,
        h,
        count(*)::integer as snapshot_count,
        max(
            extract(epoch from (captured_at-prev_at))/3600.0
        ) filter(where prev_at is not null) as max_gap_h
    from window_rows
    group by ticket_event_id,h
), evaluated as (
    select
        h.h,
        c.ticket_event_id,
        e.club_slug,
        coalesce(w.snapshot_count,0) as snapshot_count,
        w.max_gap_h,
        c.max_lead_h,
        c.min_lead_h,
        (
            c.max_lead_h >= h.h
            and c.min_lead_h <= 6.0
            and coalesce(w.snapshot_count,0) >= 3
            and coalesce(w.max_gap_h,999.0) <= 12.0
        ) as is_ready
    from horizons h
    cross join coverage c
    join public.ticket_events e on e.id=c.ticket_event_id
    left join window_agg w
      on w.ticket_event_id=c.ticket_event_id and w.h=h.h
), by_horizon as (
    select
        h,
        count(*) filter(where is_ready)::integer as ready_events,
        count(distinct club_slug) filter(where is_ready)::integer as ready_clubs,
        coalesce(
            jsonb_agg(ticket_event_id order by ticket_event_id) filter(where is_ready),
            '[]'::jsonb
        ) as ready_event_ids,
        min(snapshot_count) filter(where is_ready) as minimum_snapshots_ready,
        max(max_gap_h) filter(where is_ready) as worst_gap_hours_ready
    from evaluated
    group by h
)
select jsonb_build_object(
    'version','p9-booking-curve-readiness-v1',
    'checked_at',now(),
    'production_change',false,
    'independent_unit','ticket_event',
    'inventory_interpretation','demand_proxy_not_confirmed_sales',
    'max_interpolation_gap_hours',12.0,
    'minimum_window_snapshots',3,
    'endpoint_rule','event history begins at or before window start and reaches 6h or later',
    'completed_outcome_events',(select count(*) from coverage),
    'horizons',coalesce((
        select jsonb_object_agg(
            trim(to_char(h,'FM999999990D0')),
            jsonb_build_object(
                'ready_events',ready_events,
                'ready_clubs',ready_clubs,
                'ready_event_ids',ready_event_ids,
                'minimum_snapshots_ready',minimum_snapshots_ready,
                'worst_gap_hours_ready',worst_gap_hours_ready,
                'representation_ready',ready_events >= 3,
                'learnable_model_precommitted',false
            )
            order by h
        ) from by_horizon
    ),'{}'::jsonb),
    'full_168h_model_status',case
        when (select ready_events from by_horizon where h=168.0) >= 9 then 'COVERAGE_GATE_REACHED_MODEL_STILL_REQUIRES_PRECOMMIT'
        else 'DATA_BOUND'
    end,
    'model_results_opened',false
);
$$;

revoke all on function public.p9_booking_curve_readiness_v1() from public,anon,authenticated;
grant execute on function public.p9_booking_curve_readiness_v1() to service_role;

commit;
