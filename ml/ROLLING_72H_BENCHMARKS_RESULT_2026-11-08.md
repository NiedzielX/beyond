# Rolling72: benchmarki, bramka treningu i zamrożenie baseline v1

Data: 2026-11-08. Status: kod/precommit i prywatny audyt gotowe; rzeczywisty capture forecastów następuje dopiero po publikacji tej wersji.

## Recepta i dane

[Precommit](ROLLING_72H_BENCHMARKS_AND_CHALLENGER_PRECOMMIT_V1.md) z machineSHA9fc87bf69f796d644585ea0a5dc96800cb4322d42ad523cab2a75fb3ef5a7bc0 utrwala12cech, jeden HGBquantileP50, parametry, cutoff14:28:33UTC/15:28:33Warsaw i własne gate5meczów/3klubów perhorizon. Zapisano je przed fit; nie obniżono ich po obejrzeniu support. [Freeze baseline](artifacts/rolling72_v1/baseline_freeze.json) jest z20:14:48UTC/21:14:48Warsaw i wiąże dokładne bajty5plików kodu z precommitem. Nie jest fittedmodelem.

Odtwarzalny `ml.rolling72_receipt_dataset_v1` zweryfikował215oryginalnych receipts z3–7listopada oraz prawdziwy zachowany registry38źródłowych tożsamości. Inputissue odpowiada faktycznemu retrieved_at; pełna wtedy odebrana kopia i dokładna wersja metadanych mają konserwatywny knowledgebound. Etykieta pochodzi z pierwszego późniejszego poprawnego receipt po dojrzeniu targetu, znanego przed cutoffem. Cały fixture/alias jest jedną grupą. Ongoingfixtures pozostają poza treningiem.

| Horyzont | Wiersze z rzeczywistą etykietą | Niezależne grupy meczów / kluby |
|---|---:|---:|
| +24h | 315 | 2/2 |
| +48h | 166 | 2/2 |
| +72h | 53 | 2/2 |

Łącznie534rows, ale tylko2grupy/2kluby. Maksymalny etap toP-4,1099, najkrótszy labeledprefix121,5h. W archiwach są24jednopunktoweREADYinputs, lecz **zero jednopunktowych matchedtrainingrows**. Historyczne capture-timeP-50pokrycie z etapuA nie jest receipt-proven treningiemP-50. First-point działa w kontrakcie/testach; nie oznacza wyuczonej trafności takiego początku.

Rzeczywiste wywołanie gate/modelAPI zwróciło **NO_FIT**, a pickup **NO_FIT_INSUFFICIENT_SUPPORT**. Estymator nie został dopasowany. [Agregaty i wynik bramki](ROLLING_72H_REAL_TRAINING_GATE_2026-11-08.json); datasetSHA2afb7a6c8fe5d0be4cae6da69291dead0a3ca169cc3c1fdaadb40ec7cb6692fe. Fullrows/oryginalnereceipts pozostają prywatne. To exposed historical as-known reconstruction, nie noweprospective ani nietkniętyholdout. Testy estymatora są jawnie syntetyczne i domyślnie niedopuszczone do servingu.

## Nowy kod i granice

- Persistence prognozuje ostatni poziom od jednego punktu. Osobny drift liczy rzeczywistą kotwicę24h,4hourlypoints/span24 i `h+staleness`; minimum0, bez sztucznej górnej pojemności i damping. Stary driftstream/ledger nie zmienia się.
- Pickup ma zadeklarowane sourcefamily/h/maturity→pooledh→UNAVAILABLE, medianę z równym głosem meczu i własny gate5/3. Brak lookupu nie jest udawany jako fittedmodel.
- Nowy ledger zapisuje rzeczywisty issue/writtenclock, source/prefix/code/freezehash i wszystkie statusy horyzontów. Numericforecasts są osobno od statusrows. Pierwsza przyjęta etykieta/score są immutable; późniejsze odczyty ich nie poprawiają.
- Rejestr oryginalnych snapshotów odrzuca zmieniony payload/capture/source/scope/flags lub właściciela tego samegoID, także w starym prefixie albo podczas niedojrzałego scoringattemptu. Wszystko w jednej transakcji.
- Store cech wymaga oryginalnych bytes i ponownie odtwarza batch przed otwarciemSQLite; samo przeliczenie hashów nie pozwala podstawić innych wartości pod stary sourcehash.
- Nowy prywatnybackup namespace nie zmienia starychmanifestów ani ledgerów. Testy sprawdzają niezależny readback/restore, rozmiary/dekompresję/pathguards i brakoverwrite.

Testy odróżniają inputcounts od coordinatecounts oraz powtarzane labelattempts od finalnych targetów. Brak outcome/score nie jest zerowym błędem. Publiczna dostępność nie jest potwierdzoną płatną sprzedażą. Ceny/promocje/pula nadalUNKNOWN, brak przyczynowych obietnic.

## Kolejne wykonanie

Świeży ograniczony odczyt dwóch przyszłych meczów o21:13Warsaw przygotował rzeczywiste sourcebytes, zachowując lukę pomiędzy poprzednimi odczytami. Dopiero po publikacji frozenkodupowstanie nowy actual-timecapture persistence/drift i jego kopia prywatna; nie używamy dawnego14:14featureissue jako czasu dzisiejszej prognozy. Currentexposedfixtures dostarczą prawdziwych przyszłych targetów operacyjnych, lecz nie nowego30fixture/8clubreviewcohort.

Nowy feed/parser/geometria panelu są oddzielnym zadaniem; testowany serializer/preview nie oznacza deploy. Nowy fittedchallenger, frekwencyjneMAEokoło1200 oraz noweprospectiveMAEnadal nie są osiągnięte. Production_change=false/live_adjustment=0; starych modeli/artefaktów/issueclocków/bramek nie zmieniono.
