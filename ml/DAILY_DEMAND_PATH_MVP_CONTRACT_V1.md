# Daily demand path — MVP design and implementation gap

Date: **2026-11-03**.

Status: **DESIGN / CORE IMPLEMENTED LOCALLY / DEPLOYMENT PENDING**. This design document is not the frozen model precommit.

Implementation update, 2026-11-03: the separate [v1 implementation](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md) now provides the dataset, frozen direct model, local immutable ledger/scorer, CLI and panel rendering support. The first two legal local issues produced 18 future-day points. The implementation-gap table below records the earlier audit; Supabase deployment, a new daily scheduler, full panel build and future-target scoring remain unverified/incomplete. Formal model precommit: [DAILY_INVENTORY_PATH_PRECOMMIT_V1.md](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

User clarification: the product must consume the observed event trajectory day by day and predict its remaining daily behaviour. Daily revisions of one final-attendance number do not fulfil this requirement. This design supplements roadmap v6, preserves existing frozen lanes and requires no partner data.

## 1. Required behaviour

Illustration of time semantics, not measured data:

| Forecast issue point | Genuine observations usable as inputs | New predictions |
|---|---|---|
| P-40 | All available observations from P-50 through P-40 | Values for P-39, P-38, …, P-1 |
| P-39 | All available observations from P-50 through the newly observed P-39 | Revised values for P-38, P-37, …, P-1 |

The P-39 prediction issued at P-40 remains immutable and is scored against the later genuine P-39 observation. It is never replaced with the new observation in the forecast ledger. Only the next inference input is extended with that observation.

Support daily issue cutoffs across P-60…P-1. Use the genuine available prefix, not a mandatory complete 60-day vector. If collection began at P-12, do not fabricate P-50…P-13. Missingness and staleness are explicit.

Daily inference updates forecasts with new observations; it does not require daily model refitting. More daily inferences may improve usefulness and exploit new information, but do not automatically improve accuracy or create more independent attendance labels.

## 2. What is actually implemented

Code audited on 2026-11-03; this is not a claim that every local file matches a deployed release.

| Component | Actual behaviour | Missing capability |
|---|---|---|
| `daily_trajectory_dataset.py` | Constructs PIT-safe feature rows at P-N cutoffs across P-60…P-1. | Building a daily input is not daily model execution or a predicted future path. |
| `run_trajectory_frozen_encoder_shadow_v1.py` | `SUPPORTED_DAYS=(7,3,1)`; at most 168h prefix; one `challenger_p50` for final attendance. | Does not emit predicted values for each future day. Expanding its checkpoint list would still produce scalar final-attendance forecasts. |
| `trajectory_self_supervised_v1.py` | GRU with a one-output head predicts normalized inventory change approximately 24h ahead. | No multi-day decoder or deployed daily-path workflow. Current attendance inference uses its encoder embedding, not that output head. |
| Existing daily prospective SQL ledger | One terminal-attendance prediction per event/cutoff/model and scores against attendance outcomes. | No separate issue-time / target-future-day rows or daily inventory-target scorer. |
| Panel `SalesForecastChart.tsx` | Combines observed inventory proxy with the history of terminal P50 forecasts at their issue timestamps. | Does not receive future-day path predictions. X uses point index rather than elapsed time. |
| Panel `FeaturedMatchCard.tsx` | Draws a straight connector from the last proxy observation to the terminal forecast. | The connector is presentation geometry, not learned day-by-day behaviour. |

The panel reads `snapshots` and `forecast_observations`; it does not read the private frozen trajectory ledger. Its normal REST path excludes shadow forecasts. A successful shadow run is therefore not proof that its output appears in this chart.

An additional UI issue: `eventsService.capacityForEvent()` can infer capacity from forecasts/outcomes when a club is absent from its five-entry capacity map. That reconstructed proxy is unsuitable as a historical model input or as a PIT-verified demand level. Display verified capacity lineage or the directly observed inventory instead; do not assert that this UI reconstruction proves training leakage.

## 3. Observable target and input contract

Use public `available_total` under a stable source/measurement contract as the initial observable path target. Optionally expose a derived demand proxy only with verified capacity and clearly separate lineage. Public availability is not net paid sales, but its later observed value provides a legitimate target for forecasting its dynamics.

Inputs at issue time:

- the full genuinely available prefix up to the issue cutoff, with exact observation times;
- days/hours to kickoff, elapsed times between observations and explicit lengths/masks;
- source identity, freshness, known measurement changes and verified capacity when available;
- only context genuinely available by issue time.

For the new path version, decide the context/compression policy in its own precommit. Do not silently inherit the frozen attendance model's 168h cap when the task requires learning a longer prefix, and do not alter that existing cap in v1.

Define one deterministic target-observation rule and tolerance before evaluation. If no eligible genuine observation exists for a target day, leave that target unscored and report coverage; no interpolation or forward-fill to manufacture labels. Record nominal target time, actual captured time, source lineage and target staleness. A change in measurement/source can invalidate comparability.

Availability can rise after releases or cancellations. Do not impose monotonic sales growth or infer the cause of every availability change from the count alone.

## 4. Minimum new research lane

1. **Dataset:** prefix/issue-time → genuine future-day targets, with masks for unavailable labels. This is a different target from the closed Lane A/B final-attendance experiments.
2. **Baseline:** persistence of the latest genuine inventory value. The frozen SSP predictor may additionally be evaluated as a roughly one-day comparator under a compatible input/target contract; its old validation is exposed, not a new untouched test.
3. **Candidate:** one small direct multi-horizon predictor conditioned on the observed prefix and forecast lead. It emits a separate value for each future day. Precommit the exact architecture, objective, context policy and training procedure after the coverage audit; no architecture tournament. Predicted future points are not fed back as if they were genuine observations.
4. **Ledger:** immutable rows keyed by `(event, issued_as_of_at, target_at, model_version)`, with `lead_days`, prediction value, target kind/unit, source/data/model hashes and status. Record issue attempts even when input is insufficient. Distinguish the issue cutoff from actual execution time and precommit the permissible execution delay.
5. **Scorer:** compare each already-persisted point with the later eligible public observation. Preserve old forecast vintages when tomorrow's new forecast is issued.
6. **Scheduler:** run new inference at each eligible daily cutoff, independently of existing P-7/P-3/P-1 frozen attendance inference. Collection may run more frequently; that does not itself constitute daily forecasting.
7. **Panel:** consume actual path rows, use a real time axis, mark the as-of boundary, show observed prefix as solid and the latest future path as dashed. Allow viewing yesterday's forecast versus what actually happened. Terminal attendance is a separate endpoint/series.

## 5. Evaluation

There are two distinct coordinates:

- **P-N:** position relative to kickoff when the forecast is issued;
- **lead h:** how many days after that issue time the target observation lies.

A forecast issued at P-40 for P-39 has lead +1; the same issue for P-33 has lead +7. Evaluating +1/+3/+7 is not restricting inference to P-7/P-3/P-1.

Primary daily-path readout:

- MAE of the chosen observable, reported separately at leads +1, +3 and +7, with coverage and event counts;
- an event-balanced path MAE under precommitted issue/lead weights: average comparable errors within each event before averaging events;
- signed bias, tail error and separate results by issue P-N / support band;
- candidate/baseline comparisons on identical eligible targets.

All prefixes, issue times and future targets from one event stay in the same evaluation fold. Train only on labels genuinely available by the training cutoff. Thousands of overlapping future-day pairs do not become thousands of independent events. Use new untouched future events for prospective confirmation; a new target definition does not erase prior data exposure.

Terminal-attendance MAE remains a separate metric for existing and future attendance heads. Improved path MAE does not prove improved final-attendance MAE. The frozen **550-seat attendance threshold** and **8-event/5-club review rule** remain unchanged for their existing contracts; do not automatically transfer them to inventory-path accuracy. The new path protocol needs its own ex-ante success/review criteria.

## 6. Next implementation order and DONE

1. Audit current genuine prefix length, observation gaps and future-label support by issue P-N and lead. The dated 2026-10-28 audit had no observations at P-31…P-60; do not present it as a current live coverage measurement.
2. Precommit the path target, label matching, baseline, one candidate and clean future evaluation boundary.
3. Implement dataset + direct predictor + issued/target ledger + daily scorer/scheduler as a separate research lane.
4. Connect actual path outputs to the panel; remove/replace the geometric terminal connector so it is not presented as a learned path.
5. Verify the chain: daily cutoff → inference → immutable future-day rows → chart → later observations → matched error scores. Configuration alone is not DONE.

MVP path DONE requires real forecast points for future days, daily revisions with preserved vintages, a chart backed by those points and honest measured errors/coverage. A scalar endpoint updated daily, or a line drawn toward final attendance, does not satisfy this definition.

The Structural Prior objective-alignment experiment is a secondary adjunct, not the critical path for this user-facing capability. Existing frozen artifacts, eligibility and production flags remain unchanged: `production_change=false`, `live_adjustment=0`, fail-closed and no missed prospective backfill.
