# Structural source export and frozen predictor integration v1

2026-11-04. Implements the next input-contract task from the execution plan. No frozen model, old helper, official prior, scoring cohort or deployed workflow changes.

## Implemented boundary

1. `ml.export_structural_known_at_inputs_v1` reads current due/alias RPCs and raw history, outcomes, canonical ticket events and season-filtered sporting fixtures. Exact `Content-Range` counts, unique source identities, partition hashes and an envelope hash prevent silent API truncation. Source knowledge and row revision timestamps are retained. Exports are bounded to1000rows per source and16MiB, written exclusively to private directories. Sporting uses its actual textual `source_event_id` key.
2. `ml.structural_known_at_shadow_v1` validates a genuinely recent export, explicit activation boundary, canonical fixture/horizon, absence of target attendance and legal post-cutoff window. It filters each event's sources separately, with the existing guard plus conservative `updated_at` handling, then calls the unchanged frozen predictor. Unknown revisions are excluded; conflicting known labels stop that target. No loss, coefficient, feature definition, training, policy or support threshold is tuned.
3. Output has `shadow_forecasts`, no top-level `predictions`, and `official_persistence_allowed=false`. The old gateway cannot accept this as a normal forecast payload. This implementation does **not activate a new prospective lane** or change the current serving path. A later release must preserve these boundaries and have its own prospective authorization/precommit before accuracy evaluation.
4. `ml.archive_structural_known_at_inputs_v1` provides bounded read-only private source snapshots with a lifetime lock, implementation hashes, a separate content-addressed Storage namespace and verified upload/read-back/decompression/restore. It predicts nothing and writes no official DB rows. Past source versions are preserved for future audits; absence of a pre-cutoff snapshot remains missing, never reconstructed.

The inherited sporting feature convention still excludes same-local-day fixtures. This work addresses attendance source availability; it does not independently establish historical publication/revision timing for all sporting inputs. Independent REST reads are not a transaction snapshot; recorded row timestamps and per-cutoff checks remain necessary.

## Actual checks and current evidence

Actual service-role export succeeded with exact counts:1due target,20aliases,43history records,26outcomes,38ticket events and135sporting fixtures. The first export exposed a schema assumption; the exporter now uses the actual string `source_event_id` and tests enforce source identity. Complete revised export SHA256 `25240027f92098205312811ac1284bbad7fe9371435794092335f08b84d1fdbf`.

Actual current inference inspection:1non-ready target10500/T-30,0shadow forecasts, no official writes. This is a real no-ready health check, not a positive prospective forecast, DB chain or accuracy result. No old Górnik cutoff was repaired. Raw exports/inspection remain under `/workspace/ops-runtime/2026-11-04-known-at-integration/`.

Twenty-four new tests cover actual HTTP count receipts, missing/duplicate/tampered data, private exclusive writes, exact per-event cutoff separation, activation/future/closed windows, known target outcomes in either source, conflicting attendance, delayed revisions, canonical/alias identity and incorrect predictor output. An explicitly synthetic integration runs the real frozen predictor and compares its complete output against the original unmodified input path when all data were already known. Fitting is forbidden during inference. Archive tests exercise source changes, namespace isolation, corruption and complete restore.

## Commands and release boundary

```bash
python -m ml.export_structural_known_at_inputs_v1 \
  --output-dir /workspace/ops-runtime/<new-private-export-directory>

python -m ml.structural_known_at_shadow_v1 \
  --input /workspace/ops-runtime/<new-private-export-directory>/inputs.json \
  --output-dir /workspace/ops-runtime/<new-private-inspection-directory> \
  --artifact-dir ml/artifacts/structural_prior_runtime_v1 \
  --activation-at <explicit-reviewed-boundary>
```

The inspection activation argument is a safety boundary, not proof that a prospective experiment was frozen or enabled. Genuine accuracy evidence still requires its separate precommit, immutable capture before outcomes and cohort rules.

Bounded source archive (publish source/checks before launch):

```bash
python -m ml.archive_structural_known_at_inputs_v1 \
  --runtime /workspace/ops-runtime/2026-11-04-known-at-source-archive \
  --until 2026-11-06T20:30:00Z --interval 900
```

No new project SQL or Edge deployment is performed here. Existing managed serving still drops these timestamps until a separately reviewed integration is released. `production_change=false`, `live_adjustment=0`.

## Actual archive activation and read-only retrieval

Published source df4fc022 before launch. Bounded workerPID209974 started18:08:47UTC, interval900s, untilNov6 20:30UTC. Actual post-launch18:08:50UTCcycle: capture completed18:08:49.277936, exact counts verified, private12,105byte backup SHA256 `9a47abe50d656453128815da5e22e58a86be3c37d03af09b2a451a22acbd713e`, read-back/decompression/restore all verified. Archive source contractSHA846d1abbe99547c680b35f52fb6f9c3f5dce8b350020190214f2fac51a10bd4d. No official DB writes or predictions.

Separate `ml.select_structural_known_at_snapshot_v1` implements read-only latest-pre-cutoff lookup with a fixed60-minute freshness bound. It validates capture/recovery identity and refuses post-cutoff, stale, partial, conflicting or tampered captures. Five tests preserve the earlier captured value after a later source-row revision. Actual18:10lookup selects18:08:49; actual16:30lookup returns `NO_GENUINE_PRE_CUTOFF_SNAPSHOT`. Raw returned inputs still require per-cutoff/season/target checks before any future reviewed predictor integration. No snapshot or forecast was fabricated.

Live consumer gap is confirmed, not merely hypothetical: old managed materializer created Górnik449prior74at17:55:18UTCwith declared16:30cutoff and6season home records. Five of those records were acquired17:18UTC. This lane preserves that evidence and writes no replacement. Existing generated_at restrictions remain essential; no earlier cutoff can claim this prior was already available.

## Source coverage follow-up18:32UTC

The remaining445outcome is now composite-verified and appended with actual knowledge time; all6trackedoutcomes are present. Later captures will contain44history/27outcomes; earlier immutable snapshots correctly retain43/26. The old17forecast-event C1cohort is now fully scored, policyMAE3248.81vsprior3131.16. No new model or archive-generated forecast is validated by those old fixtures. Detailed provenance:`OUTCOME445_COMPOSITE_VERIFICATION_RESULT_V1.md`.
