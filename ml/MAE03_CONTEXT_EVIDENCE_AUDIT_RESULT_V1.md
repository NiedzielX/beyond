# MAE-03 — stored context evidence audit

Date:2026-11-03. Runner:`python -m ml.mae03_context_evidence_audit_v1 --output /private/runtime/new-directory`. Specification:`.ai/specs/implemented/2026-11-03-context-evidence-audit.md`.

## Current evidence

Reuse the existing Context Snapshot v1 pipeline; no new collector or competing feature store. Read-only export contains121stored snapshots:70prospective-window-valid and51retrospective records kept separate.62prospective snapshots have a timed, identified historical baseline;8have no baseline.11distinct events across checkpoints have confirmed post-match outcome presence. **No attendance values were requested or used by this audit.**

Source/baseline/checkpoint isolation produces37numeric feature groups.35lack event support, one has no variance, and one has insufficient grouped variation. None is ready for a new model fit.

| Feature/source/checkpoint | Paired events | Clubs | Distinct values | Finding |
|---|---:|---:|---:|---|
|Media attention / NGrams v2 /T-24h|10|10|1|all10values are0; NO_VARIANCE|
|Mention acceleration / NGrams v2 /T-24h|4|4|3|below8-event/5-club screening support|
|Mention acceleration / DOC2 /T-24h|2|2|1|different source; do not pool with NGrams|
|Media attention / NGrams v2 /T-6h, same T-1 baseline|9|9|2|only1nonzero event; removing it leaves constant training features|

The T-6h row cannot rescue the primary T-24h contract after seeing coverage. Event/club training-fold variation must remain sufficient. The stored raw zeroes remain zeroes; blocked, degraded, missing and nonnumeric fields are kept separate.

This **reconfirms**, rather than discovers a new opportunity around, existing Hype gates in `ml/global/sql/hype_challenger_v1.sql` and the presentation correction in `supabase/sql/dashboard_hype_readiness_truth_v1.sql`. The audit adds reproducible per-source/per-baseline/per-checkpoint grouping and independent timing/variance checks. No old Hype model grid was reopened.

## Evidence limits

Stored context payloads contain observed/source times but omit original observation IDs and `created_at`. Repository capture SQL applies all three cutoff filters, but inspecting that source is not independent per-row ingestion proof. Snapshot capture is insert-only by application convention; this audit does not certify an immutable database trigger. Retain these limits when designing the next actual experiment.

The source-sync job's three-hour waiting period was not reused as a new label eligibility gate: a genuine manually confirmed outcome at2h57after kickoff remains available. This affects audit counts only; no frozen experiment or outcome was changed.

Raw snapshot exports stay in `/workspace/ops-runtime/2026-11-03-context-evidence-v1-final/`, outside Git. Only aggregate metadata and hashes are committed at `artifacts/mae03_context_evidence_audit_v1/report.json`.

## Other live source checks

At20:27UTC, existing odds collection was healthy:12PIT events /10clubs /2,721quote rows; latest capture19:51UTC. P4a has5labeled events vs its unchanged9-event start gate. The combined `ml_research_readiness_v1` returnsHTTP500/PostgreSQL57014(statement timeout); separate P4/P11 endpoints work. Do not repeatedly call the expensive combined export or present it as healthy. No timeout, gate or SQL deployment was changed by this audit.

## Decision

**DATA_BOUND / NO_NEW_CONTEXT_FIT.** Continue forward-only collection; revisit only when one exact feature/source/cutoff has adequate paired and grouped-variable evidence, with a separate precommit. Keep the existing weather/timing/C2 rejections and Pre-Live v3 research anchor. Meanwhile finish isolated PostgreSQL validation of the already prepared daily-path persistence lane and retain its genuine future forecasts for scoring.

`production_change=false`, `live_adjustment=0`, `model_fit_performed=false`.
