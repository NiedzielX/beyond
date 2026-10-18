# Beyond Ticketing — C1 Synthetic Trajectory Validation v1

Last updated: **2026-10-18**  
Status: **EXPERIMENTAL VALIDATION**

This experiment belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

It tests whether train-only synthetic trajectory augmentation helps the current C1 v2 live expert generalise better to real unseen events.

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

Real observations retain most of the training weight.

For synthetic profiles the current experiment assigns:

- real rows: **65% of each event's total training weight**;
- synthetic rows combined: **35%**.

Each real event still contributes equal total event weight, regardless of how many real/synthetic rows it has.

## Profiles

### `real_only`

No augmentation. This should reproduce the current v2-style baseline as closely as possible.

### `conservative_synthetic`

Small, bounded perturbations intended to represent plausible trajectory observation variation.

This is the only augmentation profile that may become a serious challenger if it improves real held-out performance.

### `stress_synthetic`

Larger perturbations used as a robustness/stress test.

A good result here is interesting, but this profile is not intended to be promoted directly.

## Validation

### 1. Leave-One-Event-Out

Every completed event becomes the real held-out event once.

Primary outputs:

- window MAE;
- latest-row MAE;
- improvement rate vs Structural Prior;
- worst-event degradation;
- delta vs `real_only`.

### 2. Chronological walk-forward

Events are ordered by kickoff.

For each later event:

- training uses only earlier completed events;
- test uses the next real event;
- no future event/outcome can influence training or augmentation.

This is a stricter approximation of how the model would have behaved over time.

## Interpretation

Synthetic augmentation is considered **promising**, not proven, only if conservative augmentation improves the real-only model on real held-out events in both:

- LOEO;
- chronological walk-forward.

Even then:

- frozen C1 v8 is not changed automatically;
- production remains `live_adjustment = 0`;
- prospective validation is still required.

## Why this is not perpetuum mobile

Synthetic variants cannot create new information about real future outcomes. They can only help the model use the limited real information more robustly.

Success is measured exclusively on real events that were not used to create the synthetic training variants.

## Implementation

Script:

`ml/c1_synthetic_trajectory_validation_v1.py`

Workflow:

`.github/workflows/c1-synthetic-trajectory-validation-v1.yml`

The workflow uses the existing main-only C1 training export and uploads the full JSON evidence artifact.
