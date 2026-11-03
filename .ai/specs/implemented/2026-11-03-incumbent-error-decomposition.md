# Incumbent error decomposition

Status: complete. Hosted Demand Engine run41711896063 passed all tests and all ten fixed-split MAE reproductions. Draft PR206: https://github.com/NiedzielX/beyond/pull/206.

Authority: Roadmap v6 MAE-01. Exact protocol: `ml/MAE01_INCUMBENT_ERROR_AUDIT_PROTOCOL_V1.md`.

Acceptance: reproduce all ten existing horizon/season MAEs using unchanged fixed specifications; verify frozen hashes and temporal separation; rank event-balanced error contributions, common-cohort horizons and worst events; document uncertainty and derive the next research question. Tests must reject duplicate horizons, future cutoffs, inconsistent identities and tampered sources. No model artifacts or production state may change.
