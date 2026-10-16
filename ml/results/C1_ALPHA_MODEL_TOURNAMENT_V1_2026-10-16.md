# C1-alpha Model Tournament v1 — full-trajectory LOEO result

Date: **2026-10-16**  
Status: **completed / no correction candidate selected**

## Protocol

Dataset:

- 9 completed Ekstraklasa events compatible with the current Structural Prior domain;
- 206 point-in-time live trajectory rows;
- regularized sampling: latest snapshot in each event × 6h pre-kickoff bucket;
- current frozen Structural Prior replay at T-30/T-14/T-7/T-3/T-1;
- whole-event validation: **Leave-One-Event-Out**;
- equal event importance;
- no random snapshot split.

Implementation:

- `ml/C1_MODEL_TOURNAMENT_V1.md`;
- `ml/c1_alpha_model_tournament_v1.py`;
- `supabase/sql/c1_alpha_training_export_v1.sql`;
- `.github/workflows/c1-alpha-model-tournament-v1.yml`.

GitHub Actions run:

`38884934428`

Full evidence artifact:

`c1-alpha-model-tournament-v1-38884934428`

## Result

The tournament mixed all available live phases from the earliest observed snapshot through kickoff.

Structural Prior / zero-correction incumbent:

**MAE = 3,685.1**

Best candidate:

**zero correction**

No Ridge, ElasticNet, Huber, HistGradientBoosting, constrained tree, XGBoost or LightGBM live-correction candidate improved the aggregate whole-event LOEO MAE.

The strongest non-zero candidates were still worse than the incumbent. Example:

- bias median attendance residual: **3,993.6 MAE**;
- bias median occupancy residual: **3,998.6 MAE**;
- bias mean occupancy residual: **4,149.4 MAE**;
- bias mean attendance residual: **4,202.0 MAE**;
- Ridge alpha=100 occupancy: **4,566.0 MAE**.

Therefore:

- `beat_structural_prior = false`;
- `<1700 MAE = false`;
- `<1500 MAE = false`.

## Structural Prior replay by event

The aggregate result is highly heterogeneous.

| Event | Live rows | Structural Prior trajectory MAE | Latest-row error |
|---|---:|---:|---:|
| Lech Poznań — Raków Częstochowa | 65 | 2,756.0 | 5,031.1 |
| Lech Poznań — Jagiellonia Białystok | 57 | 7,421.0 | 6,691.8 |
| Lech Poznań — Radomiak Radom | 47 | 9,667.3 | 11,364.5 |
| Jagiellonia Białystok — Górnik Zabrze | 6 | 86.7 | 86.9 |
| Pogoń Szczecin — Korona Kielce | 9 | 203.9 | 89.1 |
| Cracovia — KGHM Zagłębie Lubin | 5 | 1,090.9 | 1,096.5 |
| Śląsk Wrocław — Lech Poznań | 1 | 9,723.4 | 9,723.4 |
| GKS Katowice — Wieczysta Kraków | 10 | 1,158.3 | 783.4 |
| Legia Warszawa — Wisła Kraków | 6 | 1,057.9 | 851.7 |

This result is **not directly comparable to the historical ~1.7–1.9k horizon benchmarks**, because this experiment averages a continuous replay across different live phases/checkpoint priors and contains very uneven trajectory coverage by event.

## Main diagnosis

The experiment answered an important question:

> **A single continuous correction model trained across the entire heterogeneous trajectory is not the right first C1-alpha formulation for the data currently available.**

The evidence coverage is strongly stage-dependent:

- only 2 completed events have live history extending to T-14;
- only 3 extend to T-7/T-3;
- **8 events have genuine T-1 coverage**;
- one additional completed event starts only within the final ~6h.

Therefore the all-phase model asks one learner to generalize across time regimes for which the number of independent events is radically different.

## Decision

Do **not** freeze or deploy a C1-alpha winner from v1.

Do **not** conclude that live ticketing has no predictive value. The earlier `Ticketing Challenger v1` already showed positive grouped-validation signal at the late checkpoint.

Next experiment:

### C1-alpha T-1 Tournament v2

Focus the next model on the strongest shared evidence window:

`T-1 -> kickoff`

Use:

- exact current Structural Prior T-1 as incumbent;
- exact T-1 / final-24h live inventory trajectory;
- ticketing hybrid signal where available;
- velocity / acceleration;
- sector-matched absorption/release where available;
- data-quality/source regime;
- whole-event LOEO validation.

The goal is to determine whether a late-stage ticketing correction can improve T-1 Structural Prior without contaminating the experiment with sparse T-14/T-7 evidence.

## Guardrail

The v1 negative result must not be used as justification to wait for future matches. It is a model-formulation result. We continue extracting more signal from the already completed matches by matching the model to the evidence window that actually has cross-event coverage.
