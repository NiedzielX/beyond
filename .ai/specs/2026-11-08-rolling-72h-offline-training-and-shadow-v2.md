# Rolling72 v2: jeden offline fit, genuinefuture evaluation

Data2026-11-08. Status:PRECOMMITTED_BEFORE_IMPLEMENTATION_AND_FIT. Użytkownikautoryzuje ciągłą pracę nadMVP/MAEz równoległymiagentami; roadmapdopuszcza noweosobnowersjonowane eksperymenty. V1(zamrożone5plików, strictreceiptNOFIT, rzeczywistebaselineforecasts) pozostaje nietknięty.

[Exactmachineprecommit](../../ml/artifacts/rolling72_v2/precommit.json) i [opis](../../ml/ROLLING_72H_OFFLINE_TRAINING_PRECOMMIT_V2.md) utrwalają hash źródeł, reguły, min5/3/60,12cech i TĘSAMĄHGBreceptę przedpierwszymfitem. Nie wybieramyparametrów poMAE. Feasibilitycounts23commonfixtures/14clubs/686rows nie są wynikiemdokładności.

Źródłowagranica jestodrębna: historyczneprefixycapture doofflinefit mają unknownhistoricalknowledge/metadataversions. Nie wymyślamyknown_at, nietworzymy dawnychforecastów/holdout/PITMAE. Treningwykorzystuje autentyczne pomiaryjużposiadane przed cutoffsnapshotem i potwierdzonecompletedfixtureidentities, bezattendancevalues. Pierwszyaktualnykompatybilnypomiar wspierany; sourcezmianystartująnowysegment. Staresegmentykatalogowane, candidate/VAOniesklejane.

Implementacja3części: odtwarzalnydatasetv2ztrainfeaturesbezfakeclocks, jednorazowytrustedprivateHGBartifact+manifest+mechanismaudit, oddzielnyactual-timepairedshadow/ledger. Wszystkieinferenceobserwacje i metadane mają rzeczywistyreceiptbound≤actualissue; modelepoactualfreeze. Runtimefreshnessmax1h, horizonfeatureodostatniegopomiaru(h+staleness). Baselineswspólnyissue/target, pierwszeacceptedscoreimmutable. Żadnychpoprawekstarychpredykcji, sourcegates lubautopromotion.

Nie wolno prezentować in-sample/historicalMAEjako dokładnościMVP. Ocena wyłącznie po przyszłych prawdziwych odczytach24/48/72. Odsłoniętefixtures pozostająodsłonięte, formalnyreview30new/8clubs, goalokoło1200attendanceMAEosobno. No guarantee, brakfittedintervals, no causalpricing/ad claims. Productionfalse/live0.
