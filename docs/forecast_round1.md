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

## Results (validation folds, pooled), built on 4 of 9 zones

**Deviation, recorded:** the Open-Meteo quota blocked the other five zones. National values here are means over Dhaka, Chattogram, Rajshahi and Sylhet, for both the forecast and the reanalysis. The user chose to freeze data collection and build with what is available.

| ID | Recipe | Mean MAPE | Skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|---|
| F0 | Base | 5.05% | +0.103 | +71 | [−5, +136] |
| F1 | Base + day-ahead forecast wind and cloud | 4.67% | +0.155 | +106 | [+10, +190] |
| F2 | Base + day-ahead forecast cloud only | 4.86% | +0.137 | +94 | [+20, +157] |
| F3 | Base + same-day reanalysis wind and cloud (upper bound) | 4.52% | +0.192 | +131 | [+54, +200] |

**Forecast accuracy** (validation days, 4-zone mean): cloud cover MAE 9.2 percentage points, correlation 0.94 with reanalysis; wind forecast (daily max) vs reanalysis (daily mean), correlation 0.88.

**Reading.**
- The pre-registered question (F1) is answered in the affirmative on validation: the interval excludes zero.
- F1 recovers about 60% of the gain of the same-day upper bound (skill 0.155 against 0.103 base and 0.192 upper bound). The difference between F1 and F0 was not tested with its own interval.
- Cloud cover alone (F2) carries most of the gain, which suggests wind is a smaller part of it.

**Limits.**
- Four zones, not nine. The national figure is an approximation.
- The archive gives the model run's forecast for each day: lead time roughly 0–24 hours, so close to, but not strictly, day-ahead.
- This is validation-only. The 2025–26 test has not been run for demand, and it would need to be run once with these recipes frozen before any claim is made beyond validation.
