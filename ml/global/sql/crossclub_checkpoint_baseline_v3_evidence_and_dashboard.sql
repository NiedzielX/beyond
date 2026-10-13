-- Cross-club Baseline v3 follow-up.
-- Distinguishes retrospective historical-fact reconstruction from prospective
-- system point-in-time evidence, exposes only safe dashboard columns, and adds
-- a same-event challenger comparison against the incumbent baseline.

alter table public.crossclub_checkpoint_baselines_v3
  add column if not exists evidence_mode text;

alter table public.crossclub_checkpoint_baselines_v3
  drop constraint if exists crossclub_checkpoint_baselines_v3_evidence_mode_check;

alter table public.crossclub_checkpoint_baselines_v3
  add constraint crossclub_checkpoint_baselines_v3_evidence_mode_check
  check (evidence_mode is null or evidence_mode in (
    'retrospective_historical_fact_reconstruction',
    'prospective_system_point_in_time'
  ));

update public.crossclub_checkpoint_baselines_v3
set evidence_mode=case
  when evaluation_mode='prospective' then 'prospective_system_point_in_time'
  else 'retrospective_historical_fact_reconstruction'
end
where evidence_mode is null;

create or replace view public.ml_home_attendance_history_availability_v3 as
with combined as (
  select h.club_slug,h.kickoff_at,h.actual_attendance,
    coalesce(h.competition_key,lower(regexp_replace(h.competition,'[^a-zA-Z0-9]+','_','g'))) as competition_key,
    coalesce(h.source_observed_at,h.created_at) as system_available_at,
    h.source_name,h.source_url,1 as source_priority
  from public.ml_match_history h
  union all
  select e.club_slug,e.kickoff_at,o.actual_attendance,'ekstraklasa'::text,
    coalesce(o.confirmed_at,o.created_at) as system_available_at,
    o.source_name,o.source_url,2 as source_priority
  from public.ticket_event_outcomes o
  join public.ticket_events e on e.id=o.ticket_event_id
  where lower(e.competition) like '%ekstraklasa%'
), dedup as (
  select distinct on (club_slug,kickoff_at)
    club_slug,kickoff_at,actual_attendance,competition_key,system_available_at,source_name,source_url
  from combined
  where competition_key='ekstraklasa'
  order by club_slug,kickoff_at,source_priority desc
)
select * from dedup;

revoke all on public.ml_home_attendance_history_availability_v3 from anon,authenticated;
grant select on public.ml_home_attendance_history_availability_v3 to service_role;

create or replace function public.refresh_crossclub_checkpoint_baselines_v3()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare v_rows integer := 0;
begin
  with computed as (
    select s.id snapshot_id,s.ticket_event_id,s.checkpoint_code,s.checkpoint_at,s.capture_mode,
      e.club_slug,public.match_competition_key_v1(e.competition) competition_key,
      count(h.*)::int history_count,min(h.kickoff_at) history_first_at,max(h.kickoff_at) history_last_at,
      avg(h.actual_attendance)::numeric baseline_mean,
      percentile_cont(0.5) within group (order by h.actual_attendance)::numeric baseline_median,
      case when public.match_competition_key_v1(e.competition)<>'ekstraklasa' then 'unsupported_competition'
           when count(h.*)<3 then 'insufficient_history' else 'ready' end baseline_status,
      case when s.capture_mode='prospective' then 'prospective_system_point_in_time'
           else 'retrospective_historical_fact_reconstruction' end evidence_mode
    from public.event_context_snapshots_v1 s
    join public.ticket_events e on e.id=s.ticket_event_id
    left join public.ml_home_attendance_history_availability_v3 h
      on h.club_slug=e.club_slug
     and h.competition_key='ekstraklasa'
     and h.kickoff_at<s.checkpoint_at
     and (s.capture_mode<>'prospective' or h.system_available_at<=s.checkpoint_at)
    group by s.id,s.ticket_event_id,s.checkpoint_code,s.checkpoint_at,s.capture_mode,e.club_slug,e.competition
  )
  insert into public.crossclub_checkpoint_baselines_v3(
    snapshot_id,ticket_event_id,checkpoint_code,checkpoint_at,club_slug,competition_key,
    history_count,history_first_at,history_last_at,baseline_mean,baseline_p50,baseline_model,
    baseline_status,evaluation_mode,source_cutoff_at,evidence_mode,metadata
  )
  select c.snapshot_id,c.ticket_event_id,c.checkpoint_code,c.checkpoint_at,c.club_slug,c.competition_key,
    c.history_count,c.history_first_at,c.history_last_at,c.baseline_mean,
    case when c.baseline_status='ready' then round(c.baseline_median)::int else null end,
    'club_trailing_home_median_v3',c.baseline_status,c.capture_mode,c.checkpoint_at,c.evidence_mode,
    jsonb_build_object(
      'minimum_history_count',3,'competition_scope','ekstraklasa_home_only',
      'statistic','median_verified_home_attendance',
      'history_rule',case when c.evidence_mode='prospective_system_point_in_time'
        then 'verified home attendance with kickoff and system availability before checkpoint_at'
        else 'historical home attendance from matches completed before checkpoint_at; reconstructed after migration' end,
      'production_impact','none_research_baseline_only'
    )
  from computed c
  on conflict (snapshot_id) do nothing;

  get diagnostics v_rows=row_count;

  insert into public.context_ablation_predictions_v1(
    snapshot_id,variant_key,predicted_p50,prediction_method,model_version,metadata
  )
  select b.snapshot_id,'baseline',b.baseline_p50,'crossclub_checkpoint_baseline_fallback',b.baseline_model,
    jsonb_build_object('crossclub_baseline_id',b.id,'history_count',b.history_count,
      'history_first_at',b.history_first_at,'history_last_at',b.history_last_at,
      'source_cutoff_at',b.source_cutoff_at,'evaluation_mode',b.evaluation_mode,
      'evidence_mode',b.evidence_mode,'fallback_only',true)
  from public.crossclub_checkpoint_baselines_v3 b
  left join public.context_ablation_predictions_v1 existing
    on existing.snapshot_id=b.snapshot_id and existing.variant_key='baseline'
  where b.baseline_status='ready' and b.baseline_p50 is not null and existing.id is null
  on conflict (snapshot_id,variant_key) do nothing;

  return v_rows;
end;
$$;

revoke all on function public.refresh_crossclub_checkpoint_baselines_v3() from public,anon,authenticated;
grant execute on function public.refresh_crossclub_checkpoint_baselines_v3() to service_role;

create or replace view public.dashboard_crossclub_baseline_v3
with (security_invoker=true)
as
select b.snapshot_id,b.ticket_event_id,e.home_team,e.away_team,e.kickoff_at,
  b.checkpoint_code,b.checkpoint_at,b.club_slug,b.history_count,b.history_first_at,b.history_last_at,
  b.baseline_p50,b.baseline_status,b.baseline_model,b.evaluation_mode,
  case when p.prediction_method='snapshot_historical_baseline' then 'incumbent_engine_baseline'
       when p.prediction_method='crossclub_checkpoint_baseline_fallback' then 'crossclub_fallback'
       else 'no_baseline_prediction' end selected_baseline_source,
  p.predicted_p50 selected_baseline_p50,(o.actual_attendance is not null) has_outcome,b.evidence_mode
from public.crossclub_checkpoint_baselines_v3 b
join public.ticket_events e on e.id=b.ticket_event_id
left join public.context_ablation_predictions_v1 p on p.snapshot_id=b.snapshot_id and p.variant_key='baseline'
left join public.ticket_event_outcomes o on o.ticket_event_id=b.ticket_event_id;

revoke all on public.dashboard_crossclub_baseline_v3 from public;
grant select on public.dashboard_crossclub_baseline_v3 to anon,authenticated,service_role;

drop policy if exists dashboard_crossclub_baseline_read on public.crossclub_checkpoint_baselines_v3;
create policy dashboard_crossclub_baseline_read
on public.crossclub_checkpoint_baselines_v3
for select to anon,authenticated using (true);

grant select (
  snapshot_id,ticket_event_id,checkpoint_code,checkpoint_at,club_slug,history_count,
  history_first_at,history_last_at,baseline_p50,baseline_model,baseline_status,evaluation_mode,evidence_mode
) on public.crossclub_checkpoint_baselines_v3 to anon,authenticated;

grant select (snapshot_id,variant_key,predicted_p50,prediction_method)
on public.context_ablation_predictions_v1 to anon,authenticated;

drop view if exists public.dashboard_crossclub_baseline_comparison_v3;
create view public.dashboard_crossclub_baseline_comparison_v3
with (security_invoker=true)
as
select d.checkpoint_code,count(*)::int event_count,
  round(avg(abs(d.selected_baseline_p50-o.actual_attendance)),1) incumbent_mae,
  round(avg(abs(d.baseline_p50-o.actual_attendance)),1) challenger_mae,
  round(avg(abs(d.selected_baseline_p50-o.actual_attendance))-avg(abs(d.baseline_p50-o.actual_attendance)),1) challenger_mae_uplift,
  round(avg(d.selected_baseline_p50-o.actual_attendance),1) incumbent_bias,
  round(avg(d.baseline_p50-o.actual_attendance),1) challenger_bias,
  'research_challenger_only'::text decision_status
from public.dashboard_crossclub_baseline_v3 d
join public.ticket_event_outcomes o on o.ticket_event_id=d.ticket_event_id
where d.selected_baseline_source='incumbent_engine_baseline'
  and d.has_outcome and d.baseline_status='ready'
  and d.baseline_p50 is not null and d.selected_baseline_p50 is not null
group by d.checkpoint_code;

revoke all on public.dashboard_crossclub_baseline_comparison_v3 from public;
grant select on public.dashboard_crossclub_baseline_comparison_v3 to anon,authenticated,service_role;
