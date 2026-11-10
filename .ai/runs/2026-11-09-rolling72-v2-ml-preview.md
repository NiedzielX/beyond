# Separate paired ML preview implementation

Date2026-11-09. Status: LOCAL CONTRACTS PASS; HOSTED BUILD/BROWSER PENDING PUBLICATION.

Implemented separate v2 service/parser, geometry and chart/page for `/rolling72-ml-preview` in the isolated frontend branch. App route precedes normal dashboard hooks; explicit snapshot fetch omits credentials. Original v1 parser/modelset/geometry/chart/widget remain unchanged. Candidate retains its own identity and values; unavailable models are never substituted. Future path anchors on the real last capture; missing horizons/history gaps break paths. View shows actual issue/model-freeze dates, static export status, unknown interventions and maturity extrapolation. No accuracy, attendance or continuous live feed claim.

Actual sanitized v2 snapshot from the backend agent: generated19:46:21.870612UTC, two actual10:45:31.355823UTC issues; SHA857235542d037c96c79b8681afeff9ba324ae967ac0a811e06ae9ccfbc246d3e. No artificial forecast values, source APIs or private raw export. New Nodecontracts18+geometry5PASS; unchanged v1contracts15+6PASS. Browser script syntax/diffcheck PASS. Source parser uses explicit functionfail():never for TS7 narrowing.

Existing rolling72 workflow now runs both sets of contract tests and both independent Chromium scripts in the same tool installation. New browser script checks actual route/storedcandidatevalues/modelselectors/threefuturepoints/extrapolation/focusAPI/mobileoverflow/noconfigandmalformedfailclosed. It does not establish visual readability, Tab traversal, ML accuracy or deployment. Local dependencies are absent, so full tsc/build/Chromium must be proven by hosted CI after parent publication. No local build or browser success claimed. Parent owns commits/publication/deployment evidence; agent performed no network, Git mutation, model/worker/ledger edit or production activation.


Parentcompletion: publishedbackendc14f48c/panelbd01c8b; actualtypecheck/build/contracts/Chromium/deploymentSUCCESS, see ml/ROLLING_72H_ML_PANEL_PROOF_2026-11-09.json. CompletedSDDmovedtoimplemented; no livefeed/productionmodel/accuracyclaim.
