# Seat-weighted median objective audit

Status: implementation and local diagnostic complete; gate rejected the hypothesis. Hosted verification pending.

Result: `ml/MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md`. Both development MAEs worsened; no weighted old-holdout fitting, new variant or serving change followed.

Canonical precommit: `ml/MAE02_SEAT_WEIGHTED_MEDIAN_PRECOMMIT_V1.md`. Dependency: completed historical MAE-01 decomposition.

Acceptance: isolate capacity weighting while retaining the T-3/T-1 absolute-loss model specifications; reproduce incumbent development metrics; compute paired event-balanced diagnostics and fixed simple PIT benchmarks; apply the written both-horizon development MAE/P90 gate. Reject and stop without weighted old-holdout fitting if the gate fails. Never modify serving artifacts, frozen evidence, production flags or tune the v1 mechanism from these results. Record the result, lessons and next action in canonical files and the current run log.
