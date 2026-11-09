# Read-only rolling72 v2 panel feed

Date: 2026-11-09. Status: IMPLEMENTED — actual export, hosted validation and separate preview evidence recorded.

The separately frozen experiment remains governed by `ml/artifacts/rolling72_v2/precommit.json` and `paired_shadow_freeze.json`. This adapter exports actual persisted paired forecasts; it never calls inference, fits, changes a model, writes a ledger or repairs old observations. V1 contracts and running collectors stay untouched.

Create `ml/rolling72_feed_v2.py` and meaningful synthetic contract tests. API `build_feed(database, *, generated_at=None, model_manifest=None, allow_synthetic_test=False)` opens an existing v2 SQLite in read-only query-only mode and one consistent transaction. Require exact v2 application/schema/freeze identity, internal source/issue/prediction/target/score hashes, clocks, horizon arithmetic and four-model coordinates. Missing predictions stay null; zero remains a real number. Candidate metadata and training-clock uncertainty remain explicit. No private source URLs, credentials, raw source exports, model weights or guessed capacity/attendance conversion enter the allowlisted output.

Output is explicitly NEW `rolling72-shadow-feed-v2`, evidence `immutable_actual_time_paired_shadow`, the same vintage/observation/point layout as v1 with four exact models. Candidate ID `rolling72-capture-segment-quantile-tree-v2`. Preserve the actual prefix and each actual issue, write, future target, accepted score and model/freeze lineage. Candidate maturity extrapolation flag is preserved. No historical/in-sample MAE or accuracy-gain claim. Keep `production_change=false`, `live_adjustment=0`, exposed cohort.

The ledger records the model manifest hash but not its model freeze timestamp. An optional hash-verified original manifest supplies `model_frozen_at`; without it this field is null, never inferred from the later lane freeze. Real preview export supplies the genuine private manifest. Synthetic ledgers require explicit test opt-in and retain `synthetic_test=true` so a frontend can reject them.

Acceptance: synthetic tests cover read-only bytes, model/version/lineage/hash/clock corruption, availability null versus zero, first-point and failed-coordinate cases, later immutable shared scores and arithmetic, private-field exclusion, foreign ledger and synthetic-default refusal. Export the actual ledger read-only after tests; compare values with stored rows. Publishing/deploying a feed or proving ML accuracy is outside this adapter and requires separate evidence.


Completion evidence: published backendc14f48c and panelbd01c8b. Actual snapshot SHA857235542d037c96c79b8681afeff9ba324ae967ac0a811e06ae9ccfbc246d3e retains2genuineissues/sixcandidate+sixP0forecasts.19exporttests and44frontendcontracts passed; actual hosted TypeScript/build/Chromium runs42687297466/42687307464SUCCESS, Vercelpreview7664437577SUCCESS. [Machine proof](../../../ml/ROLLING_72H_ML_PANEL_PROOF_2026-11-09.json). This closes this read-only export/explicit preview implementation, not continuous livefeed hosting, production model promotion or MAE improvement.
