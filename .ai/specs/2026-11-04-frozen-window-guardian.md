# Bounded guardian for existing frozen-encoder windows

Status:code/initial execution verified; nine tests pass in hosted Demand Engine run41811862372. The actual due-window dispatch→successful workflow→DB record chain remains pending until a genuine cutoff. First live cycles had no due checkpoint and correctly dispatched nothing.

At10:00UTC, the main frozen-encoder workflow is active and configured twice hourly, but the latest actual scheduled success is03:22UTC. The next genuine cutoff is11:15UTC. Canonical rules prioritize imminent evidence protection and permit operational hardening without changing frozen prediction semantics.

Provide a host-dependent guardian bound to24hours that reads the existing decision RPC and dispatches only the already-deployed main frozen-encoder workflow when an exact legal0..+90minute checkpoint lacks an attempt. Input-insufficient checkpoints still require honest failed-input attempts; never relax input gates. Never dispatch for missed, future or already-attempted checkpoints. Avoid dispatch while an active main workflow run exists, and throttle unsuccessful retries. Serialize guardians and keep private state/audit logs without credentials.

No new models, workflow version, production activation, DB writes by the guardian, historical backfill or external messages. Expected chain is guardian dispatch→existing workflow success→expected DB attempt/prediction; do not claim that chain before a genuine due window executes. Test boundary selection, fail-closed malformed state, retry/active-run suppression and error sanitization. Current inference worker remains separate.
