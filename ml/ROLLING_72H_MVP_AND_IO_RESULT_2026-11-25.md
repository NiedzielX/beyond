# Wynik developmentu — 25 listopada

**Panel Jagiellonii działa z rzeczywistym chronionym API, a ciężki cache
Supabase ponownie odświeża się automatycznie.**

Nowe API prezentuje zapisane wydania PERS i obserwacje z osobnym stronicowaniem,
rzeczywistymi czasami oraz późniejszymi etykietami. Prywatny dostęp obejmuje
wyłącznie zatwierdzoną parę mecz/ścieżka. Nowa bramka zachowuje E5/B, odmawia
bez kodu i dla niewłaściwych par. Nie przekazuje kluczy Supabase do przeglądarki.
[API i poprawka zegara — PR231](https://github.com/NiedzielX/beyond/pull/231),
[panel — PR10](https://github.com/NiedzielX/BeyondTicketingPanel/pull/10).

Przeglądarka załadowała82rzeczywiste wydania Jagiellonii. Wybrane najstarsze
wydanie1 zachowało6707miejsc i wyłącznie receipt1 w historii wejściowej.
Natywne odświeżanie pobrało nowe wydanie81→82 bez ręcznego odświeżenia,
podmiany zegara, zmiany wybranej wersji lub jej historii. Nie wystąpiły błędyJS
ani zapis kodu dostępu w localStorage/sessionStorage. Test lokalnej strony
używał rzeczywistego hostowanego Edge/SQL; publicznego dostępu do chronionej
strony Vercel nie potwierdzono.

Naprawiono rzadki remis mikrosekund rzeczywistego zegara wystawiania. Guard
czeka raz na prawdziwy zegar, zachowuje ścisły warunek i zwraca retryable40001,
gdy zegar nadal nie postępuje. Bazowy SQL/manifest, wcześniejsze prognozy,
wartości modelu i zamrożone E5/B pozostają zachowane; poprawka ma osobny hash.
Wydanie82 powstało automatycznie po poprawce:25XI11:25:00.782848UTC,
wartość6635, trzy cele24/48/72. Nowa lane nadal ma **zero etykiet i nieznaneMAE**.

Optymalizacja Supabase zastępuje pełne obliczenia cech w dwóch licznikach
gotowości odczytem tych samych kluczy. Zachowano okna, tie-breaks, krotności,
liczniki, progi i uprawnienia. Test zgodności i niezależne przeglądy PASS.
Po wdrożeniu zwykły cykl cache25XI11:14UTC zakończył się po40,340116s;
poprzedni przerwano po120,175365s. Harmonogramy i komendy zadań pozostały
bez zmian. Nie zmieniono płatnego planu ani konta. Zużycia fizycznego budżetu
Disk I/O nie zmierzono. [PR232](https://github.com/NiedzielX/beyond/pull/232).

Weryfikacja wydania:12testów zegara/PERS,8feedu,5uprawnień,14Edge,
20klienta/relay,TypeScript i testy przeglądarkowe PASS. CI API45603944012,
panel45603837674/45603838021 oraz cache45604786016:SUCCESS na publikowanych
commitach. Dowody: [pilot](ROLLING_72H_PERS_PROTECTED_PILOT_PROOF_2026-11-25.json),
[cache](DASHBOARD_READINESS_IO_PROOF_2026-11-25.json).

## MAE według horyzontu

Odczyt E5 z25XI11:09UTC; średnia najpierw w meczu, potem równa waga meczów.
To osobna, ujawniona kohorta dostępności miejsc, nie wynik nowej lane PERS.

| Horyzont | Oceny | Mecze | PERS MAE | drift6 | drift24 | common_flow6 |
|---|---:|---:|---:|---:|---:|---:|
| +24 h | 305 | 2 | 199,96 | 151,94 | 104,33 | 223,49 |
| +48 h | 127 | 2 | 375,92 | 269,14 | 262,56 | 341,14 |
| +72 h | 0 | 0 | — | — | — | — |

Nie dostrajano zamrożonych modeli. Dwa mecze nie dowodzą generalizacji ani
realizacji celu około1200miejsc frekwencji. Przygotowano osobny kod porównania
PERS–drift24,13testów syntetycznych i przypięte referencje. Rozdziela obliczenie
wartości od późniejszego wiązania czasu wydania, kontroluje pełne identyfikatory
sektorów/price-area oraz odmawia mieszania horyzontów. To kontrakt offline;
nowy runtime, wspólne etykiety i aktywacja pozostają kolejnym etapem.
