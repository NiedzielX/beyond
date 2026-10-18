# Beyond Ticketing — C2 Context Extension v2

Last updated: **2026-10-18**

Status: **ACTIVE EXPERIMENT / c2 STAGE 1 / NO PRODUCTION CHANGE**

## Purpose

Test whether two context families add incremental forecast accuracy beyond the current frozen historical **a2+b2 Pre-Live stack**:

1. sequence-aware sporting form;
2. PIT-safe match-stakes / table-pressure context.

This experiment does **not** retune `Future Fixture Context v1`.

## Baseline to beat

The baseline is not the old production Structural Prior alone.

Frozen historical stack before c2:

| Horizon | a2 base | b2 layer |
|---|---|---|
| T-30 | Structural Prior incumbent | none |
| T-14 | Structural Prior incumbent | none |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` |
| T-3 | Structural Prior incumbent | `ewma50-resid-k2-cap05-min3` |
| T-1 | Structural Prior incumbent | `ewma50-resid-k6-cap05-min3` |

The runner explicitly strips all new `ctx_*` columns from frozen baseline fitting before reproducing this stack. Known frozen-stack MAE values are hard-asserted.

## PIT event model

Context is reconstructed from the same canonical historical schedule/results input.

Events:

- forecast snapshot at `as_of_at` — priority 0;
- match result completion at `kickoff_at + 3h` — priority 1.

Events are sorted by:

`timestamp -> event priority -> match_key`

Therefore a snapshot at the same timestamp as a completion cannot see that result.

A match cannot see its own result.

Future results and final-season table state are forbidden.

Season participant identities are taken from the known schedule. Only their already-completed match state may influence context.

## Existing context not duplicated as-is

Structural Prior already has:

- PPG;
- GD/game;
- last-5 point sum;
- last-5 GD;
- current table positions/gaps;
- top4/bottom4 flags;
- rest/congestion;
- opponent draw / pair history.

C2 v2 adds **different representations** rather than copies of these values.

---

# A. Sequence-aware form

Current last-5 aggregates lose ordering information.

New PIT features:

- `ctx_home_win_streak`;
- `ctx_away_win_streak`;
- `ctx_home_unbeaten_streak`;
- `ctx_away_unbeaten_streak`;
- `ctx_home_loss_streak`;
- `ctx_away_loss_streak`;
- `ctx_home_points_accel3`;
- `ctx_away_points_accel3`;
- streak gaps;
- points-acceleration gap;
- home club's current home-only win streak;
- home club's current home-only unbeaten streak.

### Points acceleration

Requires at least 6 completed matches:

`sum(points last 3) - sum(points previous 3)`

Otherwise it is missing and handled by the frozen preprocessing contract.

This distinguishes, for example, `WWWLL` from `LLWWW` despite similar aggregate recent points.

---

# B. Match stakes / table pressure

These are continuous **pressure proxies**, not claims about official European qualification or relegation rules.

They use only table state known at `as_of_at`.

Known league format assumption used consistently with existing Structural Prior:

`34 matches per team`

At each snapshot calculate from completed matches only:

- leader points;
- current 4th-place points;
- current 15th-place points;
- each team's played matches;
- remaining maximum points = `3 * max(34 - played, 1)`.

### Title pressure

`season_progress * clip(1 - points_gap_to_leader / remaining_max_points, 0, 1)`

### Top-4 pressure proxy

`season_progress * clip(1 - abs(points - current_p4_points) / remaining_max_points, 0, 1)`

### Bottom-4 pressure proxy

`season_progress * clip(1 - abs(points - current_p15_points) / remaining_max_points, 0, 1)`

### Direct-points pressure

`season_progress * clip(1 - abs(home_points - away_points) / average_remaining_max_points, 0, 1)`

Derived:

- home maximum stakes;
- away maximum stakes;
- match maximum stakes;
- match mean stakes.

The `season_progress` multiplier prevents early-season table ties from being treated as high-stakes late-season states.

No final points, final positions or future match outcomes enter these features.

---

# Candidate groups

Exactly four contracts:

1. `NO_CONTEXT`;
2. `sequence_only`;
3. `stakes_only`;
4. `sequence_stakes`.

No threshold/feature-subset search beyond these predeclared groups.

## Context model architecture

For every horizon, preserve the same:

- baseline formula;
- categorical features;
- original a2 numeric feature contract;
- estimator family / hyperparameters.

Then append only the candidate context group's columns.

### T-7

Uses the frozen a2 model family/config:

- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate `0.04`;
- 300 iterations;
- 31 leaves;
- `min_samples_leaf=20`;
- L2 `1.0`;
- seed 42.

### Other horizons

Use their retained horizon-specific Structural Prior estimator unchanged.

## End-to-end b2 application

The context challenger produces a new historical base prediction.

Then the **same frozen b2 policy** is applied to that candidate's own earlier same-season prediction residuals:

- T-7: `ewma50-resid-k6-cap05-min3`;
- T-3: `ewma50-resid-k2-cap05-min3`;
- T-1: `ewma50-resid-k6-cap05-min3`;
- T-30/T-14: no b2 layer.

This is necessary to measure the actual incremental value of c2 over the current Pre-Live candidate stack.

---

# Selection protocol

Development folds only:

1. train 2021/22 -> evaluate 2022/23;
2. train through 2022/23 -> evaluate 2023/24.

A non-zero context group is eligible only if:

- MAE improves in both development folds;
- mean relative MAE improves by at least **0.5%**.

Among eligible candidates:

1. identify best mean development MAE gain;
2. keep candidates preserving >=90% of best gain;
3. minimize maximum worst-event degradation;
4. then p90 delta;
5. then absolute-bias delta;
6. then prefer fewer context columns;
7. deterministic ID.

If no group passes:

`selected = NO_CONTEXT`

## Reference scoring

Only after development selection is frozen:

- 2024/25;
- 2025/26.

References do not select context group or features.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

`promotion_allowed = false`

---

# Mandatory diagnostics

Per candidate/fold:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- exact worst-event degradation;
- exact best-event improvement;
- club breakdown where n>=5;
- context feature count;
- b2 active share after context-base prediction;
- context feature missingness.

Context quality artifact must also persist exact column definitions and candidate groups.

## Interpretation

A positive context result means only the selected PIT representation adds incremental historical value over the frozen a2+b2 stack.

It does not justify production promotion.

If a context group is promising, the next step is a fixed-config temporal robustness audit before freezing it into Pre-Live v2.

If none is proven, proceed to the next materially different c2 hypothesis (e.g. deterministic rivalry mapping or a documented squad-data blocker) rather than retuning this same group on exposed references.

## Files

Implementation:

`ml/context_extension_v2.py`

Frozen-baseline isolation runner:

`ml/run_context_extension_v2.py`

Tests:

`ml/test_context_extension_v2.py`

Workflow:

`.github/workflows/context-extension-v2.yml`
