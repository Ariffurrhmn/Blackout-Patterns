# Validation round 2: literature-based recipes (pre-registered)

Written before any of these recipes were run. Validation folds only (2023-07 to 2024-12). The 2025–26 and Jan–Jul 2026 periods are not used for any choice in this round.

## Why these recipes

Sources were found with Consensus and are cited in `docs/literature.md`.

- **Replicate the Bangladesh demand-forecasting protocol** (Islam, Turja & Habib 2025): rolling-window features, a train-through-2022 and test-on-2023 split, and a random forest. Their target is hourly demand, not daily shedding, so this is a protocol replication, not a number replication.
- **Combinations** (M4 and later reviews: simple combinations of statistical methods are hard to beat).
- **Intermittent-demand methods** (Croston / SBA / TSB), since daily shedding is zero on many days in 2019–2021.
- **Hurdle model** (occurrence × size), the classic structure for zero-inflated demand.
- **Tweedie / Poisson loss** for targets with many zeros.
- **Adaptive conformal inference** (Gibbs & Candès 2021) for prediction intervals under distribution shift, judged on coverage and width.

## Recipes

Each recipe is scored on the same three folds, with the same score set and skill versus persistence as round 1. Conformal recipes are scored on coverage and width, not MAE.

| ID | Recipe | Definition |
|---|---|---|
| P1 | Combo: persistence + R13 | Mean of yesterday's value and the round-1 winner (R13) |
| P2 | Combo: persistence + R13 + ETS | Mean of yesterday's value, R13 and simple exponential smoothing (statsmodels, fitted on each fold's training window) |
| P3 | Croston SBA | Syntetos–Boylan bias-corrected Croston on daily shedding, smoothing 0.1, fitted through each cutoff |
| P4 | TSB | Teunter–Syntetos–Babai on daily shedding, smoothing 0.1 for demand size and probability |
| P5 | Hurdle | P(shed > 0) from a gradient-boosting classifier × expected shedding given shedding, from a regressor fitted on shed days; features as F0, clean 2022+ training |
| P6 | Tweedie-style HGB | Gradient boosting with Poisson loss on the level, F0, clean 2022+ training |
| P7 | Conformal around R13 | Split conformal intervals with adaptive conformal inference (ACI, target coverage 90%, step 0.01) around the R13 point forecast; reports coverage and mean width |
| P8 | Median combo: persistence, R13, SBA | Median of yesterday's value, R13 and Croston SBA |

## Decision rule

- Rank P1–P6 and P8 by mean skill over persistence on the three folds, with the same 7-day block bootstrap interval as round 1.
- For P7, the test is whether empirical 90% coverage on the validation folds is within 5 points of 90%. Width is reported alongside it.
- Round-1 winner R13 stays the reference. A recipe in this round is only "better" if its mean skill is higher than R13's and its interval excludes zero. Even then, the claim is a validation-only result.
- Ties are reported as ties.

## Results (validation folds only)

Reference: R13 from round 1, mean skill +0.071, gain 7.6 MW (CI −0.9 to +16.6).

| ID | Recipe | Skill F1 | Skill F2 | Skill F3 | Mean skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|---|---|---|
| P1 | Combo: persistence + R13 | +0.108 | +0.033 | +0.051 | +0.064 | +7.14 | [+2.9, +11.9] |
| P2 | Combo: persistence + R13 + SES | +0.096 | -0.005 | +0.025 | +0.039 | +3.83 | [-0.2, +8.3] |
| P8 | Median: persistence, R13, SBA | +0.134 | +0.002 | +0.058 | +0.065 | +6.94 | [+0.2, +13.8] |
| P6 | Poisson HGB on the level | +0.027 | -0.113 | -0.161 | -0.082 | -12.40 | [-27.8, +2.2] |
| P5 | Hurdle (P(shed) × size) | -0.321 | -0.282 | -0.191 | -0.265 | -31.20 | [-45.3, -17.8] |
| P4 | TSB | -0.162 | -0.465 | -0.374 | -0.334 | -44.05 | [-63.0, -26.5] |
| P3 | Croston SBA | -0.281 | -0.556 | -0.683 | -0.507 | -67.31 | [-86.5, -47.3] |

### Conformal intervals (P7)

Target coverage 90%. ACI = adaptive conformal inference around R13. Fixed = split conformal with one width from the training window. Calibration uses R13's residuals on the last 180 training days, so the starting width is set from in-sample errors, which are too small.

| Fold | Days | Coverage ACI | Coverage fixed | Mean width ACI (MW) |
|---|---|---|---|---|
| 2023-07-01..2023-12-31 | 182 | 0.967 | 0.973 | 351.1 |
| 2024-01-01..2024-06-30 | 180 | 0.861 | 0.728 | 380.6 |
| 2024-07-01..2024-12-31 | 175 | 0.897 | 0.823 | 594.4 |

## Decision under the pre-registered rule

- **No recipe beats R13 on mean skill and has an interval that excludes zero.** R13 stays the reference.
- **P1 (persistence + R13 average) and P8 (median of persistence, R13 and SBA) are the most robust.** Both have intervals that exclude zero (P1 +7.1 MW, CI +2.9 to +11.9). Their mean skill is slightly below R13's, so the rule does not select them. This is a validation-only result and is not a test result.
- **The intermittent and hurdle methods are worse than persistence.** SBA, TSB and the hurdle model all lose badly. Shedding moves in jumps, so smoothing the size and occurrence separately adds lag, and the hurdle does not help in this data.
- **Poisson gradient boosting is not better than R13** (−0.08, interval includes zero).
- **Conformal intervals:** ACI is within 5 points of the 90% target in two of three folds (86% and 90%). In the first fold it over-covers (97%). The fixed split under-covers in 2024 (73% in H1), so ACI tracks the regime shift better, which is what it is designed for. Intervals are wide, 350–600 MW.

## Not done

- No test-set run in this round. The 2025–26 and Jan–Jul 2026 periods were not used for any choice.
- The Islam, Turja & Habib protocol was not replicated as a model. Their target is hourly demand, and their paper uses forecasted temperature. The protocol is listed as a source, not a result.
- Karmakar et al. (2026) could not be read; no open-access copy.
- Mridha (2026) dataset was not checked. It may allow a fresh holdout, which is the only clean test left.
