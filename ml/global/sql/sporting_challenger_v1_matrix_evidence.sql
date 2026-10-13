update public.context_feature_definitions
set collection_note = coalesce(collection_note,'') || ' Research result 2026-10-13: the first T-24h one-feature Ridge challenger using reconstructed/prospective Match Stakes was rejected because it worsened MAE versus Baseline + Ticketing in both leave-one-event-out and leave-one-club-out validation. Collection remains active shadow; no Sporting P50 is produced from this candidate.',
    updated_at = now()
where feature_key='sport.match_stakes';
