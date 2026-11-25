# Data and feature plan for demand forecasting

This is a plan, not a set of results. Each group below is a new hypothesis, and each one must go through the same validation-first protocol as before (`docs/demand_round1.md`). Nothing here has been tested.

## 1. What we forecast

| Level | Source already in hand | Notes |
|---|---|---|
| **National evening-peak demand** (MW) | Yes, 2019–2026 | Main target. Served plus shed, so it includes part of the shedding. |
| **Nine zones** (Dhaka, Chattogram, Rajshahi, Mymensingh, Sylhet, Barishal, Rangpur, Cumilla, Khulna) | Yes, 2016–2026 (Mridha `area_demand_wide.csv`) | Dhaka is the largest zone. Use as a second target. |
| **Hierarchical:** zone forecasts summed, or national forecast split by zone | Planned | Compare direct national forecast with sum of zones. Keep whichever wins on validation. |

Dhaka alone is a useful test: the same weather and calendar features apply, and its weather is the most direct.

## 2. Features, grouped

Each group is added on its own, and its value is its gain over the group below it (an ablation ladder). A group that does not help is dropped, and we report that.

| Group | Variables | Status | Expected effect on demand |
|---|---|---|---|
| **A. Calendar** | Weekday, annual Fourier, Ramadan, Eid windows | Built (Hijri calendar) | Large |
| **B. Own history** | Lags, 7-day and 28-day means | Built | Large |
| **C. Weather, zone level** | Tmax, tmean, tmin, apparent temperature, precipitation, radiation (ERA5, nine zones) | Available | Large for same-day; small for lagged |
| **D. Humidity and wind** | Relative humidity, dewpoint, wind speed, cloud cover (ERA5 via Open-Meteo) | **To collect** | Moderate: humidity raises apparent temperature and cooling load |
| **E. Heat index and extremes** | Heat-index days, consecutive hot days, rain days | Derived from C and D | Moderate: cooling demand is nonlinear above ~33 °C |
| **F. Supply conditions** | Gas supply (mmcfd), available capacity, reserve margin, Kaptai level | Gas available 2019–2026; capacity and reserve 2019–2024; Kaptai and temperature from NLDC 2025+ | Affects *measured* demand (served + shed); not demand itself |
| **G. Fuel prices** | Production cost (Tk/kWh) | Available 2025–26 only | Probably small for demand; more likely to matter for supply |
| **H. Economic** | USD/BDT rate, Brent crude, LNG spot price, monthly industrial output (BBS), tariff changes (BERC) | **To collect** | Slow-moving. Expected small at daily scale, plausibly visible monthly. |
| **I. Events** | COVID lockdown periods, nationwide strikes or holidays, plant outages (station-level shortfall reasons) | Outages available (Mridha `station_daily.csv`) | Event-specific; test with flags |

### What to collect, and why

1. **Humidity, wind and cloud cover, ERA5, nine zones, 2016–2026.** This is the most valuable addition: the current weather is only temperature and rain. Source: the same Open-Meteo ERA5 archive that built the existing weather file. Needs `archive-api.open-meteo.com` allowed (or the Mridha `fetch_weather.py` run once).
2. **Monthly industrial output, Bangladesh Bureau of Statistics.** Captures real economic activity. Monthly, so only usable as a monthly lag.
3. **USD/BDT, Bangladesh Bank; Brent and JKM LNG, public daily series.** Test whether currency or fuel moves demand or only supply (measured shedding). Honest expectation: small effect on demand.
4. **Tariff change dates, BERC.** A few discrete events; use as flags.

We do not need: wind power data (negligible in Bangladesh), solar output (small share and not in the public archive), or hourly data for the first round.

## 3. How to forecast

Three layers, run in this order. Each layer is only kept if it beats the layer below on validation.

1. **Baselines:** persistence, same weekday last week, BPDB's same-morning forecast (benchmark), and the seasonal smoother (current best, D9).
2. **Structured models:** gradient boosting and linear models on the log ratio target (`y / 7-day mean`), with the groups above added one at a time.
3. **Hierarchy:** national direct versus sum of zones; keep the better one.

Uncertainty: quantile gradient boosting or split-conformal intervals (ACI, as in round 2), judged on coverage.

## 4. Cross-dimension questions, and how to test them

| Question | Test | Watch out for |
|---|---|---|
| Does temperature matter more above 33 °C? | Add a hinge term above 33 °C; compare with a linear term | Multicollinearity with season |
| Does humidity add to temperature? | Compare apparent temperature with tmax alone; then add humidity | Two correlated predictors |
| Does USD/BDT or Brent affect demand? | Monthly lag added to the group-H ladder | Spurious correlation between slow trends |
| Does oil or FX affect measured shedding? | Same ladder on the shedding target | Shedding is a separate question |
| Does Dhaka respond to weather differently from the rest of the country? | Zone-specific model vs national | Small sample for weaker zones |

Correlation alone is not evidence. Each claim needs an ablation with a gain and an interval, under the same validation protocol.

## 5. Risks

- **Test-set reuse.** Every new group is another hypothesis. The 2025–26 test has been looked at for shedding, and five days of demand have been printed. A clean demand test needs either a pre-registered holdout or data after 2026-08-03.
- **Over-planning.** The plan is long on purpose, to show the options, not to run all of them. Groups D and H are the two worth doing first.
- **Data quality.** Some sources are PDFs and some are secondary archives. Check each one against the identity and cross-source tests used so far.

## 6. Proposed order

1. Add humidity, wind and cloud cover (group D), validate on the existing folds.
2. Build the heat-index features (group E).
3. Test Dhaka as a second target.
4. Only then test the economic groups (H and G) as monthly lags.
