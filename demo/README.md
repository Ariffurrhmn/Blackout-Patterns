# Demo: from raw data to a demand model

Bangladesh daily electricity demand, 2019-11-21 to 2026-08-03. Load-shedding prediction did not beat "tomorrow = today", so the model predicts **daily demand**.

## Status

| Piece | State |
|---|---|
| `model/model_f1.json` (300 trees) and `export_check.json` | done, committed. The tree walk matches scikit-learn exactly (max difference 0.0 on 2,340 rows). |
| `index.template.html`, `make_html.py` | done, tested on a synthetic file only. |
| `notebook.ipynb` | done, ran end to end on a synthetic file only. |
| `data/daily_demo.csv` | **missing.** It needs `data/raw/`, which is not in git and was lost with the cloud container. The wind and cloud forecasts cannot be re-fetched. Copy the CSV into `demo/data/` (or restore `data/raw/` and run `python3 demo/build_demo.py`). |
| `index.html` | made by `make_html.py` once the CSV exists. Not yet built, so the real numbers have not been checked on screen. |

## Open the HTML app

```
python3 demo/make_html.py      # inlines the CSV and the model into demo/index.html
```

Then double-click `demo/index.html`. No server, no internet. Tabs: Pipeline, Data analysis, Predict (pick a day, move the cloud and wind sliders, the model re-runs in the browser), Results (MAPE and gain computed live from the CSV). A file picker at the bottom loads a replacement CSV with the same columns.

## Run the notebook (Colab or Kaggle)

1. Open `demo/notebook.ipynb` in Colab (File > Upload) or Kaggle (Create > Import notebook).
2. Upload `daily_demo.csv` when asked (Kaggle: add it as a dataset). If no file is found, the notebook tries the public GitHub copy of the CSV, which works only after the CSV has been committed to this branch (`git add -f demo/data/daily_demo.csv`, since `*.csv` is ignored).
3. Run all cells. It plots the data, retrains the same model (cutoff 2024-12-31), scores it against "yesterday" and the BPDB same-morning forecast, and writes `model_f1_retrained.json`.

`make_notebook.py` regenerates the notebook file.

## Pipeline

```
data/raw  ->  clean (flags, cleaned demand)  ->  features (lags, calendar, holidays, wind/cloud forecast)
          ->  gradient boosting, 300 trees, trained to 2024-12-31
          ->  single frozen test, 2025-01-01 to 2026-08-03 (569 days)
          ->  export trees to JSON  ->  same predictions in JavaScript
```

Model F1: `HistGradientBoostingRegressor` (300 trees, learning rate 0.05, at most 15 leaves). Target `log(demand_t / 7-day mean of lagged demand)`. Prediction `exp(output) x 7-day mean`. Features: lr1, lr7, lm7, dow, sin1, cos1, sin2, cos2, ramadan, eid_fitr_win, eid_adha_win, fc_wind_t, fc_cloud_t.

## Frozen-test result (docs/forecast_test.md)

| Method | MAPE |
|---|---|
| Yesterday | 5.48% |
| **Model F1** | **4.52%** |
| BPDB same-morning forecast (has more information) | 4.41% |

Gain over yesterday: +110 MW (95% block bootstrap +59 to +163).

## Caveats

- This is a working result, not a final or perfect model.
- Wind and cloud forecasts cover four zones only (Dhaka, Chattogram, Rajshahi, Sylhet). Lead time is about 0 to 24 hours, not strictly day-ahead.
- 2025 to 2026 was used earlier for load-shedding work and five demand days were printed, so it is no longer a clean holdout.
- In 2025 the gain is clear. In 2026 the interval includes zero.
- Cleaning has two definitions (see `docs/cleaning_summary.md`). The 202 excluded days are definition A; the model used definition B.
