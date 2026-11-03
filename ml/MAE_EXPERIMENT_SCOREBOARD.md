# Beyond Ticketing — MAE Experiment Scoreboard

Last updated: **2026-11-03**

Status: **CANONICAL HUMAN-READABLE MAE EXPERIMENT REGISTRY**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

---

# 1. Purpose

This file records comparable MAE experiments so that model selection is driven by reproducible evidence rather than narrative memory.

One row should represent one materially distinct experiment/version.

Do not overwrite a failed experiment. Record the result and decision.

---

# 2. Headline scoreboard

| Experiment ID | Hypothesis | Incumbent | Events | Clubs | Coverage | Incumbent MAE | Challenger MAE | Delta MAE | Improvement rate | Median Delta AE | P90 / worst degradation | Signed bias | PIT audit | Decision |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| structural-incumbent-frozen-reference | frozen reference on exposed 10-event trajectory cohort | — | 10 | — | — | 2594.54 | 2594.54 | 0.00 | — | — | — | — | recorded | incumbent reference |
| trajectory-lane-a-ridge-v1 | engineered trajectory residual Ridge improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 4153.34 | +1558.80 | — | — | — | — | recorded | REJECTED |
| trajectory-lane-b-gru-raw-v1 | GRU raw-seat residual improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 2595.40 | +0.87 | — | — | — | — | recorded | DO NOT ADVANCE |
| trajectory-lane-b-gru-ratio-v2 | GRU residual-ratio mechanism improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 4792.42 | +2197.88 | — | — | — | — | recorded | MECHANISM NOT SUPPORTED |

Notes:

- the 10-event cohort above is exposed and must not be reused for post-hoc tuning and then treated as fresh evidence;
- fill missing historical guardrail fields only from reproducible existing results, never from guesses;
- target-free SSP representation results belong in representation evidence, not in attendance MAE rows unless an attendance challenger is actually evaluated.

---

# 3. Roadmap v6 experiment queue

| Work package | Planned experiment | Status | Entry criterion | Exit criterion |
|---|---|---|---|---|
| MAE-01 | incumbent error decomposition v1 | NEXT | reproducible incumbent predictions + outcomes | ranked error segments + failure taxonomy + next hypothesis |
| MAE-02 | structural baseline benchmark v1 | QUEUED | MAE-01 identifies structural error opportunities | strongest honest PIT-safe structural research anchor selected/frozen |
| MAE-03 | context residual benchmark v1 | QUEUED | timestamped PIT-safe context available | incremental context Delta MAE measured vs same-event anchor |
| MAE-04 | engineered trajectory benchmark v2 | QUEUED | genuine trajectory coverage sufficient | incremental trajectory Delta MAE measured with ablations |
| MAE-05 | horizon-specific residual v1 | QUEUED | enough events across useful horizons | horizon curve shows whether separate correction is justified |
| MAE-06 | club/regime heterogeneity v1 | QUEUED | MAE-01/02 show systematic heterogeneous error | global vs club/regime-aware comparison completed |
| MAE-07 | context/trajectory ablation v1 | QUEUED | individual signal families measured | source of combined gain identified |
| MAE-08 | calibrated ensemble v1 | QUEUED | at least two independently useful, complementary challengers | blend beats strongest simpler challenger on same events |
| sequence-next | compact sequence challenger | CONDITIONAL | engineered trajectory shows signal + plausible representation gap | beats simple trajectory benchmark under same event-grouped validation |

---

# 4. Required detail block for every new experiment

Copy this block below for each new serious experiment.

## `<experiment-id>`

**Work package:** MAE-XX  
**Status:** PLANNED / RUNNING / FROZEN / REJECTED / SUPPORTED / PROSPECTIVE_SHADOW  
**Hypothesis:**  
**Incumbent/version:**  
**Challenger/version:**  
**Dataset/version:**  
**Cutoff/horizon contract:**  
**Independent events:**  
**Distinct clubs:**  
**Coverage:**  
**PIT audit:** PASS / FAIL / PENDING  

### Result

- Incumbent event-balanced MAE:
- Challenger event-balanced MAE:
- Delta MAE:
- Event improvement rate:
- Median event Delta AE:
- P90 AE / worst-event degradation:
- Signed bias:
- Per-horizon MAE:
- Best-event improvement:
- Worst-event degradation:

### Interpretation

State what the result supports and what it does **not** support.

### Decision

`REJECT / RETAIN_AS_BENCHMARK / SUPPORT_SIGNAL / PRECOMMIT_NEXT_VERSION / FREEZE_FOR_PROSPECTIVE_SHADOW / INSUFFICIENT_EVIDENCE`

### Next hypothesis

State one next question derived from the observed residual error. Do not list arbitrary feature ideas.

---

# 5. Evaluation rules

1. Event/fixture is the independent unit.
2. Compare incumbent and challenger on the same eligible events.
3. Use PIT-safe features only.
4. Keep all rows/prefixes from one event in the same fold.
5. Primary selector is event-balanced MAE.
6. Multiple horizons from one event do not increase independent-event count.
7. Do not repair failed results post hoc on exposed outer outcomes.
8. Historical/grouped research is not prospective evidence.
9. Any promoted challenger requires a new precommit/freeze before genuine prospective scoring.
10. Production activation remains a separate explicit review.

---

# 6. Active frozen prospective reference

The currently frozen trajectory attendance candidate remains separate from Roadmap v6 research:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Its current prospective decision must be made only from its immutable future evidence stream and the precommitted evaluator/business guards.

For that active comparison the business-resolution scale remains:

`Delta MAE <= -550 seats`

Do not tune Roadmap v6 experiments toward this exact number and do not rewrite the frozen candidate based on early outcomes.
