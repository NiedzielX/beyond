# E5: rzeczywiste oceny +24 h — 24 listopada

Odczyt Supabase: **2026-11-24 14:50:53.459707 UTC** (15:50 w Warszawie).
141 sparowanych ocen pochodzi z **2 meczów**, a nie ze 141 niezależnych meczów.
Wyniki dotyczą publicznej dostępności miejsc, nie sprzedaży ani frekwencji.

| Horyzont | Mecze | Oceny | PERS MAE | drift6 MAE | drift24 MAE | common_flow6 MAE |
|---|---:|---:|---:|---:|---:|---:|
| +24 h | 2 | 141 | 139,5478 | 90,8718 | 75,9476 | 194,2310 |
| +48 h | 0 | 0 | — | — | — | — |
| +72 h | 0 | 0 | — | — | — | — |

Najpierw liczymy średni błąd bezwzględny w obrębie każdego meczu i horyzontu,
następnie średnią z meczów z równą wagą. Wszystkie cztery metody korzystają
z tych samych etykiet i współrzędnych E5; nie łączymy wyników z innymi lane.

Na tej małej próbie drift24 ma obecnie najniższy MAE. To opis ujawnionej
kohorty, nie dowód generalizacji. Wynik różni się od pierwszego odczytu
23 listopada (5 ocen), ponieważ dojrzało więcej rzeczywistych celów.
Nie zmieniono żadnej zamrożonej prognozy, modelu ani reguły oceny.

W chwili odczytu pierwsze cele +48 h pozostawały przyszłe: około
24 listopada 17:15 Europe/Warsaw. Pierwsze +72 h przypadają następnego dnia.
Brak oceny pozostaje brakiem; nie wpisujemy zera i nie rekonstruujemy historii.

Zapytanie: `rolling72_common_flow_e5_labels_v1` połączone przez `prediction_id`
z `rolling72_common_flow_e5_predictions_v1`, agregacja najpierw po
`horizon_hours,ticket_event_id`, potem po horyzoncie. `live_adjustment = 0`.
