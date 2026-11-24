# Rolling72: plan rozwoju MAE i MVP inwestorskiego

Date: 2026-11-22
Status: ACTIVE — specyfikacja developmentu; konkretne eksperymenty wymagają własnych precommitów

Aktualizacja wykonania23XI: P0-1 hosted, P0-3 kompletny z rzeczywistymi
raportami. P0-2/P0-5: nowy protected grant/Edge i panel/relay zaimplementowane;
PR10 HEAD265af87086bd4bdde85f62575aa0eb8b64309f9d, oba CI SUCCESS. **D0 BLOCKED**
przez ogólną awarię PostgREST/schema cache i cron startup timeouts; faktyczny
HTTP/browser odczyt zakończył się błędem. Nie deklarować nowego automatycznego
receipt ani poprawy MAE. P0-4a offline gotowy; P0-4b osobny runtime ma nową
specyfikację w review, bez implementacji/aktywacji. Cały plan pozostaje ACTIVE.
[Chroniony pilot i dowody](../../ml/ROLLING_72H_PROTECTED_PILOT_RESULT_2026-11-23.md).
Owner: integrator (root); osobni writerzy na ticket i pliki
Related: [MAE roadmap v6](../../ml/MAE_RESEARCH_ROADMAP_V6.md), [plan produktu Rolling72](../../ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md), [program MAE](../../ml/ROLLING_72H_MAE_REDUCTION_PLAN_V1_2026-11-17.md), [plan szybkiej ścieżki MVP](../../ml/ROLLING_72H_MVP_FAST_PATH_2026-11-17.md), [E5 wynik](../../ml/ROLLING_72H_COMMON_FLOW_E5_RESULT_2026-11-22.md), [B wyniki](../../ml/ROLLING_72H_PROSPECTIVE_BASELINES_RESULT_2026-11-22.md)

## Problem i udokumentowane wymagania

**Wymagania użytkownika:** prognozować +24/+48/+72 godziny od każdej prawdziwej obserwacji przez cały cykl sprzedaży, także z pierwszego punktu; wykorzystywać wtedy znaną historię; wspierać decyzje o cenie/promocji/reklamie pod jawnym założeniem warunków; minimalizować event-balanced MAE, nadal dążąc do ok. 1200 miejsc MAE końcowej frekwencji. `live_adjustment = 0`.

**Wymagania zapisane w repo:** `ml/AI_LITERATURE_REVIEW_AND_MVP_PLAN_2026-11-03.md` §5 opisuje „Minimalny ekran inwestorski”: osobno ścieżka dostępności i końcowa frekwencja, zachowanie wydań, wynik po meczu, scorecard per horyzont, pokrycie/fallbacki/bias/ogon oraz rozróżnienie badań historycznych, prospektywnego zbierania i gotowości do review. `ml/ROLLING_72H_MVP_FAST_PATH_2026-11-17.md` doprecyzowuje pilota 1–2 meczów i akceptację aktualnego receipt→issue→screen→genuine target→score. Wyszukiwanie `investor`, `pitch`, `deck` i `requirement` nie ujawniło w repo dodatkowego briefu konkretnego inwestora. Nie przypisujemy mu więc niezapisanych wymagań.

**Stan dowodów:** B (`public_available_total_with_scope_events_v1`, nie potwierdzona sprzedaż) ma 308.50/427.82/295.78 persistence oraz 302.79/411.87/241.76 drift24 dla +24/+48/+72; odpowiednio 5/5/3 meczów i 717/401/43 etykiet. To wczesny opis znanej kohorty, nie 30 nowych niezależnych meczów/8 klubów. E5 uruchomiono 22XI: 4 pakiety, 12 celów, 48 wartości metod, 2 przyszłe mecze (Śląsk, Wisła), 0 błędów, 0 etykiet; E5 MAE pozostaje nieznane. E5 rejestr ma pięć ustalonych ID, trzy z nich już minęły. Jego SQL, testy, precommit i audit są zamrożone. Nie wystawiano dawnych wydań wstecz.

**Rzeczywisty brak produktu:** E5 ma `public.get_rolling72_common_flow_e5_v1_status()` tylko dla `service_role`, z agregatami, bez bezpiecznego payloadu UI per wydanie. `ml/rolling72_feed_v1.py`/`v2.py` eksportują lokalne SQLite, nie live E5. Ostatni dowód panelu (`ml/ROLLING_72H_ML_PANEL_PROOF_2026-11-09.json`) dotyczy statycznego snapshotu v2, nie ciągłego feedu. Repo panelu `NiedzielX/BeyondTicketingPanel` nie ma checkoutu w `/workspace`; jego aktualnego HEAD ani UI nie zweryfikowano. Wymaga to sprawdzenia przed zmianami UI. Nie oznacza to, że dziś nie istnieje nowszy kod poza dostępnym workspace.

## Cel, zakres i granice

Dostarczyć funkcjonalny, uczciwy pilot na 1–2 przyszłych meczach oraz równolegle rozszerzalny, forward-only strumień dla nowych poprawnie przyjętych meczów. Pilot może pokazać persistence, drift i shadow E5 nawet jeśli E5 nie wygra. Po drodze nie zmieniać E5/B/v5 ani żadnego zamrożonego kontraktu.

Trzy osobne bramki:

1. **Techniczne MVP:** live immutable issue i autentyczny ekran z pending/score/fallback; test użyteczności na 1–2 meczach.
2. **Dowód MAE:** sparowane, event-balanced wyniki po horyzontach; minimum 30 nowych niezależnych meczów / 8 klubów i PIT-safe, czasowy podział zgodny z właściwym precommitem. Pilot nie spełnia tej bramki.
3. **Efekt przychodowy interwencji:** osobne dane o cenie, promocji, reklamie, ekspozycji i przychodzie oraz identyfikowalny eksperyment/wiarygodna metoda przyczynowa. Prognoza „przy obecnych warunkach” tego nie dowodzi.

Poza zakresem: produkcyjne `live_adjustment`, automatyczna zmiana cen/reklam, wysyłka/invitations do klubu/inwestora, obietnica 1200 MAE, retuning lub ponowne uruchamianie E1–E4/B/v5 na ujawnionych wynikach, historyczny PIT rekonstruowany z `created_at`, fikcyjne etykiety/interwencje/przedziały.

## Kontrakty i niezmienniki

- Horyzonty są dokładnie 24/48/72h od niezmiennego `issued_at`; issue powstaje po każdej nowej kwalifikującej się prawdziwej obserwacji, również pierwszej. Target po kickoffie ma status `OUTSIDE_KICKOFF`; spóźnione rozpoczęcie śledzenia jest jawną luką.
- `available_total` to publiczny proxy dostępności, nie sprzedane bilety, popyt, przychód ani frekwencja. Zaobserwowane `0` różni się od braku/ukrytej puli. Zmiana puli/zakresu to flagowany stan, nie potwierdzona sprzedaż.
- Zachować osobne serie/scorecardy dla availability path i attendance forecast. Wykorzystać istniejący frozen attendance incumbent z jego prawdziwym `model_id`, `issued_at` i źródłem; jeśli go nie ma lub brak sparowanego challengera, pokazać `UNAVAILABLE`/`NO_PAIRED_CHALLENGER`, nie pożyczać E5 jako challengera frekwencji.
- Scenariusz `price`, `promotion`, `advertising`, `pool_policy` ma jawny status `KNOWN`, `CHANGED`, `UNKNOWN`; dziś brak potwierdzonej historii ceny/promocji w E5, więc domyślnie `UNKNOWN`. Brak danych nie jest dowodem braku interwencji. Wydania historyczne są append-only.
- Pełna polityka, w tym fallback do persistence, to główny produktowy wynik. `learned-only` może być diagnostyką obok. Dla każdego modelu i horyzontu: tylko wspólne issue/targety; event jest jednostką niezależną; bootstrap po meczach, nigdy snapshoty. Podaj n meczów/klubów, pokrycie, fallbacki, bias, P90 i worst-event MAE. Nie wybieraj modelu osobno per horyzont po wyniku.
- Nie łączyć B i E5 w jeden ranking: różnią się kontraktem/kohortą. B: drift24 miał niższe zbiorcze MAE we wszystkich trzech raportowanych horyzontach, nie w każdym pojedynczym punkcie; +72 ma tylko 3 mecze. E5: przed nowymi etykietami nie ma żadnego wyniku jakości. `live_adjustment = 0`.

## Board wykonawczy

Kolejność odblokowuje techniczny pilot niezależnie od nowych etykiet; wyniki MAE czekają na dojrzałe cele; budowę skalowania i analizy błędów można rozpocząć od razu. Przypisanie writerów należy do integratora, pliki są rozłączne.

| ID / priorytet | Ticket i właściciel plików | Wejście → wyjście / zależności | Kryteria odbioru i weryfikacja |
|---|---|---|---|
| **P0-1 — zacząć teraz** | **Serwerowy read-only feed i error budget.** Nowy `supabase/sql/rolling72_investor_feed_v1.sql`; test `tests/postgres/test_rolling72_investor_feed_v1.py`; read-only agregator `ml/rolling72_investor_feed_v1.py` (jeśli aggregator wymaga klienta, parsuje tylko jawny JSON RPC). | Źródła: prywatne immutable tabele E5 `rolling72_common_flow_e5_*`, B `rolling72_forward_baselines_b_*`, v5 `rolling72_lad_*`, baseline v3a `rolling72_managed_*`, autentyczne snapshots/receipts. RPC status E5 sam nie wystarczy. Wynik nowego `public.get_rolling72_investor_feed_v1(...) (parametry poniżej)` wyłącznie dla `service_role`; prywatne tabele pozostają bez direct grants. | Zwraca payload określony niżej; per-event issues, obserwacje i etykiety są w kolejności czasu i oparte o ID w ledgerze. Brak wiersza ≠ 0. Każda metoda zawiera `value` lub `null`, `status`, `fallback_reason`; label ma rzeczywisty receipt/snapshot, `captured_at`, `known_at`, `age_seconds`, `absolute_error|null`. Scorecard tylko w granicach `lane_id + target + horizon`, z denominatorem i coverage; `E5 labels=0` daje `PENDING`, MAE `null`. Przedziały nie są emitowane. Test PG16: auth deny anon/authenticated, success `service_role`, empty/stale/missing/zero/scope-change, append issue nie zmienia starych ID/hash/value, wspólne etykiety, poprawny `MAE=avg(event_mae)`, P90/worst po eventach, due+label, outside-kickoff i fallbacki. Test nie dotyka live DB.
| **P0-2** | **Panel — zasilenie jednego meczu**. Po checkout/current-head audit w osobnym repo `NiedzielX/BeyondTicketingPanel`; komponent obecnego preview route `/rolling72-ml-preview` (nie wymyślać nowej aplikacji). | Serwerowy adapter panelu wywołuje P0-1. Klient nie dostaje service-role. Pierwszy pilot: obecne dwa przyszłe mecze E5, tylko z rzeczywistymi wydaniami i obserwacjami. | Jedna strona: wybrany mecz/ID, czas ostatniej obserwacji, rzeczywisty proxy-prefix, linia as-of, przyszłe wartości i zmiany z istniejących issues; oś X to rzeczywiste timestampy/upływ czasu, nie indeksy punktów; prefix wybranej wersji zawiera tylko wtedy znane dane, późniejsze obserwacje są osobną warstwą wyników; osobne serie i metki model/version/status/fallback/source age. Osobno końcowa frekwencja incumbent i jego rewizje, z rzeczywistym źródłem/model ID; brak danych to widoczne `UNAVAILABLE`. Responsywne loading/empty/error/stale/pending/stale-label; poprzedni vintage nie zmienia się po nowym receipcie. Browser test porównuje UI do exact payload z live read-only feed i przechodzi fresh→new issue→pending→mature label. Dopóki panel repo/HEAD/API auth nie są dostępne, ticket UI jest `BLOCKED_ON_CHECKOUT`, a nie deklarowany jako zrobiony.
| **P0-3** | **Scorecard i rozkład wkładu błędu.** Skrypt `ml/rolling72_investor_scorecard_v1.py`; testy fixture `ml/test_rolling72_investor_scorecard_v1.py`; używa P0-1 payload. | Per-issue paired predictions/targets plus lane/model metadata → `scorecard.json` + krótki raport. Można kodować na obecnych B/E5 fixture JSON bez czekania na kolejne targety. | Osobno availability/attendance, lane i horyzont: MAE persistence/drift6/drift24/common-flow6 i istniejący attendance incumbent; Δ wobec właściwej paired baseline; liczba issue/label i event/club; coverage, fallback, bias, P90, worst event; top 5 eventów z wkładem do `ΔMAE` i opisem statusów first-point/scope/fallback. Nie sumować pokrywających się segmentacji. Zmienne kohorty: jawna metryka pairing. Zera etykiet→`null/PENDING`. Uruchomić na zapisanym wyniku B + fixture E5 z 0 label; przy przyszłych labelach ten sam skrypt aktualizuje raport bez fitu.
| **P0-4** | **Oddzielna, rozszerzalna lane dla przyszłych fixture.** Nowe, niezależne `supabase/sql/rolling72_mvp_research_v1.sql`, test `tests/postgres/test_rolling72_mvp_research_v1.py`, lokalny kontrakt `ml/rolling72_mvp_research_v1.py`. | Wejście tylko z już poprawnie przyjętych przyszłych eventów; wykorzystać istniejący forward-only admission (`supabase/sql/roboticket_forward_only_admission_v2.sql`, `ml/roboticket_admission_plan_v1.ts`) jako dowód tożsamości, bez zmieniania jego bramek. Własny wersjonowany adapter nowych `public.snapshots`/wierszy sektorów zapisuje nowe prywatne registry/receipts/seals/bundles/predictions/labels. Kod v3a/seals stanowi wzorzec semantyki do przeglądu, a nie dynamiczne wejście nowych ID: jego zamrożone rejestry tego nie obsługują. Osobny lane ID/RPC/cron z jawną datą końca działania i kolejką nowo przyjętych fixture; bez podmiany starych funkcji/triggerów. Nie dodawać fixture ani bootstrap do zamrożonego E5/B. | Własny precommit przed aktywacją: target całkowitej publicznej dostępności z jawnie flagowanym zakresem; pierwsze prawdziwe receipt daje persistence +24/+48/+72 (bez slope/fake history); każde kolejne nowe receipt daje nowy vintage; idempotent retry po `receipt_id`; score wyłącznie na prawdziwym późniejszym odczycie po issue, `<= target`, max 6h i przed kickoff; pending/outside/missing/zero/gaps rozróżnione. Dodaj obecnie przyjęte przyszłe mecze forward-only, bez missed backfill. Pilot 1–2 świeże mecze możliwy bez nowych etykiet. Test PG16 pokrywa pierwszy punkt, nowy receipt, retry, zakres sektora, target matcher, due scorer, permissions, expiry i stary-ledger isolation. Nie promuje modelu.
| **P0-5** | **Automatyczne odświeżenie UI.** W panel repo checkout: użyć istniejącego query/cache mechanizmu; jeśli brak, minimalny polling tylko dla pilotowej strony. | P0-1/P0-2; rzeczywisty receipt cycle, nie deklaratywny cron. | Nowy rzeczywisty receipt daje nowy timestamp/version; brak receiptu nie przesuwa `as_of` ani nie fabrykuje issue. Wyświetlić freshness. Test browser/API idempotent repeat oraz stale/errors. Częstotliwość zgodna ze źródłem; nie odpytywać upstream przez UI.
| **P1-1** | **Ocena przyszłych wyników B/E5 i zamknięcie evidence gate.** Tylko score/report; bez zmian frozen lane. | Właściwe dojrzałe issue/target/receipt. E5 pierwszy +24 score attempt: 23XI ok.17:18 Warszawa; +48/+72 ok.24/25XI, status sprawdzić na realnym zegarze. | Pełna polityka E5 common-flow6 vs persistence/drift6/drift24 na dokładnie wspólnych issue/label; osobno24/48/72h, per event, fallback/full support, `<=1h` sensitivity, coverage, bias, tail. Nie używać B jako E5 control. Nie dobierać zwycięzcy per horyzont; E5 pozostaje bez refit. B bieżące wyniki opisowe. E5 proof JSON/status i run logs aktualizują evidence; brak celu pozostaje pending.
| **P1-2** | **Nowy independent cohort.** Właściciel admissions + data owner; lane P0-4 wyłącznie. | Następne przyszłe mecze/kluby z wiarygodnym schedule↔ticket ID i źródłowym availability. | Monitoruj osiągnięcie 30 nowych niezależnych meczów/8 klubów bez dopisywania starych pięciu/E5 ani liczenia snapshotów jako fixture. Raportuj first-point support, źródło, coverage i target maturity; nie zmieniaj progów przy małej próbce.
| **P1-3 — warunkowy** | **Jedna nowa hipoteza informacji po error budget.** Osobny precommit przed fitem i wystawieniem. | Error budget z P0-3 na obecnych B/danych rozwojowych + audyt rzeczywistego nowego sygnału. Prace badawcze i przygotowanie precommitu ruszają teraz; P1-1 dodaje potem wyniki E5, a P1-2 dostarcza przyszły test i nie blokuje developmentu do osiągnięcia30/8. Wybierz jedną hipotezę o nowej PIT-safe informacji, która odpowiada na największy pełnopolicyjny wkład MAE (np. potwierdzone, timestampowane informacje o zmianach warunków/puli niedostępne wcześniejszym modelom; samo ponowne nazwanie cech E1/E5 nie jest nową informacją), z persistence + fixed drift24 jako punktem odniesienia. | Dokładny target, input known-at, fold po czasie/event, brak/pierwszy punkt, budżet wariantów, paired cohorts i decyzję zamknąć przed fit. Nie powtarzać E1–E4; ich wykonane wyniki są podstawą, nie nową pracą. Jeśli nowej informacji/supportu brak, `NO_FIT` i naprawa źródła/admission jako odrębna praca. Minimum formalnej oceny nadal30 nowych/8 klubów. Żaden wynik nie aktywuje produkcji.
| **P1-4 — warunkowy** | **Osobna praca nad końcową frekwencją.** Owner attendance incumbent/MAE research. | P0-2 ujawni, jaki frozen attendance forecast i genuine attendance actuals rzeczywiście są dostępne. Użyć zgodnego z obecnym roadmap/precommit źródła; rolling availability nie jest feature/labelem bez PIT dowodu. | Zbudować osobny event-balanced attendance scorecard i error budget wobec zamrożonego structural/attendance incumbent; persistence dla availability nie jest jego baseline; następny kandydat tylko na udowodnionej nowej PIT informacji i niezależnej grupie meczów. Dążyć do ok.1200-seat MAE bez obietnicy. Nie przedstawiać E5 MAE jako frekwencji MAE.
| **P1-5 — po osobnych danych** | **Causal test ceny/promocji/reklamy**; owner komercyjny/dane, poza prognozowaniem. | Interwencje z czasem, ceną, promocją, wydatkiem/ekspozycją, pulem, ekspozycją użytkowników i przychodem/marżą; wiarygodna grupa kontrolna albo plan identyfikacji. | Uprzednio opisany test przyrostowego revenue/profit, interferencji sektor↔mecz↔czas i kosztu kampanii. Do tego czasu tylko `UNKNOWN`/scenariusz „przy utrzymaniu obecnych warunków”; nie rekomendować optymalnej ceny ani ad-spend z korelacji.

## P0-1: dokładny payload i API kontrakt (pierwsza praca do kodowania)

Nowa funkcja SQL ma być `STABLE`, wyłącznie read-only, działać przez `SECURITY DEFINER` z pustym `search_path`, odwoływać się do pełnych kwalifikowanych nazw i zwracać wyłącznie dane z listy allowlist. `REVOKE` od `PUBLIC/anon/authenticated`; `GRANT EXECUTE` wyłącznie `service_role`. Bez grantu do tabel prywatnych. Panel pobiera przez swój backend/server-only adapter; service key nigdy nie trafia do browsera. Service-only RPC można przygotować niezależnie; dostęp użytkownika do endpointu panelu wymaga zweryfikowanego istniejącego modelu autoryzacji.

Pierwszy mały zakres implementacji to **E5 + B**. v5/v3a i frekwencja mają osobne adaptery później; nie blokują pierwszego rzeczywistego ekranu E5. Nie interpretować istniejącego agregatu JSON B jako per-event eksportu: P0-3 potrzebuje prawdziwych allowlisted wierszy prognoz/etykiet z tego feedu.

Parametry RPC: `p_ticket_event_id bigint`, `p_lane_id text`, `p_before_bundle_id bigint default null`, `p_limit integer default 50` (1–200). W pierwszej wersji jeden mecz i jedna lane na wywołanie; nieobecne lub niewłaściwe ID daje jawny wynik pusty/błąd kontraktu. Paginacja po niezmiennym ID z `next_cursor` i `has_more`; observations również stronicowane, bez obcinania prefixu w sposób niewidoczny. Odpowiedź zawiera zakres czasu/ID i watermark odczytu. Scorecard wyraźnie wskazuje pełną kohortę lane i jej watermark, nie zależy od bieżącej strony issues. Endpoint panelu waliduje parametry i ogranicza zakres dostępu.

Wymagany JSON (klucze stabilne; wszystkie czasy ISO-8601 UTC; wartości bez źródła są `null`, nie 0):

```json
{
  "schema_version": "rolling72-investor-feed-v1",
  "generated_at": "...",
  "status": "OK | EMPTY | PARTIAL",
  "fixtures": [{
    "ticket_event_id": 0, "club_slug": "...", "home": "...", "away": "...",
    "kickoff_at": "...",
    "latest_observation": {
      "receipt_id": 0, "snapshot_id": 0, "captured_at": "...",
      "known_at": "...", "available_total": 0,
      "scope_status": "STABLE | CHANGED | UNKNOWN",
      "source_status": "VALID | MISSING | STALE | INVALID"
    },
    "observations": [{"receipt_id": 0, "snapshot_id": 0, "captured_at": "...", "known_at": "...", "available_total": 0, "status": "VALID"}],
    "observations_page": {"next_cursor": null, "has_more": false},
    "availability_lanes": [{
      "lane_id": "...", "model_version": "...", "target_contract": "...",
      "issues": [{
        "bundle_id": 0, "issue_receipt_id": 0, "issued_at": "...",
        "input_read_completed_at": "...", "source_age_seconds": 0,
        "origin_observation": {"receipt_id": 0, "captured_at": "...", "known_at": "...", "available_total": 0},
        "scenario": {"price": "UNKNOWN", "promotion": "UNKNOWN", "advertising": "UNKNOWN", "pool_policy": "UNKNOWN"},
        "targets": [{
          "prediction_id": 0, "horizon_hours": 24, "target_at": "...", "status": "FUTURE | DUE_UNSCORED | SCORED | UNAVAILABLE | OUTSIDE_KICKOFF",
          "methods": [{"method": "persistence", "value": 0, "predicted_delta_from_origin": 0, "status": "...", "fallback_reason": null}],
          "label": {"receipt_id": 0, "scored_at": "...", "snapshot_id": 0, "captured_at": "...", "known_at": "...", "age_seconds": 0, "actual_available_total": 0, "method_absolute_errors": {"persistence": 0}}
        }]
      }]
    }],
    "attendance_lane": {"status": "AVAILABLE | UNAVAILABLE | NO_PAIRED_CHALLENGER", "source": "...", "issues": []}
  }],
  "issues_page": {"next_cursor": null, "has_more": false},
  "scorecard_scope": {"lane_id": "...", "scope": "FULL_LANE_COHORT", "read_watermark": "..."},
  "scorecards": [{
    "lane_id": "...", "target": "public_available_total | terminal_attendance",
    "horizon_hours": 24, "method": "...", "status": "SCORED | PENDING | INSUFFICIENT",
    "issues": 0, "labels": 0, "fixtures": 0, "clubs": 0,
    "forecast_coverage": null, "scoring_coverage": null, "valid_pre_kickoff_opportunities": 0, "numeric_forecasts": 0, "matured_eligible_targets": 0, "accepted_labels": 0, "eligible_targets": 0, "future_targets": 0, "due_unscored_targets": 0, "unavailable_targets": 0, "outside_kickoff_targets": 0, "fallback_issues": 0,
    "event_balanced_mae": null, "delta_mae_vs_paired_baseline": null,
    "event_balanced_bias": null, "p90_event_mae": null, "worst_event_mae": null
  }]
}
```

Test contract: `event_balanced_mae = AVG(per_event AVG(abs_error))`; bias same two-stage weighting with signed error. P90/worst are quantiles/max of per-event MAE. Rozdzielić dwie miary: `forecast_coverage = numeric_forecasts / valid_pre_kickoff_opportunities` i `scoring_coverage = accepted_labels / matured_eligible_targets`. Pierwszy mianownik obejmuje wszystkie poprawne źródłowo okazje receipt×h przed kickoffem, również odmowę modelu/fallback, drugi wszystkie dojrzałe numeryczne cele do oceny. Osobno raportować brakujące/stare/niepoprawne źródła, niewydane okazje, UNAVAILABLE i OUTSIDE_KICKOFF oraz future/due-unscored/stale-label/missing-label. Zerowy mianownik daje null. Pełne liczniki ledgeru pozwalają rozliczyć wykluczenia; nie usuwać odmów prognozy lub braków etykiet dla podniesienia coverage. Pair comparison must use identical target ID set; otherwise delta `null`, status `UNPAIRED`. The status RPCs are different lanes; payload never merges their summary metrics. Do not leak private raw source bodies, credentials, intervention raw data, or unrelated attendees.

## Kolejność, krytyczna ścieżka, definicja ukończenia

**Krytyczna ścieżka pilota:** P0-1 feed contract + isolated PG implementation → verify panel checkout/current HEAD and exact authorized backend call → P0-2 single-match screen → compare displayed issue/receipt/label IDs against server payload → P0-5 automatic new-receipt update → run P0-3 scorecard from same feed. P0-4 may run alongside as separate lane/precommit; it is required to broaden ongoing collection, not to block the first two-match technical pilot. No step waits for E5 or 30/8 new labels to prepare.

**Technical MVP done when:** authentic new receipt creates a new immutable issue and correct horizons; panel shows the exact issue ID/values/status/as-of, baseline and scenario UNKNOWN; old issue does not change; pending then mature true label produces score; final attendance series/card stays separate and either uses verified frozen source or clearly reports unavailable; per-horizon scorecard exposes correct cohort/coverage/fallbacks; browser/client cannot read private tables or carry service-role key; actual UI agrees with server payload. A 1–2 match pilot proves only integration/readability. It does not close MAE or revenue gates.

**Kryterium przewagi:** główny horyzont72h i guardrails24/48 są zapisane przed eksperymentem. Raportować sparowane różnice MAE względem persistence i zadeklarowanego driftu, z95% przedziałem bootstrapu po meczach (10000 losowań, seed42). Minimum30/8 to warunek przeglądu, nie automatyczny PASS. Cel badawczy programu17XI to10% redukcji wobec persistence w każdym horyzoncie; nie jest gwarancją ani zmianą starych gates. Punktowa poprawa48/72 bez pogorszenia24 nie wystarcza sama do dowodu ogólnej przewagi; brak przewagi zamyka hipotezę jako niewspieraną.

**MAE review ready when:** correct precommit, 30 new independent fixtures/8 clubs, future-only truth, strict known-at, exact paired target IDs, event-grouped/time-ordered evaluation, full policy/fallback denominator, h-specific attendance and inventory metrics, uncertainty interval by event, error budget, no leakage. If any condition fails, mark `PARTIAL/UNKNOWN/NO_PIT_VALIDATION`; do not change status into a pass by lowering a gate.

Każdy nowy kontrakt targetu/modelu/kwalifikacji/cech/ekspozycji/fallbacku wymaga własnej wersji i precommitu przed pierwszym wydaniem. Nowy SQL sprawdzamy na izolowanym PG16; parser/API i panel — na właściwych testach kontraktowych i stanach fresh/error/stale/pending/scored. Integrator odpowiada za połączenie zmian, publikację i status. Specyfikacja nie dodaje rytuału potwierdzania każdego kroku; obowiązują obecne uprawnienia, autoryzacja i zamrożone kontrakty.

## Uzasadnienie literaturą i wynikami

Poziomy dostępu poniżej pochodzą z rejestru przeglądu17XI; nie oznaczają nowego odczytu pełnych publikacji w tej sesji. Dokładne DOI/linki i ograniczenia są w bibliografii programu MAE oraz `ml/ROLLING_72H_MAE_REDUCTION_PLAN_SOURCES_2026-11-17.json`.

- `ROLLING_72H_MAE_REDUCTION_PLAN_V1_2026-11-17.md` §4–6: start od P0 error-budgetu, paired persistence/drift/pickup, pełnopolicyjny fallback, event/time splits; E1–E4 already executed, nie powtarzać. Nowa hipoteza dopiero po poznaniu wkładu największych błędów.
- B1 Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (przeczytane rozdziały o prostych metodach, accuracy, rolling origin, combinations): silne benchmarki, MAE i rolling-origin; średnia/stały blend nie jest gwarancją. B2 Gneiting 2011 (pełny preprint; MAE → mediana) i B3 Hyndman & Koehler 2006 (tekst odczytany; nie wybierać procentowych miar przy zerach) uzasadniają metrykę i medianę.
- B5 Weatherford & Kimes 2003 i B6 Haensel & Koole 2011: tylko metadane/abstrakty, tekst pełny niedostępny; inspirują test prostych pickup/dynamic updating, nie transfer wyniku hotelowego. B7 Montero-Manso & Hyndman 2021: przeczytany publiczny preprint; uzasadnia test globalnego współdzielenia informacji, nie przewagę ani independent fixture claim. B4/B8/B9 to metadane bez pełnego tekstu. Żadna pozycja nie gwarantuje 1200 ani 10% gain.
- Obecny B wskazuje drift24 jako solidniejszy comparator niż persistence na znanej, małej kohorcie. E5 testuje nowy wspólnosektorowy ruch, ale nie ma labeli; jego wynik trzeba odczytać na własnych paired futures. Nie wolno wnioskować z 48 method values ani z B o E5 generalization.

## Etapy odbioru funkcjonalnego

**D0 — działający podgląd:** prawdziwy live feed, ekran, nowa automatyczna wersja i zachowane stare wydanie; przyszłe wyniki jawnie PENDING. To użyteczny pilot, jeszcze nie pełny dowód całego MVP.

**D1 — pełny łańcuch MVP:** poza D0 rzeczywiste dojrzałe etykiety i odtwarzalne błędy dla każdego24/48/72h, pokazane w panelu z pierwotnymi prognozami. Dane syntetyczne mogą sprawdzić stany UI, lecz nie zamykają tego odbioru. D1 nie dowodzi jeszcze przewagi MAE ani1200MAE frekwencji.

## Wynik / otwarte ryzyka

Specyfikacja gotowa do podziału ticketów. UI repo/HEAD/auth model niezweryfikowane z powodu braku checkoutu; pierwszy task backendowy może ruszyć bez niego. Potencjalne braki: brak potwierdzonego incumbent attendance feed w nowym panelu; nieznany stan dokumentacji konkretnego inwestora; skąpe coverage +72; price/promo/advertising history unknown; pilotowe fixture nie są niezależną walidacją.

## Najbliższy pakiet do wykonania i podział pracy

### Ustalenia implementacji22XI (nie zmieniają frozen prognoz)

- P0-1 ma sygnaturę `(p_ticket_event_id bigint, p_lane_id text, p_before_bundle_id bigint default null, p_limit integer default50, p_before_receipt_id bigint default null)`. Osobna paginacja obserwacji i wydań. `generated_at/read_watermark` to czas instrukcji SQL; spójny eksport wielu stron wymaga jednego snapshotu transakcyjnego, sam timestamp nie dowodzi widoczności commitów.
- Historyczna ważność źródła/receipt pozostaje oddzielna od `freshness_now`. Równa liczba sektorów daje `UNKNOWN`, nie dowód stabilności tożsamości puli. Etykieta przekazuje rzeczywistą zmianę liczby sektorów, bez przypisywania jej sprzedaży.
- Pierwszy feed ma pokrycie `ISSUED_TARGETS_ONLY`; nie potrafi dowieść pełnego rozliczenia wszystkich niewydanych okazji źródłowych. To jawny brak do rozliczenia w nowej ścieżce źródeł P0-4, a nie100% całego produktu.
- P0-3 raportuje pełną kohortę tylko po sprawdzeniu manifestu, ciągłości stron i wspólnego watermarku; urwane strony zostają `PARTIAL`. Dane B/E5 są zawsze oddzielone.
- P0-4a jest czysto lokalnym kontraktem przygotowania źródła/registry: sprawdza przekazane admission/runtime/read/hash i tożsamości, nie wykonuje admission, źródłowego odczytu ani forecastu i nie dowodzi autentyczności/commit visibility.
- Panel sprawdzono przez GitHub i pobrano do osobnego checkoutu: main `cfb3d675...` z5XI, roboczy rolling72 preview `bd01c8b...` z9XI. Istnieje parser/feed v2 i statyczny snapshot; nowy E5/B wymaga osobnego adaptera. Dotychczasowy klient Vite używa publishable key; service-role nie wolno dodać do jego konfiguracji.

1. **Backend A:** P0-1 w wąskim zakresie E5+B, stronicowany feed bez nowych prognoz/fitu; wynik: SQL/RPC, kontrakt i izolowany PG16 dowód. Po uruchomieniu porównać prawdziwe ID/czasy/wartości z ledgerem. To pierwsze zadanie developmentu.
2. **MAE B równolegle:** P0-3, najpierw parser i deterministyczny error-budget na fixture JSON, potem autentyczny eksport B. Wynik: tabela24/48/72 i top5 źródeł błędu, a nie licznik prognoz. Dla eventu e i h wkład błędu to suma AE punktów podzielona przez `liczba_eventów × liczba_punktów_eventu`; rozłączne wkłady muszą sumować się do MAE. Analogicznie wkład do ΔMAE liczy sparowane różnice AE z tymi samymi wagami.
3. **Źródła C równolegle:** P0-4 podzielić na rejestr/admission → własne receipts/seals → persistence issuance/scorer. Odebrać pierwszy nowy mecz spoza frozen5, w tym pierwszy punkt, i rzeczywisty automatyczny następny receipt. Nie oznaczać go jako niezależnego, jeśli był już odsłonięty/trenowany.
4. **Integrator/UI:** sprawdzić obecny HEAD panelu, potem P0-2+P0-5. Po integracji odbiór jednego kompletnego łańcucha na prawdziwych danych. Dojrzałe wyniki24/48/72 dopisują się później; ich termin zależy od rzeczywistych wydań.
5. **Następna hipoteza MAE:** po raporcie B wybrać jeden dominujący mechanizm, opisać jakie nowe dane go mierzą, policzyć support i dopiero zamrozić osobny eksperyment. Audyt timestampowanych cen/puli można wykonać teraz; znane2 zmiany cen nie uzasadniają uczenia elastyczności. Jeśli supportu brak, wynik to konkretna lista brakujących źródeł/etykiet i praca nad ich pozyskaniem, równolegle do pilota.

**Mały dodatek do użyteczności:** po ekranie przygotować ręczny dziennik decyzji/scenariusza (osobny ticket P1-6, bez integracji reklam): mecz/sektor, znany cel klubu, czas, rozważana lub wykonana czynność, cena/budżet tylko gdy podane, źródło informacji i powiązany issue. Rozróżnić zamiar od działania. Nie przepisywać historycznego scenariusza ani nie wyliczać z wpisu przyczynowego ROI. Wynik pilota: użytkownik poprawnie interpretuje zmianę24/48/72, fallback i wskazuje możliwą decyzję; zewnętrzny kontakt tylko na zlecenie użytkownika.

Przed każdym taskiem integrator przypisuje rozłączne pliki i konkretny odbiór, a po nim zapisuje dowód w run log. Pomocnicy pozostają na tańszym modelu. Nie deklarujemy kalendarzowego terminu udowodnienia MAE zależnego od30 nowych meczów; wykonanie backendu, analizy błędów, wejścia nowych źródeł i panelu nie czeka na tę próbę.
