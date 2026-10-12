-- Beyond Ticketing — Attention & Hype source readiness v2.
-- Keeps current official-source access constraints and cadence explicit.

update public.context_feature_definitions
set refresh_cadence='target 15m; degraded after 45m without a persisted sample',
    collection_note='Forward-only GDELT Web News NGrams sampler targets a 15-minute cadence. A Supabase watchdog marks the automation degraded when the newest persisted sample is older than 45 minutes, so stale collection cannot look healthy in Model Lab.',
    updated_at=now()
where feature_key in ('hype.media_attention','hype.mention_acceleration');

update public.context_feature_definitions
set collection_status='blocked_external_access',
    primary_source='Google Trends API alpha (preferred arbitrary-term source)',
    fallback_source='Google Trends BigQuery public dataset — unsuitable for match-level arbitrary-term monitoring',
    refresh_cadence='daily or event-checkpoint once API access is granted',
    collection_note='The official Google Trends API is the correct arbitrary-term source and provides consistently scaled term interest plus geographic restrictions, but access remains limited to accepted alpha testers. The public BigQuery dataset contains only daily Top 25 / Top 25 Rising terms, so it is rejected as a match-level proxy because it would create selection bias and false zeroes. No unofficial Trends scraper is used.',
    updated_at=now()
where feature_key='hype.search_interest';

update public.context_feature_definitions
set collection_status='blocked_external_access',
    primary_source='X API v2 search — preferred social-volume source',
    fallback_source='No Reddit production feed without separate commercial agreement',
    refresh_cadence='event checkpoints once X access is configured',
    collection_note='X API v2 search is the preferred match-specific public social-volume source and uses consumption-based billing. Activation requires an approved X developer app, credentials and credits. Reddit is excluded from the commercial MVP unless Beyond enters a separate Reddit agreement; no Reddit scraping is used.',
    updated_at=now()
where feature_key='hype.social_volume';
