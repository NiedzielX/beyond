# Panel ingestion freshness investigation and repair

User added screenshot investigation while historical C1replay was running. Read panelAGENTS/sharedMLinstructions before implementation. Inspected actual panel service/component and multisource dashboard refresh SQL/watchdog/racefix.

Actual public browser-role GET2026-11-05T15:37:23UTC:HTTP200,133exact rows, projection just refreshed,26nonexcluded/noncompleted UIrows. Two elapsed candidates are incorrectly presented as active:Motor48812Oct27(buffer291,lastseenOct27)andRadomiak48101Nov2(noinventory,lastseenNov2). Bothstillnullticket_event_id. DBprojection refresh is current; noHTTPcachecause established. UIuses only status exclusion and one mount-time fetch. Record freshness and new read time must be distinguished. Private receipts:`/workspace/ops-runtime/2026-11-05-panel-ingestion-freshness/`.

Implement read-time partition/history and bounded refresh UX under matchingSDD, without rewriting underlying historical source evidence or claiming a new DBdeployment.
