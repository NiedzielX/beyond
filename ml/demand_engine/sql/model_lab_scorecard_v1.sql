-- Beyond Model Lab v1 — strict canonical-horizon scorecard
--
-- Critical protocol rules:
-- - canonical horizon is derived from hours_to_kickoff, NOT legacy stored horizon labels;
-- - one nearest pre-checkpoint forecast per model/event/horizon/mode;
-- - post-checkpoint rows are never fallback candidates;
-- - shadow and production are separated;
-- - live uplift is historical MAE - final MAE.

create or replace function public.get_model_lab_scorecard_v1()
returns table(
    model_version text,
    forecast_mode text,
    horizon text,
    independent_matches bigint,
    mae numeric,
    mape_pct numeric,
    wape_pct numeric,
    bias numeric,
    within_5_pct numeric,
    within_10_pct numeric,
    interval_coverage_pct numeric,
    mean_interval_width numeric,
    historical_mae numeric,
    final_mae numeric,
    live_uplift_mae numeric
)
language sql
stable
security invoker
set search_path = public
as $$
with horizons(label,target_hours,tolerance_hours,ord) as (
    values
        ('T-30'::text, 720.0::double precision, 240.0::double precision, 1),
        ('T-14', 336.0, 96.0, 2),
        ('T-7', 168.0, 48.0, 3),
        ('T-3', 72.0, 24.0, 4),
        ('T-24h', 24.0, 12.0, 5)
),
eligible as (
    select
        fo.*,
        o.actual_attendance,
        h.label as canonical_horizon,
        h.target_hours,
        h.ord,
        case when fo.forecast_status = 'shadow' then 'shadow' else 'production' end as forecast_mode
    from public.forecast_observations fo
    join public.ticket_event_outcomes o on o.ticket_event_id = fo.ticket_event_id
    cross join horizons h
    where o.actual_attendance is not null
      and fo.final_p50 is not null
      and fo.hours_to_kickoff is not null
      and fo.hours_to_kickoff >= h.target_hours
      and fo.hours_to_kickoff <= h.target_hours + h.tolerance_hours
),
strict_candidates as (
    select
        e.*,
        row_number() over (
            partition by e.model_version, e.ticket_event_id, e.canonical_horizon, e.forecast_mode
            order by
                (e.hours_to_kickoff - e.target_hours) asc,
                e.forecast_generated_at desc,
                e.id desc
        ) as rn
    from eligible e
),
selected as (
    select * from strict_candidates where rn = 1
),
metric_rows as (
    select
        model_version,
        forecast_mode,
        canonical_horizon,
        ord,
        ticket_event_id,
        actual_attendance::numeric as actual,
        historical_p50::numeric as historical_p50,
        final_p50::numeric as final_p50,
        final_p10::numeric as final_p10,
        final_p90::numeric as final_p90,
        abs(final_p50::numeric - actual_attendance::numeric) as final_ae,
        case when historical_p50 is not null
            then abs(historical_p50::numeric - actual_attendance::numeric)
        end as historical_ae,
        abs(final_p50::numeric - actual_attendance::numeric)
            / nullif(actual_attendance::numeric, 0) * 100.0 as ape,
        (final_p50::numeric - actual_attendance::numeric) as signed_error
    from selected
)
select
    model_version,
    forecast_mode,
    canonical_horizon as horizon,
    count(distinct ticket_event_id)::bigint as independent_matches,
    round(avg(final_ae), 2) as mae,
    round(avg(ape), 2) as mape_pct,
    round(sum(final_ae) / nullif(sum(actual), 0) * 100.0, 2) as wape_pct,
    round(avg(signed_error), 2) as bias,
    round(avg((ape <= 5.0)::int) * 100.0, 2) as within_5_pct,
    round(avg((ape <= 10.0)::int) * 100.0, 2) as within_10_pct,
    round(
        avg(
            case
                when final_p10 is not null and final_p90 is not null
                then (actual between final_p10 and final_p90)::int
                else null
            end
        ) * 100.0,
        2
    ) as interval_coverage_pct,
    round(
        avg(
            case when final_p10 is not null and final_p90 is not null
                then final_p90 - final_p10
            end
        ),
        2
    ) as mean_interval_width,
    round(avg(historical_ae), 2) as historical_mae,
    round(avg(final_ae), 2) as final_mae,
    round(avg(historical_ae) - avg(final_ae), 2) as live_uplift_mae
from metric_rows
group by model_version, forecast_mode, canonical_horizon, ord
order by ord, forecast_mode, model_version;
$$;

-- Production permissions:
-- revoke all on function public.get_model_lab_scorecard_v1()
--   from public, anon, authenticated;
-- grant execute on function public.get_model_lab_scorecard_v1()
--   to service_role;
