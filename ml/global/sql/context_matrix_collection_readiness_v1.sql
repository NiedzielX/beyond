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
    'planned',
    'blocked_external_access'
  ));

update public.context_feature_definitions
set collection_status = case
  when feature_key like 'ticketing.%' then 'active_automated'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'active_automated'
  when feature_key = 'weather.kickoff_context' then 'shadow_automated'
  when feature_key in ('match.timing','match.competition_stage') then 'active_automated'
  when feature_key = 'sport.match_stakes' then 'shadow_automated'
  when feature_key in ('sport.rivalry_opponent','sport.absence_impact') then 'verified_registry'
  when feature_key = 'sport.form5' then 'active_manual'
  when feature_key in ('hype.media_attention','hype.mention_acceleration') then 'active_automated'
  when feature_key = 'hype.search_interest' then 'blocked_external_access'
  else 'planned'
end,
primary_source = case
  when feature_key in ('sport.form5','sport.match_stakes') then 'Verified sporting sources / licensed provider TBD'
  when feature_key = 'sport.rivalry_opponent' then 'Beyond verified rivalry map backed by official club/competition evidence'
  when feature_key = 'sport.absence_impact' then 'Beyond verified absence register backed by official club/competition evidence'
  else primary_source
end,
fallback_source = case
  when feature_key = 'sport.match_stakes' then 'TheSportsDB v1 shadow automation + manual official verification'
  when feature_key = 'sport.form5' then 'Manual verification against official competition/club sources'
  when feature_key = 'sport.rivalry_opponent' then 'Manual verified research for unmapped relationships'
  when feature_key = 'sport.absence_impact' then 'Manual verified research for newly discovered or unresolved absences'
  else fallback_source
end,
collection_note = case
  when feature_key like 'ticketing.%' then 'Collected from existing Roboticket/public-inventory snapshots and Beyond derived live features.'
  when feature_key in ('dq.release_activity','dq.sector_coverage_change') then 'Derived automatically from public-inventory snapshot structure; modifies confidence, not demand.'
  when feature_key = 'weather.kickoff_context' then 'Collector is active, but the feature remains shadow-only because historical validation did not improve forecast accuracy.'
  when feature_key in ('match.timing','match.competition_stage') then 'Available from ticket_events / event metadata and stored point-in-time.'
  when feature_key = 'sport.match_stakes' then 'Automated shadow collector active: Supabase pg_cron + pg_net reads complete TheSportsDB Ekstraklasa round data, reconstructs standings, applies league_match_stakes_v01 and compares each sample with the latest verified manual/official reference. Shadow values never replace Event Detail context and never affect P50. Initial validation: 7/9 comparable upcoming league events matched the stored reference exactly; remaining deltas reflect a newer completed Radomiak-Motor result versus the older reference snapshot.'
  when feature_key = 'sport.form5' then 'The feature means the last five relevant matches across competitions, not league-only form. TheSportsDB free eventslast endpoint returned only one event, so form5 remains verified manual research until a complete licensed recurring feed is selected.'
  when feature_key = 'sport.rivalry_opponent' then 'Verified rivalry relationships are stored once in a maintained symmetric map and automatically propagated to matching future fixtures. The current map is intentionally incomplete: absence of a relation means unknown, never "not a rivalry". Opponent attractiveness remains a separate unscored/historically learned part of this feature.'
  when feature_key = 'sport.absence_impact' then 'Absences are verified once from official evidence and stored with an active validity window; Beyond then propagates them automatically to matching future fixtures. The register does not infer player availability from silence, and an absence does not receive a demand score unless player salience, certainty and novelty are supported.'
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
