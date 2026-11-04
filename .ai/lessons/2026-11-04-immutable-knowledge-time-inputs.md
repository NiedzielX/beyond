# Immutable source inputs and knowledge time

Preserving source_observed_at alone is insufficient if current rows can be revised. Keep created_at, updated_at and verified_at with the value, use conservative per-cutoff availability and preserve genuine earlier source snapshots. A later current value must not replace a genuinely captured earlier value; if no snapshot exists before the cutoff, return missing. Never fabricate a snapshot timestamp or turn that lookup into a retrospective prospective forecast.

REST success is not export completeness. Require exact Content-Range totals, actual unique source keys, bounded sizes and partition/envelope hashes. SportsDB uses textual source_event_id, not an id column. The actual exporter verified43history/26outcomes/38events/135sporting rows. Raw sources stay private; archive recovery has its own namespace, source/dependency hash lock, exclusive runtime/lifetime lock and actual restore checks.

Synthetic complete-output parity with an unchanged frozen predictor establishes correctness, not accuracy. A successful no-ready cycle is not a positive forecast/DB chain. The prepared shadow envelope deliberately has no top-level predictions field, preventing accidental posting to the old gateway. No new prospective lane is activated by this code.

Evidence: `ml/STRUCTURAL_KNOWN_AT_INPUT_INTEGRATION_V1.md`. Old managed Górnikprior74 demonstrates the still-unreleased serving gap: generated17:55with canonical16:30cutoff and later-known history. Preserve its real timestamps; do not erase or retrospectively relabel it as available at16:30.

For delayed outcome445, separate the authority for fixture schedule from the provider of attendance. Exact official schedule/date/clubs/result plus a unique canonical match resolved identity; attendance3396remains the primary site's reported number. Preserve the conflicting primary display time and explicitly unknown cause; do not claim an actual kickoff delay or independent count corroboration. A narrow composite rule is different from introducing a general time-tolerance join. Evidence:`ml/OUTCOME445_COMPOSITE_VERIFICATION_RESULT_V1.md`.
