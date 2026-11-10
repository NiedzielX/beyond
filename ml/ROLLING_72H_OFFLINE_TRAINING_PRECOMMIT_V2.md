# Rolling72 v2: historyczny trening, przyszła weryfikacja

Data2026-11-08. Status:exactprecommitprzed fitem. MachineJSON: `ml/artifacts/rolling72_v2/precommit.json` jestautorytatywnydlategoodrębnegoprotokołu. Nie zmieniamy v1/czy starychC1/SSP/P9/daily.

V1poprawniepozostajeNOFITna2strictreceiptfixtures. V2sprawdza innąhipotezędanych: trenować raz na starszychgenuinecaptureprefixach z jawnienieudowodnionymi dawnymiknowledgeclocks, a skuteczność ocenić dopiero na immutableprognozach wydanych TERAZprzed przyszłymitargetami. Brakdawnychingestionclocks blokuje historycznąPITwalidację, lecz może być świadomymograniczeniem osobnegooffline-treningu. Nie przedstawiamytegojako tęsamąjakośćevidencji.

Regułydatasetu: tylkozhashowaneoryginalnereceivedsourcecopies, cutoffźródeł14:28:33UTC8listopada (actualfit/freezeznaczniepóźniej i jawniezapisane). Completedconfirmedidentities zactualoutcomes/receiptów; attendancevaluesniewchodządomodelu. OriginpierwszycapturekażdegoUTCday i pierwsyzkażdego ciągłegoexactkeysegmentu, wybieranebez przyszłychlabelów. Historia tylko bieżącegoporównywalnegosegmentu, wcześniejszesegmentyzachowane w audycie. Candidate/VAObezaliasowania. Labelrealny latest≤origin+h, max6hstary, strictlypoorigin/przedkickoffem, bezzmianypomiarulubinvalidstanuwodcinku. Zerozapisane pozostaje0, missing≠0.

Engineeringgate ten sam: min5wspólnychfixtures/3klubów na każdymh i60rows. Aliasyeventutrzymanerazem, wagiN/(E×3×n_event_h). Feasibilitydaje23common/14clubs/686rows, ale nieMAE. P50trainingbrak, P30–50tylko1fixture; później raportujemyquality/extrapolation, bezudawaniapokrycia.

Jeden HGBquantile0.5, sklearn1.8, parametry100/.05/7leaves/depth3/leaf20/l2=1/bins64/earlystopFalse/seed42, bezsearch. Dokładnie12cech v1, missingNaN, bezclubID/fittedpreprocessing. Przyinferencehorizonfeature toh+sourceage(fizycznyleadodlastcapture), sourceage≤1h; histogramowy modelniejestudowodnionymmodelemdeliverylatency. Outputmin0, bezgórnejpojemności/monotoniczności/intervals. Fittedartefactprivatehashbound, actualwallclockfreeze, jednorazowyfitmarker/refuseoverwrite. Fixedhistory-sensitivityaudit niejestMAEi nieupoważniadoretuninguprzydegeneracji.

Dalszeprognozyw nowymshadowv2, baselineporównanenatychsamychissue/input/target. Sourceknown_atprawdziwyreceipt boundna inference, żadnego oldforecastbackfill. Pierwsza przyjętalabel/scoreimmutable. Oldfixturesdescriptiveonly, formalreview30freshfixtures/8clubs/bootstrap10000seed42. Wyniki24/48/72inventoryosobnoodokoło1200attendanceMAE, bezgwarancji. Productionfalse/live0.
