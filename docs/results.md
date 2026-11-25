# Results: daily national load shedding, 2025–2026

Target: total load shedding across the nine BPDB regions on each day (MW), summed from the `*_load` columns.
Train: 2019-11-21 to 2024-12-31. Test: 2025-01-01 to 2026-08-03.
Scored on the same 515 test days, which are clean days that have the lagged values every baseline needs.

## Headline

**The model does not beat the simplest baseline.** "Tomorrow is the same as today" gives a lower error (MAE 104.8 MW) than either model (122.8 MW cleaned, 125.8 MW raw). On whether a day has any shedding at all, every method is about equally good (accuracy 0.81). Cleaning the training data improved the model slightly (MAE 125.8 → 122.8 MW), which is a small effect.

## Scores on the cleaned 2025–2026 test days

| Method | MAE (MW) | RMSE (MW) | Shed/no-shed accuracy | Shed-day F1 | Mean predicted (MW) |
|---|---|---|---|---|---|
| Always zero | 162.9 | 409.7 | 0.450 | – | 0.0 |
| Yesterday's shedding | **104.8** | **260.9** | 0.806 | 0.823 | 161.7 |
| Same weekday last week | 180.1 | 396.9 | 0.660 | 0.689 | 145.4 |
| 7-day mean | 135.1 | 289.5 | 0.682 | 0.771 | 153.7 |
| ML, trained on raw data | 125.8 | 251.2 | 0.808 | 0.825 | 164.3 |
| **ML, trained on cleaned data** | 122.8 | 259.1 | 0.808 | 0.825 | 151.0 |

Actual mean over these days: 162.9 MW.

## By year

| Year | Days | Actual mean (MW) | Yesterday MAE | ML cleaned MAE | ML cleaned mean predicted (MW) |
|---|---|---|---|---|---|
| 2025 | 329 | 66.1 | 60.7 | 81.0 | 103.6 |
| 2026 (to 3 Aug) | 186 | 334.2 | 182.8 | 196.7 | 234.9 |

- 2025 shedding is lower than the training years, and the model over-predicts it. The model was learning from 2022–2024, when shedding was higher.
- 2026 shedding is above every training year (the highest training-year mean is about 233 MW). Tree models cannot predict above the values they saw in training, so the model under-predicts 2026 (mean predicted 235 MW against 334 MW actual). This is an extrapolation limit, not a bug.

## Scored on uncleaned test days (for comparison)

Using all 576 test days with a recorded target (cleaning rules not applied to the test rows):

| Model | MAE (MW) | RMSE (MW) | Shed/no-shed accuracy |
|---|---|---|---|
| ML, trained on raw data | 142.6 | 293.0 | 0.812 |
| ML, trained on cleaned data | 142.6 | 307.1 | 0.811 |

The two models score the same on MAE here. The cleaned model's RMSE is higher, which suggests it misses a few large-shedding days that the raw model happens to catch. This is a small sample of large days, so I wouldn't read much into it.

## What this means for the question

- **Can cleaning separate anomalies from regular behaviour?** It can remove the recording errors (zero maximum demand, regional copies, supply above demand, residual outliers): 202 of 2,428 rows, see `docs/excluded_days.md`. Those rows are not real shedding, so removing them is right.
- **Does that make prediction better?** Only slightly, and not better than persistence. The main limitation is that the target moves quickly from day to day, and the features available here (lagged shedding, lagged supply limits, lagged temperature) do not capture the causes of that movement well.
- **Next things to try** (not done yet): train on 2022–2024 only, since the 2019–2021 zero-shedding regime may hurt the fit; add a comparison against a linear model on lags; check whether the regional split adds information once the copied rows are removed; and report uncertainty bands, not just point errors.
