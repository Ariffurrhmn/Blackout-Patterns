# Demand forecasting: protocol and pre-registered recipes

Written before any demand model was run. Target changes from load shedding to **national evening-peak demand** (MW).

## Facts checked before writing the protocol

1. **What the target is.** On 2,397 days with all three fields, evening-peak demand equals evening-peak generation plus national shedding exactly on 64% of days, and within 1% on 99%. In 2019–2021 the identity holds on 95–100% of days; in 2023–2026 it holds on only 12–48%. So demand is BPDB's estimate of served plus shed demand, not the sum of the two fields in every year. Shedding is part of demand, so demand carries some of the uncertainty of shedding, but most of it is weather and calendar.
2. **Independent cross-check.** Our demand field agrees with the second source's `eve_peak_demand_mw` to within 0.3 MW (median). Exact matches are rare only because our file stores whole MW. This holds for 2019–2026, so the test years are not a source problem.
3. **BPDB's own forecast** (`probable_max_demand_mw`, Mridha 2026 `bpdb_forecast_daily.csv`) covers every day 2019–2026. Its best alignment with same-date demand is shift 0 (MAE 676 MW, against 768 and 902 for the nearest shifts). **Caveat:** it sits in the report published on the target day, so it is a same-morning forecast with more information than our day-ahead models. It is a benchmark to beat, not a like-for-like day-ahead comparison. The source's own comparison gives MAPE 4.35% over 2019–2026.
4. **Weather.** The ERA5 daily file (Mridha 2026, `weather_daily.csv`) covers 2016-01-01 to 2026-08-01 by zone, with no gaps. Country values are the mean over the nine zones.
5. **Earlier look at 2025–26 demand.** While checking the identity and the cross-check, I printed five days of 2025-06 demand. Demand has otherwise not been scored or plotted for 2025–26. That disclosure is part of the test protocol below.

## Decisions (written before running)

- **Score set:** days with a recorded demand target, excluding R2 (maximum demand recorded as zero) and R7 (missing target). R5 days (identity residual above the 0.5/99.5 bounds) are **kept** in scoring and training: the identity fails on most 2023–26 days, so the residual is not a reliable error signal for demand. They are logged, not removed.
- **Persistence floor:** yesterday's demand (on the same score set).
- **Benchmark:** BPDB's same-morning forecast, reported separately because it has more information.
- **Trend:** the target is the **log ratio** y / (7-day mean of lagged demand). Demand grows every year, so levels outside the training range must not be an issue for trees.
- **Holidays:** built from a Hijri calendar (`hijri-converter`), not typed by hand. Flags: Ramadan (Hijri month 9), Eid al-Fitr window (Shawwal 1 ±1 day), Eid al-Adha window (Dhu al-Hijjah 10 ±1 day). The file's own holiday columns are not used.
- **Weather, two labelled versions:**
  - *Lagged weather* (ERA5 for day t−1): the version we could actually use.
  - *Same-day weather* (ERA5 for day t): a stand-in for a perfect forecast, to measure how much heat matters.

## Recipes (fixed before running)

| ID | Recipe | Weather | Notes |
|---|---|---|---|
| D1 | Persistence (yesterday) | none | floor |
| D2 | Same weekday last week | none | seasonal naive |
| D3 | BPDB same-morning forecast | (its own) | benchmark, not day-ahead |
| D4 | Ridge on log ratio | none | lags 1 and 7, 7-day mean, weekday, annual Fourier (2 harmonics), holiday flags |
| D5 | Ridge on log ratio | lagged | D4 plus ERA5 t−1 (tmax, tmean, precipitation) |
| D6 | Ridge on log ratio | same-day | D4 plus ERA5 t (perfect-forecast stand-in) |
| D7 | Gradient boosting on log ratio | none | D4 features, HGB squared loss |
| D8 | Gradient boosting on log ratio | lagged | D7 plus ERA5 t−1 |
| D9 | Holt-Winters, additive weekly seasonality | none | statsmodels, one-step-ahead |

## Protocol

- Same three validation folds as before (2023-07 to 2024-12; train through 2023-06-30, 2023-12-31, 2024-06-30). Recipes are selected on these folds only.
- Metrics: MAPE and MAE, skill against persistence (1 − MAE/MAE_persist), 95% moving-block bootstrap (7-day blocks). BPDB's forecast is reported as a separate comparison.
- **Single test run** on 2025-01-01 to 2026-08-03, after the validation table has been reviewed. Reported with the caveat in fact 5 above.
- A walk-forward (monthly refit) version is reported as the practical protocol.

## Not done

- Prophet (Islam et al. 2025 method) is listed as optional and only if it installs cleanly. It is not in the grid.
- No recipe uses same-day report fields (generation, supply, shedding), since they come from the same report as the target.
