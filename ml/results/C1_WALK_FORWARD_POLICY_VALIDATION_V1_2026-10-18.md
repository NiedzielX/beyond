# C1 Walk-forward Policy Validation v1 — Result 2026-10-18

Status: **COMPLETED / POLICY SAFE ON CURRENT 4 FORWARD EVENTS / NO PROMOTION**

This result belongs to:

**Walidacja obecnego modelu — najpierw sprawdzić, co naprawdę mamy.**

## Question

Raw Live generalises worse than Structural Prior on the four chronological forward events.

The relevant product question is therefore:

> Does the already-frozen v8 `Prior vs Live` policy protect the final prediction by refusing unsafe Live corrections?

No v8 threshold was changed or refitted for this experiment.

## Evidence source

GitHub Actions run: `39140096251`  
Head commit: `1065cf686d1575086a0b3ae7b3af526f65466b79`  
Artifact: `c1-walk-forward-policy-validation-v1-39140096251`  
Artifact SHA256: `db10c4d3fce60b6cf81867847fe304efc59395b3f3c81c21196c8d942b5a5fb8`

Dataset:

- version: `c1-alpha-training-export-v1`;
- 9 independent completed events available;
- 30 real final-24h rows;
- minimum earlier training events before forward scoring: **5**;
- scored forward events: **4**;
- scored rows: **16**.

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Governance:

- policy thresholds refit: **false**;
- policy thresholds changed: **false**;
- future events used for training: **false**;
- test events real only: **true**;
- production activation: **false**;
- frozen v8 package changed: **false**.

## Real-only Live expert through frozen v8 policy

| Metric | Structural Prior | Raw Live | Final v8 policy |
|---|---:|---:|---:|
| Window MAE | **452.8** | 2,103.7 | **452.8** |
| Latest-row MAE | **452.8** | 2,197.3 | **452.8** |

Policy behaviour:

- Live selected rows: **0 / 16**;
- Prior selected rows: **16 / 16**;
- Live selection rate: **0%**;
- worst policy degradation vs Prior: **0.0**.

Therefore on these four later events:

> The frozen v8 policy correctly rejected the weak Live expert every time and exactly preserved Structural Prior performance.

## Event-level result

| Event | Prior MAE | Raw Live MAE | v8 Policy MAE | Selected rows |
|---|---:|---:|---:|---|
| Jagiellonia Białystok – Górnik Zabrze | 86.9 | 3,269.1 | **86.9** | 4/4 PRIOR |
| Pogoń Szczecin – Korona Kielce | 89.1 | 1,179.2 | **89.1** | 4/4 PRIOR |
| Legia Warszawa – Wisła Kraków | 851.7 | 1,566.4 | **851.7** | 4/4 PRIOR |
| GKS Katowice – Wieczysta Kraków | 783.4 | 2,400.0 | **783.4** | 4/4 PRIOR |

Main rejection reasons included:

- `live_slope_not_positive`;
- `insufficient_disagreement`.

This matches the intended v8 safety logic: Live is not trusted merely because a Live prediction exists.

## Synthetic Live variants through the same fixed policy

The policy was also applied to independently generated train-only synthetic Live variants in this run.

| Training mode | Raw Live MAE | Final policy MAE | Live selected rows |
|---|---:|---:|---:|
| `conservative_synthetic` | 1,954.6 | **452.8** | 0 / 16 |
| `stress_synthetic` | 2,212.4 | **452.8** | 0 / 16 |

The exact synthetic raw-Live numbers differ from the standalone synthetic experiment because this workflow uses its own deterministic augmentation seed. The important policy result is unchanged: **all 16 rows stayed on Prior**.

## Decision

`real_only_policy_beats_raw_live = true`

`real_only_policy_beats_prior = false`

`real_only_policy_safe_vs_prior = true`

`promotion_allowed = false`

Interpretation:

1. raw Live is not currently safe as a universal replacement for Structural Prior;
2. train-only synthetic augmentation improves raw Live in the dedicated validation experiment and remains worth developing;
3. the already-frozen v8 gate behaved conservatively and safely on all four chronological forward events;
4. this is retrospective validation, not prospective proof;
5. frozen v8 remains unchanged;
6. production remains `live_adjustment = 0`.

## What this means for the plan

The main immediate validation concern is narrower than before.

We do **not** currently have evidence that final v8 inherits the raw-Live walk-forward failure. On the current four forward events it does not — it falls back to Prior.

The remaining uncertainty is whether v8 can also recognise future cases where Live is genuinely better and safely switch to it. That requires more independent real events, especially prospective outcomes.

Synthetic trajectory augmentation should continue as a train-side challenger, but not be promoted automatically.
