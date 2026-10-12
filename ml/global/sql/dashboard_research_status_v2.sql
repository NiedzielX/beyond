-- Browser-safe dashboard projections for Beyond research status.
-- Keeps leakage-safe cross-club v2 readiness separate from the independent
-- 20-outcome learned-correction evidence gate, and surfaces weather as a
-- research-only side track unless validation shows stable positive uplift.

create or replace function public.get_dashboard_research_readiness_v2()
returns table (
  crossclub_study_events bigint,
  crossclub_study_clubs bigint,
  strict_study_rows bigint,
  crossclub_gate_met boolean,
  crossclub_event_target integer,
  crossclub_club_target integer,
  independent_outcome_events_total bigint,
  outcome_clubs_total bigint,
  learned_correction_gate_met boolean,
  learned_correction_event_target integer,
  generated_at timestamptz
)
language sql
stable
security definer
set search_path = public
as $$
  with study as (
    select
      count(distinct ticket_event_id)::bigint as events,
      count(distinct club_slug)::bigint as clubs,
      count(*)::bigint as rows
    from public.crossclub_live_signal_study_rows_v2
  ), outcomes as (
    select
      count(*)::bigint as events,
      count(distinct e.club_slug)::bigint as clubs
    from public.ticket_event_outcomes o
    join public.ticket_events e on e.id = o.ticket_event_id
  )
  select
    study.events,
    study.clubs,
    study.rows,
    study.events >= 8 and study.clubs >= 3,
    8,
    3,
    outcomes.events,
    outcomes.clubs,
    outcomes.events >= 20,
    20,
    now()
  from study cross join outcomes;
$$;

create or replace view public.dashboard_research_readiness_v2 as
select * from public.get_dashboard_research_readiness_v2();

create or replace function public.get_dashboard_weather_research_v1()
returns table (
  historical_study_version text,
  historical_sample_size integer,
  historical_seasons integer,
  baseline_mae numeric,
  loocv_weather_mae numeric,
  loocv_uplift numeric,
  loso_weather_mae numeric,
  loso_uplift numeric,
  historical_signal_status text,
  prospective_weather_events bigint,
  prospective_weather_rows bigint,
  prospective_t24_outcome_pairs bigint,
  generated_at timestamptz
)
language sql
stable
security definer
set search_path = public
as $$
  with latest_study as (
    select *
    from public.weather_signal_study_reports
    order by generated_at desc
    limit 1
  ), prospective as (
    select
      count(distinct ticket_event_id)::bigint as events,
      count(*)::bigint as rows
    from public.weather_forecast_observations
    where capture_kind = 'prospective'
  ), t24_pairs as (
    select count(distinct e.id)::bigint as pairs
    from public.ticket_event_outcomes o
    join public.ticket_events e on e.id = o.ticket_event_id
    where exists (
      select 1
      from public.weather_forecast_observations w
      where w.ticket_event_id = e.id
        and w.capture_kind = 'prospective'
        and w.captured_at <= e.kickoff_at
        and w.hours_to_kickoff >= 24
    )
  )
  select
    s.study_version,
    s.sample_size,
    s.seasons,
    s.baseline_mae,
    s.loocv_weather_mae,
    s.loocv_uplift,
    s.loso_weather_mae,
    s.loso_uplift,
    case
      when s.loocv_uplift > 0 and s.loso_uplift > 0 then 'candidate_signal'
      else 'research_only_no_uplift'
    end,
    p.events,
    p.rows,
    t.pairs,
    now()
  from latest_study s
  cross join prospective p
  cross join t24_pairs t;
$$;

create or replace view public.dashboard_weather_research_v1 as
select * from public.get_dashboard_weather_research_v1();

revoke all on function public.get_dashboard_research_readiness_v2() from public;
revoke all on function public.get_dashboard_weather_research_v1() from public;
grant execute on function public.get_dashboard_research_readiness_v2() to anon, authenticated, service_role;
grant execute on function public.get_dashboard_weather_research_v1() to anon, authenticated, service_role;

revoke all on public.dashboard_research_readiness_v2 from public;
revoke all on public.dashboard_weather_research_v1 from public;
grant select on public.dashboard_research_readiness_v2 to anon, authenticated, service_role;
grant select on public.dashboard_weather_research_v1 to anon, authenticated, service_role;
