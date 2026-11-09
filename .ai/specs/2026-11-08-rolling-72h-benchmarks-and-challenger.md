# Rolling72 — wspólne benchmarki i jeden challenger

Data: 2026-11-08. Status: DESIGN_IN_PROGRESS; przed implementacją/fitem. Rozwinięcie MAE_RESEARCH_ROADMAP_V6 i ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1. Nie zmienia frozen lanes ani odrzuconych eksperymentów.

## Autoryzacja i cel

Użytkownik zlecił dalszą ciągłą pracę z agentami. Najbliższy wynik: te same realne wejścia i cele +24/+48/+72h dla persistence, osobno wersjonowanego driftu, warunkowego pickup i jednego małego globalnego medianowego modelu zmiany. Około1200MAE frekwencji pozostaje celem osobnego targetu, bez zastępowania błędem inventory.

## Kolejność

1. Audyt niezależny: benchmarki, walidacja, źródła treningu. Dalsze agentowe zadania są jawnie autoryzowane.
2. Dokładny precommit benchmarków/kandydata i danych przed fit; zapis/publikacja przed ekspozycją nowych wyników.
3. Implementacja i sensowne testy granic clocks, grup, baseline, missingness i artefaktu. Model nie czyta etykiet przy predykcji.
4. Tylko autoryzowany w precommicie jeden fit, jeśli dane i support spełnią jawny kontrakt. Brak automatycznego wyboru algorytmu/parametrów po wyniku.
5. Freeze/hash, nowy przyszły ledger, rzeczywiste prognozy przed targetami i późniejsze genuineoutcomes. Nie odtwarzamy missedprospective.

## Granice danych

Receipt-bound features mają dodatni realny przypadek2issues/6wierszy; nie są forecastami. Stary eksport to historicaldevelopment, bez pierwotnych czasów ingestii, i odsłonięte mecze. Dane mogą być znane przy dzisiejszym fit cutoff, co nie dowodzi ich dostępności przy dawnych replayissues. Te dwa zegary muszą pozostać rozdzielone. Nie dopisujemy fikcyjnego historicalknown_at i nie ogłaszamy starego cohortu nowym holdoutem.

Do czasu dokładnego precommitu nie wolno wykonać fitu. Wersja/model/cechy/hiperparametry/minsupport/sampling/groupweights/labelavailability i fallback muszą być utrwalone z góry. Wcześniejsze frozen drifty nie przyjmą nowych arbitralnych issues; komparator ma oddzielną wersję i zapis.

Production_change=false, live_adjustment=0. Brak automatycznej aktywacji produkcji, reklamy lub zmian cen; panel/feed osobny etap.

## Wykryta poprawka granicy źródła przed dalszym zapisem

Audyt niezależny wykrył, że persist_batch sprawdza hashe/cechy i knowledgebound, lecz nie odtwarza batchu z oryginalnych sourcebytes. Sam prepare_receipt odrzuca capture po exportcutoff; publiczne persist powinno dowodzić tego samego i pełnego źródłowego powiązania. Naprawa obejmuje wyłącznie nowyreceiptstore i testy: obowiązkowe oryginalne bytes, rederiveprepare→dokładnycanonicalbatchcompare przedDB, test forgedcanonicalissue/sourcehash. Zmienia walidację błędnej ścieżkiAPI, nie stare dane, modele, predykcje lub frozenkontrakty. Agent walidacji ma izolowaną własnośćtych2plików.

## Osobny ledger baseline i scoring — kontrakt przed implementacją

`ml/rolling72_shadow_ledger_v1.py` tworzy nowySQLite własnego application_id i odmawia otwarcia obcych/frozenledgerów. Manifest zamrożenia zawiera actualfreezeclock, precommitSHA i SHA kodów features/labels/receiptstore/baselines/ledger. Capture odbywa się tylko przy obecnychzgodnychbajtach źródła, pofreeze i przedtargetami; CLIbezbackdate, actualissued/writtenclocks, brakUPDATE/REPLACEstarychissues/predictions. Baselinespersistence/drift mogą działać bezfitu; pickupUNAVAILABLE. Każdy z24/48/72 i statusunsupportedpozostaje w ledgerze; numericforecasts są liczone oddzielnie odstatusrows. Currentexposedfixtures są operacyjnymi przyszłymi obserwacjami, nie nowym30fixturereviewcohort.

Scoringczyta późniejsze oryginalne źródło, dopasowuje genuine label przyreceiptknownboundpo dojrzeniu targetu, utrwala pierwszą przyjętą etykietę/receipt i oddzielne błędy każdego dostępnegobaseline. Późniejsze poprawki/odczyty nie nadpisują score. Fail/missing/pending zachowane; brakscore nie znaczyMAE0. Raportevent-balanced oddzielnie perh i model, actuallead/staleness oraz exposurecohort. BrakSupabasewrite i produkcyjnej aktywacji. Testy dotyczą realnych zegarów, source/freezehashów, niewłaściwego ledgeru, niezmienności vintages/score i wspólnego targetu.

## Osobny feed/parser — kontrakt przed implementacją

Nowyfeed `rolling72-shadow-feed-v1`, readonlyserializer nowegoSQLitebezSQLwrite ani publicznego deploy. Pola: generated_at, metric=public-displayed-available-total-v1, evidence_kind=immutable_shadow_ledger, productionfalse/live0, frozen_at i vintages. Każdyvintage zachowuje ticket_event_id/club/kickoff/event_known_at/issued_at/written_at/status/measurementkey/hashlineage/scenarioUNKNOWN/cohort; observations rzeczywiste capture/known/value/ID oraz points dokładnie24/48/72z targetat/status/models(persistence,drift,pickup). Model ma actualid/status/reason/predicted_available_total/predicted_delta i nullablepóźniejszyscore z actualtargetcapture/known/value/scored_at/error. StatusUNAVAILABLEniejest0. Żadnychsecretów/sourceAPIURL/rawreceipts.

Nowyparser/geometria wpanelu oddzielnie odfrozendailyv1 i starego final_p50; nie rozluźnia starychparserów. Obsługuje firstpoint/arbitraryissue, zachowuje wszystkievintages i nullhoryzonty. Kotwica wyłącznie faktyczny capture/L, bez sztucznego punktu przyissue. Futureline actualpersistedpoints; brakhoryzontuprzerywalinię. Baselines jawnieopisane jako benchmark, nie trainedML/P50. Missing/malformedfeed failclosedbezfallbackhistorycznejfrekwencji. Lokalnyparser/build/testniejest deployedfeedaniMAE.

Agentfeedownsnowepliki backendserializer/test orazpanelservice/geometry+tests; nie zmieniaexistingcharts/parserów/package/configure/deploy. DocelowyUI/wdrożenieosobno po source→persistedforecast→feedproof.

## Prywatna odtwarzalność nowego ledgeru — przed kodem

Osobny modułbackup używa istniejącego prywatnego Storagebucket, wyłącznie namespace `rolling72-shadow-v1/<contenthash>.json`, bez zmiany starychlatestmanifests. SnapshotSQLiteprzezreadonlybackup+integrity/FK, oryginalnereceipts i freeze/metadata są prywatnymkompresowanymbundle. Rozmiarograniczony, hashewszystkichfiles/manifestu, immutabilityput i readbackverify, niezależnyrestoretownowymfolderze, bez nadpisania staregoDB. Nigdypublicbucket/signedURL/sekretwlogach, żadnegoSQLwrite, modelactivate lubsourcecallback. Kod/testy możeprzygotowaćagent; rzeczywistyStoragewritepodopublikacji/freeze/pierwszymlocalforecast jest kopią odzyskiwania, nieprovenhostedDBforecast.

## Codzienne bounded source/score/forecastcycle — przed kodem

Nowycyclerunner poza5frozenplikami, z własnym kodhashlockiem i deadline≤72h. Nie odnawia starychcollectorów. Wejście: nowybaselineSQLite/ostatnizweryfikowanyexport/oryginalnyregistry/freeze. Źródło:3boundedGET(per2eventmetadata +snapshotincrementalperfixture), tylkoid>lastseen, capture<=actualrequesttime, max500rows/event i failclosedprzycap/truncacji; żadnego globalfullhistorypoll. Verifyprovider/source_domain/club/externalIDwregistry. Nowo pobrane wcześniejsze capture są autentycznymi rowami poznanymi teraz; nie zmieniają prefixów/starych prognoz. Zachować hash/actualsource-receipt, przekazać doscorethenactualcapture.

Localchecksco≤60sbezDBnetwork. Fullcycle dopiero gdy futuretargetdojrzeje+10min albo min24hodostatniegoissue+10min. Żadnychcatchup/backdatedissues; po przerwie eventualnewissue ma actualnow. Missing/failedgatesgenuine, nie0. Przydeclareddeadlinestopz auditlogiem i pendingforecasts; nieobiecuje siębezterminowejusługi. Po każdej pozytywnej zmianie atomowystate/currentfeed i prywatnyverifiedbundle+restore. Zbieraćpathswszystkichźródełwledger.sources. Activeprocesshealth wymaga nieZ oraz actualcycle/audit, nie samegoPID.

Opcjonalnyhostedworkflow_dispatch na osobnym researchrefmoże odtworzyćprivatebundle, wykonaćcycle, backupi sanitizedfeedartifact. Schedule/defaultmainniejestautomatycznieaktywowane; configuredworkflow≠hostedrun≠expectedDBrecord. Wyłącznie nowyprivateSQLite+Storage, brakSQLproductionwrites/modelactivate.

## Panel: rzeczywisty snapshot do przeglądu i oddzielny komponent

Po rzeczywistymcapture12forecastów serializer→parser→geometria przeszły na prawdziwym feedzie2fixtures. Można przygotować nowy komponent Rolling72ForecastChart i odrębnąresearchpreviewpage korzystającą **jawnie z autentycznego zahashowanego snapshotu** serializerJSON. Nie jest to testfixture ani zastępstwo missinglivefeed. Snapshot ma czytelny czas wygenerowania/issue, etykietębadawczą, benchmarknames, brakpaid-sales/MLaccuracyclaim, zachowujevintages i nullstatusy. Sanityzowany derivedfeed nie zawiera sourceURL/secret/rawAPIpayload i nie jest prywatnymźródłowymexportem; prawdziwe rawreceipts pozostają pozaGit.

Komponent normalnegoeventpage używa wyłączniejawniekonfigurowanego nowegoURL; brakURL/feed/error daje jawnąniedostępność, bezpodstawieniastaticsnapshotu. Osobnaroutepreview może jawnieotworzyćplik `public/research/rolling72-shadow-snapshot-v1.json` pochodzącyz rzeczywistegoexportu, nieprzeliczaprognoz. Existingdailyv1/final_p50niezmienione. Mainprodukcyjny pozostaje bezmerge/release; researchpreview/draftPRsą konkretne dooceny. Dalszebuild/typecheck/browserCIweryfikowaneoddzielnieoddeploy/livebackend.
