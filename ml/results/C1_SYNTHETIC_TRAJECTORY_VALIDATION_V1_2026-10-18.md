# C1 Synthetic Trajectory Validation v1 — Result 2026-10-18

Status: **COMPLETED / NOT PROVEN FOR PROMOTION**

This result belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## Evidence source

GitHub Actions run: `39139461760`  
Head commit: `479ee7446278a526bcca8434124219776ff87518`  
Artifact: `c1-synthetic-trajectory-validation-v1-39139461760`  
Artifact SHA256: `428bff63d8b01b19c81199c4d2c482cf7e1dd551c3e6bb2d48677aa6e702e00a`

Dataset:

- version: `c1-alpha-live-training-v1.0`;
- independent completed events: **9**;
- full live rows in export: **206**;
- real final-24h rows used by this experiment: **30**;
- model: `ridge_directocc_compact_generic_a10`;
- test rows were always real;
- synthetic variants were train-only and never counted as independent events.

## Leave-One-Event-Out — 9 real held-out events

| Training mode | Structural Prior MAE | Live model window MAE | Live model latest-row MAE | Worst event degradation vs Prior |
|---|---:|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 2,757.0 | 203.3 |
| `conservative_synthetic` | 3,968.7 | 2,813.4 | 2,582.1 | 85.9 |
| `stress_synthetic` | 3,968.7 | **2,742.4** | **2,582.3** | 163.8 |

Delta vs `real_only`:

- conservative: **-115.9 MAE** window and **-174.9 MAE** latest-row;
- stress: **-186.9 MAE** window and **-174.7 MAE** latest-row.

Interpretation:

> Synthetic trajectory augmentation improved the live expert in LOEO on real held-out events.

This is useful evidence that trajectory perturbation can act as regularisation on the current small dataset.

## Chronological walk-forward — 4 later real events

A minimum of five earlier completed events was required before scoring a later event, therefore only four events could be evaluated chronologically.

| Training mode | Structural Prior MAE | Live model window MAE | Live model latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **1,711.0** | 4,499.9 | 4,455.0 |
| `conservative_synthetic` | **1,711.0** | 4,550.5 | 4,465.3 |
| `stress_synthetic` | **1,711.0** | **4,383.3** | **4,332.6** |

Delta vs `real_only`:

- conservative: **+50.6 MAE worse** window and **+10.2 MAE worse** latest-row;
- stress: **-116.6 MAE better** window and **-122.4 MAE better** latest-row.

Interpretation:

> Conservative synthetic augmentation did not improve chronological generalisation. Stress augmentation improved the live expert relative to `real_only`, but the live expert still lost very clearly to Structural Prior on these four forward folds.

The key result is therefore not that synthetic data solved the model-quality problem. It did not.

## Decision

Automated experiment decision:

`conservative_augmentation_signal = NOT_PROVEN`

`promotion_allowed = false`

Current conclusion:

1. synthetic trajectory augmentation is a useful **research / regularisation direction**;
2. it improves LOEO on the nine real events;
3. it is **not proven** under chronological walk-forward;
4. chronological walk-forward exposes a larger problem: the current v2 live expert generalises poorly when trained only on genuinely earlier events;
5. frozen C1 v8 remains unchanged;
6. production remains `live_adjustment = 0`;
7. no synthetic result may be presented as prospective accuracy.

## What this changes in the plan

Stay inside **Walidacja obecnego modelu** before moving to b/c/d.

Immediate validation work should explain the chronological failure, especially:

- which four forward events create the error;
- whether the issue is club/domain shift, sparse live history, phase/coverage differences or unstable live features;
- whether the Structural Prior/live disagreement can identify when the live expert should not be trusted;
- whether train-only synthetic augmentation can be narrowed to realistic perturbations that improve forward folds without damaging other events.

Synthetic augmentation remains a challenger/regularisation technique, not a new source of truth.
