# Rolling72 — etap A i kontrakt wejść

Data: 2026-11-08. Status: AUDIT_AND_LOCAL_CODE_VERIFIED; source integration and model remain open.

## Cel

Wykonać kolejny etap planu po przeglądzie literatury: ustalić rzeczywiste pokrycie od pierwszego odczytu i etykiet +24/+48/+72 h, bez zmiany modeli frozen. Użytkownik jawnie autoryzował równoległych agentów.

## Rozdział pracy

- Agent danych: wyłącznie zachowane eksporty i prywatne agregaty; bez DB/fit.
- Agent kontraktu: audyt PIT, cech i frozen ograniczeń; read-only.
- Agent panelu: rzeczywisty feed/release i sektory; read-only.
- Główny agent: SDD, integracja i ewentualny osobny kontrakt B z testami; bez fitu i deploy.

Prywatne agregaty: `/workspace/ops-runtime/2026-11-08-rolling72-stage-a/`. Nie commitujemy raw danych ani sekretów.

## Wykonanie

Przeczytano canonical roadmap/execution/progress/trajectory/handoff, AGENTS, lessons, plan i przegląd literatury. HEAD początkowy 1d241f4e62b1fa3b471c80778eccfcd9be9f46a5; czyste drzewo. Agenci uruchomieni do niezależnych audytów. Brak odczytów sieciowych/DB, fitu, aktywacji i odnowienia workerów.

## Konkretny rezultat

- Dane:38meczów/16klubów/29,063snapshotrows; firstpoint+72h19/13, allprefix+72h20/14, P50only1/1.1014literalzeros zachowane.10fixturemeasurementchanges. Brak historycznych snapshotknown_at i stałej puli.
- Agent danych zapisał prywatny audit/summary, agent kontraktu sprawdził33staretesty, agent panelu podał konkretne braki feedu. Podczas dalszego kodowania obaj aktywni agenci trafili na limit użycia. Główny agent przejrzał zapisane pliki, dokończył testy i moduł etykiet, bez ponawiania agentów.
- Nowe wersje: `rolling72_features_v1`, `rolling72_labels_v1`, `rolling72_coverage_audit_v1`; stare źródła/model/artifact/ledger bez zmian. Osobny testowy workflow wykonuje audytowe testy; żadna workflowkolekcji/produkcji nie została zmieniona.
- Publiczny raport/agregaty pozbawione raw danych, canonical5docs/README/plan/lessons zaktualizowane razem.

## Weryfikacja

-218DemandEngine +25audyt/source-state =243testyPASS.41nowychrolling72testów; reszta to istotne istniejące kontrakty.
- Hash oryginalnego cache i jego manifest sprawdzone; wszystkie macierze i agregaty odtworzone kodemrepo.
- YAMLworkflow parsuje; gitdiffcheckPASS. Brak zmian starych frozenartefaktów/ledgerów.
- GitHubGETmain potwierdził bcec6b027e33a6ed6260d3ee469006c05f6f1010. Zwykły sandboxowyGETnie miał sieci; autoryzowany odczyt poza sandboxem zadziałał. Brak wywołań Supabase, DBwrite, fitu, deploy, odnowienia wygasłychworkerów lub dawnychslotów.

## Następny krok

Receipt-bound source adapter, wersjonowany zapis cech i dokładny precommit benchmarków/kandydata. Nowe wejścia/etykiety są kodem, nie uruchomionym modelem ani nowymMAE. Odsłonięte dane pozostają diagnostyczne. Pełne B/C/D/E i cel1200MAE nadal otwarte. Publikacja na istniejącej gałęzi badawczej przygotowana; main i produkcja mają pozostać bez zmian.

## Kolejny wykonany krok B

Pierwszy commit b74b3d0e5522d83ce7c6d9fc3b1457724c089c78 opublikowano i zweryfikowano na istniejącej gałęziPR227. HostedDemandEngineSmoke42488118781/42488114629SUCCESS; też cztery inne sprawdzone kontraktoweActionsSUCCESS. Nie są to dowodyDB/panel.

Po dopisaniu kontraktuSDDzaimplementowano `rolling72_receipt_store_v1`: konserwatywny knowledge-upper-boundrzeczywistego receipt, immutablelokalnySQLite, osobne metadane/cechy/statusy, bez forecast/score/fit.13nowych testówPASS. Finalny lokalny zestaw218+38=256PASS;54nowychrolling72testów. Workflow testów uzupełniono o receipt/storetesty.

ActualCLI14:09:28UTC: oryginalnycacheSHA3a5981ce…→38nowych inputissues/114feature-statusrows→33pastkickoff/2stale/3measurementchanged→0READY/0forecasts. Integrity/foreignkeyPASS; proofJSONiSQLite pozaGit. To świadczy o rzeczywistym fail-closedzapisie dla starego wejścia, nie świeżej prognozie aniSupabase/panelchain.

Dalszy krok: świeży ograniczony odczyt, rzeczywisty dodatni przypadek źródło→store oraz dokładny precommit benchmarków/kandydata przedfit. Dawne unknownclocks pozostają unknown; nie przepisano starych ledgerów.

Bieżący cache ma5przyszłychfixtures:2na8listopada,2na20listopada,1na10grudnia. Korekta po powiązaniu statusów z konkretnymi datami: tylko jedna z trzech dłuższych historii ma source-keychange, dwie mają zgodny klucz i sąstale. Pozostałe dwa measurementchanged dotyczą meczów8listopada. Sam refresh nie dowodzi zgodności kluczy, ale może dać poprawne wejście dwóm stabilnym seriom. Następny audyt ma rozstrzygnąć zakres/kompatybilność pomiarów, bez usuwania niezgodnych punktów dla poprawy MAE ani nadpisywania v1.

## Pozytywna integracja i publikacja drugiej części

395ef0eab9b01ad6c2eea48802cae7ab76074ce1opublikowano/zweryfikowano. HostedDemandEngineSmoke42488648388/42488642850SUCCESSi cztery inne odczytane kontraktySUCCESS. Main nadalbcec6b0bezmerge.

Zamiast pełnego eksportu wykonano3małeGETSupabase:2metadane event i po1latest snapshot. Actualcapture14:05:03/14:13:02UTC, receipt14:14:04UTC. Metadane tych2eventów identyczne zcache. Nowy kompozyt oryginalnego prefixu+2autentyczne świeże punkty zachowuje hash obu źródeł i jawny brak punktów w luce; nie odtwarza historii ani dawnych forecasts. Receiptkompozycji14:14:57UTCkonserwatywnie wiąże całość znanej kopii.

ActualCLI14:14:57.490UTC→2READYissues/6READYfeature rows→osobnylokalnySQLite.38wcześniejszychfailedissueszachowanych, retry0insert, integrity/FKPASS; utworzono checkpointSQLite. Publiczny proofJSONbezraw: `ml/ROLLING_72H_FEATURE_STORE_PROOF_2026-11-08.json`; pełne receipts/checkpointprywatnie. Nie maforecast/score/fit/MAE, Supabasewrite, paneldeployment ani dowodu stałej puli.

Dalszy krok to dokładny precommit benchmarków/kandydata i eksperymentC. Nie przedstawiać6cechowych wierszy jako6prognoz. Trzeci mecz>72h ze zmianąsourcekeypozostaje osobnym blokiem pokrycia.
