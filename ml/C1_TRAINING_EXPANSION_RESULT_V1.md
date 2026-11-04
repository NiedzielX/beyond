# C1 training expansion v1 — frozen, accuracy unknown

2026-11-04. Implements `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md`, published in79ab4b00before any fit. Implementation/source guards were published infb1e2ed/47d39bb; hosted source checks41829260829and41829272385passed. This is one training-support experiment after the matched C1/D2audit, not a C1v8replacement.

## Actual freeze

- Package: `c1-training-expansion-v1-frozen-2026-11-04-n20`.
- Frozen2026-11-04T12:26:39.371491Z, one deliberate build-time fit.
- Serialized estimator SHA256: `04dbdf1e5b8846782194f2ca1e833078a10238d1c9ca151b8391a869449027ba`.
- Exactly20confirmed training events /74rows /11clubs, input cutoff12:17:04.736622Z. These are training data, including the former11exposed holdouts. None can enter this candidate's prospective test.
- Same30features, median/indicator imputation, standard scaling, Ridge alpha10, direct occupancy, equal event weight, capacity clipping and v8policy. No tuning or model selection.
- Verified all900original training feature cells, original targets/capacities, outcome agreement/confirmation cutoff, raw snapshot/time/PIT identities and all old dependency hashes. Load-back returns74finite predictions. **No training MAE was calculated.**
- Manifest/precommit/implementation/dependency checksums are enforced during inference; a separate freeze receipt protects accidental manifest edits. Old C1v8artifact and all existing prospective lanes remain unchanged.

Private training/input/artifact backup:472,724bytes, byte-for-byte read-back verified, SHA`6fa1dcb191aeda5fe69e5303045dd94412d51a42007c72d564da0260aa0b2357`, new`c1-expansion-v1/`namespace. This is a private recovery object, not relational prediction persistence.

## Actual inference and pending collection

The real current DB collector→both frozen runtimes→capture CLI executed at12:27:04UTC. It returned **0eligible candidates /0new predictions**. That establishes the no-due path and integrity checks, not a forecast, DB prediction record, lower MAE or active managed scheduler. There are0prospective scores and MAEisnull.

The new inference adapter captures paired structural/C1v8/newraw/newpolicy outputs at the same current observation, with exact IDs, actual issue time and input checksum. Exclusive files retain original bytes/issue time across repeats and reject conflicts. Rejects known outcomes/training IDs, old collector requests, sources before freeze or older than2hours, invalid prior timing/PIT/representatives and observations beyond current final24. Failed coverage is recorded, not turned into a prediction.

The separate host-dependent collector `watch_c1_training_expansion_v1` holds a lifetime lock, invokes inference only, saves operational attempts and makes byte-verified private backups in its own namespace. It requires an explicit deadline within72hours and polls every15minutes. Command used for the verified bounded launch below; inspect the actual post-launch proof before relying on its health:

```bash
python -m ml.watch_c1_training_expansion_v1 \
  --artifact-dir /workspace/beyond/ml/artifacts/c1_training_expansion_v1 \
  --runtime /workspace/ops-runtime/2026-11-04-c1-training-expansion \
  --until 2026-11-06T20:30:00Z --interval 900
```

At the12:17UTCfixture read, the first final24window opensNov5 17:00UTC forMotor5091, followed byWisła448 at19:30. This is later than the existing daily/guardian/drift workers' Nov5 09:30deadline. The new collector has a separate explicit Nov6 20:30deadline; it is not a renewal of those processes or a perpetual coding service. Eligibility/prior/source gates can still fail; a planned window is not a forecast. Later capture requires this host to survive or a separately verified deployment/renewal. Never recreate a missed issue.

## Evidence gate and next action

Local validation:354unit checks (189core+165entry-point/operational), including15candidate timing/integrity/immutability,4worker/backup/source-lock,8confirmed-outcome scoring and3exact-anchor enrichment cases. Hosted artifact checks41829752800/41829761093passed onbadcdac; finalcollector/scorer checks41830872028passed on4fe12fc. No fit occurs during these checks.

Keep the verified bounded collector healthy; inspect its first genuine immutable paired forecast and private read-back when its legal window opens. No lower-MAE claim until future confirmed outcomes exist. First fixed review is30new scored events /8clubs with paired event-bootstrap intervals against both originalv8policy and shared prior. If raw improves but the unchanged policy does not, this candidate has not met its primary objective; do not change its thresholds after the result. Bias/tail and coverage must be reported. Source publication-time verification and missing current-season history remain separate limitations.

Production remainsOFF: `production_change=false`, `live_adjustment=0`. No old gateway rows, historical forecasts or labels changed.

## Complete collection/scoring path prepared

Actual SQL inspection showed the existing C1input RPC omits `prior.target_as_of_at`. The separate `collect_c1_training_expansion_v1` adapter resolves the actual prior at the latest source time, verifies ID/values/model/contract/generated time, and adds only that real metadata before calling the unchanged frozen inference code. No computed substitute, model change, gate relaxation or refit. Raw input/resolution packs are private and content-addressed. Direct no-due invocation of the old adapter did not prove this positive-candidate branch; three schema tests now cover it.

`score_c1_training_expansion_v1` attaches only genuinely later confirmed attendance with source provenance; known/future/invalid/changed outcomes fail closed. It preserves immutable per-observation scores, latest-time selection, equal-event window MAE, paired deltas, bias/P90/worst, descriptive club/horizon groups and explicit coverage failures. Below30events/8clubs, review and bootstrap gates remainfalse/null. At first eligibility it preserves an immutable review; it never substitutes the better expert after outcomes. Eight synthetic lifecycle/denominator/label/integrity/review tests are correctness evidence only. Actual DBscorer returned0events/nullMAE.

Manual complete cycle at12:35:39UTC: current collector0eligible→inference0predictions→scorer0scores/nullMAE→private compressed backup read-backverified. Payload SHA00ac0a29b54b2bf6e373d5938de106581430c26ee2e147e9d2614d2500a3ef0f. New backup encoding retains original filebytes/hashes; a focused recovery test verifies whitespace/byte preservation. The bounded worker freezes its collector/scorer implementation hashes at first launch, protecting future evidence from subsequent code changes. Source-contract lock and actual post-launch proof are recorded below.

## Actual bounded launch12:37UTC

PID169529started12:37:36UTC, processstateSsl. Post-launch12:37:41UTCcompletecycle verified0eligible/0predictions/0scores/nullMAE, private read-backSHA3d31d87cd4cb9e9e0d90ee781d2596a35781ce35a34b9ca46795fee447a101e9. Source-contractfile now locks collector/scorer/worker code. DeadlineNov6 20:30UTC; existing workers retainNov5 09:30deadline. This actual process remainshost-dependent; no managedscheduler or positiveforecast/scoring proof. Hosted354-checksource4fe12fc DemandEngine41830872028passed. Next evidence is a genuine eligible paired capture afterNov5 17:00UTC, then a separately confirmed outcome.
