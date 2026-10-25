# P11 Context Families — Target-Free Audit

Date: **2026-10-25**

Status: **P11a COLLECTING / P11b CONTRACT LIVE / P11c DATA-BOUND / P11d PARTLY CLOSED + COLLECTING**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Purpose

Audit the remaining P11 context families without opening new attendance labels or fitting a new model.

Roadmap order:

1. P11a — market-implied match quality / uncertainty;
2. P11b — price / promotion context;
3. P11c — lineup / star strength / verified absences;
4. P11d — weather / attention / hype.

This audit is target-free and is intended to prevent rebuilding already-existing collectors or reopening closed research loops under a new name.

## P11a — market odds

Status: **GENUINE_PIT_DATA_ACCUMULATING**.

First genuine capture completed successfully and scheduled six-hour capture is enabled.

Canonical evidence:

`ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`

Current readiness after the first capture:

- genuine PIT events: 2;
- events with >=3 bookmakers: 2;
- events reaching 24h: 2;
- events reaching 72h: 1;
- events reaching 168h: 0;
- model precommitted: false.

Decision: **collect only; no P11a model yet**.

## P11b — price / promotion

### Existing data

The existing ticketing pipeline already collects genuine price context:

- `ticket_price_observations_v1`: **118,156 rows / 7 events** at audit time;
- `sector_price_area_observations_v1`: **241,525 rows / 13 events**;
- existing ticketing/price collection jobs are healthy.

Future-event coverage at the audit time:

- event 6 Lech Poznań vs Wisła Kraków: full ticket-price + price-area context;
- event 22 Legia Warszawa vs Lech Poznań: price-area context only; no full ticket-price observations.

### New PIT-safe contract

Live function:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

It exposes only data captured at or before `as_of_at`:

- min / median / max positive visible ticket price;
- zero-price presence as a separate factual field;
- number of price areas / price types / distinct prices;
- previous-capture median price and delta;
- visible price-area inventory mix;
- capture lineage / timestamps;
- target-free / production-safe flags.

Historical-cutoff replay was verified: an earlier `as_of_at` returns the earlier price/inventory state rather than today's state.

### Promotion rule

There is **no explicit promotion source in the current schema audit**.

Therefore:

- promotion flag remains `null`;
- `explicit_evidence_available=false`;
- price reductions are **not** labeled as promotions;
- the contract explicitly records `DO_NOT_INFER_PROMOTION_FROM_PRICE_CHANGE`.

Decision: **P11b representation contract is ready; model/ablation remains separately gated**.

## P11c — lineup / stars / verified absences

Existing source:

`public.sporting_verified_absences`

Current genuine evidence at audit time:

- total verified absence rows: **1**;
- active/PIT-valid rows: **1**;
- represented teams: **1**.

The only active row is official-source evidence for a Lech Poznań player absence and is genuinely time-stamped before the relevant future event.

The refresh job is healthy, but the data volume is insufficient for a controlled attendance ablation.

Decision:

**DATA_BOUND. Continue collection. Do not fit an absence/star-strength challenger.**

No missing absence is interpreted as "no absence" unless the source coverage contract later proves that interpretation valid.

## P11d — weather

Existing prospective/weather infrastructure is already substantial:

- `weather_forecast_observations`: **518 rows / 23 events** at audit time;
- both future events in the 14-day window had PIT-known weather;
- weather collector is healthy.

Existing weather research status:

`research_only_no_uplift`

Historical study metadata:

- study: `weather-signal-v1-t7-ecmwf`;
- historical sample: 37 matches / 3 seasons;
- prospective weather events: 19;
- prospective weather rows: 502 at the status check;
- prospective T-24 outcome pairs: 10.

Decision:

**Do not reopen the same weather mechanism as a new P11d experiment.**

Weather can be reconsidered only with a materially new mechanism or as a separately precommitted interaction after another context family demonstrates value.

## P11d — media attention / hype

Existing prospective-only collector:

`media_attention_samples_v2`

Audit state:

- sample rows: >1,000;
- event coverage: 12;
- non-zero collector events: 5;
- completed eligible events for media attention: 7 across 7 clubs;
- prospective T-24 events: 12 across 11 clubs;
- historical backfill allowed: **false**.

Current readiness:

- `hype.media_attention`: `prospective_collecting`;
- `hype.mention_acceleration`: `prospective_collecting_warmup`;
- local fan buzz: planned;
- search interest: blocked by external access;
- social volume: blocked by external access;
- sentiment: deferred until attention itself proves value.

At the audit time the headline media-attention feature still lacks sufficient useful variance for evaluation.

Decision:

**Continue prospective-only collection; do not force an ablation yet.**

## Collector health

Latest audited runs for these existing pipelines were successful:

- ticketing/price collection;
- weather collection;
- verified absence refresh;
- attention health refresh;
- event-context snapshots;
- price-area pricing refresh.

No duplicate collector was added.

## Current P11 decision tree

`P11a odds -> collecting genuine PIT data`

`P11b price -> as-known representation ready; promotion evidence missing; no model yet`

`P11c absences -> data-bound`

`P11d weather -> existing mechanism closed/no uplift`

`P11d attention -> prospective collecting, not yet evaluation-ready`

## Guardrails

- no attendance labels were queried for this audit;
- no future target observations were used;
- no closing odds are backfilled;
- no promotion is inferred from price movement;
- missing absence data is not treated as a negative absence signal;
- existing weather no-uplift evidence is not relabeled/reopened;
- no production activation;
- `live_adjustment = 0`.
