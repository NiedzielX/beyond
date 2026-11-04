# Direct-person C1 median v1 — actual freeze and operational evidence

2026-11-04. Precommit: `C1_SEAT_MEDIAN_PRECOMMIT_V1.md`; implementation published before fit. Package `c1-live-seat-median-v1-frozen-2026-11-04-n20` fitted exactly once at **13:44:30.790122 UTC** after hosted 376-check validation. No training MAE or reused holdout score was computed.

Same exposed 20 events / 74 rows / 11 clubs and 30 features as the frozen expanded Ridge; exact fitted preprocessor reused without fit. QuantileRegressor(q=.5, alpha=.1, solver=highs), direct attendance in persons, equal-event weights, unchanged governed policy. Nine nonzero coefficients are descriptive only. This changes learner, target decoding and regularization, and is not a loss-only ablation.

Artifact SHA256 `96e3b1a86eafd1922eb09f2f0493c054b7eac4e8e017b4b0a9c1e193cdf08c4a`; manifest SHA256 `8c59720f0f34f39e3590d35eb002d2050d05383b22d87676a4c680df388d4367`. Source-frame SHA256 `be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549`. Original artifacts and the expanded-Ridge frozen helpers remain unchanged. Load-back verifies source/dependency/artifact identities and direct-person decoding without capacity multiplication.

Private training/freeze recovery: 37,032 bytes, SHA256 `29d9a892e39619261b80c52718cbee0be3f9d1ba143de10f18a2a025ea7b389a`, read-back verified. No raw training rows in Git. Separate runtime `/workspace/ops-runtime/2026-11-04-c1-seat-median/`, bounded worker PID200395, launched17:18:59 UTC until **Nov6 20:30 UTC**, interval900s. Actual post-launch17:19:05 UTC capture→scorer→verified private backup cycle: **0 eligible / 0 forecasts / 0 scores / MAE=null**. Backup SHA256 `394ededa61c7a79e1782e340a6c0c0a1176a635e62e4fea0af670b953d01a8bc` (4,855 bytes). A separate restore check reconstructed all five backed-up evidence files byte-for-byte without modifying the active runtime. Host-dependent worker, not managed deployment or perpetual coding.

First possible final24 window is **Nov5 17:00 UTC (18:00 Warsaw)**. Collect median / expanded Ridge / original C1 / shared prior simultaneously from identical genuinely current validated inputs, before outcomes. Existing Oct30–Nov2 outcomes became training/exposed evidence before this freeze and cannot score this new model prospectively. First review requires 30 new scored events / 8 clubs, paired event bootstrap and separate raw-learner/product-policy gates. No advancement or accuracy claim yet.

`production_change=false`, `live_adjustment=0`.
