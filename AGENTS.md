# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/CURRENT_MODEL.md` if model/pipeline state matters.
3. Read `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` only when implementation sequencing matters.
4. Read `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md` and `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md` for current live-automation state.
5. Do **not** retrain, rebuild or reproduce frozen historical benchmarks merely to recover context.
6. Re-run only when a trigger listed in `AI_BOOTSTRAP.md` is present.
7. For latest-state questions, prefer a small targeted DB/GitHub query over historical recomputation.
8. Continue from the first unfinished action in the bootstrap/current-state docs.
9. Never store secrets, tokens, service-role keys or credentials in repo files.

Current operational state: Live Forecast Orchestrator v1 and automatic frozen-artifact Structural Prior materialization for T-30/T-14 are deployed and live. Do not rebuild those models during a normal session.

Current operational next step: freeze executable current-event Structural Prior runtimes for **T-7 / T-3 / T-1** so the live loop keeps a genuine historical anchor after an event leaves the T-14 window. Until then those horizons must remain fail-closed; there is no legacy fallback.

Current product principle: optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.
