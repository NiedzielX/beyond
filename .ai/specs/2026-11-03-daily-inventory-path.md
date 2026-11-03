# Daily inventory path MVP

Status: implemented locally and in draft PRs; remote scheduled deployment pending.

Canonical specification: `ml/DAILY_DEMAND_PATH_MVP_CONTRACT_V1.md`. Frozen experimental contract: `ml/DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`. Deployment evidence and blockers: `ml/DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`.

Acceptance: genuine observed P-N prefix → predictions for each remaining day; immutable issue vintages; genuine future scoring against persistence; event-balanced/per-lead MAE and honest missingness; usable read-only daily-path chart. Public available inventory must not be presented as paid ticket sales or attendance.

Local capture, private backup/restore, frontend typecheck/build and backend CI have evidence. Remote SQL/gateway/scheduled capture is not DONE until workflow → successful execution → expected immutable records → genuine later target score is demonstrated. Do not refit v1 or activate production while completing deployment.
