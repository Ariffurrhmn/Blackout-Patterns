# Demand validation round 1 (validation folds only)

Protocol and recipes: `docs/demand_round1.md`. Folds: train through 2023-06-30, 2023-12-31 and 2024-06-30; validate on the following six months. Score set: days with demand, excluding R2 and R7. Skill is 1 − MAE/MAE(persistence). Gain is in MW, with a 95% moving-block bootstrap.

| ID | Recipe | Mean MAPE | Skill F1 | Skill F2 | Skill F3 | Mean skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|---|---|---|---|
| D1 | Persistence (yesterday) | 5.84% | +0.000 | +0.000 | +0.000 | +0.000 | +0 | [+0, +0] |
| D2 | Same weekday last week | 9.20% | -0.502 | -0.852 | -0.632 | -0.662 | -469 | [-642, -298] |
| D3 | BPDB same-morning forecast (benchmark) | 4.28% | +0.218 | +0.287 | +0.267 | +0.260 | +178 | [+110, +256] |
| D4 | Ridge, no weather | 5.99% | -0.007 | -0.096 | -0.051 | -0.051 | -38 | [-100, +11] |
| D5 | Ridge, lagged weather | 5.93% | +0.022 | -0.103 | -0.041 | -0.041 | -33 | [-96, +18] |
| D6 | Ridge, same-day weather (stand-in) | 5.21% | +0.139 | -0.009 | +0.080 | +0.070 | +41 | [-34, +113] |
| D7 | Gradient boosting, no weather | 4.95% | +0.223 | -0.024 | +0.173 | +0.124 | +71 | [-5, +136] |
| D8 | Gradient boosting, lagged weather | 4.94% | +0.204 | -0.011 | +0.175 | +0.122 | +71 | [-1, +130] |
| D9 | Seasonal smoother (weekly), no weather | 4.99% | +0.243 | +0.059 | +0.133 | +0.145 | +93 | [+44, +142] |

## Reading

- **Demand is more predictable than shedding, as expected.** Persistence has MAPE 5.8%, and the best day-ahead recipe has 5.0%.
- **BPDB's same-morning forecast is the bar.** At 4.3% MAPE it beats our best day-ahead recipe by about 0.7 points. It uses same-day information we do not have, so this is not a like-for-like comparison, but it is the number to report.
- **The best recipe is the simplest seasonal smoother** (D9, a weekly-seasonal exponential smoother implemented here, parameters picked on training data). Its gain over persistence is +93 MW, with an interval of +44 to +142 MW, so it excludes zero on validation.
- **Gradient boosting is close** (D7, +0.12), but its interval includes zero.
- **Linear ridge is worse than persistence** (D4, −0.05). A linear model on these features does not capture the weekly and annual pattern well.
- **Lagged weather adds nothing** (D5 ≈ D4, D8 ≈ D7). Yesterday's temperature does not help predict today's peak once the calendar is in.
- **Same-day weather helps a linear model:** D6 is +0.06 against D4's −0.05, about +0.11 skill from knowing today's temperature. That is an upper bound for what a weather forecast could add, not a forecast.

## Deviations from the pre-registered list

- The advisor suggested a mean of several models. It was not in the protocol I wrote, so it is not in this table. If added, it must be labelled exploratory.
- Holt-Winters is my own one-step weekly smoother, not statsmodels. It is labelled as D9 in the protocol.

## Status

No test-set run yet. The test period (2025-01-01 to 2026-08-03) has not been scored for demand. Five days of 2025-06 demand were printed during the identity check, and that is disclosed in the protocol.
