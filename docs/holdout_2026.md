# Hold-out: January to July 2026

**Read this first.** These months were already scored in the earlier 2025–26 test runs (`test_results.md`). The model was not trained on them here, but the data was seen before, so this is a re-split, not a fresh holdout. The only data that has never been used is from August 2026 onward.

Setup: recipe R13 (same as before), trained only on data up to 2025-12-31, scored on 2026-01-01 to 2026-07-31 (210 days with a target). Yesterday's value is the baseline. Interval: 95% moving-block bootstrap.

| Protocol | MAE model (MW) | MAE yesterday (MW) | Gain (MW) | 95% CI | Skill | Mean predicted / actual (MW) |
|---|---|---|---|---|---|---|
| Frozen, trained to 2025-12-31 | 210.43 | 222.76 | +12.33 | [-7.3, +36.8] | +0.055 | 293.1 / 371.0 |
| Walk-forward, monthly refit | 209.77 | 222.76 | +12.99 | [-7.1, +34.9] | +0.058 | 308.1 / 371.0 |

## Month by month (walk-forward)

| Month | Days | Gain vs yesterday (MW) | Mean actual (MW) |
|---|---|---|---|
| 2026-01 | 31 | +23.8 | 139.7 |
| 2026-02 | 28 | -1.1 | 16.6 |
| 2026-03 | 31 | +2.9 | 13.4 |
| 2026-04 | 30 | -31.6 | 779.6 |
| 2026-05 | 29 | +12.0 | 141.1 |
| 2026-06 | 30 | +61.4 | 919.6 |
| 2026-07 | 31 | +22.3 | 568.7 |

## Reading

- Both versions have a positive point estimate (about +12 to +13 MW), but both intervals include zero. This is consistent with the earlier test result, not a new one.
- The model under-predicts the mean: 293 to 308 MW predicted against 371 MW actual. The largest misses are in April and June 2026, the high-shedding months.
- Monthly results are mixed: the model wins in January, March, May and July, and loses in February and April.
- Because the months are not fresh, this check cannot settle the question. It mainly shows that the earlier result holds on a slightly different window.

## Files

- `src/holdout_2026.py` produces this table.
- `data/processed/holdout_2026.json` (git-ignored) holds the raw numbers.
