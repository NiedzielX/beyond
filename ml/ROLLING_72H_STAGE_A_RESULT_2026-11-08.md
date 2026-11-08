# Rolling72: rzeczywiste pokrycie i nowy kontrakt wejść

Data: **2026-11-08**. Status: **audyt historycznego pokrycia wykonany; moduły wejść i etykiet zaimplementowane lokalnie; fit, nowy ledger, feed i wdrożenie pozostają otwarte**.

Wykonanie etapu A i części B [planu produktu](ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md), po [przeglądzie literatury](ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md). Użytkownik jawnie autoryzował równoległe zadania agentów. Dane, kontrakt ML i panel zbadano osobno; integrację, ukończenie kodu i testy wykonał główny agent po osiągnięciu limitu przez agentów.

## 1. Co naprawdę mamy

Audyt wykorzystuje zachowany eksport z **2026-11-07 20:10:54 UTC**, odebrany o20:11:06UTC. Nie pobierano ponownie całej historii ani niczego z Supabase. To aktualny dla tego audytu cache, nie odczyt live z8listopada.

- **38 meczów /16 klubów /29 063 rzeczywiste rekordy snapshotów**.
- **1014 literalnych zer** zachowano jako zapisane wartości; eksport nie niesie historycznych flag active/visible, więc sam nie rozstrzyga znaczenia każdego zera.
- **10 meczów zmienia measurement_key** w historii. Późniejszy prefix z wieloma kluczami nie jest porównywalnym wejściem w tym audycie.
- Najwcześniejsze śledzenie zaczęło się około**P-56,45**, lecz tylko**1 mecz** ma pierwszy odczyt co najmniejP-50, a**2 mecze** co najmniejP-30.
- Brak historycznych czasów ingestii snapshotów, dowodu stałej uwolnionej puli i daty otwarcia sprzedaży. Pierwszy odczyt nie dowodzi startu sprzedaży.
- Ten eksport zawiera `sector_count`, lecz **zero rekordów z identyfikatorami i wartościami poszczególnych sektorów**. To ograniczenie eksportu, nie twierdzenie, że w projekcie nie ma danych sektorowych.

## 2. Pokrycie przyszłych pomiarów

Każda komórka oznacza **niezależne mecze / kluby** z co najmniej jednym dopasowanym pomiarem. Te same mecze mogą występować w wielu wierszach; nie sumujemy ich jako nowych zdarzeń.

| Etap w chwili historycznego wejścia | +24 h | +48 h | +72 h |
|---|---:|---:|---:|
| Co najmniejP-50 | 1/1 | 1/1 | 1/1 |
| P-30 doP-50 | 2/2 | 2/2 | 2/2 |
| P-15 doP-30 | 6/3 | 6/3 | 6/3 |
| P-7 doP-15 | 18/13 | 18/13 | 17/12 |
| P-3 doP-7 | 18/13 | 18/13 | 18/13 |
| Mniej niż3dni przed kickoffem | 24/13 | 21/13 | 0/0 |

Granice przedziałów są jawne w [agregatach](ROLLING_72H_COVERAGE_AUDIT_2026-11-08.json): np.P-15doP-30 oznacza15≤days<30. Ostatni wiersz nie wymaga prognozy po kickoffie; dlatego72h jest niedostępne.

**Od samego pierwszego odczytu:** przyszły pomiar+24h ma**26 meczów/14klubów**, +48h**23/14**, +72h**19/13**. W całym badanym okresie+72h ma4004 zależne pary pomiarów, ale tylko**20 niezależnych meczów/14klubów**. Tysiące par nie zwiększają próby do tysięcy meczów.156par przyP-50dotyczy jednego meczu.

Próbkowanie audytu: pierwszy rzeczywisty punkt oraz ostatni rzeczywisty punkt w każdej godzinieUTC, bez wstawiania brakujących godzin. Cały znany według capture prefix musi mieć jeden klucz pomiaru; target to najnowszy rzeczywisty odczyt na/przed nominalnym terminem, maksymalnie6h wcześniejszy, późniejszy od wejścia i przed kickoffem. To **diagnostyka historycznego pokrycia**, nie walidacja nowego modelu ani dowód wiedzy w dawnym czasie. Nie wystawiono historycznych prognoz.

Tolerancja6h oznacza np. nominalny+72h oceniany odczytem z+66do+72h; czasy rzeczywiste muszą pozostać w raporcie. Klucz provider/source nie dowodzi niezmienionej puli; ten audyt nie certyfikuje wszystkich znalezionych par jako danych gotowych do uczciwej walidacji PIT. Cache zachowuje9rekordów oznaczonych `roboticket_candidate_backfill`; nie stają się nowymi obserwacjami prospective.

## 3. Co zaimplementowano teraz

Nowy, oddzielny moduł [`rolling72_features_v1.py`](demand_engine/rolling72_features_v1.py):

- dopuszcza pojedynczy rzeczywisty punkt oraz dowolny świadomy czas issue przed meczem;
- wymaga odrębnych `captured_at` i `known_at`, również dla dokładnej wersji metadanych meczu;
- odcina późno poznane i przyszłe rekordy przed walidacją wartości i hashowaniem wejścia;
- zachowuje cały dostępny prefix, ostatni realny poziom, zmianę od początku oraz dostępne zmiany/tempo6/24/72h z rzeczywistych kotwic;
- brak okna pozostaje `null`; liczba pomiarów jest metadanymi jakości, poza cechami popytu;
- liczy horyzont od **issue**, nie od starego snapshotu; target o/po kickoffie jest jawnie niedostępny;
- sprawdza hashe, konflikty tożsamości, zmianę pomiaru, hidden/inactive i staleness. Maksymalny wiek6h nie jest wymogiem6h historii.

Nowy [`rolling72_labels_v1.py`](demand_engine/rolling72_labels_v1.py) dopasowuje późniejsze prawdziwe odczyty przy jawnym czasie oceny/treningu. Zachowuje czas pomiaru i poznania; nie używa etykiety poznanej dopiero po cutoffie. Nie interpoluje ani nie omija niepoprawnego najnowszego znanego targetu na rzecz starszej wygodnej wartości. Wykrywa zmianę klucza pomiaru między issue a targetem także wtedy, gdy klucz później wrócił. Osobne stany opisują niedojrzały cel, brak danych i nieporównywalny pomiar. Nie dopisuje score do frozen ledgeru.

Nie ma adaptera wpisującego fikcyjne dawne `known_at` do cache. Deklarowany measurement_key musi opisywać źródło i zakres pomiaru; sam moduł nie potrafi dowieść stałej puli. Nieznane flagi pozostająUNKNOWN. Podane zegary i hashe nie są dowodem niezmienności tabel źródłowych.

Audyt można odtworzyć bez sieci:

```bash
python -m ml.rolling72_coverage_audit_v1 \
  --input /private/path/public-export.json \
  --output /private/path/new-coverage-audit.json
```

Skrypt sprawdza hash manifestu i zachowuje SHA256 oryginalnego pliku. Błędy i nieporównywalne prefixy zostają w mianownikach pokrycia. Wszystkie liczniki pierwszego prywatnego audytu odtworzono niezależnie kodem repozytorium. Raw dane pozostają pozaGit; receipt pliku: `3a5981ce558ce0b2b98b1a4082d61b169fb6b1674f68d94792dd153d97d839bd`.

Weryfikacja lokalna: **218 testów Demand Engine oraz25testów audytu/source-state — 243łącznie, wszystkie PASS**. Obejmuje41nowych testów rolling72:17wejść,12etykiet i12audytu. Zmiana przyszłego payloadu nie zmienia wejścia ani wcześniejszej etykiety; osobne testy rozstrzygają późny known_at, pierwszy punkt/P-50, hidden/zero, zmianę tożsamości, rzeczywiste kotwice oraz granicę kickoffu. YAML testowego workflow parsuje się poprawnie; `git diff --check` przechodzi. To lokalna weryfikacja kodu, nie wynik hosted ani dowód panel/DB.

## 4. Rzeczywista luka w panelu

Obecny research parser daily-path wymaga4punktów/24h historii, dokładnego dziennego issue i wszystkich pozostałych dni. Nie przyjmie nowego kontraktu rolling72. Kafelki pokazują+1/+3/+7dni. Stara zielona linia nadal czyta historię `forecast_observations.final_p50`.

Ostatni udokumentowany commit produkcyjny panelu `cfb3d675…`, sprawdzony lokalnie, nie zawiera nowego daily-path. Bieżącego deploymentu nie odczytywano przez sieć. Istniejący gateway jest POST/service-role/GitHubOIDC; zapisJSON do artefaktuActions nie dostarcza feedu przeglądarce. Samo wdrożenie staregoSQL/Edge nie domknie tego połączenia.

W projekcie istnieją sektory/E0. Właściciela ustala łańcuch `sector_inventory.snapshot_id → snapshots.id → snapshots.ticket_event_id`; nie pole `sector_inventory.event_id`. ProjekcjaE0na kickoff nie jest niezmienną prognozą rolling72. Historyczne per-sector coverage wymaga osobnego, ograniczonego odczytu; nie ma go w powyższych38meczach eksportu.

## 5. Co dalej i czego ten etap nie rozstrzyga

1. **DokończyćB:** podłączyć rzeczywiste źródło do jawnych receipt/metadata clocks i wersjonowanego zapisu cech. Dotychczasowy source-state-v2jest przygotowany i sprawdzony izolowanie, lecz nie wdrożony; zachować jego ograniczenia. Dawne nieznane zegary pozostają nieznane. Na tej podstawie zamknąć reguły kwalifikacji treningu i benchmarków persistence/pickup/nowego odpowiednika driftu na wspólnych issue; starego drift ledgeru nie rozszerzać.
2. **Przed fitC:** utrwalić jeden dokładny kandydat, cechy, parametry, cutoff, grouping i wszystkie baseline. Odsłonięte mecze pozostają development/diagnostic, bez nowego „czystego” holdoutu przez zmianę nazwy. Macierz pokrycia pokazuje, żeP-50wymaga dalszej rzeczywistej obserwacji; nie blokuje samej obsługi pierwszego punktu przez kontrakt.
3. **D/E:** nowy immutable ledger i wersja feedu, bezpieczny odczyt dla panelu oraz nowe rzeczywiste issue→przyszłe odczyty→score. Przy30nowych meczach/8klubach przegląd według planu; wcześniej tylko opisowe wyniki.

**Brak nowego MAE i poprawy potwierdzonej na przyszłych meczach.** Cel około1200miejsc MAE frekwencji trwa; inventory/24/48/72h raportujemy osobno. Nie zmieniono frozen modeli, starych prognoz/bramek, nie odnowiono workerów i nie wykonano DBwrite/deploy. `production_change=false`, `live_adjustment=0`.
