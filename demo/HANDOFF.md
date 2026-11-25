# Handoff: demo for the teacher (continue on the local machine)

Branch: `claude/hopeful-ramanujan-uxbrjq`. Do not open a pull request unless asked.

## Goal (user's words, short)
A demo to show a teacher: a pipeline from raw data to the final model; a local HTML app that
reads a CSV dataset (data analysis); a notebook that runs on Colab or Kaggle with the same data
and trains the model; and the model ported into the same HTML so predictions show visually.

## Project state (all pushed)
- Bangladesh electricity, daily, 2019-11-21 to 2026-08-03. Load-shedding prediction did not beat
  "tomorrow = today", so the target is daily demand.
- Read `docs/cleaning_summary.md` first (definitions A and B). Validation: `docs/demand_round1.md`,
  `docs/demand_validation.md`, `docs/forecast_round1.md`. Single frozen test: `docs/forecast_test.md`.
- Final model F1: HistGradientBoostingRegressor (300 trees, lr 0.05, max 15 leaves), target
  log(demand_t / 7-day mean of lagged demand), trained through 2024-12-31, 13 features:
  lr1, lr7, lm7, dow, sin1, cos1, sin2, cos2, ramadan, eid_fitr_win, eid_adha_win, fc_wind_t, fc_cloud_t.
  Prediction = exp(output) * m7.
- Frozen test (2025-01-01 to 2026-08-03, 569 days): F1 MAPE 4.52%, persistence 5.48%, BPDB same-morning
  forecast 4.41%. Gain over persistence +110 MW (95% block bootstrap +59 to +163); in 2026 the interval
  includes zero.
- Caveats to print on the page: wind/cloud forecasts cover four zones only (Dhaka, Chattogram, Rajshahi,
  Sylhet); lead time about 0-24 h, not strictly day-ahead; 2025-26 was used earlier for shedding and five
  demand days were printed, so it is no longer a clean holdout. Never call the model final or perfect.
  Do not run any new recipe or tuning on 2025-26.

## What exists in `demo/`
- `build_demo.py`: builds `demo/data/daily_demo.csv` (2,448 rows) and `demo/model/model_f1.json`
  (300 trees; node fields v, f, t, l, r, leaf, mgl) plus `export_check.json`.
- `model/model_f1.json`, `model/export_check.json`: committed. Check passed: tree walk matches sklearn
  exactly (max diff 0.0 on 2,340 rows).

## What is missing
- `demo/data/daily_demo.csv` is NOT in git (`*.csv` is gitignored) and `data/raw/` is gitignored too.
  Cloud container lost them. Regenerate locally: `python3 demo/build_demo.py` from the repo root
  (needs `data/raw/`, checksums in `data/MANIFEST_raw_sha256.txt`). If raw data is gone, the Open-Meteo
  forecasts cannot be re-fetched (quota, collection frozen), so ask the user for the CSV instead.
- Commit the CSV with `git add -f demo/data/daily_demo.csv` so Colab/Kaggle can use a raw GitHub URL.
- Columns: date, split (train/test), demand_mw, demand_yesterday_mw, bpdb_forecast_mw, shed_mw,
  quality_flag, cloud_reanalysis_pct, wind_reanalysis_ms, tmax_c_national, rain_mm_national, m7_mw,
  the 13 features, pred_f1_mw.

## To build
1. `demo/index.html`: single self-contained file, works by double-click (no server, no CDN, no fetch of
   local files). Embed CSV and model JSON as JS constants; also a file input to load a replacement CSV.
   Hand-written SVG charts. Tabs:
   - Pipeline: step cards with real counts (2,428 rows, 202 excluded days with reasons, 13 features,
     300 trees, 569 test days).
   - Data analysis: demand timeline (7-day average), shedding timeline, cleaning-flag counts, demand vs
     cloud scatter, sortable dataset preview.
   - Predict: date picker over the test period; feature values; JS tree-walk prediction; actual,
     yesterday, BPDB forecast; sliders for forecast cloud and wind that re-run the model; predicted vs
     actual chart.
   - Results: live metrics from the CSV (MAPE, MAE, gain over persistence, by year) with caveats.
2. `demo/notebook.ipynb`: load CSV (upload or raw GitHub URL), EDA, train the same model and cutoff,
   evaluate vs persistence and BPDB, write the model JSON. Must run on Colab/Kaggle. Execute locally
   with nbclient (needs nbformat, nbclient, ipykernel).
3. `demo/README.md`: how to open the HTML, run the notebook, one-diagram pipeline, caveats.
4. Verify index.html with Playwright Chromium: no console errors, screenshot every tab at
   deviceScaleFactor 2, look at them.
5. Commit in logical steps and push. Commit messages carry no model name.

## Rules
- Do not download new data unless the user asks. Open-Meteo has a daily quota; do not retry it.
- Keep the final summary in plain language.
- Earlier plan: consult the advisor (Opus) once before fixing the HTML architecture and once before
  declaring done, if that tool is available.
