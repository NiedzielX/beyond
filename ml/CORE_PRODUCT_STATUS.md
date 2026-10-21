# Beyond Ticketing — Core Product Status

Last verified: **2026-10-21**

Purpose: current product/model source of truth. Research strategy is governed by `ml/MAE_RESEARCH_ROADMAP_V3.md`; detailed package state is in `ml/CURRENT_MODEL.md`.

> **North star:** minimize true out-of-sample attendance-forecast MAE early enough for clubs to act, while preserving point-in-time safety, reproducibility and honest evidence classes.

## Executive state

Beyond has three distinct forecasting layers that must not be conflated:

1. a **global historical / structural core** trained across Ekstraklasa;
2. **frozen live-ticket packages** collecting forward evidence;
3. a separate **MAE-first challenger R&D lane** that continues without waiting for prospective labels.

Production does not automatically consume any research package.

`live_adjustment = 0`

until explicit reviewed activation.

---

## Global historical core

Current research champion family: **Global Model v2.1**.

Data:

- 1,530 complete Ekstraklasa matches across 2021/22–2025/26;
- 306 matches per season;
- 7,650 canonical PIT snapshots = 1,530 matches × five horizons;
- horizons: T-30d, T-14d, T-7d, T-3d, T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global learned residual -> structural P50`

Selected model families in the frozen v2.1 historical experiment:

- HistGradientBoosting at T-30/T-7/T-3/T-1;
- XGBoost at T-14.

Historical later-season results:

| Horizon | 2024/25 baseline MAE | 2024/25 model MAE | 2025/26 baseline MAE | 2025/26 model MAE |
|---|---:|---:|---:|---:|
| T-30 | 2491.3 | **2092.6** | 2633.5 | **2061.5** |
| T-14 | 2436.1 | **1998.5** | 2508.4 | **1979.6** |
| T-7 | 2340.0 | **1800.5** | 2429.1 | **1896.4** |
| T-3 | 2316.6 | **1785.3** | 2397.5 | **1851.7** |
| T-1 | 2297.5 | **1749.6** | 2396.9 | **1833.7** |

This is roughly 16–24% historical MAE improvement over the club-history baseline across the two later seasons.

Important: these seasons have now been repeatedly inspected. They remain valuable historical evidence but are no longer unseen for new challenger development.

---

## Current feature signal

Feature families already shown to contain useful signal include:

- home attendance / demand history;
- opponent demand;
- home–opponent pair history;
- timing / seasonality;
- sporting state;
- recent-vs-long-run demand trends.

Current product conclusion:

> **More predictive information has produced more reliable gains than decorative model complexity.**

New feature families enter the point forecast only after leakage-safe ablation demonstrates incremental MAE improvement.

---

## Frozen final24 live package

Current package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Purpose:

- prospective validation;
- delayed-label diagnostics;
- eventual promotion evidence.

It must not be retuned from future outcomes.

Pre-Live v3 T-1 is exactly equivalent to v2 T-1 on the frozen replay, so no cosmetic final24 retrain is justified.

---

## Frozen long72 live package

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope: `24<hours_to_kickoff<=72`

Architecture:

- T-3 frozen anchor;
- inventory-linear-extrapolation;
- ±0.10 occupancy cap;
- P2 observation-maturity reliability.

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`.

This is exposed historical research evidence, not production proof.

---

## Evidence Lane vs R&D Lane

### Evidence Lane

Frozen packages collect forward evidence without mutation.

Long72 must use two-phase persistence:

`forecast materialized before label -> label attached later -> errors appended`

### MAE R&D Lane

Development continues immediately and independently.

Current priority:

1. rolling / forward validation;
2. MAE-native losses / median forecasts;
3. uncertainty around `ΔMAE`;
4. new PIT-safe fixture-cannibalization context;
5. controlled context ablations;
6. forecast combinations;
7. live inventory as incremental residual over the strongest structural model;
8. 72–168h learned model after `N>=9`;
9. modest club-specific calibration only if it improves pooled generalization.

---

## Next context hypothesis

The first new context family to test is **fixture substitution / cannibalization**.

Candidate features:

- days until next home match;
- attractiveness/strength of next opponent;
- next-match competition / importance;
- fixture density over 7/14/30 days;
- time since previous home match.

Then test verified absences, rivalry/stakes, PIT weather forecasts and PIT-safe media/search/social attention.

---

## Forecast combination direction

Do not assume one single model must dominate.

Combine materially different sources:

- global structural forecast;
- MAE-native residual model;
- new context forecast;
- live inventory correction;
- final24 live correction where relevant.

Test simple mean/median and convex blends before complex stacking. Learn weights only inside training folds.

---

## Validation state

Historical/global development must now emphasize rolling/expanding time-respecting folds rather than repeatedly optimizing against already-opened later seasons.

Live research must keep the event as the independent unit and add forward-event views ordered by kickoff.

Random row/snapshot splits are not accepted as headline evidence.

---

## 72–168h

Last audited valid independent-event coverage above 72h: `8`.

Predeclared research-start floor: `N>=9`.

At `N>=9`, freeze exact event/as-of identities before opening results and create a new challenger package. The threshold starts research; it is not a production gate.

---

## Current modelling priority

The next modelling milestone is no longer “wait for prospective evidence”.

It is:

> **Global structural model + forward validation + MAE-aligned challengers + new PIT-safe context + forecast combination, while frozen live packages collect prospective evidence in parallel.**

## Production boundary

Research champion status never changes production by itself.

Promotion requires genuine future evidence, reproducible frozen lineage, lower prospective MAE, acceptable bias/tail behavior and explicit reviewed activation.
