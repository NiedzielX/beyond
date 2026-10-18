# C1 Forward Event Diagnostic v1 — 2026-10-18

Status: **COMPLETED / HETEROGENEOUS RAW-LIVE FAILURE / NO MODEL CHANGE**

## Evidence

GitHub Actions run: `39147616986`  
Main commit: `ec9d1bde84142e515437ba5d4bdd61a1d97318f3`  
Artifact: `c1-forward-event-diagnostic-v1-39147616986`  
Artifact id: `12143434981`  
Artifact SHA256: `66c454c867aeb73be81e9264e18f3f03424af12bb5d3f122c356d7892206f727`

Experiment:

`c1-forward-event-diagnostic-v1`

The diagnostic reused the same four retrospective chronological forward folds as the fixed-v8 policy validation. It did not change frozen v8, policy thresholds, production or the training set.

## Baseline result

| Metric | Structural Prior | Raw Live |
|---|---:|---:|
| Window MAE | **452.8** | 2,103.7 |
| Latest-row MAE | **452.8** | 2,197.3 |

Raw Live latest-row error direction:

- underprediction: **3 / 4 events**;
- overprediction: **1 / 4 events**;
- exact: **0 / 4**.

This rejects a simple single-direction global calibration explanation.

## Feature-group ablation

Each row refits the same direct-occupancy Ridge after removing one compact feature group. Negative delta means the ablated model improved relative to full raw Live.

| Removed group | Window MAE | Delta vs full | Latest MAE | Latest delta | Events improved — window |
|---|---:|---:|---:|---:|---:|
| `release_coverage` | 2,077.4 | **-26.3** | 2,283.5 | +86.2 | 1 / 4 |
| `motion_velocity` | 2,094.5 | **-9.2** | **1,852.5** | **-344.7** | 1 / 4 |
| `baseline_prior` | 2,120.5 | +16.8 | 2,195.6 | -1.6 | 1 / 4 |
| `data_quality` | 2,216.5 | +112.8 | 2,432.2 | +234.9 | 1 / 4 |
| `inventory_level` | 2,759.0 | +655.4 | 2,789.4 | +592.2 | 2 / 4 |

### Interpretation

There is **no feature group whose removal consistently fixes the four events**.

- the best aggregate window ablation, `release_coverage`, improves only **26 seats MAE** and only **1 / 4 events**;
- `motion_velocity` materially improves the latest-row aggregate, but its window effect is almost neutral and event-specific;
- removing `inventory_level` is strongly harmful in aggregate, so public-inventory level is not globally the problem;
- therefore this evidence does not justify deleting or globally down-weighting any feature group.

Ablation is diagnostic sensitivity, not causal attribution.

## Event-level result

| Event | Prior window MAE | Raw Live window MAE | Latest raw-Live signed error | Strongest local diagnostic |
|---|---:|---:|---:|---|
| Jagiellonia Białystok – Górnik Zabrze | **86.9** | 3,269.1 | -3,536.2 | large feature-state drift; removing `baseline_prior` reduces raw-Live error but still leaves it far behind Prior |
| Pogoń Szczecin – Korona Kielce | **89.1** | 1,179.2 | -1,151.4 | `prior_expected_occupancy`, `available_index` and `signal_ready` are shifted vs training; no stable ablation fix |
| Legia Warszawa – Wisła Kraków | **851.7** | 1,566.4 | -2,320.6 | strongest local case: removing `motion_velocity` improves window MAE by ~857; removing `release_coverage` by ~717 |
| GKS Katowice – Wieczysta Kraków | **783.4** | 2,400.0 | +1,780.8 | opposite error sign; modest improvement when inventory/data-quality groups are removed |

## Drift observations

The largest train-vs-test robust median shifts are also event-specific:

- Jagiellonia – Górnik: `matched_sector_count` ~**+12.9** robust scales, `available_index` ~**+3.8**;
- Pogoń – Korona: `prior_expected_occupancy` ~**+3.34**, `available_index` ~**+2.54**, `signal_ready` ~**+2.41**;
- Legia – Wisła: `net_removed_24h` ~**-1.96**, `velocity_24h` ~**-1.94**, with higher missingness in those motion fields;
- GKS – Wieczysta: no comparably dominant single drift feature.

These shifts support a **small-sample / distribution-shift / event-interaction** diagnosis more than a single broken feature hypothesis.

## Prediction-path observation

The raw Live forecast does not fail in one uniform way:

- Jagiellonia – Górnik: raw Live remains materially below outcome and moves further away through much of the final window;
- Pogoń – Korona: persistent moderate underprediction;
- Legia – Wisła: underprediction worsens near kickoff as the Live path slopes down;
- GKS – Wieczysta: raw Live starts too high but moves toward the outcome.

All four latest raw-Live slopes are negative, but a negative slope is not itself universally wrong: it hurts the first/third cases while helping the fourth. This is another reason not to hard-code a global direction rule beyond the already-frozen v8 safety gate.

## Decision

1. **Do not change frozen C1 v8.** The gate correctly protected final forecasts in the preceding validation.
2. **Do not delete a compact feature group globally.** No ablation is stable across the four events.
3. Treat the raw-Live issue as **heterogeneous generalisation under very small independent-event count**, with event-specific feature-state drift and interactions.
4. Do not use these four events to retune the frozen package.
5. Continue prospective collection automatically and move active development to the next canonical workstream: **b) Current Season Adjustment**.

This result is retrospective diagnostic evidence only and does not permit production promotion.
