# Future fixture coverage — actual read-only audit

**At November9,20:50:43 Warsaw, the live `ticket_events` table contains exactly three future fixture rows across three clubs.** This is not merely an old pinned-registry restriction: the one bounded live GET returned HTTP200, `Content-Range: 0-2/3`,1124bytes. [Machine evidence](FUTURE_FIXTURE_COVERAGE_AUDIT_2026-11-09.json). Original response and actual receipt are private under `/workspace/ops-runtime/2026-11-09-future-fixture-coverage/`.

| Current future fixture | Club | Kickoff, Warsaw | In pinned registry | Tracked by rolling72 |
|---|---|---|---|---|
|10500|PiastGliwice|November20,18:00|Yes|Yes|
|452|PogońSzczecin|November20,20:30|Yes|No|
|24|Jagiellonia|December10,21:00|Yes|Yes|

All three source identities and all nine selected comparable metadata fields are unchanged from the38-row pinned registry. There are zero new IDs or new source identities. The current rows have distinct source identities; this audit does not turn them into fresh formal-review fixtures. All three have more than72hours until their stored kickoff, so metadata alone permits24/48/72h pre-kickoff windows. No snapshot was requested: usable prefixes, first-observation support, source freshness and actual future labels remain unverified for the untracked fixture.

**Repeated daily forecasts on two fixtures cannot produce the30 fresh fixtures /8clubs required for formal review.** The present metadata supply has only three clubs. Neither repeated snapshots, another model version nor a registry-adapter change creates those missing independent events. The current admission/collection bottleneck therefore needs investigation before model retuning; one metadata read alone does not explain its upstream cause.

One provenance field requires a semantic check before broader admission: Pogoń452has ticket-source domain `bilety.pogonszczecin.pl` while its `source_url` points to `ekstraklasa.org`, identically in the old registry and current metadata. The latter may be a fixture-confirmation URL. This is a proven host difference, **not proof that the fixture or ticket-source identity is wrong**. A next contract must distinguish ticket-source identity from sporting confirmation; do not silently guess aliases or edit the active frozen gate.

Next steps, without changing the current experiment:

1. Audit existing fixture discovery/collector code, actual workflows/runs and admission diagnostics to explain the three-row future supply. Preserve unresolved fixtures and missing kickoff confirmation; do not backfill forecasts or blindly enable jobs.
2. Once genuinely new source fixtures are available, precommit a separately versioned registry-admission/collection route using the **same frozen v2 weights and parameters**, with no refit or retrospective accuracy selection. Bind actual receipt-time metadata, complete source identities, explicit alias groups, immutable snapshot ownership and retained scope changes. Distinguish confirmation URLs from ticket-source domains by an explicit schema.
3. Keep current v1/v2 registries, worker deadlines, predictions and scores unchanged. Admit new forecasts only after actual metadata/source availability and the new operational freeze. Old/exposed fixtures remain exposed; fresh-review status needs its own verified exposure record. Continue paired prospective24/48/72h scoring and the existing30/8gate.

One metadata GET; zero snapshot/history GETs, database writes, forecasts or model fits. `production_change=false`, `live_adjustment=0`. Public availability errors remain separate from the approximately1200-seat attendance-MAE objective.
