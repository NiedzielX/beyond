# Beyond Ticketing — Demand Forecast Development Plan v2

Last updated: **2026-10-21**

Status: **SUPERSEDED EXECUTION VIEW — SEE `ml/MAE_RESEARCH_ROADMAP_V3.md` FOR CANONICAL STRATEGY**

This file remains as the operational development-plan entry point, but the research strategy is now governed by `ml/MAE_RESEARCH_ROADMAP_V3.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with honest, reproducible, point-in-time-safe evidence.**

## Governing rules

1. frozen evidence packages are immutable;
2. previously opened historical holdouts remain exposed for all future variants;
3. validation and R&D run in parallel;
4. primary optimization objective is MAE;
5. tail/bias/stability are guardrails;
6. random row/snapshot split is not headline evidence;
7. ensemble weights and hyperparameters must be learned inside training folds;
8. production promotion is separate from research-champion selection;
9. production remains `live_adjustment = 0` until explicit review and activation.

---

# 1. Evidence Lane

## Final24

Frozen package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Purpose:

- delayed-label diagnostics;
- true post-freeze prospective scoring;
- promotion evidence.

Do not tune from new outcomes.

## Long72

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`.

Required next infrastructure:

1. persist forecast before final attendance is known;
2. preserve anchor/raw/P2/reliability/PIT lineage/code hashes;
3. append outcome later;
4. never recompute the prediction after label exposure;
5. maintain append-only scorecard.

---

# 2. Structural/global research baseline

Current multi-club historical core:

- Global Model v2.1;
- 1,530 Ekstraklasa matches;
- five complete seasons;
- 7,650 PIT snapshots;
- five horizons T-30/T-14/T-7/T-3/T-1;
- residual architecture: club-history baseline + global learned correction.

Historical 2024/25 and 2025/26 later-season results are already exposed. New challengers must not optimize repeatedly against them and then report them as unseen.

---

# 3. Active MAE R&D priorities

## Priority 1 — canonical rolling / forward evaluation

Historical/global:

- rolling or expanding season/fixture origin;
- no future-season training for an earlier evaluation fold;
- persist fold definitions;
- report per horizon, fold, club and aggregate.

Live:

- complete-event independence;
- LOEO diagnostic;
- forward-event evaluation by kickoff;
- no random snapshot split.

## Priority 2 — MAE-native residual models

Test a compact, predeclared candidate set:

- current HistGBR/XGB controls;
- LAD / median regression;
- quantile regression `q=0.50`;
- tree boosting with absolute-error / median objective;
- robust regularized residual model.

Primary selector: time-respecting MAE.

## Priority 3 — uncertainty around `ΔMAE`

Use event/fixture as the independent resampling unit.

Report:

- incumbent MAE;
- challenger MAE;
- absolute/relative `ΔMAE`;
- interval for `ΔMAE`;
- event-improvement rate;
- per-club distribution.

## Priority 4 — new PIT-safe context

First hypothesis: fixture substitution / cannibalization.

Features:

- days to next home match;
- next-opponent attractiveness;
- next-match importance/competition;
- fixture density 7/14/30d;
- previous-home proximity.

Then test:

- verified absences;
- rivalry / table stakes;
- PIT weather forecast;
- PIT-safe search/media/social attention.

Every family requires ablation versus the same incumbent.

## Priority 5 — forecast combination

Test:

1. mean;
2. median;
3. fixed convex weights;
4. MAE-optimized convex weights inside train folds;
5. regularized stacker only if simpler blends fail.

Components should represent different information sources, not minor hyperparameter variants.

## Priority 6 — live inventory over strong structural baseline

The relevant question is no longer “does ticketing beat a weak baseline?”. It is:

> **Does PIT inventory lower MAE after the strongest structural/global forecast has already explained historical demand?**

Evaluate residual corrections and reliability/shrinkage over the strongest structural model.

## Priority 7 — 72–168h

Current readiness at last audit: `8/9` independent events beyond 72h.

At `N>=9`:

1. freeze event/as-of identities;
2. define PIT-safe T-7 anchor transition;
3. start with simple/regularized models;
4. include MAE-native candidates;
5. use event-safe and forward-event validation;
6. create a separate package/version.

`N=9` opens research; it does not imply promotion readiness.

## Priority 8 — club calibration / shrinkage

Because the global model already pools all clubs, test only modest club-specific calibration:

- global only;
- global + shrinkage home-club residual;
- global + opponent calibration.

Advance only if improvement survives forward/rolling evaluation and is not concentrated in one club.

---

# 4. Promotion boundary

Research champion != production.

Production requires:

- genuine future evidence;
- lower prospective MAE;
- acceptable bias/tail behavior;
- reproducible frozen lineage;
- explicit reviewed activation.

Until then:

`live_adjustment = 0`

---

# 5. Immediate work order

1. finish long72 two-phase prospective persistence/scoring;
2. implement reusable rolling/forward validation utilities;
3. run the MAE-native global residual tournament;
4. add block-based `ΔMAE` uncertainty;
5. materialize next-fixture/cannibalization features;
6. run controlled feature ablations;
7. run simple forecast-combination tournament;
8. test live-ticket incremental residual uplift over the strongest structural forecast;
9. keep final24/long72 prospective evidence collecting in parallel;
10. trigger 72–168h research at `N>=9`;
11. do not activate production automatically.

## One-line handoff

> **Evidence packages stay frozen; active development is a parallel MAE-first challenger program governed by forward validation, MAE-aligned losses, new PIT-safe information and forecast combination.**
