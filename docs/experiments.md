# Recipe search log

Validation only. The 2025–2026 test set was **not** used to choose anything in this log.

## Protocol (frozen before running)

- Folds (train through the cutoff, validate on the next half-year):
  - F1: train ≤ 2023-06-30, validate 2023-07-01 to 2023-12-31
  - F2: train ≤ 2023-12-31, validate 2024-01-01 to 2024-06-30
  - F3: train ≤ 2024-06-30, validate 2024-07-01 to 2024-12-31
- Score set (identical for every recipe): days with a recorded target, not a full-row duplicate, and with an observed target the day before.
- Skill per fold = 1 − MAE(model) / MAE(persistence). Recipe ranking = mean skill over the three folds.
- Cleaning variants change only training rows and feature masks, never the score set.
  - `raw`: training excludes only missing-target and duplicate rows.
  - `clean`: training also excludes R2 (maximum demand = 0), R4 (supply above demand) and R5 (residual outlier, thresholds fitted up to each fold's cutoff). R3 (regional copy) masks regional-load features only.
- Confidence interval: 95% moving-block bootstrap (7-day blocks, 2,000 draws) on the pooled 537 validation days.

## Disclosure

Before this protocol was written, the 2025–2026 test scores had already been printed once, in `docs/results.md`, by the first model script. Those numbers were not used to pick any recipe below, but the test set is no longer a clean holdout for this project. The final test run should be reported as the second look at it.

## Results (17 recipes, validation folds only)

Sorted by mean skill over persistence. Gain is the mean reduction in absolute error versus yesterday's value, in MW. Positive is better.

| Rank | ID | Recipe | Skill F1 | Skill F2 | Skill F3 | Mean skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|---|---|---|---|
| 1 | R13 | HGB diff F0 2022+ clean | +0.149 | -0.002 | +0.067 | +0.071 | +7.61 | [-0.9, +16.6] |
| 2 | R12 | HGB diff F0 all clean | +0.169 | -0.020 | +0.049 | +0.066 | +6.48 | [-2.2, +15.4] |
| 3 | R16 | HGB diff F1 all clean | +0.084 | -0.012 | +0.051 | +0.041 | +4.53 | [-2.4, +11.8] |
| 4 | R09 | HGB level F0 all raw | +0.113 | -0.089 | +0.093 | +0.039 | +4.20 | [-6.0, +14.9] |
| 5 | R14 | HGB diff F1 2022+ clean | +0.070 | -0.004 | +0.046 | +0.037 | +4.20 | [-2.9, +11.7] |
| 6 | R15 | HGB diff F1 2022+ raw | -0.047 | -0.005 | +0.074 | +0.007 | +2.29 | [-4.7, +9.8] |
| 7 | R10 | HGB level F0 all clean | +0.055 | -0.063 | +0.012 | +0.001 | -0.57 | [-11.2, +9.7] |
| 8 | R01 | persistence (yesterday) | +0.000 | +0.000 | +0.000 | +0.000 | +0.00 | [+0.0, +0.0] |
| 9 | R11 | HGB level F0 2022+ clean | +0.054 | -0.079 | +0.014 | -0.004 | -1.16 | [-12.3, +9.6] |
| 10 | R05 | Ridge level F0 all clean | +0.049 | -0.036 | -0.042 | -0.009 | -2.28 | [-7.7, +4.2] |
| 11 | R17 | HGB level F1 2022+ clean | +0.008 | -0.060 | +0.014 | -0.012 | -1.60 | [-12.1, +8.3] |
| 12 | R06 | Ridge level F0 2022+ clean | +0.011 | -0.047 | -0.112 | -0.049 | -7.50 | [-13.6, -0.2] |
| 13 | R04 | EWMA alpha=0.6 | +0.006 | -0.077 | -0.078 | -0.050 | -7.19 | [-14.2, -1.0] |
| 14 | R08 | Ridge diff F1 all clean | -0.051 | -0.067 | -0.046 | -0.054 | -6.70 | [-13.1, +0.6] |
| 15 | R07 | Ridge diff F1 2022+ clean | -0.145 | -0.087 | -0.110 | -0.114 | -13.58 | [-21.0, -5.1] |
| 16 | R03 | EWMA alpha=0.4 | -0.012 | -0.203 | -0.133 | -0.116 | -15.98 | [-27.5, -5.6] |
| 17 | R02 | EWMA alpha=0.2 | -0.052 | -0.361 | -0.242 | -0.218 | -29.53 | [-46.1, -13.0] |

## Reading the table

- **Winner by the frozen rule:** R13, HGB predicting the day-to-day change, using 2022–2024 training data and the clean rows. Mean skill +0.071.
- **The winner's interval includes zero** (gain +7.6 MW, 95% CI −0.9 to +16.6). On validation it is not clearly better than persistence.
- **Fold 2 is a tie for R13** (skill −0.002). Its advantage comes from folds 1 and 3.
- **Nine of the 16 model recipes are worse than persistence on average.** EWMA and linear level models are clearly worse, because shedding changes in jumps and smoothing lags it.
- **Predicting the change beats predicting the level** for the boosted trees (R13 vs R11, R12 vs R10). This is the one pattern that held in every comparison.
- **Cleaning is mixed.** For the change model, clean training beats raw by about 2 MW (R14 +4.2 MW vs R15 +2.3 MW, same features and window). For the level model, raw training beats clean by about 5 MW (R09 +4.2 MW vs R10 −0.6 MW). So the cleaning rules do not help the level model.

## Cleaning audit (requested by the advisor)

- **Full-row duplicates:** none exist in the file. The 2022-01-02 and 2022-01-03 rows match only on regional demand, not on every column, so they are not duplicates.
- **R5 does not remove the hardest days.** On validation, flagged days averaged 166, 214 and 87 MW against kept-day averages of 129, 200 and 300 MW. Most R5 flags in 2024-H2 are zero-maximum-demand days, which R2 already handles.
- **Sensitivity:** after R3 was removed from the bound fit, the lower R5 bound moved from about −237 MW to exactly 0 MW, because many training residuals are exactly zero. Only days with a residual below zero are flagged on the low side.

## Confirmatory check (validation only, run after the grid)

Walk-forward R13 (monthly refit) over 2023-07 to 2024-12: gain +6.1 MW over yesterday's value, 95% interval −2.4 to +14.9, on 537 days. This matches the frozen-by-fold result for the same days (+7.6 MW, interval −0.9 to +16.6). Neither interval excludes zero.

## Recipes not run (kept out of the grid)

- A walk-forward monthly refit, and a separate shed/no-shed classifier, are planned as a second protocol after the test run.
- No recipe in this grid uses the same-day temperature (it would not be known in advance).

## Honest limits

- 17 recipes were compared, so the winner's validation score is optimistic. The bootstrap interval does not correct for that.
- The validation window is only 537 days, and its fold-level scores vary a lot.
