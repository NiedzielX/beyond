# Existing context snapshot evidence audit

Status: complete.15tests and the hosted checks passed in runs41715153450and41715203331. Draft PR208. No context model authorized by this audit.

Reuse the existing `event_context_snapshots_v1` and its source contract rather than building another feature store or collector. Inspect prospective and retrospective records separately. Check snapshot/event/checkpoint identity, legal capture window, baseline lineage and context observation timestamps. Keep missing/blocked/degraded values distinct from genuine numeric zero. Count independent paired events and clubs by feature, source and checkpoint using only outcome presence/confirmation time; do not choose features from attendance error.

Stored context payloads do not include original observation `created_at` or observation ID. Report that limitation instead of claiming independent bitemporal validation from payload timestamps alone. Use the existing SQL's three-time filter as implementation evidence, not proof of historical ingestion time for every original row. Keep model versions and sources visible; do not pool different source definitions blindly.

Acceptance: a pure auditable analyzer, read-only cloud export, meaningful invalid/missing/zero/duplicate/late-capture tests and aggregate report. Require feature variation in every held-out event/club training fold; one nonzero event cannot establish that support. The source-sync job's three-hour wait is not a new eligibility gate for genuine earlier post-match confirmations. No model fit, gate relaxation, backfill or production change. Previously rejected C2 sequence/stakes, weather and timing candidates remain closed; fresh source availability does not reopen them automatically.
