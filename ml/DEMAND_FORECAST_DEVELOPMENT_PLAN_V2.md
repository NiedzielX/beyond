# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **CANONICAL ACCURACY ROADMAP**

Canonical rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Historical strategy baseline:

`ml/MODEL_DEVELOPMENT_STRATEGY.md`

Frozen prospective contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

Active a2 closure audit:

`ml/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1.md`

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Two rules are equally important:

1. a frozen champion/evidence package must not be mutated from exposed outcomes;
2. **R&D must not wait for prospective sample-count gates when honest historical or newly predeclared research is available now.**

A failed challenger closes the challenger, not the workstream.

---

# 1. Two parallel tracks — mandatory

## Track A — Frozen validation / promotion evidence

Purpose:

> Measure the already-frozen model stack on delayed-label and genuinely future events without retraining it.

Frozen stack:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

This track:

- keeps Pre-Live v2 unchanged;
- keeps `ridge-a10` unchanged;
- keeps `P2-observation-maturity` unchanged;
- scores new events append-only;
- separates `DELAYED_LABEL_HOLDOUT` from `TRUE_POST_FREEZE_PROSPECTIVE`;
- produces production-promotion evidence.

**Track A may wait for genuinely future evidence because that evidence does not exist yet.**

## Track B — Active accuracy R&D

Purpose:

> Continue improving the modelling approach now, using only valid evidence boundaries.

This track does **not** wait for a fixed number of new prospective events.

It may start a new versioned challenger when at least one is true:

- a bounded part of the original investigation is still incomplete;
- a materially new hypothesis exists;
- materially new historical data exists;
- a new PIT-safe feature/source becomes available;
- a materially different target/model/ensemble formulation can be tested honestly.

Requirements:

- new candidate/version ID;
- explicit train/development/reference boundary before tuning;
- exposed prospective events never relabeled as unseen;
- current frozen stack retained as benchmark;
- no silent production write.

**Production promotion waits for prospective evidence. R&D does not.**

---

# 2. Current frozen state

Historical sequence already completed:

`a2 historical -> b2 -> c2 historical -> Frozen Pre-Live v2`

Live sequence already completed:

`d2 Stage 0 -> d2 Stage 1 ridge-a10 -> d2 Stage 2 P2 -> event-5 holdout`

Frozen Pre-Live ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Frozen d2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Production remains:

`live_adjustment = 0`

No new R&D experiment mutates those IDs.

---

# 3. Frozen Pre-Live v2

Historical contract:

| Horizon | Historical base | b2 | c2 | Frozen reference mean MAE |
|---|---|---|---|---:|
| T-30 | Structural Prior | no adjustment | no context | 1,867.82 |
| T-14 | Structural Prior | no adjustment | no context | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | no context | 1,691.40 |
| T-3 | Structural Prior | `ewma50-resid-k2-cap05-min3` | no context | 1,682.63 |
| T-1 | Structural Prior | `ewma50-resid-k6-cap05-min3` | no context | 1,661.52 |

The current frozen candidate is reproducible and sealed.

Historical a2 is **not** to be randomly reopened or retuned against the same exposed references.

However, one bounded a2 gap remained: external model families were only canonically tested at T-7. That gap is now handled as a separately versioned Track-B closure audit.

---

# 4. Track B priority 1 — a2 External Model + Ensemble Closure Audit

Status:

**ACTIVE — PR #120 / workflow `a2 External + Ensemble Closure v1`**

Contract:

`ml/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1.md`

Question:

> Can CatBoost / LightGBM / XGBoost / HGB or a heterogeneous ensemble improve the current a2 historical base at T-30/T-14/T-7/T-3/T-1?

Development boundary:

- train: 2021/22 + 2022/23;
- select: 2023/24 only;
- exposed references: 2024/25 and 2025/26;
- references never used for model/weight selection.

Candidates:

- current frozen a2 base;
- fixed HGB where not already champion;
- CatBoost depth 4/6;
- LightGBM leaves 15/31;
- XGBoost depth 2/3;
- median of top development family members;
- non-negative development-selected 0.25-grid weighted ensemble with at least two non-zero members.

Decision per horizon:

- if current a2 wins development -> close this challenger for that horizon;
- if development winner fails references -> retain current a2;
- if winner improves both exposed references -> advance unchanged contract to a separate fixed-temporal robustness audit.

A positive result here does **not** automatically replace Frozen Pre-Live v2.

---

# 5. Track A — frozen d2 prospective validation

Stage-1 expert:

`ridge-a10`

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- Ridge latest uplift `807.62 / 19.56%`;
- Ridge window MAE `3619.19`;
- worst latest-event degradation `4326.90`.

Stage-2 package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Development:

- latest MAE `3240.99`;
- latest uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`;
- 75% reduction in worst degradation vs raw Ridge.

Event 5:

Lech Poznań vs Korona Kielce, actual `37,407`.

Latest errors:

- Structural T-1 base `7,669.07`;
- Frozen Pre-Live v2 `9,832.52`;
- raw Ridge `6,652.81`;
- P2 `6,652.81`;
- persisted C1 v8 `7,669.07`.

Event 5 is exposed permanently.

---

# 6. Delayed-label diagnostics

Delayed-label events are useful diagnostics but are not genuine post-freeze promotion evidence.

Current recovered outcomes already show why component-level scoring matters:

- GKS Katowice vs Pogoń: Frozen Pre-Live latest error `1,356`, d2/P2 latest error about `2,074`;
- Cracovia vs Legia: Frozen Pre-Live latest error `434`, d2/P2 latest error about `1,068`.

These outcomes must not trigger post-hoc mutation of the frozen package.

They are evidence for future hypotheses and future separately versioned challengers.

Capacity/outcome blockers should be repaired as data-contract work, not treated as a reason to stop R&D.

---

# 7. Track B priority 2 — d2 next-generation research

The frozen P2 package remains untouched in Track A.

In Track B, a new versioned d2 challenger may be researched **without waiting for N future events**, provided its evaluation boundary is declared in advance.

Priority research questions:

## 7.1 Alternative target formulations

Test materially different targets rather than repeatedly tuning Ridge:

- current capacity-normalized delta to Frozen Pre-Live;
- remaining demand from the current live state;
- anchor-error direction / signed correction classification plus magnitude;
- other PIT-safe formulations declared before fitting.

## 7.2 Reliability as a learned component

Current P2 is a simple frozen rule.

A new challenger may test whether reliability should be learned from PIT-safe signals such as:

- observation count;
- observation span;
- time to kickoff;
- trajectory stability;
- velocity / acceleration;
- correction magnitude;
- disagreement vs Frozen Pre-Live;
- release/replenishment flags;
- sector/coverage changes;
- missingness/data-quality state.

This must be a new policy/model ID, not a modification of P2.

## 7.3 Heterogeneous live-model comparison

A new d2 tournament may compare a compact set of materially different experts, for example:

- Ridge;
- HGB / LightGBM / CatBoost where sample size supports them;
- transparent inventory extrapolation;
- explicitly governed ensembles.

Do not create an open-ended model zoo.

## 7.4 TSFM boundary

Stage-1 zero-shot Chronos-2 and Chronos-Bolt-small did not beat plain Ridge.

Therefore the old Stage-1 TSFM formulation remains closed.

TSFM may be reopened only through a materially different predeclared hypothesis, e.g. a different trajectory target such as remaining demand, or materially more independent trajectories.

No same-data tuning to rescue the failed Stage-1 Chronos challenger.

---

# 8. Track B priority 3 — prospective c2/context research

Historical c2 remains:

`NO_CONTEXT_ALL_HORIZONS`

But forward context collection/research continues now where valid PIT sources exist.

Candidate sources already represented in the repository include:

- verified rivalry/derby;
- verified absences/suspensions;
- sporting context;
- media/GDELT attention;
- hype/search/social where source semantics are valid.

Rules:

- collect point-in-time;
- never backfill from final-state knowledge;
- keep context challengers separate from frozen Pre-Live v2;
- prove incremental MAE value before any integration.

---

# 9. What waits and what does not

## Must wait

Only evidence that genuinely does not yet exist:

- true post-freeze match outcomes;
- future live ticket trajectories;
- forward-only context observations.

## Must not wait

Research that can be done honestly now:

- bounded historical closure audits;
- new model-family or ensemble hypotheses;
- new target formulations;
- feature engineering from already PIT-safe data;
- reproducibility/CI hardening;
- context collection infrastructure;
- new versioned d2 research on declared development data.

---

# 10. Promotion boundary

Production promotion requires materially more genuine prospective evidence than the current sample.

Require:

- positive aggregate latest/window uplift;
- acceptable tail risk;
- no unresolved systematic component failure;
- reproducible frozen package;
- explicit reviewed promotion decision.

Until then:

`live_adjustment = 0`

---

# 11. Immediate work order

1. finish `a2 External Model + Ensemble Closure Audit v1`;
2. if any horizon advances, run its fixed-temporal robustness audit under the frozen selected contract;
3. if none advances, mark this bounded a2 gap closed and continue Track-B R&D;
4. keep frozen prospective scoring running in parallel;
5. repair readiness/capacity/truth-source blockers without using them as R&D gates;
6. start the next separately versioned d2 formulation research cycle;
7. continue PIT-safe c2/context collection.

## One-line rule

> **Frozen validation protects evidence integrity. It does not pause model development.**
