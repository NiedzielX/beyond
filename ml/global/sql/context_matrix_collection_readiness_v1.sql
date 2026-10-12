-- Beyond Ticketing Context Matrix — collection readiness metadata.
-- Distinguishes what is actually automated today from manual research,
-- planned sources, shadow collection and external-access blockers.

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
    'shadow_automated',
    'planned',
    'blocked_external_access'
  ));

update public.context_feature_definitions
set collection_status = case
  when feature_key like 'ticketing.%' then 'active_automated'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'active_automated'
  when feature_key = 'weather.kickoff_context' then 'shadow_automated'
  when feature_key in ('match.timing','match.competition_stage') then 'active_automated'
  when feature_key in ('sport.match_stakes','sport.rivalry_opponent','sport.form5','sport.absence_impact') then 'active_manual'
  when feature_key in ('hype.media_attention','hype.mention_acceleration') then 'active_automated'
  when feature_key = 'hype.search_interest' then 'blocked_external_access'
  else 'planned'
end,
primary_source = case
  when feature_key in ('sport.form5','sport.match_stakes') then 'Verified sporting sources / licensed provider TBD'
  when feature_key in ('sport.absence_impact','sport.rivalry_opponent') then 'Official club/competition evidence / licensed provider TBD'
  else primary_source
end,
fallback_source = case
  when feature_key in ('sport.form5','sport.match_stakes') then 'Manual verification against official competition/club sources'
  when feature_key in ('sport.absence_impact','sport.rivalry_opponent') then 'Manual verified research'
  else fallback_source
end,
collection_note = case
  when feature_key like 'ticketing.%' then 'Collected from existing Roboticket/public-inventory snapshots and Beyond derived live features.'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'Derived automatically from public-inventory snapshot structure; modifies confidence, not demand.'
  when feature_key = 'weather.kickoff_context' then 'Collector is active, but the feature remains shadow-only because historical validation did not improve forecast accuracy.'
  when feature_key in ('match.timing','match.competition_stage') then 'Available from ticket_events / event metadata and stored point-in-time.'
  when feature_key in ('sport.form5','sport.match_stakes') then 'OpenLigaDB was technically validated but has no Ekstraklasa 2026 coverage. football-data.org does not list Poland in current coverage. Direct product scraping of ekstraklasa.org is not used due to current site terms. Point-in-time values remain verified manual research until a licensed recurring feed is selected.'
  when feature_key = 'sport.rivalry_opponent' then 'Rivalry/opponent evidence is verified manually from public club/competition sources. A maintained rivalry map is the intended stable product layer.'
  when feature_key = 'sport.absence_impact' then 'Verified absences are collected from public official evidence. No recurring scraper is used. Demand impact remains unscored unless player salience, certainty and novelty are supported.'
  when feature_key in ('hype.media_attention','hype.mention_acceleration') then 'Forward-only GDELT Web News NGrams sampler runs every 15 minutes and waits for comparison coverage before interpreting acceleration.'
  when feature_key = 'hype.search_interest' then 'Official Google Trends API remains alpha/early-access and requires approval; no unofficial scraper is used as a production dependency.'
  when feature_key = 'hype.social_volume' then 'Planned after media-attention baseline; provider/API and commercial-use constraints must be confirmed before automation.'
  when feature_key = 'hype.local_fan_buzz' then 'Planned as club-specific public-source configuration rather than one universal Polish forum source.'
  when feature_key = 'hype.sentiment' then 'Deliberately deferred until volume/acceleration signals prove useful.'
  when feature_key = 'match.opponent_historical_uplift' then 'Requires enough leakage-safe historical attendance by opponent/opponent class before scoring.'
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
