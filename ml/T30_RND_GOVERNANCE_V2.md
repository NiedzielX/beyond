# Beyond — T-30 Historical R&D Governance v2

Effective: **2026-10-16**

## Why this exists

T-30 is the highest-priority Structural Prior horizon for club actionability and remains above the strategic `<1700 MAE` objective.

On 2026-10-16, T-30 Challenger v2 was selected on 2023/24, frozen, then evaluated once on 2024/25 and 2025/26. It improved development MAE by 1.43% but failed to generalize: combined validation MAE worsened from 1867.64 to 1879.51.

The lesson is methodological, not a new tuning signal: **a small one-season development win is insufficient evidence for T-30 promotion.**

## Evidence status after 2026-10-16

The seasons 2024/25 and 2025/26 have now been exposed to T-30 R&D decisions and must no longer be described as pristine or untouched holdouts for future challenger cycles.

They remain useful as:

- fixed historical validation/regression seasons;
- comparability evidence against already-published model generations;
- stability diagnostics after a candidate has been fully pre-registered.

They must not be used to iteratively tune parameters, features, blending weights, baselines or model-family choices.

Fresh promotion evidence must come from genuinely unseen prospective outcomes (currently 2026/27) or from another explicitly locked future evaluation period.

## Pre-validation gate for every new T-30 challenger

Before reading the exposed historical validation seasons, a challenger must be selected using only the pre-validation development window.

Default rolling-origin folds:

1. **Fold A** — train 2021/22, evaluate 2022/23;
2. **Fold B** — train 2021/22 + 2022/23, evaluate 2023/24.

The production T-30 runtime must be scored on the same folds as the control.

A candidate may proceed only when all are true:

- the hypothesis and candidate family were defined before validation-season results are read;
- no future/PIT leakage is introduced;
- it improves the production control on **both** rolling-origin folds;
- its combined rolling-origin improvement is material; default gate is **>=3% MAE improvement** unless a different threshold is explicitly pre-registered before the experiment;
- bias and worst-fold behaviour do not materially deteriorate;
- the exact candidate spec is frozen in Git before any historical validation/regression read.

Failing this gate means **stop**. Do not open 2024/25 or 2025/26 merely to see what happens.

## Historical validation/regression after a candidate passes the gate

2024/25 and 2025/26 can then be evaluated once for the frozen candidate as an exposed-but-fixed regression set.

Required reporting:

- MAE per season and combined;
- median AE;
- WAPE;
- bias;
- sample count;
- delta vs current production runtime;
- club/season stability where useful.

A weak or mixed result blocks promotion and must not trigger parameter tweaking inside the same challenger version.

## Production promotion

Historical improvement alone is not enough to silently replace the live T-30 runtime.

Promotion requires:

- frozen reproducible code/artifact;
- successful PIT/current-event compatibility;
- historical regression evidence;
- no degradation of the live materializer/resolver contract;
- explicit human review;
- prospective 2026/27 evidence once enough outcomes exist to make the comparison meaningful.

Until then, challengers remain research/shadow candidates.

## T-30 v3 registered hypothesis

The next challenger family is **PIT-safe home-demand baseline smoothing**, not further ExtraTrees leaf/max-feature tuning.

Rationale:

`baseline_season` switches to the current-season home mean as soon as one current-season home attendance exists. At T-30, that estimate can be based on very few matches and therefore be noisy.

v3 will test a pre-registered shrinkage baseline using only already-available PIT fields:

- `season_home_n`;
- `season_home_mean`;
- `prev_season_home_mean`;
- `home_attendance_mean` as fallback;
- verified capacity and the existing Structural Prior PIT feature contract.

Candidate selection will use only Fold A + Fold B above. 2024/25 and 2025/26 will not be read unless the pre-validation gate is passed.

## Prohibited shortcuts

Do not:

- tune v2 ExtraTrees parameters from its 2024/25 or 2025/26 errors;
- repeatedly open the historical validation seasons for weak dev candidates;
- relabel an exposed season as untouched;
- use current-match attendance or later sporting state in historical features;
- promote on one aggregate metric while hiding a materially worse fold/season;
- auto-promote a challenger from CI.
