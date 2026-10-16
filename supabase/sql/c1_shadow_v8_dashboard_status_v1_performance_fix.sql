-- Cover the two C1 v8 foreign keys identified by Supabase performance advisor.

create index if not exists c1_shadow_v8_predictions_source_snapshot_idx
    on private.c1_shadow_v8_predictions_v1(source_snapshot_id);

create index if not exists c1_shadow_v8_scores_latest_prediction_idx
    on private.c1_shadow_v8_event_scores_v1(latest_prediction_id);
