# Beyond Ticketing — Context Matrix v0.1

Status: **frozen research prior**  
Target: **final attendance / demand pressure**  
Production impact on P10/P50/P90: **none until explicit promotion**

## Why this exists

The matrix defines what contextual evidence Beyond wants to collect around each ticketed event. The weights are **research priors**, not trained model coefficients. They help us prioritise data collection and interpret signals consistently before enough completed events exist to estimate stable effects.

## Groups and research-prior weights

| Group | Weight | Current role |
|---|---:|---|
| Live Ticketing Signal | 45% | existing live-signal research / primary dynamic evidence |
| Sporting Context | 30% | point-in-time research evidence |
| Attention & Hype | 15% | forward-only point-in-time research evidence |
| Match Context | 10% | point-in-time/static research evidence |
| Weather | 0% | shadow only; historical test did not improve accuracy |
| Data Quality | 0% | confidence modifier, never demand itself |

Active-prior weights sum to 100%. This does **not** mean the forecast is calculated as a weighted average of these groups.

## Feature matrix

| Feature | Prior weight | Data status | Score status | P50 status |
|---|---:|---|---|---|
| ticketing.trajectory_position | 18% | available | research/live feature | not promoted by this matrix |
| ticketing.velocity_24h | 10% | available | research/live feature | not promoted by this matrix |
| ticketing.velocity_6h | 7% | available | research/live feature | not promoted by this matrix |
| ticketing.acceleration | 5% | available | research/live feature | not promoted by this matrix |
| ticketing.scarcity | 5% | available | research/live feature | not promoted by this matrix |
| sport.match_stakes | 12% | collecting | heuristic v0.1 available | **shadow/research** |
| sport.rivalry_opponent | 7% | collecting | raw verified flags/evidence | **shadow/research** |
| sport.form5 | 6% | collecting | raw values | **shadow/research** |
| sport.absence_impact | 5% | collecting | demand-shock scoring refuses unsupported salience | **shadow/research** |
| hype.search_interest | 4% | not automated | none | **shadow/research** |
| hype.social_volume | 3% | not automated | none | **shadow/research** |
| hype.mention_acceleration | 3% | derived from sampled media windows when enough history exists | comparison ratio | **shadow/research** |
| hype.media_attention | 2% | **15-minute sampled collection active** | sampled Polish match mentions + rolling comparison | **shadow/research** |
| hype.local_fan_buzz | 2% | not automated | none | **shadow/research** |
| hype.sentiment | 1% | not automated | deliberately low priority | **shadow/research** |
| match.timing | 4% | collecting | raw context | **shadow/research** |
| match.competition_stage | 3% | collecting | raw context | **shadow/research** |
| match.opponent_historical_uplift | 3% | historical-data dependent | none yet | **shadow/research** |
| weather.kickoff_context | 0% | collecting | historical test negative | **shadow only** |
| dq.release_activity | 0% | available | confidence modifier | never demand |
| dq.sector_coverage_change | 0% | available | confidence modifier | never demand |

## Sporting Context v0.1

### Match Stakes

`league_match_stakes_v01` produces a transparent 0–100 **research score** from:
- season progress;
- home club table zone (title/Europe/relegation proximity);
- direct-table-clash proximity;
- late-season endgame pressure.

Rivalry and opponent prestige are intentionally excluded and are separate features.

For a UEFA-style league phase, `european_league_phase_stakes_v01` uses competition baseline, league-phase progress and previous-result pressure.

Every stored score must carry `research_heuristic_not_model_active`.

### Absence Impact

We distinguish:
1. **sporting availability** — a player is unavailable;
2. **ticket-demand shock** — the absence is likely to change fan demand.

A confirmed injury alone is not enough to create a demand score.

Research formula:

`Demand Shock = Player Salience × Absence Certainty × Novelty × 100`

If Player Salience is unsupported, the scorer returns no number. A long-known injury should receive low novelty even when absence certainty is near 1.0.

## Attention & Hype v0.1

For the Polish MVP:
- Reddit is excluded as a core source;
- volume and acceleration matter more than positive/negative sentiment;
- source relevance should be club/match specific;
- Polish-audience attention is preferred over generic global volume;
- no source should be promoted if its commercial-use rights or rate limits are unsuitable for Beyond.

### Active media-attention source

The active forward-only collector uses **GDELT Web News NGrams sampled data**, not the legacy GDELT DOC search API.

Why:
- the legacy DOC API returned repeated `429` responses during integration tests;
- Google News RSS was technically accessible but its feed terms were unsuitable for Beyond's commercial/product use;
- raw GDELT Web News NGrams files are downloadable without an application API key and GDELT explicitly recommends Web NGrams for rate-limited/high-volume native-language research.

Collection model:
1. GitHub Actions runs at minutes `07, 22, 37 and 52` of each hour;
2. GitHub OIDC obtains a short-lived token with audience `beyond-media-ingest`;
3. Supabase Edge verifies the OIDC token and returns the current event/team-alias configuration — no Supabase service-role secret is stored in GitHub;
4. the runner selects one recent immutable GDELT Web NGrams source file;
5. for each team, all document IDs containing any configured alias are collected;
6. match-level candidates are the intersection of home-team and away-team document IDs, even when the two team names occur in different n-gram rows of the same article;
7. the source TOC is read only for candidate documents and Polish-language candidates are persisted as `media_attention_samples`;
8. `(ticket_event_id, source_file_timestamp)` is unique, so rerunning the same GDELT interval cannot double-count a sample;
9. `dashboard_attention_context_v1` compares rolling sampled windows and exposes a layperson status to the dashboard.

The media count is explicitly a **sampled signal**, not a complete count of all articles on the internet.

Interpretation gates:
- fewer than 12 samples in the current 24h window → `collecting_baseline`;
- at least 12 current samples but fewer than 12 comparison samples → `collecting_comparison`;
- at least 12 samples in both windows and zero mentions in both → `no_signal`;
- only when both windows have at least 12 samples and at least one mention exists is an acceleration ratio interpreted as `rising`, `falling` or `stable`.

A zero in an individual sample is **not** interpreted as “no hype”. `no_signal` is available only after the comparison gate above is satisfied.

Current candidate order after media attention:
1. search interest;
2. public social volume/acceleration;
3. club-specific local fan buzz;
4. sentiment last.

## Data-quality / leakage rules

Every context observation must be point-in-time and contain:
- `ticket_event_id`;
- `feature_key`;
- `observed_at`;
- source identity;
- source record key;
- confidence;
- raw value/evidence.

No post-kickoff fact may be backdated into a pre-match feature snapshot.

A structural inventory release or sector-coverage change modifies confidence; it is never interpreted as demand by itself.

## Promotion rule

A context feature may affect production P10/P50/P90 only after a documented out-of-sample comparison shows incremental value over the relevant baseline.

Minimum comparison sequence:
1. baseline;
2. baseline + ticketing;
3. + sporting;
4. + attention/hype;
5. weather remains separate unless new evidence reverses the current negative historical result.

Evaluation must be event-level, not snapshot-level, to avoid pseudo-replication.

Until promotion, dashboard copy must explicitly say that contextual features are informative and **do not yet change the main forecast**.
