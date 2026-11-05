# Current persisted C1 error decomposition

Implement a read-only diagnostic of the complete current C1v8 event scoreboard, following MAE-01 and `C1_LIVE_MAE_1200_PLAN_V1.md`. The old11-event audit stays unchanged. Use persisted latest forecasts and window errors, canonical event identities and confirmed outcomes; do not replay a new model, fit, select parameters or create forecasts.

Validate package, unique canonical home-matchday units, source/forecast/confirmation chronology, exact label identity, selected-expert output and stored errors. Reconcile all aggregate latest/window MAEs and forecast/scored counts to the current status view; reject inconsistent reads instead of silently filtering bad rows. Keep unscored events in coverage. Separate the earlier11-event scope and newly labeled6-event scope as exposed descriptive cohorts, never fresh validation.

Report event-balanced latest/window MAE, signed bias, P90/worst errors, paired policy-versus-prior differences, selection counts, largest-error contribution, descriptive club/horizon/attendance-level groups and the explicitly outcome-aware oracle lower bound for choosing between already persisted prior/raw outputs. No new eligibility threshold, significance claim, promotion rule or claim of model improvement. Raw rows and detailed reports remain private outside Git; public reporting contains aggregate diagnostics and source hashes only.

Tests must reject corrupted labels/errors, future or naive timestamps, duplicate fixtures, wrong packages, misleading aggregate denominators and malformed unscored rows. Verify the result on fresh actual inputs, preserving immutable read receipts. Existing frozen code/artifacts/collectors and `production_change=false`, `live_adjustment=0` remain unchanged.

ImplementedNovember5:6tests and actual17-event fully reconciled read; result`ml/C1_CURRENT_ERROR_DECOMPOSITION_RESULT_V1.md`. Private raw receipts and ranked report preserved; no new learner or gate.
