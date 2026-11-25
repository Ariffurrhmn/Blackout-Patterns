# Humidity and wind: pre-registered recipes (validation folds only)

Written before running. Source: NASA POWER daily (MERRA-2 based), one point per zone, national value = mean of nine zones. Variables: RH2M (relative humidity, %), WS10M (wind speed, m/s), CLOUD_AMT (cloud amount, %), T2M_MAX, and a temperature × humidity product.

Same target and score set as `docs/demand_round1.md`; same three validation folds; same gradient-boosting learner, D7 features as the base.

| ID | Recipe | Weather inputs | Question |
|---|---|---|---|
| H0 | Base (= D7) | none | reference |
| H1 | Base + lagged ERA5 temperature (= D8) | ERA5 t−1 | current best weather |
| H2 | Base + lagged NASA | RH, wind, cloud, T max (t−1) | does humidity add? |
| H3 | Base + lagged NASA + ERA5 | both (t−1) | does NASA add to ERA5? |
| H4 | Base + same-day NASA | RH, wind, cloud, T max (t) | upper bound with perfect weather |
| H5 | Base + lagged NASA + temperature × humidity | as H2 plus T max × RH (t−1) | interaction (heat and humidity together) |

Selection rule (as before): highest mean skill over persistence on the three folds, and the 95% block-bootstrap interval must exclude zero. A recipe that is only different from H0 without an interval excluding zero is reported as "no evidence."

## Results (validation folds, pooled over three folds)

| ID | Recipe | Mean MAPE | Mean skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|---|
| H0 | Base | 4.95% | +0.124 | +71 | [−5, +136] |
| H1 | + lagged ERA5 temperature | 4.94% | +0.123 | +71 | [−1, +130] |
| H2 | + lagged NASA (humidity, wind, cloud, Tmax) | 5.10% | +0.089 | +45 | [−34, +116] |
| H3 | + lagged NASA + ERA5 | 5.05% | +0.102 | +55 | [−17, +117] |
| H4 | + same-day NASA (perfect-weather stand-in) | **4.44%** | **+0.209** | **+131** | **[+53, +203]** |
| H5 | + lagged NASA + Tmax × humidity | 5.05% | +0.102 | +55 | [−20, +122] |

**Reading.** Lagged humidity and wind do not help; H2 is slightly worse than H0. Only the same-day stand-in (H4) gives an interval that excludes zero. That is an upper bound for a perfect forecast of the day's weather, not a forecast. Reanalysis values are not known in advance.

## Post-hoc ablation (diagnostic, not a pre-registered recipe)

Same-day inputs, validation folds, pooled. Run after H0–H5 to see which part of H4 does the work. This does not change the selection.

| Same-day inputs | Mean skill | Gain (MW) | 95% CI (MW) |
|---|---|---|---|
| Temperature only | +0.078 | +54 | [−22, +117] |
| Humidity only | +0.083 | +57 | [−26, +130] |
| Temperature and humidity | +0.080 | +55 | [−34, +125] |
| Temperature, humidity, wind and cloud | +0.192 | +131 | [+53, +203] |

**What this says.** Humidity on its own adds about as much as temperature on its own, and together they add no more than either one. The large gain needs wind and cloud cover as well. That combination was not tested alone, so the source of the gain is not yet pinned down. A follow-up would need its own pre-registered recipes (for example, temperature with wind and cloud, without humidity), and it would use the same validation folds.

**Conclusion so far.** Humidity is not a useful stand-alone indicator in this data. Same-day weather as a group clearly helps. Whether the group can be forecast a day ahead is the next question, and it has not been tested.

## Follow-up: wind and cloud without humidity (pre-registered before running)

Question: is the gain in the post-hoc ablation from wind and cloud cover, and does humidity add anything once they are included?

| ID | Recipe | Same-day inputs | Lagged inputs |
|---|---|---|---|
| W1 | Base + same-day temperature, wind, cloud | Tmax, wind, cloud | none |
| W2 | Base + same-day wind and cloud (no temperature) | wind, cloud | none |
| W3 | Base + lagged temperature, wind, cloud | none | Tmax, wind, cloud (t−1) |

Reference recipes already run: H0 (base), A (same-day temperature only), D (same-day temperature, humidity, wind, cloud, from the post-hoc ablation). Same selection rule and same folds.

### Results of the follow-up (validation folds, pooled)

| ID | Recipe | Mean MAPE | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|
| W1 | Same-day temperature, wind, cloud | 4.47% | +135 | [+55, +210] |
| W2 | Same-day wind and cloud only | 4.52% | +132 | [+52, +207] |
| W3 | Lagged temperature, wind, cloud | 5.17% | +51 | [−26, +117] |

Reference: H0 base 4.95%; full same-day set (temperature, humidity, wind, cloud) 4.52%.

**Reading.** Same-day wind and cloud cover, with no temperature or humidity, give the whole gain. Adding temperature or humidity changes nothing. Lagged versions of the same inputs do not reach a significant gain. So the signal is in the same-day weather regime, not in humidity and not in yesterday's weather.

**Caveats.**
- These are reanalysis values for the same day. They are an upper bound, not a forecast.
- Cloud cover and wind may be standing in for monsoon and storm days, which also change demand for other reasons. Correlation with demand is not a causal explanation.
- This is the third look at this validation design (H, ablation, W). The result is stable, but it has not been checked on a holdout.
