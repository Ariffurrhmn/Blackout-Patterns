# Test run: day-ahead wind and cloud forecast (frozen recipes)

Run once. Training through 2024-12-31; test 2025-01-01 to 2026-08-03 (569 days with a demand value). Recipes frozen from `docs/forecast_round1.md`. Built on 4 of 9 zones (Dhaka, Chattogram, Rajshahi, Sylhet), as recorded there.

**Disclosure.** The 2025–26 period was already used for shedding, and five days of demand were printed earlier. Demand has not been scored on it until this run.

| Recipe | MAPE | Skill vs yesterday | Gain (MW) | 95% CI (MW) |
|---|---|---|---|---|
| Persistence (yesterday) | 5.48% | 0 | 0 | — |
| F0 base | 5.14% | +0.013 | +9 | [−50, +73] |
| **F1 base + day-ahead forecast wind and cloud (selected)** | **4.52%** | **+0.153** | **+110** | **[+59, +163]** |
| F3 base + same-day reanalysis (upper bound) | 4.77% | +0.090 | +65 | [+1, +131] |
| BPDB same-morning forecast (context, has more information) | 4.41% | +0.180 | +129 | [+71, +182] |

## By year

| Recipe | 2025 MAPE | 2025 gain (MW) | 2026 MAPE | 2026 gain (MW) |
|---|---|---|---|---|
| F0 base | 4.62% | +29 | 6.01% | −25 |
| F1 forecast | 3.88% | +140 | 5.59% | +59 (CI −38 to +147) |
| F3 reanalysis | 4.08% | +110 | 5.92% | −11 |
| BPDB | 4.19% | +107 | 4.77% | +167 |

## Reading

- The pre-registered recipe F1 beats persistence on the test period, and its interval excludes zero. This is the answer to the question.
- In 2025 the gain is large and clear. In 2026 the point estimate is positive, but the interval includes zero.
- BPDB's same-morning forecast is still the strongest, and it has more information than our day-ahead model. F1 comes within 0.1 percentage points of it on the test period.
- **Anomaly.** F3, the same-day reanalysis version, scored worse than F1 on the test period. It should be at least as good, because it uses the actual weather. The likely reason is that the forecast inputs are smoother and less noisy than the reanalysis, which the model may handle better; this was not tested. The upper bound on validation therefore isn't a strict ceiling. We should not rely on F3 as a bound.
- **Caveats** from the protocol still apply: four zones, lead time of roughly 0–24 hours, and the test period has been used for other targets before.
