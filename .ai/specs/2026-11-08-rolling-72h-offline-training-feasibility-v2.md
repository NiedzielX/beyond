# Rolling72 v2: feasibility historical training, genuine prospective evaluation

Data:2026-11-08. Status:READ_ONLY_FEASIBILITY, bez fitu i bez zmiany v1.

V1 pozostaje immutable:2strictreceiptfixtures, NO_FIT, nowe baselineforecasts. Sprawdzamy osobną hipotezę danych do szybkiegoMVP: czy starsze autentyczne capture-prefixy, już rzeczywiście posiadane przed aktualnymfitcutoff, mogą posłużyć jednorazowemu treningowi tego samego małegoHGBP50, pod jawnym założeniem nieznanej dawnej ingestii/metadanych. Ocena skuteczności WYŁĄCZNIE na późniejszych rzeczywiście wydanych prognozach i genuinefuturetargets. Nie przedstawiamy historicalcapture-replay jako PIT/holdout/prospective, nie tworzymy known_at=captured_at i nie używamy in-sampleMAE jako wynikuMVP.

Na razie tylko policzyć support bez dopasowania modelu/wyliczania błędów. Gate5niezależnychmeczów/3klubów w każdymh, wspólnychmin5 i60rows nie zmienia się. Ongoing/nonconfirmedfixtures pozostają wyłączone; originalactualoutcomes mogą dowodzić zakończenia, ale attendancevalue nie wchodzi do targetu/cechinventory.

Deterministyczna definicja porównywalnej historii: zachować wszystkie suroweobserwacje w audycie; dla actualcaptureorigin użyć tylko bieżącego ciągłego segmentu tej samej measurementkey. Po zmianiekey zaczyna się nowysegment; starsze nieporównywalne wartości nie są sklejane ani wymazywane z historii. Nienormalizowaćcandidate_backfill/VAOdo roboticket bez odrębnejudowodnionejzgodności. Wspierane numeryczne segmenty tylko normalRoboticket/Stellis zwhitelistv1; literal0pozostaje0, invalid/hiddenfailclosed. Sourcekeytransitionbeforetargetjest unscorableboundary, nie opportunity toselecteasycases. Origin: pierwszy rzeczywisty pomiar każdegoUTCday plus pierwszyrzeczywistypomiar segmentu, wybierany bezfuturetargetów. Label: latestactualcapture≤origin+h w6h, strictlyafterorigin/beforekickoff, ten sam nieprzerwany segment. Fullsourcecopy musi istnieć przed futurefitcutoff; historicalknowledge_unproven=true.

To nowy kontrakt danych, nie luzowanie starejbramki. Jeśli feasibility ma support i brak source-qualityblockerów, potrzebnyosobnyexactprecommitV2 przedjednorazowymfit. HGB12cech/parametrybezsearchmają pozostaćjakwe wcześniejszejrecepcie; tej samej przyszłej obserwacji nie wolno użyć dotreningu, a nowa wersja nie oczyszcza starychexposedfixtures.

Productionfalse/live0; brakDBwrite, backfillstarychforecastów, podmiany currentC1 lub autorelease.
