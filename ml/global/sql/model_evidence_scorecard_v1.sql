-- Beyond Ticketing — Model Evidence Scorecard v1
-- Central governance layer over Context Matrix research categories.
-- Research-prior weights remain hypotheses, not model coefficients.
-- No category is automatically promoted to production P50.

create table if not exists public.model_evidence_scorecard_v1 (
  category_key text primary key,
  sort_order integer not null,
  display_name text not null,
  research_prior_weight_pct numeric(5,2) not null check (research_prior_weight_pct >= 0 and research_prior_weight_pct <= 100),
  decision_status text not null check (decision_status in ('promotable','collecting','rejected','blocked')),
  evidence_signal text not null check (evidence_signal in ('positive','negative','mixed','unproven')),
  primary_protocol text,
  candidate_key text,
  validation_event_count integer,
  validation_club_count integer,
  promotion_evidence_count integer not null default 0,
  promotion_event_target integer not null default 20,
  promotion_club_target integer,
  promotion_progress_pct numeric(6,2) not null default 0,
  incumbent_mae numeric,
  bias_control_mae numeric,
  challenger_mae numeric,
  uplift_vs_incumbent numeric,
  incremental_uplift_vs_bias numeric,
  prospective_event_count integer,
  decision_reason text not null,
  next_action text not null,
  production_impact text not null default 'none_shadow_only',
  source_refreshed_at timestamptz,
  evidence jsonb not null default '{}'::jsonb,
  refreshed_at timestamptz not null default now()
);

alter table public.model_evidence_scorecard_v1 enable row level security;
revoke all on public.model_evidence_scorecard_v1 from anon,authenticated;
grant select on public.model_evidence_scorecard_v1 to anon,authenticated;
grant select,insert,update,delete on public.model_evidence_scorecard_v1 to service_role;

drop policy if exists dashboard_model_evidence_scorecard_read on public.model_evidence_scorecard_v1;
create policy dashboard_model_evidence_scorecard_read
on public.model_evidence_scorecard_v1
for select to anon,authenticated using (true);

create or replace function public.refresh_model_evidence_scorecard_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  t public.ticketing_challenger_dashboard_summary_v1%rowtype;
  sp public.sporting_challenger_dashboard_summary_v1%rowtype;
  mc public.match_context_challenger_dashboard_v1%rowtype;
  hs public.hype_challenger_summary_v1%rowtype;
  hc public.hype_challenger_cv_summary_v1%rowtype;
  w public.weather_signal_study_reports%rowtype;
  v_weather_prospective_events integer := 0;
  v_weather_t24_pairs integer := 0;
  v_rows integer := 0;
begin
  select * into t from public.ticketing_challenger_dashboard_summary_v1
  where protocol='leave_one_club_out' order by refreshed_at desc limit 1;

  select * into sp from public.sporting_challenger_dashboard_summary_v1
  where protocol='leave_one_club_out' order by refreshed_at desc limit 1;

  select * into mc from public.match_context_challenger_dashboard_v1
  where protocol='leave_one_club_out'
  order by case when event_count>=8 and club_count>=5 then 0 else 1 end,
           uplift_vs_ticketing desc nulls last, refreshed_at desc
  limit 1;

  select * into hs from public.hype_challenger_summary_v1 order by refreshed_at desc limit 1;

  select * into hc from public.hype_challenger_cv_summary_v1
  where protocol='leave_one_club_out'
  order by case when candidate_status='positive_research_signal' then 0 else 1 end,
           uplift_vs_ticketing desc nulls last, refreshed_at desc
  limit 1;

  select * into w from public.weather_signal_study_reports order by generated_at desc limit 1;

  select count(distinct ticket_event_id)::int into v_weather_prospective_events
  from public.weather_forecast_observations where capture_kind='prospective';

  select count(distinct e.id)::int into v_weather_t24_pairs
  from public.ticket_event_outcomes o
  join public.ticket_events e on e.id=o.ticket_event_id
  where exists (
    select 1 from public.weather_forecast_observations wf
    where wf.ticket_event_id=e.id
      and wf.capture_kind='prospective'
      and wf.captured_at<=e.kickoff_at
      and wf.hours_to_kickoff>=24
  );

  insert into public.model_evidence_scorecard_v1(
    category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
    primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
    promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
    challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
    decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
  ) values (
    'ticketing',1,'Live Ticketing',45,
    case when t.protocol_status='positive_research_signal' and coalesce(t.event_count,0)>=20 and coalesce(t.club_count,0)>=5 then 'promotable'
         when t.protocol_status='positive_research_signal' then 'collecting'
         when t.protocol_status in ('insufficient_sample','collecting') or t.protocol_status is null then 'collecting'
         else 'rejected' end,
    case when t.protocol_status='positive_research_signal' then 'positive'
         when t.protocol_status='rejected_no_uplift' then 'negative' else 'unproven' end,
    'leave_one_club_out',t.candidate_model,t.event_count,t.club_count,coalesce(t.event_count,0),20,5,
    least(100::numeric,round(100.0*coalesce(t.event_count,0)/20.0,2)),
    t.baseline_mae,t.bias_control_mae,t.challenger_mae,t.uplift_vs_baseline,t.incremental_ticketing_uplift,null,
    case when t.protocol_status='positive_research_signal' and coalesce(t.event_count,0)<20
         then format('Positive leave-one-club-out evidence on %s events / %s clubs, but the 20-event promotion gate is not met.',coalesce(t.event_count,0),coalesce(t.club_count,0))
         when t.protocol_status='positive_research_signal'
         then 'Positive leave-one-club-out evidence and the promotion sample gate is met.'
         else 'Current live-ticketing candidate does not meet promotion criteria.' end,
    case when coalesce(t.event_count,0)<20
         then format('Keep collecting independent completed matches; %s more needed for the v1 promotion gate.',20-coalesce(t.event_count,0))
         else 'Review promotion package, stability by club, bias and operational safeguards before any production activation.' end,
    'shadow_only',t.refreshed_at,
    jsonb_build_object('bias_control_required',true,'gate_basis','independent_completed_events','model_status',(select status from public.ticketing_challenger_models_v1 order by trained_at desc limit 1)),now()
  ) on conflict (category_key) do update set
    sort_order=excluded.sort_order,display_name=excluded.display_name,research_prior_weight_pct=excluded.research_prior_weight_pct,
    decision_status=excluded.decision_status,evidence_signal=excluded.evidence_signal,primary_protocol=excluded.primary_protocol,
    candidate_key=excluded.candidate_key,validation_event_count=excluded.validation_event_count,validation_club_count=excluded.validation_club_count,
    promotion_evidence_count=excluded.promotion_evidence_count,promotion_event_target=excluded.promotion_event_target,
    promotion_club_target=excluded.promotion_club_target,promotion_progress_pct=excluded.promotion_progress_pct,
    incumbent_mae=excluded.incumbent_mae,bias_control_mae=excluded.bias_control_mae,challenger_mae=excluded.challenger_mae,
    uplift_vs_incumbent=excluded.uplift_vs_incumbent,incremental_uplift_vs_bias=excluded.incremental_uplift_vs_bias,
    prospective_event_count=excluded.prospective_event_count,decision_reason=excluded.decision_reason,next_action=excluded.next_action,
    production_impact=excluded.production_impact,source_refreshed_at=excluded.source_refreshed_at,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  insert into public.model_evidence_scorecard_v1(
    category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
    primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
    promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
    challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
    decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
  ) values (
    'sporting',2,'Sporting Context',30,
    case when sp.protocol_status='positive_research_signal' and coalesce(sp.event_count,0)>=20 and coalesce(sp.club_count,0)>=5 then 'promotable'
         when sp.protocol_status='positive_research_signal' then 'collecting'
         when sp.protocol_status='rejected_no_uplift' then 'rejected' else 'collecting' end,
    case when sp.protocol_status='positive_research_signal' then 'positive'
         when sp.protocol_status='rejected_no_uplift' then 'negative' else 'unproven' end,
    'leave_one_club_out',sp.candidate_model,sp.event_count,sp.club_count,coalesce(sp.event_count,0),20,5,
    least(100::numeric,round(100.0*coalesce(sp.event_count,0)/20.0,2)),
    sp.baseline_ticketing_mae,sp.bias_control_mae,sp.challenger_mae,sp.uplift_vs_ticketing,sp.incremental_sporting_uplift,null,
    case when sp.protocol_status='rejected_no_uplift'
         then 'The tested Match Stakes candidate worsens MAE versus Baseline + Ticketing in leave-one-club-out validation.'
         else 'Sporting evidence is not yet sufficient for production promotion.' end,
    case when sp.protocol_status='rejected_no_uplift'
         then 'Do not add Match Stakes to P50. Keep other sporting features separate and require their own leakage-safe ablation before reconsidering the category.'
         else 'Continue independent evidence collection without changing production P50.' end,
    'none_shadow_only',sp.refreshed_at,
    jsonb_build_object('tested_feature','sport.match_stakes','candidate_status',sp.protocol_status,'ablation_prediction_created',false),now()
  ) on conflict (category_key) do update set
    sort_order=excluded.sort_order,display_name=excluded.display_name,research_prior_weight_pct=excluded.research_prior_weight_pct,
    decision_status=excluded.decision_status,evidence_signal=excluded.evidence_signal,primary_protocol=excluded.primary_protocol,
    candidate_key=excluded.candidate_key,validation_event_count=excluded.validation_event_count,validation_club_count=excluded.validation_club_count,
    promotion_evidence_count=excluded.promotion_evidence_count,promotion_event_target=excluded.promotion_event_target,
    promotion_club_target=excluded.promotion_club_target,promotion_progress_pct=excluded.promotion_progress_pct,
    incumbent_mae=excluded.incumbent_mae,bias_control_mae=excluded.bias_control_mae,challenger_mae=excluded.challenger_mae,
    uplift_vs_incumbent=excluded.uplift_vs_incumbent,incremental_uplift_vs_bias=excluded.incremental_uplift_vs_bias,
    prospective_event_count=excluded.prospective_event_count,decision_reason=excluded.decision_reason,next_action=excluded.next_action,
    production_impact=excluded.production_impact,source_refreshed_at=excluded.source_refreshed_at,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  insert into public.model_evidence_scorecard_v1(
    category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
    primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
    promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
    challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
    decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
  ) values (
    'match_context',3,'Match Context',10,
    case when mc.candidate_status='positive_research_signal' and coalesce(mc.event_count,0)>=20 and coalesce(mc.club_count,0)>=5 then 'promotable'
         when mc.candidate_status='positive_research_signal' then 'collecting'
         when mc.candidate_status='rejected_no_uplift' then 'rejected' else 'collecting' end,
    case when mc.candidate_status='positive_research_signal' then 'positive'
         when mc.candidate_status='rejected_no_uplift' then 'negative' else 'unproven' end,
    'leave_one_club_out',mc.feature_key,mc.event_count,mc.club_count,coalesce(mc.event_count,0),20,5,
    least(100::numeric,round(100.0*coalesce(mc.event_count,0)/20.0,2)),
    mc.baseline_ticketing_mae,mc.bias_control_mae,mc.challenger_mae,mc.uplift_vs_ticketing,mc.incremental_match_context_uplift,null,
    case when mc.candidate_status='rejected_no_uplift'
         then format('Best currently testable Match Context candidate (%s) still worsens MAE versus Baseline + Ticketing in leave-one-club-out validation.',coalesce(mc.feature_key,'unknown'))
         else 'No Match Context candidate is currently promotion-ready.' end,
    'Keep rejected timing features out of P50. Test competition stage and historical opponent uplift only when their point-in-time coverage becomes sufficient.',
    'none_shadow_only',mc.refreshed_at,
    jsonb_build_object('selected_feature',mc.feature_key,'selection_rule','best qualifying leave-one-club-out uplift among current candidates','untested_features',(select coalesce(jsonb_agg(feature_key order by feature_key),'[]'::jsonb) from public.match_context_feature_readiness_v1 where readiness_status not in ('tested_rejected_current_candidates'))),now()
  ) on conflict (category_key) do update set
    sort_order=excluded.sort_order,display_name=excluded.display_name,research_prior_weight_pct=excluded.research_prior_weight_pct,
    decision_status=excluded.decision_status,evidence_signal=excluded.evidence_signal,primary_protocol=excluded.primary_protocol,
    candidate_key=excluded.candidate_key,validation_event_count=excluded.validation_event_count,validation_club_count=excluded.validation_club_count,
    promotion_evidence_count=excluded.promotion_evidence_count,promotion_event_target=excluded.promotion_event_target,
    promotion_club_target=excluded.promotion_club_target,promotion_progress_pct=excluded.promotion_progress_pct,
    incumbent_mae=excluded.incumbent_mae,bias_control_mae=excluded.bias_control_mae,challenger_mae=excluded.challenger_mae,
    uplift_vs_incumbent=excluded.uplift_vs_incumbent,incremental_uplift_vs_bias=excluded.incremental_uplift_vs_bias,
    prospective_event_count=excluded.prospective_event_count,decision_reason=excluded.decision_reason,next_action=excluded.next_action,
    production_impact=excluded.production_impact,source_refreshed_at=excluded.source_refreshed_at,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  insert into public.model_evidence_scorecard_v1(
    category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
    primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
    promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
    challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
    decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
  ) values (
    'hype',4,'Attention & Hype',15,
    case when hc.candidate_status='positive_research_signal' and coalesce(hc.event_count,0)>=20 and coalesce(hc.club_count,0)>=5 then 'promotable'
         when hc.candidate_status='no_prospective_uplift' then 'rejected'
         when hs.overall_status ilike 'blocked%' then 'blocked' else 'collecting' end,
    case when hc.candidate_status='positive_research_signal' then 'positive'
         when hc.candidate_status='no_prospective_uplift' then 'negative' else 'unproven' end,
    'leave_one_club_out',coalesce(hc.feature_key,'hype.media_attention'),
    coalesce(hc.event_count,hs.completed_media_eligible_count),coalesce(hc.club_count,hs.completed_media_club_count),
    coalesce(hs.completed_media_eligible_count,0),20,5,
    least(100::numeric,round(100.0*coalesce(hs.completed_media_eligible_count,0)/20.0,2)),
    hc.baseline_ticketing_mae,hc.bias_control_mae,hc.challenger_mae,hc.uplift_vs_ticketing,hc.incremental_hype_uplift,
    hs.prospective_t24_count,
    case when coalesce(hs.completed_media_eligible_count,0)<8
         then format('Prospective-only evidence is still below the testability gate: %s/8 completed eligible T-24h events and %s/5 clubs.',coalesce(hs.completed_media_eligible_count,0),coalesce(hs.completed_media_club_count,0))
         when hc.candidate_status is null then 'The prospective testability gate is met, but no stable cross-club Hype result is available yet.'
         else 'Prospective Hype evidence has been evaluated; see primary validation metrics.' end,
    case when coalesce(hs.completed_media_eligible_count,0)<8 then 'Continue forward-only collection. Do not backfill historical Hype observations.'
         when coalesce(hs.completed_media_eligible_count,0)<20 then 'Run/refresh leakage-safe cross-club evaluation and continue toward the 20-event promotion gate.'
         else 'If cross-club evidence remains positive, review promotion safeguards before any P50 activation.' end,
    'none_shadow_only',hs.refreshed_at,
    jsonb_build_object('testability_event_target',8,'testability_club_target',5,'historical_backfill_allowed',hs.historical_backfill_allowed,'collector_version',hs.collector_version,'collector_nonzero_event_count',hs.collector_nonzero_event_count),now()
  ) on conflict (category_key) do update set
    sort_order=excluded.sort_order,display_name=excluded.display_name,research_prior_weight_pct=excluded.research_prior_weight_pct,
    decision_status=excluded.decision_status,evidence_signal=excluded.evidence_signal,primary_protocol=excluded.primary_protocol,
    candidate_key=excluded.candidate_key,validation_event_count=excluded.validation_event_count,validation_club_count=excluded.validation_club_count,
    promotion_evidence_count=excluded.promotion_evidence_count,promotion_event_target=excluded.promotion_event_target,
    promotion_club_target=excluded.promotion_club_target,promotion_progress_pct=excluded.promotion_progress_pct,
    incumbent_mae=excluded.incumbent_mae,bias_control_mae=excluded.bias_control_mae,challenger_mae=excluded.challenger_mae,
    uplift_vs_incumbent=excluded.uplift_vs_incumbent,incremental_uplift_vs_bias=excluded.incremental_uplift_vs_bias,
    prospective_event_count=excluded.prospective_event_count,decision_reason=excluded.decision_reason,next_action=excluded.next_action,
    production_impact=excluded.production_impact,source_refreshed_at=excluded.source_refreshed_at,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  insert into public.model_evidence_scorecard_v1(
    category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
    primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
    promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
    challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
    decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
  ) values (
    'weather',5,'Weather',0,
    case when coalesce(w.loocv_uplift,0)>0 and coalesce(w.loso_uplift,0)>0 and v_weather_t24_pairs>=20 then 'promotable'
         when coalesce(w.loocv_uplift,0)<=0 or coalesce(w.loso_uplift,0)<=0 then 'rejected' else 'collecting' end,
    case when coalesce(w.loocv_uplift,0)>0 and coalesce(w.loso_uplift,0)>0 then 'positive' else 'negative' end,
    'leave_one_season_out',w.study_version,w.sample_size,null,v_weather_t24_pairs,20,null,
    least(100::numeric,round(100.0*v_weather_t24_pairs/20.0,2)),
    w.baseline_mae,null,w.loso_weather_mae,w.loso_uplift,null,v_weather_prospective_events,
    case when coalesce(w.loso_uplift,0)<=0
         then 'Historical leave-one-season-out weather evidence worsens MAE versus the baseline; weather is not a production point feature.'
         else 'Historical weather evidence is positive, but prospective T-24h outcome evidence is not yet at the promotion gate.' end,
    case when coalesce(w.loso_uplift,0)<=0
         then 'Keep weather in shadow/research only. Continue collecting prospectively to detect whether a future interaction or regime-specific signal emerges.'
         else 'Continue prospective T-24h collection to the 20-pair gate before considering promotion.' end,
    'shadow_only',w.generated_at,
    jsonb_build_object('historical_seasons',w.seasons,'loocv_uplift',w.loocv_uplift,'loso_uplift',w.loso_uplift,'prospective_t24_outcome_pairs',v_weather_t24_pairs),now()
  ) on conflict (category_key) do update set
    sort_order=excluded.sort_order,display_name=excluded.display_name,research_prior_weight_pct=excluded.research_prior_weight_pct,
    decision_status=excluded.decision_status,evidence_signal=excluded.evidence_signal,primary_protocol=excluded.primary_protocol,
    candidate_key=excluded.candidate_key,validation_event_count=excluded.validation_event_count,validation_club_count=excluded.validation_club_count,
    promotion_evidence_count=excluded.promotion_evidence_count,promotion_event_target=excluded.promotion_event_target,
    promotion_club_target=excluded.promotion_club_target,promotion_progress_pct=excluded.promotion_progress_pct,
    incumbent_mae=excluded.incumbent_mae,bias_control_mae=excluded.bias_control_mae,challenger_mae=excluded.challenger_mae,
    uplift_vs_incumbent=excluded.uplift_vs_incumbent,incremental_uplift_vs_bias=excluded.incremental_uplift_vs_bias,
    prospective_event_count=excluded.prospective_event_count,decision_reason=excluded.decision_reason,next_action=excluded.next_action,
    production_impact=excluded.production_impact,source_refreshed_at=excluded.source_refreshed_at,evidence=excluded.evidence,refreshed_at=excluded.refreshed_at;

  select count(*)::int into v_rows from public.model_evidence_scorecard_v1;
  return v_rows;
end;
$$;

revoke all on function public.refresh_model_evidence_scorecard_v1() from public,anon,authenticated;
grant execute on function public.refresh_model_evidence_scorecard_v1() to service_role;

select public.refresh_model_evidence_scorecard_v1();

create or replace view public.dashboard_model_evidence_scorecard_v1
with (security_invoker=true)
as
select category_key,sort_order,display_name,research_prior_weight_pct,decision_status,evidence_signal,
  primary_protocol,candidate_key,validation_event_count,validation_club_count,promotion_evidence_count,
  promotion_event_target,promotion_club_target,promotion_progress_pct,incumbent_mae,bias_control_mae,
  challenger_mae,uplift_vs_incumbent,incremental_uplift_vs_bias,prospective_event_count,
  decision_reason,next_action,production_impact,source_refreshed_at,evidence,refreshed_at
from public.model_evidence_scorecard_v1
order by sort_order;

revoke all on public.dashboard_model_evidence_scorecard_v1 from public;
grant select on public.dashboard_model_evidence_scorecard_v1 to anon,authenticated,service_role;

create or replace view public.dashboard_model_evidence_summary_v1
with (security_invoker=true)
as
select count(*)::int category_count,
  count(*) filter (where decision_status='promotable')::int promotable_count,
  count(*) filter (where decision_status='collecting')::int collecting_count,
  count(*) filter (where decision_status='rejected')::int rejected_count,
  count(*) filter (where decision_status='blocked')::int blocked_count,
  count(*) filter (where evidence_signal='positive')::int positive_signal_count,
  'Baseline + Ticketing (shadow evidence chain)'::text current_evidence_backed_chain,
  'No context layer is automatically promoted to production P50.'::text governance_note,
  max(refreshed_at) refreshed_at
from public.model_evidence_scorecard_v1;

revoke all on public.dashboard_model_evidence_summary_v1 from public;
grant select on public.dashboard_model_evidence_summary_v1 to anon,authenticated,service_role;

-- Internal refresh cadence used in production:
-- cron.schedule('model_evidence_scorecard_6h','37 */6 * * *',
--   $$select public.refresh_model_evidence_scorecard_v1();$$)
