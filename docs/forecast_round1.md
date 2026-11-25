# Day-ahead weather forecasts: pre-registered recipes (validation folds only)

Question: does a forecast of wind and cloud cover, made before the day, add anything to demand forecasting? The earlier result (`docs/humidity_round1.md`, W2) used same-day reanalysis, which is an upper bound. This round uses past forecasts from Open-Meteo's historical forecast archive (`historical-forecast-api.open-meteo.com`, the forecasts actually issued on each past day, not the reanalysis).

**Caveat on lead time.** The archive returns the forecast from the model run for each day. For a daily value this is typically a 0–24 hour lead, which is close to but not strictly day-ahead. State this wherever results are reported.

Data: daily `wind_speed_10m_max` and `cloud_cover_mean` for the nine zones, 2019-11-21 to 2026-08-01, averaged to a national value.

| ID | Recipe | Weather inputs (day t) | Notes |
|---|---|---|---|
| F0 | Base (= H0) | none | reference |
| F1 | Base + forecast wind and cloud | forecast wind, forecast cloud | the day-ahead question |
| F2 | Base + forecast cloud only | forecast cloud | checks whether cloud alone carries the signal |
| F3 | Base + reanalysis wind and cloud (= W2) | NASA same-day | upper bound, already run |

Same selection rule and folds as before. The forecast's own accuracy against the reanalysis is reported separately (MAE of wind and cloud on validation days), so a weak result can be traced to a weak forecast.
