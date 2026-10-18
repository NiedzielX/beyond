# Beyond Ticketing — C1 Synthetic Trajectory Validation v1

Last updated: **2026-10-18**  
Status: **COMPLETED / NOT PROVEN FOR PROMOTION**

This experiment belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

It tests whether train-only synthetic trajectory augmentation helps the current C1 v2 live expert generalise better to real unseen events.

Canonical result:

`ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`

## Result in one sentence

Synthetic augmentation improved LOEO on real held-out events, but did **not** establish reliable chronological generalisation; the current live expert still loses badly to Structural Prior on the four walk-forward folds.

## Main numbers

### Leave-One-Event-Out — 9 real events

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 2,757.0 |
| `conservative_synthetic` | 3,968.7 | 2,813.4 | **2,582.1** |
| `stress_synthetic` | 3,968.7 | **2,742.4** | 2,582.3 |

### Chronological walk-forward — 4 real later events

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **1,711.0** | 4,499.9 | 4,455.0 |
| `conservative_synthetic` | **1,711.0** | 4,550.5 | 4,465.3 |
| `stress_synthetic` | **1,711.0** | **4,383.3** | **4,332.6** |

Decision:

`conservative_augmentation_signal = NOT_PROVEN`

`promotion_allowed = false`

Frozen C1 v8 and production are unchanged.

## What this is

We have only a small number of completed events with useful live trajectory history. Synthetic augmentation is used as a **regularisation experiment**, not as fake evidence.

We compare three training modes using the same real held-out events:

1. `real_only`;
2. `conservative_synthetic`;
3. `stress_synthetic`.

Current model under test:

`ridge_directocc_compact_generic_a10`

## Hard rule

> Synthetic data may exist only on the training side. The held-out / scored event is always 100% real.

For every LOEO fold:

- one real event is removed from training;
- no row from that event is used to generate synthetic data;
- training uses the remaining real events;
- synthetic variants may be generated only from those training events;
- evaluation is performed only on the untouched real held-out event.

The same rule applies to chronological walk-forward: only earlier real events may generate synthetic training variants.

## What is synthetic

Synthetic rows preserve the real training event and its real final attendance.

We perturb only plausible observable trajectory conditions, including bounded changes to:

- public availability / availability index;
- net inventory movement;
- 6h / 24h velocity;
- matched absorption;
- release / coverage effects;
- acceleration;
- small timestamp / observation-position jitter;
- limited missingness in live trajectory features.

The purpose is to make the model less sensitive to one exact observed trajectory shape.

## What is NOT synthetic

We do **not** generate:

- fake held-out matches;
- fake final attendance outcomes and then score against them;
- thousands of synthetic events counted as independent evidence;
- synthetic rows in the test set;
- synthetic evidence used to claim production MAE.

A synthetic row remains part of its real source training event and does not increase independent event count.

## Weighting

For synthetic profiles:

- real rows retain **65% of each event's total training weight**;
- synthetic rows combined receive **35%**.

Each real event still contributes equal total event weight regardless of synthetic row count.

## Profiles

### `real_only`

No augmentation. Reproduces the current v2-style baseline.

### `conservative_synthetic`

Small, bounded perturbations intended to represent plausible trajectory observation variation.

This profile improved LOEO but did not improve chronological walk-forward, so it is **not proven**.

### `stress_synthetic`

Larger perturbations used as a robustness/stress test.

It improved both LOEO and walk-forward relative to `real_only`, but the absolute walk-forward live error remained far worse than Structural Prior. It is therefore not promotable evidence.

## Why this is not perpetuum mobile

Synthetic variants cannot create new information about real future outcomes. They can only help the model use limited real information more robustly.

Success is measured exclusively on real events that were not used to create the synthetic training variants.

## Implementation

Script:

`ml/c1_synthetic_trajectory_validation_v1.py`

Workflow:

`.github/workflows/c1-synthetic-trajectory-validation-v1.yml`

Successful evidence run:

`39139461760`

Artifact:

`c1-synthetic-trajectory-validation-v1-39139461760`

## Next validation step

Do not move from this result directly to promotion or claim that synthetic data solved C1.

Within **Walidacja obecnego modelu**, diagnose why chronological walk-forward produces ~4.4–4.5k live MAE vs ~1.7k Structural Prior MAE on four later events, and identify whether the failure is caused by domain/club shift, sparse history, coverage differences or unstable trajectory features.
