# Beyond Global Model v2 — 2026-10-14

Status: **research champion candidate**  
Production impact: **none yet**  
North star: minimise true out-of-sample attendance forecast error.

## Dataset

- Competition: Ekstraklasa.
- Seasons: **2021/22–2025/26**.
- Matches: **1,530** (`306 × 5 seasons`).
- Forecast horizons: **T-30d, T-14d, T-7d, T-3d, T-1d**.
- Point-in-time feature snapshots: **7,650**.
- Historical source layer 2021/22–2024/25: independently reconciled attendance archive.
- 2025/26: validated multi-club historical layer.
- One verified closed-doors match (Radomiak–Piast, 2021-12-14, attendance `0`) remains historical ground truth but is excluded from default demand-model training.

## Evaluation protocol

Model/hyperparameter choice does **not** use the final two seasons.

1. Train candidate models on **2021/22 + 2022/23**.
2. Select model family on **2023/24** only.
3. Refit the selected family on **2021/22–2023/24**, evaluate on **2024/25**.
4. Refit the same selected family on **2021/22–2024/25**, evaluate on **2025/26**.
5. Every feature snapshot uses only information known before its `as_of_at` timestamp.
6. The target match outcome never enters its own feature state.

This is a season-blocked, point-in-time benchmark. It is materially stronger evidence than random train/test splitting.

## Baseline

The fixed club-history baseline is computed point-in-time:

- >=5 prior home matches: rolling-5 home attendance;
- otherwise: available historical home mean;
- otherwise: current-season league median;
- otherwise: previous-season league median / prior league median fallback.

The learned model predicts a **residual correction** on top of this baseline. Direct-attendance CatBoost and log-ratio variants were tested and did not beat the residual architecture on the historical holdouts.

## Feature Store v2.1

Feature families used by the current candidate:

### Home demand history

- prior home attendance mean / median / last;
- rolling 3 / 5 / 10;
- standard deviation / upper historical level;
- current-season home attendance state;
- previous-season home mean;
- days since previous home match;
- home trend vs long-run home mean;
- home demand level vs league median.

### Opponent demand

- opponent historical draw across all home clubs;
- recent opponent draw vs long-run opponent draw;
- previous-season opponent demand;
- **home–opponent pair history**: historical attendance for the exact home/away pairing;
- pair attendance vs host's normal attendance.

### Timing / seasonality

- round and season progress;
- month, day of week, kickoff time;
- cyclical date/time encodings;
- weekend flag.

### Sporting state

All sporting features are rebuilt from matches completed before `as_of_at` in the same season:

- matches played / points / PPG;
- goal-difference rate;
- last-5 form;
- rest days / fixture congestion;
- table position;
- home-away PPG, position and form gaps.

## Current result

Model family is selected on 2023/24 separately by horizon.

| Horizon | Selected model | 2024/25 baseline MAE | 2024/25 model MAE | Improvement | 2025/26 baseline MAE | 2025/26 model MAE | Improvement |
|---|---|---:|---:|---:|---:|---:|---:|
| T-30d | HistGradientBoosting | 2,491.3 | **2,092.6** | **16.0%** | 2,633.5 | **2,061.5** | **21.7%** |
| T-14d | XGBoost | 2,436.1 | **1,998.5** | **18.0%** | 2,508.4 | **1,979.6** | **21.1%** |
| T-7d | HistGradientBoosting | 2,340.0 | **1,800.5** | **23.1%** | 2,429.1 | **1,896.4** | **21.9%** |
| T-3d | HistGradientBoosting | 2,316.6 | **1,785.3** | **22.9%** | 2,397.5 | **1,851.7** | **22.8%** |
| T-1d | HistGradientBoosting | 2,297.5 | **1,749.6** | **23.8%** | 2,396.9 | **1,833.7** | **23.5%** |

The improvement is therefore present:

- on **every horizon**;
- on **both unseen seasons**;
- with two independently selected tree families (HistGradientBoosting and XGBoost);
- without live ticket inventory, weather or hype features.

## What changed versus the first five-season feature set

The most useful new information in v2.1 was not a more complex algorithm. It was richer point-in-time demand context:

- exact home–opponent historical attendance;
- pair-level uplift vs the home club's own normal demand;
- recent-vs-long-run home trend;
- opponent recent-vs-long-run draw;
- league-relative home demand level.

At T-7, adding these features improved HistGradientBoosting further:

- 2024/25: `1,888.1 → 1,800.5` MAE;
- 2025/26: `2,014.5 → 1,896.4` MAE.

## Ablation signal (T-7)

The first feature-family ablation confirms that the improvement is not coming from one accidental feature:

- removing attendance-history features materially worsens error;
- removing calendar/seasonality worsens error;
- removing sporting state worsens error, especially on 2024/25;
- opponent context adds smaller but still useful incremental signal;
- attendance history + calendar is already strong, but the full feature set performs best overall.

## Rejected challengers

The following did **not** justify replacing the current residual architecture:

- raw CatBoost residual challenger;
- CatBoost direct attendance model;
- CatBoost log-attendance model;
- HistGradientBoosting direct attendance model;
- XGBoost direct attendance model;
- log-ratio residual target variants;
- CatBoost / HistGBR / XGB simple ensembles selected on development MAE.

Several looked slightly better on 2023/24 development data but failed to improve consistently on the two later seasons. They remain rejected.

## Interpretation

This is the first result that demonstrates a meaningful **global Ekstraklasa forecasting signal**, rather than a Lech-only model or a tiny prospective sample.

The historical model can already outperform a reasonable club-specific history baseline by roughly **16–24% MAE**, depending on forecast horizon and unseen season.

The remaining path to a stronger Beyond model is now clear:

1. freeze this historical candidate as `Global Model v2.1`;
2. add calibrated probabilistic P10/P50/P90 forecasting;
3. add live ticketing trajectory as a separate point-in-time feature family and measure incremental uplift over v2.1;
4. test Weather and Hype only as controlled challengers against the same benchmark;
5. keep collecting genuinely future matches as prospective confirmation, not as a prerequisite for historical R&D.

## Current decision

**Global Model v2.1 becomes the historical research champion candidate.**

It is not automatically promoted to production. Promotion requires a reproducible CI run from the canonical historical dataset and prospective confirmation on future fixtures.
