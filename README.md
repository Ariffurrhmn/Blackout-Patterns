# Blackout Patterns

Load shedding in Bangladesh, 2019 to 2026: cleaning a messy daily record of the national grid, and testing how well the cleaned data predicts next-day shedding.

This is a class data-mining project. The goals are to clean the data, find out which records are errors and which are real, and check whether a model trained on the cleaned data predicts shedding in 2025–2026 better than simple baselines.

## Result so far

The cleaning step works, and removes 202 of 2,428 days. The prediction step does not beat the simplest baseline. Yesterday's shedding gives an error of 104.8 MW, against 122.8 MW for the cleaned model. Full numbers are in [`docs/results.md`](docs/results.md).

## Data

Both datasets are from the Bangladesh Power Development Board (BPDB) daily generation reports, published on Mendeley Data under CC BY 4.0.

| Dataset | Used for | Coverage | Link |
|---|---|---|---|
| Hossain, Nafs & Yeaser (2025), v2 | 2019–2024 training rows (deduplicated, not smoothed) | 2019-11-21 to 2024-12-30, 1,850 rows | [doi:10.17632/x7r7wdb39k.1](https://doi.org/10.17632/x7r7wdb39k.1) |
| Extended dataset (2026) | 2025–2026 test rows (raw values) | 2019-11-21 to 2026-08-03, 2,428 rows, 45 columns | [Mendeley yp5y4thtfm](https://data.mendeley.com/datasets/yp5y4thtfm/1) |

The extended file's 2019–2024 rows are smoothed (they equal version 5 of the 2025 dataset). So training uses version 2, and the test period uses the raw extended rows. Checksums of the raw files are in [`data/MANIFEST_raw_sha256.txt`](data/MANIFEST_raw_sha256.txt).

Target: total load shedding (MW) across nine regions on each day (the sum of the `*_load` columns).

## Cleaning

Each rule flags rows; nothing is imputed. Full rules and counts are in [`docs/cleaning_summary.md`](docs/cleaning_summary.md), and every excluded day is listed in [`docs/excluded_days.md`](docs/excluded_days.md).

- **Zero maximum demand** (30 days): the report left the field blank.
- **Regional copies** (144 days): two regions have identical demand on the same day. Almost all are in 2019–2020.
- **Supply above demand** (2 days) and **residual outliers** (28 days) outside thresholds set from 2019–2024 only.
- **Weekday label mismatches** (6 days): logged, kept, because the date is trusted.
- **Missing calendar days** (20 days): left as gaps.

Thresholds come from 2019–2024 only, and the same rules are applied to 2025–2026.

## Method

`src/model.py` predicts next-day shedding from data known before the day starts: lagged shedding (1, 2 and 7 days, 7- and 28-day means), lagged supply limits, lagged maximum demand and temperature, and day of week and month. Same-day values are excluded, so there is no leakage.

Two gradient-boosting models use the same features: one trained on raw training rows, one on cleaned rows. Both are scored on the same cleaned 2025–2026 test days, against four baselines (zero, yesterday, same weekday last week, 7-day mean).

## Run it

```bash
pip install -r requirements.txt
python3 src/clean.py    # writes data/processed/ and the cleaning summary
python3 src/model.py    # writes data/processed/model_results.json and predictions
```

The raw files in `data/raw/` must be downloaded first (see the links above). They are not in this repository. Copy the two datasets into `data/raw/` with the same folder names as in `data/MANIFEST_raw_sha256.txt`.

## Repository layout

```
Blackout-Patterns/
├── README.md
├── requirements.txt
├── data/
│   ├── MANIFEST_raw_sha256.txt   Checksums and sizes of the raw files
│   ├── raw/                      Raw downloads (ignored by git)
│   └── processed/                Cleaned table and predictions (ignored by git)
├── src/
│   ├── clean.py                  Merges the sources, flags errors, writes the clean table
│   └── model.py                  Features, baselines, models and scoring
└── docs/
    ├── cleaning_summary.md       Rules, counts and source choice
    ├── excluded_days.md          Every excluded day with reasons
    └── results.md                Scores, by-year breakdown and next steps
```

## Limits

- Shedding is recorded per region, and the regional copy problem means the 2019–2020 regional split is unreliable. The model uses only the national total.
- Tree models cannot predict above the values seen in training. 2026 shedding is above every training year, so the model under-predicts 2026.
- The features do not include generation outages or fuel prices, which probably drive most of the day-to-day change.

## Status

- [x] Find, check and organise the two datasets
- [x] Cleaning rules, with a log of every excluded day
- [x] Baselines and models, scored on the same cleaned 2025–2026 days
- [ ] Train on 2022–2024 only, to test whether the 2019–2021 zero-shedding years are hurting the fit
- [ ] Linear model on lags as a stronger baseline
- [ ] Uncertainty bands for the predictions

## Source

Data: Hossain, Md Ikrama; Nafs, Tasnia; Yeaser, Sakif (2025). *Structured Dataset of Daily Electricity Demand, Generation, Load Shedding, and Supply Constraints in Bangladesh (2019–2024).* Mendeley Data V1, [doi:10.17632/x7r7wdb39k.1](https://doi.org/10.17632/x7r7wdb39k.1). The extended 2019–2026 dataset is from the Mendeley record linked above and uses BPDB reports, and it is covered by CC BY 4.0 in the same way.
