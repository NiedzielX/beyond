# Guardian: genuine encoder-window chain verified

Observed 2026-11-04, Korona603 versus Radomiak, P-3 cutoff **11:15 UTC**. This is operational persistence evidence for an input-insufficient window, not a forecast-accuracy result.

| Stage | Actual evidence |
|---|---|
| Legal window | Read-only preflight at11:15:00UTC: `WINDOW_OPEN_INPUT_INSUFFICIENT`; no attempt/prediction existed |
| Guardian dispatch | Audit at11:18:58.798931UTC: exact event603/P-3/cutoff, `dispatched=true` |
| Existing workflow | [Run41819915267](https://github.com/NiedzielX/beyond/actions/runs/41819915267), `workflow_dispatch`, branch`main`, SHA`bc17f48c791b12b397de989f5b0a3a1a4fe85566`; created11:19:02UTC |
| Successful execution | Run completed`success`, updated11:19:53UTC |
| Expected DB record | Fresh preflight at11:20:05UTC reads `private.daily_trajectory_attempts_v1`: `MODEL_INPUT_INSUFFICIENT`, attempted11:19:48.745719UTC, event603/P-3; prediction remainsnull |
| Counter verification | Decision RPC11:20:35UTC: encoder9attempts /5predictions /0scores; P9v1 6/0/0, P9v2 5/3/0; productionfalse, adjustment0 |

The private probe retained the initial open/unrecorded state, guardian dispatch, complete workflow metadata and post-run DB-derived checkpoint in:

`/workspace/ops-runtime/2026-11-04-review/encoder-chain/verified-chain.json`

SHA256:`50e3239b68314f554cf614b30abac6381d260d76ba6132f6500fac8cc290bdbe`.

`supabase/sql/trajectory_frozen_encoder_preflight_v1.sql` obtains attempt status/time directly from the private attempts table for the exact event, horizon and frozen model. Observed ordering satisfies:

`cutoff <= guardian check <= workflow creation <= DB attempt <= successful workflow completion`

The full guardian→existing encoder workflow→success→expected DB record chain is therefore proven for this genuine fail-closed checkpoint. The frozen input rule was preserved: no observations within its168-hour window, no invented zero, no forecast. Historical misses remain missing. No manual encoder dispatch was needed for this cutoff.

Scope: this proves the guardian's fail-closed encoder capture. READY prediction/scoring paths require their own genuine evidence; P9heartbeat redundancy is a separate chain. New daily-path SQL/Edge deployment remains blocked, and MAE improvement remains unproven.

## Separate daily-path evidence at the same cutoff

The unchanged local daily v1cycle captured event603at11:15:09.397892UTC, status`INSUFFICIENT_PREFIX_SPAN`,12hourly observations in its different60-day prefix contract. No new forecast; private backup verified. The separate drift watcher automatically captured that new post-freeze issue at11:19:58UTCwith the same insufficient-input status and0points; private backup verified. Its initial oldNov3issues were excluded.

These are separate ledgers/contracts from the encoder DB record. The manual attempt to launch an additional drift CLI while its watcher held the lifetime lock was correctly refused; the existing watcher performed the actual capture. No duplicate watcher was started. Current local v1state:8attempts /4predicted events /57future points /0scores. Drift:1attempt /0points /0scores. Both MAEs remainnull.

Next ready encoder checkpoint:Górnik449/P-3at16:30UTC(17:30Warsaw). First existing daily v1targets mature17:00UTC(18:00Warsaw). Keep the original model and new drift rule frozen while genuine evidence accumulates.
