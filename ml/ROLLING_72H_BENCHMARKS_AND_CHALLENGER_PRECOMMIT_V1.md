# Rolling72: benchmarki i jeden kandydat — precommit v1

Data: 2026-11-08. Status: PRECOMMITTED_DESIGN; bez fitu i bez nowych forecastów w chwili zapisu.

Kanoniczna recepta, czas cutoff i SHA256: [machine-readable precommit](artifacts/rolling72_v1/precommit.json). Dokument rozwija rolling72 plan i literaturę. Żaden frozenmodel, istniejący drift ani stary ledger nie zmienia się. Min5fixtures/3clubs wskazano przed zakończeniem audytu support; wynik audytu2/2 nie uzasadnia obniżenia progu. To minimalny engineeringgate, nie gwarancja statystyczna.

## Źródła i trening

Wyłącznie rzeczywiste oryginalne receipts, z inputissue w czasie faktycznego odebrania; metadane tej wersji oraz wszystkie otrzymane wtedy obserwacje dostają konserwatywny knowledgeboundreceipt. Nie tworzymy known_at=capture dla historycznych wierszy. Etykieta pochodzi z pierwszego późniejszego receipt, który po dojrzeniu nominalnego targetu daje porównywalny rzeczywisty odczyt w6htolerancji. Receipt etykiety musi istnieć przed fitcutoff. Zmiany oryginalnego snapshotID są konfliktem. To historyczna rekonstrukcja as-known, nadal exposed development, nie noweprospective.

Model używa tylko ukończonych przed cutoffem meczów, z labelami dla wszystkich3horyzontów. Min5niezależnych meczów/3klubów na każdym horyzoncie, wspólnychmin5meczów i60rowsłącznie. Ongoingfixtures nie są fitowane. Każdy wspólny mecz ma równy głos; wewnątrz niego każdyhorizon1/3, a potem każdy jego row równą część. Wagi przeskalowane dośredniej1. Wszystkie prefixy i aliasy meczu są jedną grupą. Źródłowe tożsamości wymagają prawdziwego zachowanego registry; równa liczba odczytów nie dowodzi aliasu.

Wykorzystujemy wszystkie genuine receiptissues, bez wyboru najkorzystniejszej godziny lub thinning po targetach. Skorelowane rows nie zwiększają liczby niezależnych meczów. Znane już38fixtures pozostają exposed; ich nowe przyszłe targety mogą służyć działaniu i opisowym wynikom, ale nie są nowymi niezależnymi fixtures formalnego przeglądu.

## Benchmarki przed uczeniem

Persistence: ostatnia prawdziwa dostępność, odjednego punktu. Nowy drift jest osobnym protokołem: min4genuineUTChourlylatestpoints ospanie24h, rzeczywista kotwica24h z6htolerancją. Przedłuża tempo aż do issue+h, czyli przezh+staleness od ostatniego capture. Brak kotwicy/support oznaczaUNAVAILABLE. Staryfrozenstream nie otrzymuje nowych issues.

Pickup: ważona dolna mediana delta z równą łączną wagą meczu. Routing wyłącznie counts: samafamilia+horizon+maturity przymin5/3; wprzeciwnym razie samafamilia+horizonpooled przymin5/3; inaczejUNAVAILABLE. Brak perclubsearch, mieszania niezgodnych provider/source, interpolacji mediany lub aliasowaniacandidate_backfill/vao. Pooledroute jawnie oznacza brak maturityconditioning. Persistence fallback pozostaje osobno nazwany, nigdy udawany jako wynik pickup/driftu.

## Jeden kandydat

HistGradientBoostingRegressor P50,100iteracji, learning_rate0.05, max_leaf_nodes7, max_depth3, min_samples_leaf20, l2_regularization1, max_bins64, early_stoppingFalse, seed42. Dokładne12cech i sklearn1.8.0 sąwJSON. BrakiNaN, bez dynamicznego wyboru kolumn/clubID i bez fittedpreprocessing. Target delta w miejscach; wynik last+delta, min0, bez górnej pojemności i wymuszonej monotoniczności. Przedziały dopiero po osobnej kalibracji.

Nie wykonujemy fitu, gdy gate nie przechodzi. Kod/testy mogą korzystać z danych syntetycznych, jawnie nie będąc realnym fittedchallengerem. Po jednorazowym fit utrwalamy artefakt, data/source/code/precommit hashes i faktyczny freezeclock. Nie retunujemy na później widzianych błędach. Test mechanizmu sprawdza użycie historii, a nie wymusza zmienną linię.

## Nowy zapis i ocena

Forecastissue jest rzeczywistym czasem uruchomienia, po zamrożeniu recepty/artefaktu i przed targetami. Nie nadajemy dawnym przygotowanymfeatures czasu nowej prognozy po fakcie. Źródło może być wcześniejsze, jeśli jest znane i świeże≤6h; horizon odissue. Osobny immutable ledger nie otwiera starychSQLite. Zachowuje sourcebyteshash, input/prefixhash, wersjęforecastu i rzeczywisty czas zapisu.

Scoring utrwala pierwszą poprawną etykietę wraz z jej receipt i known_at; następne odczyty nie zmieniają wcześniejszego score. Dojrzały brak etykiety jest brakującym targetem, nie zerem. Mierzymy+24/+48/+72h oddzielnie, główny72h; event-balancedMAE, bias/P90/worst, maturity/prefix/source/coverage. Ostrzeżenieinventorydrop≥250miejsc ma uprzednią definicję wJSON; jego skuteczność to osobne precision/recall/falsealarms/leadtime, nie dowód wpływu reklamy/ceny.

Formalny przegląd po30nowych niezależnych meczach/8klubach i bootstrapie po fixtures10000seed42. Wczesne wyniki opisowe. Wszystkie cohorty/failed/unsupported/missing są jawne; nie wybieramy dogodnego błędu ani dnia. Celokoło1200MAE frekwencji pozostaje odrębny od inventory. Production_change=false/live_adjustment=0.
