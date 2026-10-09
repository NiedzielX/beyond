# Beyond Demand Engine v1

This package is the versioned forecasting core for Beyond.

## Principle

The engine deliberately separates three questions:

1. **Historical expectation** — what attendance is expected from match/club context before live ticketing signals?
2. **Live demand correction** — does proprietary public-inventory behaviour justify moving that expectation?
3. **Final calibrated forecast** — what P10/P50/P90 should be persisted and shown to the product?

The algorithm behind each layer is replaceable. The data contract, lineage and benchmark gate are not.

## Pipeline

```text
ForecastRequest
     |
     v
HistoricalForecaster
     |
     +--> historical P10 / P50 / P90
     |
     v
LiveFeatureProvider
     |
     +--> inventory index
     +--> velocity 6h / 24h
     +--> acceleration
     +--> anomaly / quality state
     |
     v
LiveCorrector
     |
     +--> live adjustment + reason + version
     |
     v
Beyond Demand Engine v1
     |
     +--> final P10 / P50 / P90
     +--> full lineage
     |
     v
forecast_observations
```

## Safety rule

`NoOpLiveCorrector` is the reference implementation. It preserves the historical forecast and records live signals in shadow mode. A live correction model/rule can be promoted only after the benchmark shows incremental value without unacceptable bias, calibration or segment regressions.

## Required lineage for every forecast

- engine version;
- historical model name + version;
- historical feature-set version;
- live feature version;
- correction version;
- source snapshot ID and timestamp;
- signal readiness;
- historical P10/P50/P90;
- live adjustment;
- final P10/P50/P90.

The existing `forecast_observations` schema already stores the main forecast decomposition. Additional lineage lives in `payload.engine`, so no schema migration is required for v1 scaffolding.

## Historical model status

### Incumbent evidence

`lech_v13_early_seasonality` / GB v1.3 is the current historical model identified in live v0.3 records.

### v1.7 research

Historical R&D artifacts confirm later horizon-specific T30/T7 Ridge experiments and per-match prediction outputs. However, the final v1.7 source/selection script has not yet been recovered from the available indexed artifacts. Therefore v1.7 is **not reimplemented from inference** here.

It will be connected as a shadow `HistoricalForecaster` only when its exact final implementation or a reproducible specification is recovered.

## Promotion gate

A candidate historical/live model must be evaluated through the benchmark harness using the same no-leakage protocol. Minimum reporting:

- MAE;
- MAPE;
- WAPE;
- Bias;
- within ±5%;
- within ±10%;
- P10/P50/P90 pinball loss;
- P10–P90 empirical coverage;
- results by T-30 / T-14 / T-7 / T-3 / T-24h;
- results by club once multi-club outcomes are sufficient.

A lower single metric is never sufficient for automatic promotion.

## Next implementation

1. Recover and reproduce the exact v1.7 T30/T7 historical model.
2. Add adapters for v1.3 and v1.7 and run both in shadow mode.
3. Implement a Supabase-backed `LiveFeatureProvider` using the existing live feature columns / snapshot pipeline.
4. Replay historical live observations where outcome exists to benchmark candidate correction rules.
5. Only then promote a non-zero live correction.
