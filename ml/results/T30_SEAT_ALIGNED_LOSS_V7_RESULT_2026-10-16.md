# T-30 Seat-Aligned Loss v7 — rolling-origin result

Date: **2026-10-16**  
Decision: **STOPPED AT PRE-VALIDATION / NO PRODUCTION CHANGE**

Candidate:

`structural-prior-t30-v7-seat-aligned-extra`

## Hypothesis

The low-occupancy mechanism audit showed that the worst T-30 failures are high absolute-demand matches in large-capacity environments. Because the production target is an occupancy residual while the primary evaluation metric is absolute attendance MAE, v7 tested direct objective alignment:

- target remained verified-capacity occupancy residual;
- baseline remained `baseline_season`;
- feature set remained the production full PIT contract;
- ExtraTrees structural parameters remained 500 trees / leaf=3 / max_features=0.8;
- criterion changed from squared error to `absolute_error`;
- training `sample_weight = verified capacity`.

Rationale:

`capacity * |occupancy residual error| = absolute seat error`.

2024/25 and 2025/26 were **not scored**.

## Rolling-origin result

### Fold A — train 2021/22 -> evaluate 2022/23

- current MAE: **2,157.147**;
- v7 MAE: **2,191.742**;
- v7: **1.60% worse**;
- current bias: -35.841;
- v7 bias: +182.014.

Low baseline occupancy <=45% improved modestly:

- current MAE: 2,737.839;
- v7 MAE: 2,673.504.

### Fold B — train 2021/22 + 2022/23 -> evaluate 2023/24

- current MAE: **2,559.741**;
- v7 MAE: **2,631.453**;
- v7: **2.80% worse**;
- current bias: -433.388;
- v7 bias: -388.445.

Low baseline occupancy <=45% worsened:

- current MAE: 4,532.877;
- v7 MAE: 4,671.155.

### Combined

N = **587**.

- current MAE: **2,358.101**;
- v7 MAE: **2,411.223**;
- v7: **2.25% worse**;
- current bias: -234.276;
- v7 bias: **-102.730**.

The fit improved average bias but increased absolute-error dispersion and failed the primary metric.

## Gate

- improves Fold A: **NO**;
- improves Fold B: **NO**;
- combined improvement >=3%: **NO**;
- result: `STOP_PRE_VALIDATION_GATE_NOT_MET`.

## Decision

- do not score 2024/25 or 2025/26;
- do not promote or freeze v7 for prospective shadow;
- do not change production target/loss/estimator;
- production remains `structural-prior-runtime-v1-t30-extra-full`.

## R&D conclusion

The controlled 2026-10-16 v2-v7 cycle tested estimator regularization, historical baseline smoothing, capacity-normalized historical anchoring, cold-start-only anchoring, explicit baseline occupancy state, and seat-aligned loss weighting.

None produced a robust pre-registered improvement sufficient for promotion. Continuing parameter/model-family experimentation on the same historical evidence would increase selection bias without a new mechanism.

**Historical T-30 architecture R&D is therefore paused.**

Next priority:

- prospective 2026/27 evidence collection;
- live-data quality and checkpoint completeness;
- reliable actual-attendance/outcome capture;
- same-event Structural Prior vs future live-correction evaluation readiness.

Reopen historical T-30 challenger work only when new data, a genuinely new structural signal, or a new locked evaluation period exists.
