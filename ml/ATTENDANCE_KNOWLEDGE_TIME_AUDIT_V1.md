# Attendance knowledge-time consumer audit v1

2026-11-04 17:28UTC. This follows the verified-source import and does not change a frozen model, feature builder, prior, collector or old score.

## Confirmed consumer gap

`ml_home_attendance_history_v2` exposes fixture time/count/provenance but no source knowledge timestamp. C1attendance export inherits those columns. `supabase/functions/structural_prior_materializer_v1/index.ts` selects the timestamp-free view, and `ml/demand_engine/current_structural_prior_features.py` filters current attendance only by kickoff. Therefore DBknowledge timestamps alone do **not** prove end-to-end PIT enforcement. Passing900original-training-cell parity proves numerical stability for that cohort, not availability of every new source at an old cutoff.

Current prior read17:25UTC found Motor5091/T-3prior71and Wisła448/T-3prior72already persisted before today's import; they were not rewritten. Górnik449/T-3was missing at that read. Do not regenerate an old cutoff using newly verified history or treat a late generated prior as known at its canonical earlier cutoff. Existing generated_at checks remain essential.

## Separate read-only guard, actual proof

New adapter `ml/attendance_knowledge_time_guard_v1.py` consumes raw history/outcomes/canonical events, preserving source identities and conservative `known_at=max(observed_or_confirmed,created,verified_if_present)`. Unknown/naive/invalid metadata, mismatched season/competition, nonpositive labels and knowledge before kickoff are rejected. Filter source availability before deduplication; a later outcome cannot hide already known history, and conflicting known counts fail closed. No prior model is fitted or scored by this adapter.

Actual private audit17:28:08UTC: all15newly imported history records are **ineligible at16:30UTC and eligible at the actual later read**. Full raw catalog64accepted source records/5out-of-contract competition records,57eligible distinct fixtures at the later cutoff,0conflicts. Seven targeted tests cover availability boundary, verification timestamp, missing/timezone metadata, outcome priority after availability filtering, conflicting labels, future fixtures and season/competition/identity. Private full diagnostics remain outsideGit.

**Serving integration remains NOT_DEPLOYED.** This adapter is a tested boundary for the next separately reviewed input-contract release; it does not silently repair the existing timestamp-free view/materializer. No old forecast can be relabelled PIT-safe from this audit. Newly imported data may inform future cutoffs only through an input path that preserves actual knowledge time. Both Nov4C1freezes remain unchanged and their first final24window is later than this import.

Next concrete integration: versioned raw-source export preserving knowledge timestamps → guard filtering per declared target cutoff → unchanged frozen predictor, with synthetic and actual private input tests, explicit new contract identity, no historical prior overwrite/backfill. A draft implementation or YAML alone cannot establish live enforcement. `production_change=false`, `live_adjustment=0`.
