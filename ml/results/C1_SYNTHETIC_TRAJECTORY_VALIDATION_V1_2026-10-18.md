# C1 Synthetic Trajectory Validation v1 — Result 2026-10-18

Status: **COMPLETED / PROMISING FOR FURTHER VALIDATION / NO PROMOTION**

This result belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## Evidence source

GitHub Actions run: `39139461760`  
Head commit: `358c6850383867f69f26d956c0a1b4d2b8870f59`  
Artifact: `c1-synthetic-trajectory-validation-v1-39139461760`  
Artifact SHA256: `428bff63d8b01b19c81199c4d2c482cf7e1dd551c3e6bb2d48677aa6e702e00a`

Dataset:

- version: `c1-alpha-training-export-v1`;
- independent completed events: **9**;
- real final-24h rows used by this experiment: **30**;
- model: `ridge_directocc_compact_generic_a10`;
- test rows were always real;
- synthetic variants were train-only and never counted as independent events.

## Leave-One-Event-Out — 9 real held-out events

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | 3,968.7 | 2,929.3 | 3,046.6 |
| `conservative_synthetic` | 3,968.7 | **2,261.5** | **2,213.9** |
| `stress_synthetic` | 3,968.7 | 2,498.8 | 2,481.7 |

Delta vs `real_only`:

- conservative: **667.8 MAE better** window and **832.8 better** latest-row;
- stress: **430.5 better** window and **565.0 better** latest-row.

Interpretation:

> Synthetic trajectory augmentation materially improved the raw live expert in LOEO on real held-out events.

Conservative perturbation was better than the more aggressive stress profile in LOEO.

## Chronological walk-forward — 4 later real events

A minimum of five earlier completed events was required before scoring a later event, therefore four events could be evaluated chronologically.

| Training mode | Structural Prior MAE | Live window MAE | Live latest-row MAE |
|---|---:|---:|---:|
| `real_only` | **452.8** | 2,103.7 | 2,197.3 |
| `conservative_synthetic` | **452.8** | 1,939.5 | 2,017.0 |
| `stress_synthetic` | **452.8** | **1,876.7** | **1,915.2** |

Delta vs `real_only`:

- conservative: **164.2 MAE better** window and **180.2 better** latest-row;
- stress: **227.0 better** window and **282.0 better** latest-row.

Interpretation:

> Synthetic augmentation also improved the raw live expert in chronological walk-forward. It did not make raw Live better than Structural Prior on these four events.

So two things are simultaneously true:

1. synthetic trajectory augmentation is helping the live model generalise better;
2. raw Live should still not replace Structural Prior universally.

## Automated experiment decision

`conservative_augmentation_signal = PROMISING_FOR_FURTHER_VALIDATION`

`promotion_allowed = false`

The conservative profile beat `real_only` in all four required comparisons:

- LOEO window;
- LOEO latest-row;
- walk-forward window;
- walk-forward latest-row.

This is a real signal because every scored event remained real and held out from augmentation.

It is **not** enough to promote a model because:

- only 9 independent completed events exist in this live dataset;
- only 4 events can currently be tested in chronological walk-forward;
- synthetic data creates robustness, not new real outcome information;
- prospective evidence is still required.

## Final interpretation

Synthetic trajectory variants are worth keeping as a **train-side regularisation technique**.

They do not create a perpetuum mobile and do not replace new real matches. Their value is narrower:

> use the limited real events more efficiently by teaching the live expert plausible variations of trajectory shape, then validate only on untouched real events.

The next validation question is not whether raw Live should replace Prior. It should not.

The next question is whether the already-frozen v8 `Prior vs Live` gate correctly rejects Live when it is unsafe in chronological walk-forward.
