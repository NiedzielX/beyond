# Beyond Ticketing — Match Context Challenger v1

Status: **no promotable candidate**  
Production impact: **none**

## Goal

Test the Match Context layer after the current best research chain:

`Baseline → Baseline + Ticketing → Match Context`

The three Matrix components are evaluated independently:
- timing;
- competition stage;
- opponent historical uplift.

## Timing

Timing is fully reconstructable from `ticket_events.kickoff_at` in `Europe/Warsaw`, so it can be tested historically without backfilling information that was not known at the time.

Three simple fixed candidates were tested at T-24h with Ridge alpha 30:
- weekend flag;
- prime window flag (local kickoff hour 17–20);
- local kickoff hour.

Primary validation is leave-one-club-out.

### Leave-one-club-out results

| Candidate | N | Clubs | Baseline + Ticketing MAE | Candidate MAE | Uplift vs Ticketing |
|---|---:|---:|---:|---:|---:|
| weekend flag | 8 | 6 | 5,007.3 | 7,102.8 | -2,095.5 |
| local hour | 8 | 6 | 5,007.3 | 7,185.8 | -2,178.5 |
| prime window | 7 | 5 | 5,532.3 | 7,939.6 | -2,407.3 |

No timing candidate improves the current Baseline + Ticketing forecast.

## Competition stage

Status: `not_testable_current_sample`.

All current evaluation rows are Ekstraklasa matches and the event source does not provide an explicit stage. Beyond intentionally does not infer a stage from the competition name alone. There is therefore no trustworthy stage variation to evaluate.

## Opponent historical uplift

Status: `insufficient_history`.

The existing shadow gate requires:
- at least 8 prior home outcomes for the club;
- at least 3 prior home meetings with the same opponent;
- same competition class;
- only historical outcomes before target kickoff;
- 730-day lookback.

No current event passes this gate. Missing opponent history remains null and is never replaced with a zero uplift.

## Decision

Match Context v1 does **not** create a `baseline_ticketing_sporting_match` prediction.

`context_ablation_predictions_v1` intentionally contains **0** predictions for this variant.

This is not a rejection of Match Context as a product category. It means that the components currently available for leakage-safe evaluation do not justify a forecast correction.

## Automation

`match_context_challenger_summary_6h` refreshes the research summary every six hours. It is an internal database job only and does not send user notifications.

## Next evidence needed

A new Match Context candidate becomes worthwhile when at least one of the following is true:
- opponent uplift passes its history gate on enough independent completed matches;
- the source provides real competition-stage information;
- substantially larger prospective data supports a timing effect that survives leave-one-club-out validation.
