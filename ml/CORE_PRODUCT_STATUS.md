# Beyond Ticketing — Core Product Status

Last verified: **2026-10-14**  
Purpose: canonical source of truth for the forecasting core, evidence gates, known gaps and the next implementation sequence.

> Product north star: Beyond must predict future attendance / ticket-demand behaviour over time, show how the forecast changes as the match approaches, and prove forecast quality on genuinely future matches. Growth/activation is downstream and must not distract from the forecasting core.

## Executive state

Beyond can already produce forecasts, but the investor-grade multi-club forecasting core is **not finished**.

Current position:

- verified attendance outcomes: **10 events / 7 clubs**;
- strict cross-club research dataset: **8 eligible events / 6 clubs**;
- cross-club study gate: **met** (`8/8` events, target `>=3` clubs; actual 6 clubs);
- learned-correction outcome gate: **10/20** total independent outcomes;
- Live Ticketing promotion evidence: **8/20** eligible completed events, **6 clubs**;
- Live Ticketing promotion gap: **12 more eligible completed events**;
- current/future monitored events: **13** through 2026-10-31 across **11 clubs**;
- current canonical Feature Store table `ml_feature_snapshots`: **0 rows** — schema exists, canonical population does not;
- current live runtime still uses the older `lech_v13_early_seasonality` historical baseline for Lech forecasts;
- the stronger frozen historical champion is **v1.7**, but exact executable v1.7 runtime inference is still not reconstructed and promoted;
- multi-club baseline v3 exists as a **research fallback**, not as a production forecasting engine;
- Weather, Sporting Context and Match Context remain out of P50 after negative validation;
- Hype is prospective-only and not yet testable on completed eligible T-24h events.

## What does “we can predict” mean?

There are three different gates and they must not be mixed.

### Gate A — Forecast exists

**Already true.** No additional matches are required simply to generate a P50/P10/P90-like forecast output for supported events.

This is not enough for an investor-quality claim because the current runtime, model lineage and multi-club coverage are inconsistent.

### Gate B — MVP evidence / first promotion review

Existing governance requires **20 independent eligible completed events** for the Live Ticketing candidate.

Current evidence: **8 / 20**.  
Missing: **12 eligible completed events**.

This is the minimum product/research gate for a first serious promotion review. It is not a guarantee of statistical certainty.

### Gate C — stronger investor-grade evidence

The current 8-event leave-one-club-out result is directionally positive but noisy.

Current incremental ticketing uplift versus the bias-only control is about **+166.8 MAE points** on average, but event-level effects are heterogeneous. A bootstrap of the current 8 event-level uplift observations has a 95% interval that crosses zero (approximately **-143 to +629** MAE points). Therefore 20 events should be treated as an MVP/process gate, not as the final proof that the feature is universally beneficial.

If the current effect size and variance were to remain similar, roughly **50+ independent eligible events** would be a more credible evidence milestone for a stable positive mean effect. This is a planning estimate, not a fixed mathematical requirement; it must be recalculated as new events arrive.

## Can we reach 20 quickly?

There are **13** currently tracked current/future events through 2026-10-31. One is Lech–Bayer 04 Leverkusen (UEFA Europa League), which is outside the current Ekstraklasa-only cross-club fallback baseline.

That leaves **12 upcoming league matches**.

### Baseline-ready now — 8 matches

Under the current fallback rule (Ekstraklasa home event + at least 3 prior verified home league attendances), these matches are baseline-ready now:

1. GKS Katowice – Pogoń Szczecin — 2026-10-17
2. Cracovia – Legia Warszawa — 2026-10-17
3. Lech Poznań – Korona Kielce — 2026-10-18
4. Pogoń Szczecin – Radomiak Radom — 2026-10-24
5. Jagiellonia Białystok – Wisła Płock — 2026-10-25
6. Legia Warszawa – Lech Poznań — 2026-10-25
7. Śląsk Wrocław – Wieczysta Kraków — 2026-10-25
8. Lech Poznań – Wisła Kraków — 2026-10-31

If all eight produce a valid prospective T-24h feature snapshot and a verified final attendance, Live Ticketing evidence would move from **8 to 16**, still four short of the 20-event gate.

### Not baseline-ready now — 4 league matches

1. Górnik Zabrze – Piast Gliwice — 2026-10-18
2. KGHM Zagłębie Lubin – Jagiellonia Białystok — 2026-10-18
3. Wisła Płock – Radomiak Radom — 2026-10-19
4. Wisła Kraków – Raków Częstochowa — 2026-10-24

Current `ml_match_history` has no historical home rows for these four clubs. The fastest path is **not to wait for more future home games**, but to collect and verify at least 3 prior Ekstraklasa home attendances for each club before the relevant T-24h checkpoint.

If those historical rows are added in time and the future T-24h snapshots remain valid, the 12 upcoming league matches are sufficient in principle to move Live Ticketing from **8/20 to 20/20 by the end of October 2026**. This still depends on valid scraper coverage, baseline generation, T-24h feature capture and verified post-match attendance for every event.

## The 12 questions we should always know

### 1. How is P50 generated today?

There are multiple layers and this is currently a core architecture gap.

- Stored Lech runtime/shadow forecasts still identify the historical baseline as `lech_v13_early_seasonality`.
- Current shadow rows use `beyond-demand-engine-v1-shadow`.
- The database stores `historical_p50`, `live_adjustment`, and `final_p50` separately.
- The stronger frozen historical champion is v1.7 (T-30/T-7), but exact executable v1.7 inference is not yet reconstructed in the current runtime.
- Multi-club `club_trailing_home_median_v3` exists only as a research fallback for checkpoint studies.

**Required correction:** one canonical prediction contract must explicitly distinguish production, shadow and challenger forecasts. The investor dashboard must never pick “latest row” across mixed statuses without filtering model role.

### 2. Which features actually enter the model?

For the current T-24h Live Ticketing challenger:

- model target: `actual_attendance / baseline_p50 - 1`;
- model family: one-feature Ridge;
- feature: `hybrid_v6`;
- `hybrid_v6` prefers sector-matched 6h inventory velocity and falls back to raw 6h velocity;
- Ridge alpha: 30.

The historical models have separate historical/context feature contracts. Weather, hype, sporting and match-context signals currently live in their own research pipelines and are not part of the promoted P50.

### 3. Do all features pass through one Feature Store?

**No. This is a P0 gap.**

`ml_feature_snapshots` exists but currently contains **0 rows**.

Point-in-time feature evidence is fragmented across:

- `event_context_snapshots_v1`;
- `forecast_observations` live payload fields;
- `weather_forecast_observations`;
- `media_attention_samples_v2`;
- sporting/context research tables;
- ticketing challenger dataset/views.

The next architecture milestone is to populate a canonical point-in-time Feature Store and make training/scoring consume the same feature contracts.

### 4. What is the baseline?

There are three different baseline concepts today:

1. historical runtime incumbent for Lech: v1.3-derived `lech_v13_early_seasonality`;
2. frozen historical research champion: **v1.7**;
3. multi-club research fallback: median verified prior home Ekstraklasa attendance, minimum 3 prior home outcomes (`club_trailing_home_median_v3`).

These must be unified into a clear runtime hierarchy.

### 5. How is train / validation / test handled?

Historical benchmark:

- no-leakage walk-forward by season;
- development: 2022/23 and 2023/24;
- untouched holdout: 2024/25 and 2025/26;
- attendance history is shifted to completed matches only;
- sporting context is pre-match only.

Live Ticketing challenger:

- canonical horizon: T-24h;
- leave-one-event-out (LOEO);
- leave-one-club-out (LOCO) — primary generalisation protocol;
- forward shadow scoring only for genuinely prospective checkpoints after training;
- no backfill using the fitted forward model.

### 6. Which model families have actually been compared?

Tested / documented:

- Rolling-5 baseline;
- opponent historical mean baseline;
- Gradient Boosting v1.3;
- Ridge horizon models (v1.4–v1.7);
- CatBoost challenger — rejected on untouched historical holdout;
- v1.8 Elo challenger — rejected;
- v1.8 prior-season opponent-popularity challenger — research-only;
- Live Ticketing Ridge residual challenger (`hybrid_v6`, alpha 30).

Not yet part of a canonical multi-club benchmark harness: global multi-club LightGBM/XGBoost-style models, temporal/global forecasting models such as Chronos, and a properly calibrated probabilistic/quantile stack.

### 7. What is performance by forecast horizon?

Historical documented results include:

- v1.4 T-30 Ridge MAE: 5,279.0;
- v1.4 T-7 Ridge MAE: 4,370.3;
- v1.4 T-1 Ridge MAE: 4,414.2;
- v1.6.1 T-30 MAE: 5,228.6;
- v1.6.1 T-7 MAE: 4,232.4;
- v1.7 T-30 OOS MAE: **4,723.8**;
- v1.7 T-7 OOS MAE: **4,151.1**.

The current multi-club Live Ticketing challenger is validated only at **T-24h**. We do not yet have a single canonical multi-club model evaluated consistently at T-14/T-7/T-3/T-1/T-6h. Building that horizon matrix is part of the core roadmap.

### 8. How good is cross-club generalisation?

Live Ticketing LOCO, 8 events / 6 clubs:

- baseline MAE: **5,266.1**;
- bias-only control MAE: **5,174.0**;
- challenger MAE: **5,007.3**;
- uplift vs baseline: **+258.9**;
- incremental uplift vs bias-only: **+166.8**.

Status: positive research signal, shadow-only, too small for promotion.

### 9. What did the Ticketing challenger prove?

It showed that 6h public-inventory movement contains incremental predictive signal beyond the baseline and beyond a simple bias-only correction on the current tiny sample.

It did **not** prove production-grade uplift yet. The sample is only 8 events and event-level effects are heterogeneous.

### 10. Why were Weather / Sporting / Match Context not promoted?

Current scorecard:

- Weather: historical leave-one-season-out challenger MAE **4,165.7** vs incumbent **3,896.9** — worse by about 268.8; rejected for P50, collection remains shadow.
- Sporting / Match Stakes: challenger MAE **7,314.0** vs Baseline + Ticketing **5,007.3** — materially worse; rejected.
- Match Context / weekend flag: challenger MAE **7,102.8** vs Baseline + Ticketing **5,007.3** — materially worse; rejected.

The correct behaviour is to keep collecting raw context but not force weak features into P50.

### 11. Is Hype ready?

No.

Current scorecard:

- eligible completed validation events: **0 / 8** initial testability gate;
- eligible clubs: **0 / 5**;
- prospective events with evidence: 0 at the current completed T-24h gate;
- GDELT collection exists, but media-attention automation is currently marked degraded;
- no historical Hype backfill is allowed because the feature is intentionally prospective-only.

Hype must remain shadow until genuinely future events complete.

### 12. What important modelling techniques are still missing?

The highest-value missing work is not “try random algorithms”. It is:

1. reconstruct executable historical v1.7 in runtime;
2. create one canonical point-in-time Feature Store;
3. establish a global multi-club training dataset and benchmark;
4. compare pre-registered model families under the same LOCO/time-aware protocol;
5. build horizon-specific models or a single model with horizon as a feature, then benchmark both approaches;
6. calibrate P10/P50/P90 using quantile loss and empirical interval coverage;
7. add model registry / prediction role (`production`, `shadow`, `challenger`) and stop mixing rows by recency alone;
8. maintain ablation so Weather/Hype/Sporting only enter if they add out-of-sample value.

## Immediate core-product backlog

### P0 — canonical prediction contract

Create a single forecast contract with at least:

- event ID;
- `as_of_at`;
- horizon;
- model version;
- historical baseline version;
- feature-set version;
- prediction role: production / shadow / challenger;
- P10/P50/P90;
- point-in-time validation flag;
- source feature snapshot ID;
- data-quality / signal-readiness metadata.

Dashboard must explicitly select production predictions; shadow/challenger rows belong in Model Lab.

### P0 — Feature Store v1

Populate `ml_feature_snapshots` from the existing point-in-time source tables. Do not recompute training features using future state.

Recommended first canonical families:

- historical baseline/context;
- ticketing inventory level/index;
- 6h and 24h velocity;
- acceleration;
- sector-matched movement;
- release/coverage quality flags;
- timing / competition metadata;
- weather shadow features;
- hype shadow features;
- sporting/match-context shadow features.

Training and inference must consume the same versioned feature contracts.

### P0 — historical runtime alignment

Reconstruct exact executable v1.7 inference and run it in shadow alongside the existing v1.3-derived runtime. Do not silently replace v1.3 until same-protocol future evidence passes governance.

### P0 — make the next 12 league matches eligible

Before their T-24h checkpoints, collect and verify historical Ekstraklasa home attendance for:

- Górnik Zabrze — minimum 3 prior home matches;
- Zagłębie Lubin — minimum 3;
- Wisła Płock — minimum 3;
- Wisła Kraków — minimum 3.

This is the fastest route to potentially reaching the 20-event Ticketing gate by the end of October rather than waiting for four additional future fixtures.

### P0 — outcome capture

Every monitored completed match must receive a verified attendance outcome and source as soon as possible after completion. An event without a verified outcome cannot become model evidence.

### P1 — 20-event retraining / benchmark

At 20 eligible events:

- freeze the dataset version;
- retrain the pre-registered model families;
- run LOCO as the primary protocol;
- keep bias-only control;
- report MAE, WAPE/MAPE where appropriate, bias, median AE and per-club/per-horizon diagnostics;
- create a promotion candidate only if governance passes.

### P1 — canonical horizon matrix

Evaluate at minimum:

- T-14d;
- T-7d;
- T-3d;
- T-24h;
- T-6h / T-1 where coverage permits.

The MVP should visually show how prediction uncertainty contracts and P50 changes as kickoff approaches.

### P2 — stronger evidence milestone

Continue from 20 to approximately **50+ independent eligible events** across multiple clubs. Re-estimate the required sample from observed effect size/variance rather than treating 50 as a hard permanent rule.

## What the investor MVP should show

For each selected match:

1. current public-demand state and data quality;
2. P10 / P50 / P90 at multiple historical checkpoints;
3. forecast trajectory over time;
4. final verified attendance when the match completes;
5. error for each checkpoint;
6. baseline vs Beyond comparison;
7. transparent model version / confidence / data freshness;
8. portfolio-level accuracy across completed matches and clubs.

The strongest investor statement is not “we have AI”. It is:

> Beyond observes public ticket-demand behaviour before kickoff, turns it into point-in-time features, predicts final attendance at defined horizons, and proves on future multi-club matches whether the live signal improves a leakage-safe historical baseline.

## Current strategic rule

Do not add a feature to production because it sounds useful.  
Do not promote a model because it is more sophisticated.  
Do not display a shadow forecast as production because it is the newest row.  
Do not claim causal commercial impact without causal data.

**Every change must improve the forecasting core or improve the evidence that the forecasting core works.**
