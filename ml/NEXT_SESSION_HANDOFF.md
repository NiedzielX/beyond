# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V5.md`

Trajectory plan: `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Feature contract: `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`

Validation contract: `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`

---

# 1. Current phase

Beyond is doing two things in parallel:

1. **protect genuine prospective P7/P9/Form5 evidence**;
2. **develop the first trajectory-first Lane A vs Lane B comparison**.

The trajectory infrastructure phase is no longer only planned. The core backend is already implemented/live.

---

# 2. What is already delivered for Daily Trajectory

Implemented in repo:

- canonical daily P-N dataset builder;
- PIT/future-snapshot/structural-prior leakage tests;
- executable Trajectory Feature Contract v1;
- executable strict-forward validation fold contract v1;
- Demand Engine CI coverage.

Live in Supabase:

- immutable daily attempt ledger;
- immutable daily prediction ledger;
- immutable post-outcome score ledger;
- controlled service-role RPC writes;
- MAE-by-horizon scoring backend.

Canonical SQL:

`supabase/sql/daily_trajectory_prospective_evidence_v1.sql`

No synthetic daily prediction was inserted to manufacture progress.

---

# 3. Data reality

Coverage audit:

`ml/DAILY_TRAJECTORY_COVERAGE_AUDIT_2026-10-28.md`

Current genuine pre-kickoff inventory sample:

- 32 events;
- 14 clubs;
- median first observation ~P-9.3;
- p75 ~P-14;
- earliest ~P-30.3;
- current historical P-31...P-60 coverage = 0.

Representative snapshot coverage:

- P-30: 3.0%;
- P-14: 21.9%;
- P-7: 61.5%;
- P-3: 75.0%;
- P-1: 95.0%.

Therefore:

- P-60 is a collection horizon, not a required full input vector;
- sequence models use genuine variable-length prefixes;
- no forward-fill/fabricated daily history;
- padding requires an explicit mask/length.

Current checkpoint audit under the shared Lane A/B input gate:

| Horizon | Input-ready events | Labeled ready events |
|---|---:|---:|
| T-30 | 0 | 0 |
| T-14 | 1 | 0 |
| T-7 | 7 | 4 |
| T-3 | 9 | 5 |
| T-1 | 10 | 10 |

This is why the primary development validation is strict expanding temporal folds, not random CV.

---

# 4. Frozen trajectory development contracts

## Feature Contract v1

`trajectory-feature-contract-v1`

Shared eligibility requires:

- PIT-valid structural incumbent;
- >=4 clean snapshots;
- >=24h genuine observation window;
- canonical `signal_readiness=ready`;
- no future target snapshots/outcomes.

Lane A receives engineered scalar summaries.

Lane B receives the ordered genuine snapshot sequence, compressed to at most one real observation per integer hour-to-kickoff bucket, with no interpolation/forward-fill.

Both lanes exclude unrelated odds/weather/hype/match-stakes/context in v1.

## Validation Fold Contract v1

`trajectory-validation-fold-contract-v1`

Primary method:

- strict expanding temporal event folds;
- same-kickoff events stay together;
- minimum 5 prior train events;
- minimum 4 prior train clubs;
- every prefix from one event inherits the event fold;
- Lane A and Lane B use the exact same registry.

LOEO/LOCO may be diagnostics only. Random row CV is prohibited.

---

# 5. Next new-model work

The next task is now **model-development precommit**, not more infrastructure invention.

## Lane A

Freeze one small benchmark protocol around:

`structural P50 + engineered trajectory residual -> attendance P50`

Candidate families must remain small and precommitted.

## Lane B

Freeze the first small sequence protocol around:

`genuine variable-length trajectory + structural P50 -> residual`

Start with a small GRU/LSTM/TCN design. Do not jump directly to a large Transformer.

Both lanes must use:

- the same event identities;
- the same strict-forward folds;
- the same cutoffs;
- the same incumbent;
- the same scoring rules.

---

# 6. Current frozen prospective state

## P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine attempt:

- event443 Cracovia–Motor T-48;
- 2026-10-28 17:00 UTC;
- result `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored;
- correct fail-closed.

## P9 v2

Separately precommitted/deployed. Same exact five v1 neighbors and support gate; Structural fallback only under frozen rule; never retro-predict event443; never pool v1/v2 evidence.

## P7

53 immutable rows / 6 events / 0 scored. No retuning.

## Form5

First legal T-24 capture: **event443 — 2026-10-29 17:00 UTC**.

## Long72

5 scored; 6082.40 -> 6039.39; improvement 43.01 / 0.71%; frozen/low priority.

## P11

6 events / 6 clubs; T-24/T-72/T-168 = 5/5/0; no model fit yet.

---

# 7. Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains an inventory watch. Unknown inventory is not zero.

---

# 8. Hard rules

- protect imminent prospective windows before lower-priority R&D;
- no target future trajectory at an earlier cutoff;
- no target attendance during prediction;
- no manufactured history;
- no random daily-row split;
- all prefixes from one event stay together;
- no gate relaxation for coverage;
- no retuning on exposed prospective outcomes;
- no inventory-derived attendance labels;
- no hidden inventory = zero assumption;
- no production activation without explicit reviewed promotion;
- `live_adjustment=0`.
