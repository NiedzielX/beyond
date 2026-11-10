# One real fit and mechanism evidence

The separately precommitted rolling72 v2 candidate was fitted once after code publication: [actual fit proof](../../ml/ROLLING_72H_OFFLINE_FIT_PROOF_2026-11-09.json). Preserve that artifact and its source dependencies. A per-directory exclusive fit marker is not a global experiment registry: fix one canonical real output directory in the run log before fitting, and never fit the same experiment elsewhere. Synthetic contract-test artifacts are explicitly unservable by default.

The earlier daily-v1 model had zero value-history coefficients. V2 has263 value-history splits and the fixed predeclared synthetic probes change future outputs when prior history changes while the anchor stays fixed. This proves computational sensitivity, not accuracy or correct direction. No tuning, alternate fit or winner selection follows from the probes. Lower MAE requires genuinely future matched outcomes.

Capture-aligned historical fit inputs all have staleness0. Live predictions shift the horizon by actual source age and reject age>1h; this is a declared transport assumption, not a learned latency model. Keep this limitation and early-maturity coverage flags visible. Historical ingestion/metadata clocks remain unproven even when source files are byte-hashed and the model loads correctly.

A successful Vercel Vite build does not imply TypeScript validation: the initial rolling72 preview deployed despite TS7 narrowing failure. Explicit hosted typecheck/build and the separate Chromium job later succeeded after fixing the helper declaration. Distinguish those checks from visual inspection, Tab navigation, current production deployment and a continuously hosted live feed. [Exact panel evidence](../../ml/ROLLING_72H_PANEL_CI_PROOF_2026-11-09.json).
