# Beyond Ticketing — C1 Synthetic Trajectory Validation v1

Last updated: **2026-10-18**  
Status: **COMPLETED / PROMISING FOR FURTHER VALIDATION / NO PROMOTION**

This experiment belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

It tests whether train-only synthetic trajectory augmentation helps the current C1 v2 live expert generalise better to real unseen events.

Canonical result:

`ml/results/C1_SYNTHETIC_TRAJECTORY_VALIDATION_V1_2026-10-18.md`

## Result in one sentence

Synthetic augmentation improved the raw Live expert on real held-out events in both LOEO and chronological walk-forward, but raw Live still lost to Structural Prior on the four chronological events.

## Main numbers

### Leave-One-Event-Out — 9 real events

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 3,046.6 |
| `conservative_synthetic` | 3,968.7 | **2,261.5** | **2,213.9** |
| `stress_synthetic` | 3,968.7 | 2,498.8 | 2,481.7 |

### Chronological walk-forward — 4 real later events

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **452.8** | 2,103.7 | 2,197.3 |
| `conservative_synthetic` | **452.8** | 1,939.5 | 2,017.0 |
| `stress_synthetic` | **452.8** | **1,876.7** | **1,915.2** |

Decision:

`conservative_augmentation_signal = PROMISING_FOR_FURTHER_VALIDATION`

`promotion_allowed = false`

Frozen C1 v8 and production are unchanged.

## Hard rule

> Synthetic data may exist only on the training side. The held-out / scored event is always 100% real.

For every validation fold:

- the real test event is excluded from training;
- no row from that event is used to generate synthetic data;
- synthetic variants may be generated only from training events;
- evaluation is performed only on untouched real events;
- synthetic rows never count as new independent matches.

## What is synthetic

Synthetic rows preserve the real training event and its real final attendance.

We perturb plausible observable trajectory conditions, including bounded changes to:

- public availability / availability index;
- net inventory movement;
- 6h / 24h velocity;
- matched absorption;
- release / coverage effects;
- acceleration;
- small timestamp / observation-position jitter;
- limited missingness in live trajectory features.

## What is NOT synthetic

We do **not** generate:

- fake held-out matches;
- fake final attendance outcomes and then score against them;
- synthetic events counted as independent evidence;
- synthetic rows in the test set;
- synthetic evidence used to claim prospective production MAE.

## Weighting

For synthetic profiles:

- real rows retain **65% of each event's total training weight**;
- synthetic rows combined receive **35%**.

Each real event still contributes equal total event weight regardless of synthetic row count.

## Profiles

### `real_only`

No augmentation. Current v2-style baseline.

### `conservative_synthetic`

Small, bounded trajectory perturbations.

This profile produced the best LOEO result and improved chronological walk-forward vs `real_only`.

### `stress_synthetic`

Larger perturbations used as a robustness/stress test.

It produced the best raw-Live chronological walk-forward result, but still remained much worse than Structural Prior on those four events.

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

Artifact SHA256:

`428bff63d8b01b19c81199c4d2c482cf7e1dd551c3e6bb2d48677aa6e702e00a`

## Next validation step

Synthetic augmentation is worth keeping as a challenger/regularisation technique, but it does not justify replacing Structural Prior with raw Live.

Next, validate whether the fixed v8 `Prior vs Live` policy protects the final forecast during chronological walk-forward without changing any v8 thresholds.
