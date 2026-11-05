# Verified history consumption audit

Executed November5,16:15UTC, read-only. Source export SHA`ad1fc737f607297f20ea171e0ea99d4d3398fccccb959a6980339bceb6d67afa`; actual view/prior capture SHA`801687d44307f2ac8bab90e8b026e1a5d23446d5c918c20faca649a59ae0d929`. Raw evidence stays private under`/workspace/ops-runtime/2026-11-05-history-consumption-audit/`. Public aggregates:`artifacts/history_consumption_audit_v1.json`.

## What is established

All16verified Nov4imports are present with identical values in the current62fixture serving attendance view. Ten future canonical ticket events have28already-due horizon reads;20actual priors exist and8are missing. No new prior was generated.

Reconstructing the four home-history aggregate fields with the unchanged frozen builder gives:

| Stored prior evidence | Rows |
|---|---:|
| Matches current home aggregates with imports, differs without |1|
| Matches home aggregates without imports, differs with |5|
| Imports do not distinguish the home's aggregate fields |12|
| Neither current reconstruction matches stored home aggregates |2|

Seventeen of20stored priors match the reconstructed knowledge-safe home aggregates. The prior RPC does not expose its original full source rows or feature hash. These are aggregate consistency findings, **not proof of exact per-source consumption**, complete original-input replay, or accuracy improvement.

The five older Wisła448/Górnik449priors match data without later imports, as expected:the records were not known at their cutoffs. Their stored immutable values must not be replaced. Górnik449/T-3matches the imported6home rows, but5were learned after the canonical cutoff and before its actual later generation. This confirms the already documented serving knowledge-time gap; it is not new legal pre-cutoff evidence. Lech451/T-14/T-7differ from both current reconstructions; revisions/source differences remain unresolved. Do not label them as a proved import effect.

## Consequence for the next experiment

Treat source presence, eligibility at observation, aggregate consistency, actual forecast capture and MAE as separate evidence levels. Existing16imports cannot be inserted into old historical training observations. Future T-1inputs may legally use them when genuinely known; unchanged old forecast contracts/records remain unchanged.

A target-free prepared representation has34of80historical live rows with already-known home history, covering13fixtures/9clubs. Three explicit source-derived features(support count, latest-three-home level relative to shared prior, recency)are absent from compact30live inputs. They supply a specific separately testable representation difference. Source timestamps are conservatively filtered, while historical original source snapshots remain independently unverified. All26fixtures remain exposed training, never fresh validation.

The next exact ablation is registered in`C1_HISTORY_SUPPORT_RESIDUAL_PRECOMMIT_V1.md`:same small residual median learner/data/settings,6existing input summaries versus those6plus3explicit history features. No new-head training/history MAE, no broad model search. Primary future comparison isolates the history information; product gain has separate benchmarks/gates. Code correctness and input variation do not establish predictive value.

Twelve audit tests and11feature tests pass, plus13new prospective/residual guards;347registered root checks pass. Actual audit did not fit or call a predictor. Frozen artifact/source identities remain unchanged. Production defaultsfalse/0.
