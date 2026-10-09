# Lech League-wide Feature Factory Research v1.8

v1.8 is a **research checkpoint**, not a promoted production/historical model.

## Baseline

Frozen baseline entering v1.8:

- T-30 v1.7 MAE: **4723.8**
- T-7 v1.7 MAE: **4151.1**

## Research decisions

### League-wide Elo / sporting-strength transfer

**Rejected.**

Best observed overall MAE:

- T-30: 5087.5
- T-7: 4364.6

Both were worse than v1.7.

### Prior-season opponent home-attendance popularity

**Promising for T-30, but not promoted.**

Best candidate:

`T30_pop_ratio_missing_a0.3`

Metrics:

- development MAE: 4578.5 vs v1.7 4571.3 — marginally worse;
- holdout MAE: 4557.8;
- overall MAE: **4568.2** vs v1.7 4723.8;
- overall improvement: ~155.6 persons MAE;
- paired bootstrap 95% CI: [-332.9, -2.7];
- probability candidate better: 0.978.

Why it was not promoted:

- development was marginally worse than v1.7;
- most of the gain was concentrated in 2025/26;
- the fresh 2026/27 two-match sanity check was mixed;
- insufficient genuinely future evidence to replace the frozen baseline.

### T-7 popularity signal

**Rejected.** Only ~21 MAE overall improvement and the bootstrap interval crossed zero.

### T-7 blend / stage switch

**Rejected.** Best gain was ~6 MAE and did not justify additional production complexity.

## v1.8 conclusion

Historical/context engineering had reached diminishing returns. v1.7 remained the frozen baseline, while the primary R&D direction shifted to kickoff-anchored live ticket inventory trajectories.

This means a later version number does **not** imply a later champion. v1.8 contains challengers and research evidence; v1.7 remains the accepted baseline until a challenger passes the promotion gate.
