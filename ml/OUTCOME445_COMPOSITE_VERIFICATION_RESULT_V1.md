# Outcome445 — composite fixture verification and genuine scoring

2026-11-04. The last of the six tracked Oct30–Nov2 outcomes is now verified and appended. No canonical schedule, earlier outcome, forecast or frozen model was changed.

## Exact evidence and limits

Primary attendance source: https://www.frekwencyjny.pl/, retrieved13:45UTC in successful hosted run41840960556. Its unique Nov2 Zagłębie–Korona1:0 row reports3396 and displays18:10Warsaw.

Independent official match report: https://www.zaglebie.com/Aktualnosci/Pierwszy-zespol/trzy-punkty-na-rozpoczecie-tygodnia_n20423, HTTP200/full extraction in hosted run41886729706. Official card explicitly gives Zagłębie Lubin, Ekstraklasa round13, **Nov2 18:00Warsaw**, Korona Kielce and1:0; report body confirms `KGHM Zagłębie Lubin 1-0 Korona Kielce`. This exactly agrees with canonical event445 /17:00UTC. There is one canonical same-club/opponent/date/competition fixture.

The official report does **not** independently supply the attendance count or explain the primary site's clock difference. Attendance remains the primary provider's reported count. Composite verification stores both sources/hashes/retrieval times, both clock values, the exact official fixture excerpt and `official_attendance_corroborated=false`, `cause_of_time_discrepancy_verified=false`. No delay was guessed, no blanket10-minute tolerance introduced, no existing clock moved. The original single-source strict parser is unchanged. A narrow tested event445 verifier anchors fixture identity to the exact official schedule and the attendance to the matching primary fixture/date/result.

Earlier official-source discovery runs41885686157and41886126731succeeded with incomplete retrieval coverage: club news200, guessed/mecze404, away club403; follow-ups located the exact official report. Retrieval success alone never imported a label. Raw receipts stay private under `/workspace/ops-runtime/2026-11-04-blocked-outcome445-source-audit/`.

## Actual append-only operation

Composite verification18:28:48UTC; history ingestion started **18:29:36.681277UTC**. Exactly1absent `ml_match_history` row inserted with reported attendance3396 and official canonical17:00kickoff; original primary17:10is preserved in provenance. Existing exact-match sync inserted outcome445at **18:29:37.697032UTC**. Read-back proves all older outcomes unchanged, all frozen artifact hashes unchanged and canonical schedule unchanged. The new fixture is later than every frozen training cutoff; no old training frame was rebuilt or fitted.

This completes **16new history records /6tracked genuine outcomes** across both Nov4source tasks. It does not repair any missed inventory observation or prospective forecast.

## Existing frozen evaluations after the last genuine outcome

| Lane | Independent events | Incumbent MAE | Challenger / policy MAE | State |
|---|---:|---:|---:|---|
| Original C1v8, latest event row |17|3131.157876 prior|3248.807865 policy|101forecast rows /17forecast events; unchanged model |
| Frozen encoder attendance |4|1051.043479|1623.917287|Early worse;4/8event gate,4/5clubs; no promotion |
| P9v2 attendance |2 (3rows)|1248.354372|1984.717101|Unchanged early worse result |
| P9v1 attendance |0|null|null|No prediction to score |

C1rawMAE6241.964642; window policy3913.558409. For event445 alone, original policy kept PRIOR3773.089059 vs actual3396, AE377.089059; raw4857.179819, AE1461.179819. Frozen scorers inserted1C1score and1encoder score; P9added none.

Earlier C1 policy4121.45on11 and3428.29on16 remain dated cohorts. **3248.81on17 reflects completed outcome coverage, not a changed or improved model.** All17already-issued C1forecast events now have genuine outcomes. New expanded Ridge20and direct-person median still have0future scores/nullMAE; the six ended fixtures do not become prospective validation for Nov4freezes. `production_change=false`, `live_adjustment=0`.

Private verification recovery:11files /44911bytes, SHA256 `ff0776226ae1b0a1592914f5b1cfdc4595abef9e80c77de169ab8ebbc363d133`; upload, byte-read-back and decompression verified. A first upload timed out; immutable retry/read-back succeeded, without repeating any database insert or score mutation.
