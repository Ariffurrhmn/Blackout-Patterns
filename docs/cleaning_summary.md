# Cleaning summary

Run `python3 src/clean.py` to rebuild `data/processed/daily_flagged.csv` and `daily_clean.csv`.

| Item | Count |
|---|---|
| Rows in the combined table (2019-11-21 to 2026-08-03) | 2,428 |
| Rows kept after cleaning | 2,226 |
| Rows excluded | 202 |
| Calendar days with no record (left as gaps) | 20 |
| Training rows kept (2019–2024) | 1,669 of 1,851 |
| Test rows kept (2025–2026) | 557 of 577 |

## Rules

| Rule | Flags | Excludes row? | Meaning |
|---|---|---|---|
| R1 weekday label mismatch | 6 | no | Label in the file disagrees with the calendar date; date kept. |
| R2 maximum demand = 0 | 30 | yes | Blank report field recorded as zero. |
| R3 regional copy | 144 | yes | Two regions have the same positive demand on the same day. Almost all are in 2019–2020, where Rajshahi equals Khulna and Barishal equals Rangpur. |
| R4 supply above demand in a region | 2 | yes | Impossible for a single region. |
| R5 national residual outlier | 28 | yes | Max demand minus evening-peak generation minus total shedding falls outside the 0.5th–99.5th percentile of clean 2019–2024 rows (−237 to +112 MW). |
| R6 shedding above same-day max demand | 0 | yes | Not triggered after R2. |
| R7 missing target | 1 | yes | A region's load is blank (2026-05-13). |

## Source choice for 2019–2024

- `version 2.xlsx` of Hossain, Nafs & Yeaser (2025): deduplicated and raw.
- `version 4.xlsx`: imputed. Differs from version 2 in about 20,600 cells.
- `version 5.xlsx`: smoothed with a rolling median. Equal to the extended file's 2019–2024 rows, so the extended file is smoothed for those years and raw for 2025–26.
- Decision: use version 2 for 2019–2024 and the extended file for 2025–26. Both have the same target values (`*_load` is identical across these sources), so only demand and supply differ.
- Cross-check: version 2 and the extended file agree exactly on the target (`*_load`) for 2019–2024, but differ in 972 cells across 30 columns, mostly demand, supply and generation values.

See `docs/excluded_days.md` for every excluded day and its reasons.
