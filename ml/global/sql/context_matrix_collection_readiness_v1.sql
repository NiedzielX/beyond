-- Beyond Ticketing Context Matrix — collection readiness metadata.
-- Distinguishes what is actually automated today from manual research,
-- verified registries, planned sources, shadow collection and external-access blockers.

alter table public.context_feature_definitions
  add column if not exists collection_status text,
  add column if not exists collection_note text;

alter table public.context_feature_definitions
  drop constraint if exists context_feature_definitions_collection_status_check;

alter table public.context_feature_definitions
  add constraint context_feature_definitions_collection_status_check
  check (collection_status is null or collection_status in (
    'active_automated',
    'active_manual',
    'verified_registry',
    'shadow_automated',
    'degraded_automation',
    'planned',
    'blocked_external_access'
  ));

update public.context_feature_definitions
set collection_status = case
  when feature_key like 'ticketing.%' then 'active_automated'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'active_automated'
  when feature_key = 'weather.kickoff_context' then 'shadow_automated'
  when feature_key in ('match.timing','match.competition_stage') then 'active_automated'
  when feature_key = 'match.opponent_historical_uplift' then 'shadow_automated'
  when feature_key = 'sport.match_stakes' then 'shadow_automated'
  when feature_key in ('sport.rivalry_opponent','sport.absence_impact') then 'verified_registry'
  when feature_key = 'sport.form5' then 'active_manual'
  when feature_key in ('hype.media_attention','hype.mention_acceleration')
    then case when collection_status='degraded_automation' then 'degraded_automation' else 'active_automated' end
  when feature_key = 'hype.search_interest' then 'blocked_external_access'
  else 'planned'
end,
primary_source = case
  when feature_key in ('sport.form5','sport.match_stakes') then 'Verified sporting sources / licensed provider TBD'
  when feature_key = 'sport.rivalry_opponent' then 'Beyond verified rivalry map backed by official club/competition evidence'
  when feature_key = 'sport.absence_impact' then 'Beyond verified absence register backed by official club/competition evidence'
  when feature_key = 'match.opponent_historical_uplift' then 'Beyond verified attendance history'
  when feature_key in ('match.timing','match.competition_stage') then 'ticket_events'
  else primary_source
end,
fallback_source = case
  when feature_key = 'sport.match_stakes' then 'TheSportsDB v1 shadow automation + manual official verification'
  when feature_key = 'sport.form5' then 'Manual verification against official competition/club sources'
  when feature_key = 'sport.rivalry_opponent' then 'Manual verified research for unmapped relationships'
  when feature_key = 'sport.absence_impact' then 'Manual verified research for newly discovered or unresolved absences'
  when feature_key = 'match.opponent_historical_uplift' then 'No score until history gate is met'
  else fallback_source
end,
collection_note = case
  when feature_key like 'ticketing.%' then 'Collected from existing Roboticket/public-inventory snapshots and Beyond derived live features.'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'Derived automatically from public-inventory snapshot structure; modifies confidence, not demand.'
  when feature_key = 'weather.kickoff_context' then 'Collector is active, but the feature remains shadow-only because historical validation did not improve forecast accuracy.'
  when feature_key = 'match.timing' then 'Kickoff day/time is refreshed automatically from ticket_events in Europe/Warsaw. Reschedules overwrite the stable v2 observation rather than leaving stale timing context.'
  when feature_key = 'match.competition_stage' then 'Competition is refreshed automatically from ticket_events. Stage remains explicitly unknown when the event source does not provide it; Beyond does not infer it from competition name alone.'
  when feature_key = 'match.opponent_historical_uplift' then 'Automated leakage-safe readiness gate uses only verified outcomes before the target kickoff, within the same home club and competition class. Uplift is emitted only after >=8 prior club outcomes and >=3 prior home meetings with the same opponent in a 730-day lookback; otherwise the value stays null rather than defaulting to zero.'
  when feature_key = 'sport.match_stakes' then 'Automated shadow collector reconstructs Ekstraklasa standings from completed FT results and compares the research score with verified references. It never replaces Event Detail context or P50.'
  when feature_key = 'sport.form5' then 'The feature means the last five relevant matches across competitions, not league-only form. TheSportsDB free eventslast endpoint returned only one event, so form5 remains verified manual research until a complete licensed recurring feed is selected.'
  when feature_key = 'sport.rivalry_opponent' then 'Verified rivalry relationships are stored once in a maintained symmetric map and automatically propagated to matching future fixtures. Absence of a relation means unknown, never "not a rivalry".'
  when feature_key = 'sport.absence_impact' then 'Absences are verified once from official evidence and propagated automatically to matching future fixtures. Silence never means confirmed availability; demand impact stays unscored without player salience, certainty and novelty.'
  when feature_key in ('hype.media_attention','hype.mention_acceleration') then 'Forward-only GDELT Web News NGrams sampler targets a 15-minute cadence. A Supabase watchdog marks the automation degraded when the newest persisted sample is older than 45 minutes, so stale collection cannot look healthy in Model Lab.'
  when feature_key = 'hype.search_interest' then 'Official Google Trends API remains alpha/early-access and requires approval; no unofficial scraper is used as a production dependency.'
  when feature_key = 'hype.social_volume' then 'Planned after media-attention baseline; provider/API and commercial-use constraints must be confirmed before automation.'
  when feature_key = 'hype.local_fan_buzz' then 'Planned as club-specific public-source configuration rather than one universal Polish forum source.'
  when feature_key = 'hype.sentiment' then 'Deliberately deferred until volume/acceleration signals prove useful.'
  else collection_note
end,
updated_at = now();

drop view if exists public.dashboard_context_matrix_v1;

grant select (
  feature_key,group_key,display_name,description,value_type,production_role,
  refresh_cadence,primary_source,fallback_source,is_active,collection_status,collection_note
)
on public.context_feature_definitions to anon, authenticated;

create view public.dashboard_context_matrix_v1
with (security_invoker = true)
as
select
  w.matrix_version,
  d.feature_key,
  d.group_key,
  d.display_name,
  d.description,
  w.weight_pct,
  d.production_role,
  d.refresh_cadence,
  d.primary_source,
  d.fallback_source,
  d.collection_status,
  d.collection_note,
  w.rationale
from public.context_feature_weights w
join public.context_feature_definitions d on d.feature_key = w.feature_key
join public.context_matrix_versions m on m.version = w.matrix_version
where w.matrix_version = 'context-v0.1'
  and m.status = 'frozen'
  and d.is_active = true;

revoke all on public.dashboard_context_matrix_v1 from public;
grant select on public.dashboard_context_matrix_v1 to anon, authenticated, service_role;
