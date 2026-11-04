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

The separate host-dependent collector `watch_c1_training_expansion_v1` holds a lifetime lock, invokes inference only, saves operational attempts and makes byte-verified private backups in its own namespace. It requires an explicit deadline within72hours and polls every15minutes. Prepared command below; startup and actual post-launch cycle proof must be recorded in handoff before calling it active:

```bash
python -m ml.watch_c1_training_expansion_v1 \
  --artifact-dir /workspace/beyond/ml/artifacts/c1_training_expansion_v1 \
  --runtime /workspace/ops-runtime/2026-11-04-c1-training-expansion \
  --until 2026-11-06T20:30:00Z --interval 900
```

At the12:17UTCfixture read, the first final24window opensNov5 17:00UTC forMotor5091, followed byWisła448 at19:30. This is later than the existing daily/guardian/drift workers' Nov5 09:30deadline. The new collector has a separate explicit Nov6 20:30deadline; it is not a renewal of those processes or a perpetual coding service. Eligibility/prior/source gates can still fail; a planned window is not a forecast. Later capture requires this host to survive or a separately verified deployment/renewal. Never recreate a missed issue.

## Evidence gate and next action

Local validation:341unit checks (189core+152entry-point/operational), including15candidate timing/integrity/immutability cases and2collector-bound/namespace cases. Frozen package validation passed without fitting. Hosted validation including the committed new artifact is still pending at this entry.

Start and verify the bounded collector; later inspect its first genuine immutable paired forecast and private read-back. No lower-MAE claim until future confirmed outcomes exist. First fixed review is30new scored events /8clubs with paired event-bootstrap intervals against both originalv8policy and shared prior. If raw improves but the unchanged policy does not, this candidate has not met its primary objective; do not change its thresholds after the result. Bias/tail and coverage must be reported. Source publication-time verification and missing current-season history remain separate limitations.

Production remainsOFF: `production_change=false`, `live_adjustment=0`. No old gateway rows, historical forecasts or labels changed.
