# Demo: from raw data to a demand model

Bangladesh daily electricity demand, 2019-11-21 to 2026-08-03. Load-shedding prediction did not beat "tomorrow = today", so the model predicts **daily demand**.

## Status

The original final model (F1) used Open-Meteo weather forecasts that could not be collected again, and the raw data folder was lost. The demo was therefore **rebuilt with the F3 recipe** (same model and cutoff, but with the same-day wind and cloud from NASA POWER instead of forecasts). F3 was already tested in `docs/forecast_test.md`.

| Piece | State |
|---|---|
| Raw data | re-downloaded into `data/raw/` (gitignored). The two Mendeley files and the Zenodo files match the checksums in `data/MANIFEST_raw_sha256.txt`. The NASA POWER file was fetched again at city-centre coordinates (the originals were not recorded), so it is close but not identical. |
| `data/daily_demo.csv` | rebuilt, 2,448 rows, committed (forced past `.gitignore`) so Colab and Kaggle can read it from GitHub. |
| `model/model_f3.json` | 300 trees. The JavaScript tree walk matches scikit-learn exactly (`model/export_check.json`) and matches the CSV's `pred_mw` on all 2,448 rows. |
| `model/model_f1.json` | the earlier model, kept for reference only. Its weather-forecast inputs no longer exist. |
| `index.html`, `notebook.ipynb` | built and run on the real CSV. `index.html` opened in Chromium with no console errors; the notebook ran end to end locally. Not yet run on Colab or Kaggle. |

**Rebuild vs the original F3 run** (test days 2025-01-01 to 2026-08-03): MAPE 4.80% against 4.77% reported; persistence 5.48% and the BPDB forecast 4.41% match exactly. Gain over persistence is +59 MW against +65 MW reported.

## Open the HTML app

```
python3 demo/make_html.py      # already run once; re-run after changing the CSV. Inlines the CSV and the model into demo/index.html
```

Then double-click `demo/index.html`. No server, no internet. Tabs: Pipeline, Data analysis, Predict (pick a day, move the cloud and wind sliders, the model re-runs in the browser), Results (MAPE and gain computed live from the CSV). A file picker at the bottom loads a replacement CSV with the same columns.

## Run the notebook (Colab or Kaggle)

1. Open `demo/notebook.ipynb` in Colab (File > Upload) or Kaggle (Create > Import notebook).
2. Upload `daily_demo.csv` when asked (Kaggle: add it as a dataset). If no local file is found, the notebook downloads the CSV from this public repository; Colab's upload dialog is the last resort.
3. Run all cells. It plots the data, retrains the same model (cutoff 2024-12-31), scores it against "yesterday" and the BPDB forecast issued that morning, and writes `model_f3_retrained.json`.

`make_notebook.py` regenerates the notebook file.

## Pipeline

```
data/raw  ->  clean (flags, cleaned demand)  ->  features (lags, calendar, holidays, same-day wind and cloud)
          ->  gradient boosting, 300 trees, trained to 2024-12-31
          ->  single frozen test, 2025-01-01 to 2026-08-03 (569 days)
          ->  export trees to JSON  ->  same predictions in JavaScript
```

Model F3: `HistGradientBoostingRegressor` (300 trees, learning rate 0.05, at most 15 leaves). Target `log(demand_t / 7-day mean of lagged demand)`. Prediction `exp(output) x 7-day mean`. Features: lr1, lr7, lm7, dow, sin1, cos1, sin2, cos2, ramadan, eid_fitr_win, eid_adha_win, ra_wind_t, ra_cloud_t.

## Frozen-test result

| Method | MAPE, this rebuild | MAPE, original run |
|---|---|---|
| Yesterday | 5.48% | 5.48% |
| **Model F3 (same-day weather)** | **4.80%** | 4.77% |
| BPDB forecast issued that morning (a real forecast; F3 gets the day's actual weather) | 4.41% | 4.41% |
| Model F1 (weather forecasts, cannot be rebuilt) | n/a | 4.52% |

Gain over yesterday for this rebuild, with a 95% block bootstrap interval (`E.bootstrap_gain` from `src/experiments.py`, run on the CSV's fixed predictions): overall +60 MW (-2 to +128, includes zero), 2025 +108 MW (+35 to +173), 2026 -21 MW (-142 to +95). The original F3 run had +65 MW (+1 to +131). BPDB's gain is +129 MW.

## Caveats

- This is a working result, not a final or perfect model.
- The model uses wind and cloud as they happened on the day (four zones: Dhaka, Chattogram, Rajshahi, Sylhet). That is not known the day before, so this is not a true day-ahead forecast.
- 2025 to 2026 was used earlier for load-shedding work and five demand days were printed, so it is no longer a clean holdout.
- The model's gain over yesterday is small overall and its interval touches zero. It is clearer in 2025 and about zero in 2026.
- The notebook reads the CSV with `float_precision="round_trip"`. With pandas' default parser, tiny float differences change the retrained trees (about 47 MW average difference); with it, the retrain matches the export.
- Cleaning has two definitions (see `docs/cleaning_summary.md`). The 202 excluded days are definition A; the model used definition B.
