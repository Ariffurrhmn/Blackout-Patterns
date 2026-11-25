# Blackout Patterns

Load shedding in Bangladesh, 2019 to 2026. A data-mining class project: clean a messy daily record of the national grid, separate recording errors from real shedding, and test how well the cleaned data predicts next-day shedding.

## Findings

1. **The data needs a serious audit.** Of 2,428 daily rows, 202 fail first-pass checks: zero recorded maximum demand (30 days), regional copies (mostly 2019–2020), supply above demand, and residual outliers. The 2019–2024 rows in the extended dataset are smoothed, so they cannot be used as training data without going back to the raw version.
2. **Yesterday's value is a strong baseline.** Daily load shedding changes in jumps, and "tomorrow equals today" is hard to beat. Across 17 recipes on validation data, nine model recipes are worse than it on average. Smoothing models (EWMA) are clearly worse.
3. **A model trained on one regime loses to that baseline.** The frozen model, trained through 2024, is 7.8 MW worse than yesterday's value on 2025–26 (interval −14.9 to +3.5). In 2025 it is clearly worse (−15.4 MW, interval −24.0 to −8.2), because it predicts the 2022–2024 crisis level for a calmer year.
4. **Refitting monthly recovers most of the gap.** The walk-forward version is 5.6 MW better than yesterday's value (interval −1.8 to +14.7). On validation data only, the same approach gives +6.1 MW (interval −2.4 to +14.9). Consistent, but not statistically clear.

Figures are in [`docs/figures/`](docs/figures/). Start with the timeline and the monthly error chart.

| Figure | Shows |
|---|---|
| [01 timeline](docs/figures/01_timeline_shedding.png) | Shedding 2019–2026, with rows excluded from training marked |
| [02 test predictions](docs/figures/02_test_predictions.png) | 2025–26 actual, yesterday's value, frozen and walk-forward models |
| [03 monthly error](docs/figures/03_monthly_mae.png) | Monthly error of the three methods; shows the 2025 failure and the recovery |
| [04 cleaning flags](docs/figures/04_cleaning_flags.png) | Counts of each error type in the training window |

## Data

Both datasets are from the Bangladesh Power Development Board (BPDB) daily generation reports, published on Mendeley Data under CC BY 4.0.

| Dataset | Used for | Coverage | Link |
|---|---|---|---|
| Hossain, Nafs & Yeaser (2025), v2 | 2019–2024 training rows (deduplicated, not smoothed) | 2019-11-21 to 2024-12-30, 1,850 rows | [doi:10.17632/x7r7wdb39k.1](https://doi.org/10.17632/x7r7wdb39k.1) |
| Extended dataset (2026) | 2024-12-31 to 2026-08-03 rows (test period is 2025–26) | 2019-11-21 to 2026-08-03, 2,428 rows, 45 columns | [Mendeley yp5y4thtfm](https://data.mendeley.com/datasets/yp5y4thtfm/1) |

Target cross-check: an independent zone-level extraction (Mridha 2026, Zenodo 10.5281/zenodo.21783852) agrees with our national target on 96% of days 2019–2024; see [`docs/crosscheck_mridha.md`](docs/crosscheck_mridha.md).

The extended file's 2019–2024 rows are smoothed (they equal version 5 of the 2025 dataset), so training uses version 2 instead. Checksums of the raw files are in [`data/MANIFEST_raw_sha256.txt`](data/MANIFEST_raw_sha256.txt).

Target: total load shedding (MW) across nine regions on each day (the sum of the `*_load` columns).

## Cleaning

Two cleaning definitions exist, and [`docs/cleaning_summary.md`](docs/cleaning_summary.md) explains the difference. The model results use definition B (`src/experiments.py`): R2, R4 and R5 exclude training rows, R3 masks regional features, and R5 bounds are fitted up to each cutoff. The 202-day list in [`docs/excluded_days.md`](docs/excluded_days.md) uses the first-pass definition A (`src/clean.py`).

Nothing is imputed. Calendar days with no record (20 days) are left as gaps.

## Method

- **Target:** next-day national shedding (MW).
- **Features:** lagged shedding (1, 2 and 7 days, 7- and 28-day means), lagged supply limits, maximum demand and temperature, day of week and month. Nothing from the same day is used.
- **Model:** gradient boosting predicting the change from yesterday (the best validation recipe, R13), trained on 2022 onward with clean rows.
- **Scoring:** same test days for every method, against yesterday's value. Intervals use a moving-block bootstrap (7-day blocks).
- **Protocols:** frozen (train through 2024) and walk-forward (refit monthly). The walk-forward version was added after the frozen result, so it is exploratory.

Full recipe grid and validation results: [`docs/experiments.md`](docs/experiments.md). Test results: [`docs/test_results.md`](docs/test_results.md). The first-pass results, now superseded, are in [`docs/results.md`](docs/results.md).

## Run it

```bash
pip install -r requirements.txt
python3 src/clean.py          # definition A: first-pass audit and excluded-days list
python3 src/experiments.py    # validation grid (uses only 2019–2024)
python3 src/test_run.py       # the single test run (frozen and walk-forward)
python3 src/figures.py        # figures from saved predictions
```

The raw files in `data/raw/` must be downloaded first. They are not in this repository. Copy the two datasets into `data/raw/` with the folder names listed in `data/MANIFEST_raw_sha256.txt`.

## Limits

- The test period has been used twice. Any further modelling would need a fresh holdout, such as data published after August 2026.
- Tree models predict the change from yesterday, so they can go above the training maximum, but in 2026 they learned to pull back after high-shedding days.
- Shedding is recorded per region, but the 2019–2020 regional split is unreliable (copied values). The models use only the national total.
- The features do not include generation outages or fuel prices, which probably drive most of the day-to-day change.
- The 17-recipe search means the validation winner is optimistic.

## Repository layout

```
Blackout-Patterns/
├── README.md
├── requirements.txt
├── data/
│   ├── MANIFEST_raw_sha256.txt   Checksums and sizes of the raw files
│   ├── raw/                      Raw downloads (ignored by git)
│   └── processed/                Derived tables and predictions (ignored by git)
├── src/
│   ├── clean.py                  Definition A: flags errors, writes the first-pass table
│   ├── experiments.py            Definition B: validation-only recipe search
│   ├── test_run.py               The single test run (frozen and walk-forward)
│   └── figures.py                Figures from saved predictions
└── docs/
    ├── cleaning_summary.md       Both cleaning definitions, rules and counts
    ├── excluded_days.md          Excluded days under definition A
    ├── experiments.md            Recipe grid, validation results, confirmatory check
    ├── test_results.md           Final test results and interpretation
    ├── results.md                First pass (superseded)
    └── figures/                  Four PNG figures
```

## Status

- [x] Find, check and organise the two datasets
- [x] Cleaning rules, with a log of every excluded day
- [x] Validation-only recipe search (17 recipes)
- [x] Single test run, frozen and walk-forward
- [x] Figures and findings
- [x] Independent cross-check of the shedding target (96% agreement, see `docs/crosscheck_mridha.md`)
- [ ] Fresh holdout, when data after 3 August 2026 is published (none found yet)

## Source

Hossain, Md Ikrama; Nafs, Tasnia; Yeaser, Sakif (2025). *Structured Dataset of Daily Electricity Demand, Generation, Load Shedding, and Supply Constraints in Bangladesh (2019–2024).* Mendeley Data V1, [doi:10.17632/x7r7wdb39k.1](https://doi.org/10.17632/x7r7wdb39k.1). The extended 2019–2026 dataset is [Mendeley yp5y4thtfm](https://data.mendeley.com/datasets/yp5y4thtfm/1). Both are CC BY 4.0 and use BPDB daily reports.
