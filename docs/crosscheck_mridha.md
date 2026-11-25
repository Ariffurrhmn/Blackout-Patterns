# Fresh-holdout search and independent cross-check

## Can we get a fresh holdout?

**No, not from any public source we can reach.** The Mridha (2026) dataset (Zenodo DOI 10.5281/zenodo.21783852, record 21783853) covers 2019-10-19 to **2026-08-01**. Our file runs to 2026-08-03, so the dataset does not extend past the period we have already scored. The only clean test left is data published after the file's last date, which does not yet exist in the sources checked.

## What the dataset is useful for

It is an independent second extraction of the same BPDB and NLDC reports, built by a separate team. It contains per-zone shedding back to 2016, a zone total, and a separate system-level field. We can use it to check our target. It is not used to choose or tune anything.

## Results (`src/crosscheck_mridha.py`, `data/processed/crosscheck_mridha.json`)

Overlap: 2019-11-21 to 2024-12-30, 1,833 days with both values.

| Comparison | Days | Exact agreement |
|---|---|---|
| Our national target vs their zone total | 1,833 | **95.9%** |
| Our national target vs sum of their zones | 1,833 | 95.9% (same, their total equals their zone sum on 100% of days) |
| Their system-level field vs their zone total | 1,835 | **70.5%** |

By year, our target matches their zone total on 100% (2019), 99.4% (2020), 99.7% (2021), 87.2% (2022), 97.2% (2023) and 95.4% (2024) of days. Zone by zone, agreement ranges from 96.3% (Mymensingh) to 99.8% (Barishal).

## What this means

- **Our target is supported.** Two independent zone-level extractions agree on about 96% of days. The disagreement is concentrated in 2022, the first year of the crisis, where agreement is 87%.
- **The source's own system field is the less reliable one.** It matches its own zone total on only 70% of days. Earlier in this project I said the two sources disagreed on about 30% of days. That was wrong: the disagreement is inside the second source, and our target agrees with its zone-level data.
- **Known limit:** the 2022 disagreements (about 13% of days) are not resolved. Neither source has been checked against a third source.

## Holdout status

The fresh holdout is still not available. Re-check when data past 2026-08-03 is published.
