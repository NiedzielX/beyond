# Rolling72 v2 — genuine paired forecasts now running

[Machine proof](ROLLING_72H_FIRST_PAIRED_SHADOW_PROOF_2026-11-09.json). On **November9 at11:45:31 Warsaw**, after published code8b02d71 and freeze30e1c98, the single frozen model issued **six learned forecasts**, paired with **six persistence forecasts**, for two real fixtures and24/48/72h. There are24 status rows; drift lacks its required24h anchor and pickup lacks a fitted artifact, so neither is silently replaced by another model.

The actual bounded cycle used three GETs and received five new observations, preserved their original receipt, appended predictions to a separate cloudSQLite, and remotely backed up/restored a **793066-byte private bundle** containing model, manifest, freeze, registry, original sources and ledger. This proves source→actual future prediction→private recovery. It does not prove managedSQL serving, a hostedActions forecast job, deployed panelv2 or improved MAE.

| Fixture | Last real availability | Model +24h | Model +48h | Model +72h |
|---|---:|---:|---:|---:|
| Jagiellonia, event24 | 8439 | 8252.81 | 8001.29 | 7816.30 |
| PiastGliwice, event10500 | 4308 | 4163.63 | 3993.29 | 3821.67 |

These are **publicly available places**, not paid sales or attendance. Exact values are immutable in the machine proof; the table only rounds for reading. The Jagiellonia issue is outside the maturity range represented in training and retains that warning. A plausible changing curve is not evidence of accuracy. The1200-seat attendance-MAE goal remains separate.

**Automatic future scoring is active:** cloud workerPID936149 started10:45:37UTC, verified running with538localcycles/0errors at19:43UTC. It checks locally everyminute and performs bounded remote work only at declared windows, with15minute retry throttling. Deadline **November12 at13:00Warsaw**; this covers the first72h target plus scoring grace. Later issues may remain pending beyond expiry. Hosting depends on this cloud machine. V1workerPID931348/deadline is unchanged.

First v2 targets mature **November10/11/12 at11:45:31Warsaw**; source/scoring begins at11:55:31. Scores are currently zero and MAE is **not yet available**, not zero. All current fixtures remain exposed/unverified for formalreview;30freshfixtures/8clubs gate remains closed. No old predictions, scores, source clocks, parameters or production serving changed. Defaultsfalse/0.

**Independent recovery replay,19:46UTC:** fetched the existing private remote object again, restored all10files to a new isolated private directory, loaded the unchanged trusted model, and reproduced allsix stored candidate values exactly without refitting or modifying either original ledger. Hosted code/freeze DemandEngine runs42603139826/42603156836 and42603267279/42603310774 succeeded. These CI runs tested code; the actual forecasts were issued by the cloud process.
