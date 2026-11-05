# P9 non-ready correction released

## Deployment and preserved contract

The user continued the plan that included deploying the prepared P9 correction. The exact four-file PR212 diff and all three successful contract checks were reviewed again. The draft was marked ready and merged through normal GitHub enforcement at **2026-11-05 12:16:24UTC**.

- [Merged PR212](https://github.com/NiedzielX/beyond/pull/212), reviewed head`794f74a7a6ab8cdbd4d68015ba2e659b2a243ae4`.
- New remote main:`e04033fb2e01622cf393da398eead16a2d1c4831`.
- The deployed builder's complete bytes match the reviewed head. Only explicit non-ready0–4-neighbor inputs gain an insufficient-support diagnostic instead of a crash; predictions remain empty. Original valid five-neighbor outputs match all four before-edit synthetic goldens.
- No change to k5, minimum3same-family references, ranking, family priority, model weights, horizons, SQL or production adjustment. No other PR was merged. C1support26and the other research packages remain on their own branches/private collectors; this release does not promote them.

## Actual hosted execution

The main-push [P9run42025734609](https://github.com/NiedzielX/beyond/actions/runs/42025734609) completed **SUCCESS**at12:17:11UTC, including build/persist. This ran in Korona603/T48's genuine11:15–12:45UTCwindow.

An independent heartbeat was explicitly requested at12:19:58UTCafter verifying no P9/heartbeat run was active:

1. [Heartbeat42026225277](https://github.com/NiedzielX/beyond/actions/runs/42026225277), main e04033f, created12:20:00UTC, **SUCCESS**12:20:09UTC.
2. Its [P9child42026240780](https://github.com/NiedzielX/beyond/actions/runs/42026240780), same main SHA, created12:20:06UTC, **SUCCESS**12:20:48UTC. The build/persist step is successful.
3. Fresh12:22:12UTCDBreads verify v1=8attempts/0predictions/0scores; v2=7attempts/3predictions/3score rows across2independent events. The last v2attempt remains exactly11:16:24.872757UTC; no row was rewritten or duplicated. C1v8remains17scored/MAE3248.807865/live adjustment0.

All observed main checks are successful. No unavailable job-log contents are claimed; proof uses actual run/job/step records and fresh DBsummaries. The earlier11:15failed heartbeat child and later pre-release failed scheduled/dispatch runs remain failed history.

## Acceptance boundary

**Deployed correction: proven. Corrected hosted heartbeat→child success: proven. Existing expected negative DBstate/idempotency: proven. Fresh DBrow created by that heartbeat: not yet proven.**

Korona's legitimate v2row had already been created locally at11:16UTCafter the original child failed. A successful retry cannot turn it into a new hosted insertion or change its time/github_sha. Keep the strict fresh end-to-end redundancy milestone open until a genuinely unrecorded window. Next candidate:Górnik449/T48at16:30UTC(17:30Warsaw), protected by the existing bounded guardian. Verify actual heartbeat dispatch, successful child and expected new DBrecord then; do not backfill any missed historical case. Prediction readiness may still fail closed legitimately.

Private proof directory:`/workspace/ops-runtime/2026-11-05-p9-release/`. Twenty release/run/job/before-after DBreceipts were privately backed up:69196compressed bytes, SHA256`f85aa7340d7da24deae380d21502706e8710890ea6cefa5ae3bb23743a9eb75f`, namespace`p9-release-evidence-v1/`. Exact remote read-back, independent decompression and every file checksum verified.

The research checkout is a stacked branch; remote main's newly released P9 file is verified independently. Do not mistake its older local ancestor for the deployed main implementation. Existing frozen collectors remain alive with their own source locks. New panel feed deployment still requires its separate project administrator binding. `production_change=false`, `live_adjustment=0`.

## Fresh full-chain acceptance —16:34UTC

The later449/T48window provides the missing fresh proof:guardian→heartbeat42065252556SUCCESS→child42065268900SUCCESS→newv1attempt16:31:47/newfirstprediction16:31:48plusv2V1_COVEREDattempt. Full-chain redundancy acceptance is nowDONEfor this positive window; it is not a new negativefallback-branch test. No localwriter, oldrecordoverwrite or historicalbackfill. Detailed evidence/recovery:`P9_FRESH_HEARTBEAT_CHAIN_RESULT_2026-11-05.md`. Earlier pending/603idempotent paragraphs remain dated history.
