# Test results: 2025-01-01 to 2026-08-03

Recipe: R13 from `docs/experiments.md`, the validation winner. Nothing was re-selected on the test set.
Score set and cleaning are the same as validation. The R5 thresholds are fitted only on data up to each cutoff.

Gain is the reduction in MAE versus yesterday's value (MW). Positive is better. The interval is a 95% moving-block bootstrap (7-day blocks).

## Protocol A: frozen (train through 2024-12-31, predict all of 2025–26)

| Scope | Days | MAE model | MAE yesterday | Gain (MW) | 95% CI | Skill | Mean predicted / actual (MW) |
|---|---|---|---|---|---|---|---|
| All | 573 | 129.25 | 121.42 | -7.84 | [-14.9, +3.5] | -0.065 | 187.4 / 190.2 |
| 2025 | 360 | 76.42 | 61.04 | -15.38 | [-24.0, -8.2] | -0.252 | 99.0 / 67.9 |
| 2026 | 213 | 218.55 | 223.46 | +4.91 | [-10.1, +29.6] | +0.022 | 336.8 / 396.9 |

## Protocol B: walk-forward (refit at the start of each month, using data up to the day before)

| Scope | Days | MAE model | MAE yesterday | Gain (MW) | 95% CI | Skill | Mean predicted / actual (MW) |
|---|---|---|---|---|---|---|---|
| All | 573 | 115.86 | 121.42 | +5.56 | [-1.8, +14.7] | +0.046 | 164.0 / 190.2 |
| 2025 | 360 | 58.91 | 61.04 | +2.13 | [-2.7, +7.7] | +0.035 | 66.0 / 67.9 |
| 2026 | 213 | 212.09 | 223.46 | +11.37 | [-8.5, +33.4] | +0.051 | 329.6 / 396.9 |

## What this says

- **Protocol A fails.** Overall the frozen model is 7.8 MW worse than yesterday's value (CI −14.9 to +3.5, so not clearly worse). In 2025 it is clearly worse (−15.4 MW, CI −24.0 to −8.2). It predicts a mean of 99 MW against an actual 68 MW. Training on 2022–2024 learned the crisis level, and 2025 was calmer. That is a regime shift the frozen model cannot follow.
- **Protocol B is slightly better than yesterday overall** (+5.6 MW, CI −1.8 to +14.7). It is not statistically clear. The gain comes from refitting, which lets the model follow the level change. In 2025 the gain is +2.1 MW (CI −2.7 to +7.7), and in 2026 it is +11.4 MW (CI −8.5 to +33.4).
- **2026 is still under-predicted in mean.** Walk-forward predicts 330 MW on average against an actual 397 MW, and trees cannot exceed the highest level seen in training.
- **Both protocols get the shed / no-shed call about right.** Accuracy is 0.82, against 0.81 for yesterday's value.

## Honest reading

- Daily load shedding is hard to beat with the lag and report features available here. The best honest result is that a monthly-refit model matches yesterday's value and may be slightly better. The gain is not statistically clear.
- The frozen-protocol failure is the most useful finding for a class project. A model trained on one regime and tested in another loses to the simplest baseline. Refitting fixes most of it.
- The test set has now been used twice (the first run earlier in the project, and this run). Protocol B was added after seeing Protocol A, so treat its result as exploratory.

## Files

- `src/test_run.py` produces both protocols.
- `data/processed/test_results.json`, `test_frozen_predictions.csv` and `test_walkforward_predictions.csv` hold the raw outputs (git-ignored).
