# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/CURRENT_MODEL.md` if model/pipeline state matters.
3. Read `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` only when implementation sequencing matters.
4. Do **not** retrain, rebuild or reproduce frozen historical benchmarks merely to recover context.
5. Re-run only when a trigger listed in `AI_BOOTSTRAP.md` is present.
6. For latest-state questions, prefer a small targeted DB/GitHub query over historical recomputation.
7. Continue from the first unfinished action in the bootstrap/current-state docs.
8. Never store secrets, tokens, service-role keys or credentials in repo files.

Current product principle: optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.
