# Beyond Ticketing — Attention & Hype Challenger v1

Status: **prospective evidence collection active**  
Production impact: **none**

## Why Hype is prospective-only

The current completed T-24h evaluation sample predates the Attention collector. None of the 8 completed Ticketing Challenger events has a media signal that was available in Beyond at its historical checkpoint.

Therefore Beyond does **not** backfill current media/search/social observations into historical T-24h snapshots. Hype is the first Context Matrix category that must be evaluated entirely on future prospective checkpoints.

## Current evaluation chain

The empirical research chain is currently:

`Baseline → + Ticketing ✅ → Sporting ❌ → Match Context ❌ → Hype collecting`

Because Sporting and Match Context candidates were rejected, the Hype challenger is evaluated directly against **Baseline + Ticketing** rather than on top of rejected layers.

## Media Attention v2

The first GDELT sampler required both teams to occur in the same sampled article and produced persistent false-zero event signals.

v2 separates two concepts:

1. **Broad event-team attention** — Polish documents that mention either team using conservative strong aliases.
2. **Match-pair mentions** — documents that contain aliases for both teams; retained as a stricter diagnostic signal.

The broad signal is the candidate input for `hype.media_attention`. Pair mentions are not treated as required coverage.

The collector samples several recent GDELT Web News NGrams source files per run and persists every source timestamp separately. Reprocessing overlapping files is idempotent through `(ticket_event_id, source_file_timestamp)` uniqueness.

Current v2 source semantics are consistent with GDELT Web News NGrams: each source file contains `DOCID / QUADGRAM / COUNT`, and the corresponding TOC maps DOCIDs to URL/title/language. DOCIDs reset per source file.

## Prospective gate

Before Hype MAE is treated as testable, the feature requires:
- at least **8 independent completed prospective T-24h events**;
- at least **5 clubs**;
- a valid Baseline + Ticketing P50 at the checkpoint;
- v2 media attention frozen inside the prospective Context Snapshot;
- source observation at or before the checkpoint;
- at least 2 distinct observed feature values.

Primary validation: **leave-one-club-out**.  
Secondary validation: leave-one-event-out.

A candidate must beat both:
1. Baseline + Ticketing;
2. bias-only control.

No `baseline_ticketing_hype` ablation prediction is created before this evidence exists.

## Current state — 2026-10-14

- Prospective T-24h snapshots: **0**
- Completed media-eligible prospective events: **0 / 8**
- Eligible clubs: **0 / 5**
- Hype ablation predictions: **0**
- Historical backfill allowed: **false**

The first v2 rolling samples have started. The matcher now finds some global strong-alias documents, but the current short sample contains no Polish-language broad hits. This is treated as observed source coverage, not converted into artificial non-zero attention.

## Feature readiness

- `hype.media_attention` — prospective collecting
- `hype.mention_acceleration` — prospective collecting / comparison-window warmup
- `hype.search_interest` — blocked external access; no unofficial scraper
- `hype.social_volume` — blocked external access; Reddit excluded from Polish MVP
- `hype.local_fan_buzz` — planned, club-specific source configuration needed
- `hype.sentiment` — deferred until attention volume/acceleration first prove forecast value

## Automation

- Media Attention Collector: GitHub Action at `4,19,34,49 * * * *`
- Hype research readiness/CV refresh: `hype_challenger_summary_6h`

These are internal jobs only. They do not send ChatGPT notifications and do not change production P50.
