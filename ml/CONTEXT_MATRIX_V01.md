# Beyond Ticketing — Context Matrix v0.1

Status: **frozen research prior**  
Target: **final attendance / demand pressure**  
Production impact on P10/P50/P90: **none until explicit promotion**

## Why this exists

The matrix defines what contextual evidence Beyond wants to collect around each ticketed event. The weights are **research priors**, not trained model coefficients. They help us prioritise data collection and interpret signals consistently before enough completed events exist to estimate stable effects.

Active-prior weights sum to 100%. This does **not** mean the forecast is calculated as a weighted average of these groups.

## Groups and research-prior weights

| Group | Weight | Current role |
|---|---:|---|
| Live Ticketing Signal | 45% | primary dynamic evidence |
| Sporting Context | 30% | point-in-time research evidence |
| Attention & Hype | 15% | forward-only point-in-time research evidence |
| Match Context | 10% | event metadata + leakage-safe historical evidence |
| Weather | 0% | shadow only; historical test did not improve accuracy |
| Data Quality | 0% | confidence modifier, never demand itself |

## Feature matrix

| Feature | Prior weight | Data status | Score status | P50 status |
|---|---:|---|---|---|
| ticketing.trajectory_position | 18% | automated | research/live feature | not promoted by this matrix |
| ticketing.velocity_24h | 10% | automated | research/live feature | not promoted by this matrix |
| ticketing.velocity_6h | 7% | automated | research/live feature | not promoted by this matrix |
| ticketing.acceleration | 5% | automated | research/live feature | not promoted by this matrix |
| ticketing.scarcity | 5% | automated | research/live feature | not promoted by this matrix |
| sport.match_stakes | 12% | **automated shadow + verified reference** | heuristic v0.1 + source comparison | **shadow/research** |
| sport.rivalry_opponent | 7% | **verified registry + automatic propagation** | verified rivalry flag; opponent attractiveness still unscored | **shadow/research** |
| sport.form5 | 6% | verified manual | last five relevant matches across competitions | **shadow/research** |
| sport.absence_impact | 5% | **verified registry + automatic propagation** | no demand score without supported player salience | **shadow/research** |
| hype.search_interest | 4% | **blocked: Google Trends alpha access** | none | **shadow/research** |
| hype.social_volume | 3% | **blocked: X developer access/credits** | none | **shadow/research** |
| hype.mention_acceleration | 3% | automated GDELT sampler + health watchdog | comparison ratio after evidence gate | **shadow/research** |
| hype.media_attention | 2% | automated GDELT sampler + health watchdog | sampled Polish match mentions | **shadow/research** |
| hype.local_fan_buzz | 2% | planned | none | **shadow/research** |
| hype.sentiment | 1% | deferred | deliberately low priority | **shadow/research** |
| match.timing | 4% | **automated refresh** | raw event context | **shadow/research** |
| match.competition_stage | 3% | **automated refresh; stage may remain explicitly unknown** | raw event context | **shadow/research** |
| match.opponent_historical_uplift | 3% | **automated shadow readiness gate** | median attendance uplift only after sample gate | **shadow/research** |
| weather.kickoff_context | 0% | automated collection | historical test negative | **shadow only** |
| dq.release_activity | 0% | automated | confidence modifier | never demand |
| dq.sector_coverage_change | 0% | automated | confidence modifier | never demand |

## Sporting Context v0.1

### Match Stakes — 12%

`league_match_stakes_v01` produces a transparent 0–100 research score from season progress, home-club table zone, direct-table-clash proximity and late-season pressure. Rivalry and opponent prestige remain separate features.

Ekstraklasa has a shadow-only automated validation path:
1. Supabase `pg_cron` calls TheSportsDB round endpoints through `pg_net` every 6 hours;
2. fixtures are cached in `sporting_league_matches_shadow`;
3. a match counts toward standings **only when `strStatus = FT`**; live/HT scores are ignored;
4. standings are reconstructed from completed matches;
5. the Match Stakes formula is reproduced in SQL;
6. each shadow score is compared with the latest verified reference and stored in `sporting_context_shadow_samples`;
7. Model Lab reads `dashboard_sporting_shadow_v1` and `dashboard_sporting_shadow_summary_v1`.

The first validated run produced **7 exact matches out of 9 comparable upcoming Ekstraklasa events**. The two differences were consistent with the automated source containing a newer completed Radomiak result than the older manual reference. A delta is therefore a review signal, not automatically an error.

TheSportsDB free v1 is a **shadow research source, not the canonical production provider**.

### Rivalry / opponent attractiveness — 7%

Verified rivalry relationships are stored once in `sporting_rivalry_relations` and automatically propagated to matching fixtures. The first relation is Górnik Zabrze–Piast Gliwice (`Derby Śląska`) from previously verified official club evidence.

Rules:
- configured relation = verified rivalry;
- missing relation = **unknown**, never “not a rivalry”;
- opponent attractiveness is not invented by the registry and remains a separate future/historical-learning problem.

### Recent Form — 6%

`sport.form5` means the **last five relevant matches across competitions**, not simply the last five league fixtures. TheSportsDB free `eventslast.php` returned only one event per team during validation, so automating it would silently change the feature definition. It remains verified manual research until a complete recurring cross-competition source is available.

### Absence Impact — 5%

Verified absences are stored in `sporting_verified_absences` and propagated automatically to future fixtures during their active validity window. The initial registry contains João Moutinho based on verified official Lech evidence.

Rules:
- missing player = unknown, not confirmed available;
- an estimated recovery window is not converted into an exact automatic return date;
- `review_due_at` is a quality-review reminder, not an auto-expiry;
- a confirmed absence alone does not create a demand score.

Research formula remains:

`Demand Shock = Player Salience × Absence Certainty × Novelty × 100`

If player salience is unsupported, the score stays null.

## Match Context v0.1

### Timing — 4%

`refresh_match_context_base_v2()` refreshes kickoff day/time from `ticket_events` in `Europe/Warsaw`. A reschedule updates the stable v2 observation instead of leaving stale timing context.

### Competition / stage — 3%

Competition is refreshed from `ticket_events`. When stage is not provided by the source, Beyond stores it explicitly as unknown (`stage_status = not_provided_by_event_source`) rather than inferring knockout/league phase from the competition name.

### Historical opponent uplift — 3%

`refresh_opponent_historical_uplift_shadow_v1()` implements a leakage-safe readiness gate. For each future home match it uses only verified outcomes with kickoff strictly before the target kickoff, in the same home club and canonical competition class, within a 730-day lookback.

A score is emitted only when:
- at least **8** prior home outcomes exist for the club; and
- at least **3** prior home meetings exist with the same opponent.

When ready:

`Opponent uplift = opponent median attendance / club median attendance - 1`

Until both gates are met, `uplift_pct` remains null. Insufficient history is never represented as a fake 0% effect.

## Attention & Hype v0.1

Volume and acceleration are prioritised over sentiment. All hype signals remain research-only and do not affect P50.

### Media attention + mention acceleration — 5%

The forward-only collector uses **GDELT Web News NGrams sampled data**. It is a sampled signal, not a complete count of all articles on the internet.

Flow:
1. GitHub Actions targets a 15-minute cadence (`04,19,34,49` each hour);
2. GitHub OIDC obtains a short-lived token for `beyond-media-ingest`;
3. Supabase Edge returns the live event/team-alias configuration;
4. the runner scans one recent immutable GDELT NGrams source file;
5. match candidates are document IDs mentioning both configured teams;
6. Polish-language candidates are persisted to `media_attention_samples`;
7. `(ticket_event_id, source_file_timestamp)` is unique;
8. `dashboard_attention_context_v1` compares rolling windows.

Interpretation gates:
- fewer than 12 current samples → `collecting_baseline`;
- enough current samples but fewer than 12 comparison samples → `collecting_comparison`;
- only after both windows have enough coverage can Beyond classify `rising`, `falling`, `stable` or `no_signal`.

A zero in one sample is never interpreted as “no hype”.

#### Collector health watchdog

GitHub scheduled workflows are best-effort. Beyond therefore monitors persisted sample freshness independently in Supabase:
- expected cadence: 15 minutes;
- older than 45 minutes → `degraded_automation`;
- `dashboard_attention_collector_health_v1` exposes health to the dashboard;
- the Event Detail panel warns when collection is stale and does not interpret stale comparison windows.

The re-registered workflow successfully completed an end-to-end run and persisted a fresh sample; the watchdog returned to `healthy` immediately afterward. Scheduled recurrence still remains health-monitored rather than assumed.

### Search interest — 4%

The correct source is the **official Google Trends API alpha**, because it supports arbitrary monitored terms, consistently scaled search interest and geographic restrictions. Access remains limited to accepted alpha testers.

The public `bigquery-public-data.google_trends` dataset was evaluated and rejected as a match-level proxy: it contains daily Top 25 / Top 25 Rising terms rather than arbitrary query interest. Using it would create selection bias and false zeroes for normal club matches.

Status: `blocked_external_access`. No unofficial Google Trends scraper is used.

### Social volume — 3%

Preferred source: **X API v2 search**. X currently exposes consumption-based API billing, so Beyond can later use narrow configured match queries at explicit checkpoints instead of a firehose.

Activation requires:
- approved X developer app;
- API credentials;
- purchased credits/billing setup.

Reddit is excluded from the commercial MVP unless Beyond enters a separate Reddit agreement. Reddit’s current Data API / Developer Terms require separate commercial permission; no Reddit scraping is used.

### Local fan buzz — 2%

Planned as a club-specific source registry rather than one universal Polish forum scraper. Each source must be evaluated for public accessibility, stability and permitted commercial use before automation.

### Sentiment — 1%

Deliberately deferred. Raw positive/negative sentiment is not treated as a strong demand feature until volume/acceleration evidence proves useful.

## Data-quality / leakage rules

Every context observation must be point-in-time and contain source identity, source record key, observation timestamp and confidence/evidence where applicable.

No post-kickoff fact may be backdated into a pre-match feature snapshot.

A structural inventory release or sector-coverage change modifies confidence; it is never interpreted as demand by itself.

A shadow source may be newer than a verified reference. Such a delta must be preserved and reviewed rather than automatically treated as an error or overwriting the verified reference.

Unknown is a valid state. Missing rivalry, absence, stage, search interest or historical evidence must never silently become a negative/zero value.

## Promotion rule

A context feature may affect production P10/P50/P90 only after a documented out-of-sample comparison shows incremental value over the relevant baseline.

Minimum comparison sequence:
1. baseline;
2. baseline + ticketing;
3. + sporting;
4. + attention/hype;
5. weather remains separate unless new evidence reverses the current negative historical result.

Evaluation is event-level, not snapshot-level, to avoid pseudo-replication.

Until explicit promotion, dashboard copy must say that contextual features are informative and **do not yet change the main forecast**.
