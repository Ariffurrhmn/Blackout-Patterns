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
