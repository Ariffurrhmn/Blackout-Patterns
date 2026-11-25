"""Build one cleaned daily table of Bangladesh load shedding (BPDB daily reports).

Sources (see data/MANIFEST_raw_sha256.txt):
  * 2019-11-21 .. 2024-12-30  -> version 2.xlsx of Hossain, Nafs & Yeaser (2025),
    Mendeley x7r7wdb39k. Deduplicated but NOT imputed or smoothed.
    (Version 4 is imputed and version 5 is smoothed; the extended file's
    2019-2024 rows equal version 5, so they are not used for training.)
  * 2025-01-01 .. 2026-08-03  -> extended file, Mendeley yp5y4thtfm (raw values).

Cleaning rules. Every rule flags rows; nothing is imputed.
  R1  weekday recomputed from Date; mismatches logged (Date is trusted).
  R2  Max. demand at evening peak == 0 is a missing value, not a reading.
  R3  Two regions with identical (positive) demand on the same day = regional copy.
  R4  Any region with supply > demand.
  R5  National residual |max_demand - evening_peak_gen - total_shed| above the
      0.5th / 99.5th percentile of 2019-2024 rows that pass R2-R4.
  R6  Total shedding above the same-day evening max demand.
  R7  Missing target (any region's load missing).
  Calendar dates with no record are left as gaps (no target imputation).

Thresholds for R5 are estimated on 2019-2024 only and then applied to 2025-2026.
Holiday columns are dropped (2025-26 entries are almost all "No Holiday").
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_V2 = ROOT / "data/raw/bpdb_ds1_mendeley_x7r7wdb39k/version 2/version 2.xlsx"
RAW_EXT = ROOT / "data/raw/bpdb_ds2_mendeley_yp5y4thtfm/Bangladesh_Electricity_Dataset_2019_2026.csv"
OUT_DIR = ROOT / "data/processed"
DOC_DIR = ROOT / "docs"

TRAIN_END = pd.Timestamp("2024-12-31")  # 2019-2024 inclusive; v2 ends 12-30, extension starts 12-31
TEST_START = pd.Timestamp("2025-01-01")
REGIONS = ["Dhaka", "Chattogram", "Rajshahi", "Mymensingh", "Sylhet",
           "Barishal", "Rangpur", "Cumilla", "Khulna"]
MAXDEM = "Max. Demand at eve. peak (Generation end)"
EVEPEAK = "Evening-peak Generation (Generation end)"
HOLIDAY_COLS = ["Holiday name", "Holiday_cat", "Year", "Month"]


def load_raw() -> pd.DataFrame:
    v2 = pd.read_excel(RAW_V2)
    v2["Date"] = pd.to_datetime(v2["Date"].astype(str), format="%d.%m.%y")
    ext = pd.read_csv(RAW_EXT, parse_dates=["Date"])
    ext = ext[ext["Date"] > pd.Timestamp("2024-12-30")]
    base_cols = [c for c in v2.columns if c not in HOLIDAY_COLS]
    df = pd.concat([v2[base_cols], ext[base_cols]], ignore_index=True)
    df["source"] = np.where(df["Date"] <= pd.Timestamp("2024-12-30"), "v2_2019_2024", "extended_2025_2026")
    if df["Date"].duplicated().any():
        raise ValueError("duplicate dates after merge")
    return df.sort_values("Date").reset_index(drop=True)


def flag_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    load_cols = [f"{r}_load" for r in REGIONS]
    dem_cols = [f"{r}_demand" for r in REGIONS]
    sup_cols = [f"{r}_supply" for r in REGIONS]

    df["target_mw"] = df[load_cols].sum(axis=1, min_count=len(load_cols))
    df["R7_missing_target"] = df["target_mw"].isna()

    # R1 weekday
    df["weekday"] = df["Date"].dt.day_name()
    df["R1_weekday_label_mismatch"] = df["Day of the week"].astype(str) != df["weekday"]

    # R2 zero max demand = missing
    df["R2_max_demand_zero"] = df[MAXDEM].fillna(-1) == 0

    # R3 regional copy: two regions with identical positive demand
    def has_copy(row):
        vals = [row[c] for c in dem_cols if pd.notna(row[c]) and row[c] > 0]
        return len(vals) != len(set(vals))
    df["R3_regional_copy"] = df.apply(has_copy, axis=1)

    # R4 supply above demand in any region
    df["R4_supply_gt_demand"] = (df[sup_cols].values > df[dem_cols].values).any(axis=1)

    # residual used by R5 (only meaningful where R2 is not triggered)
    df["national_residual"] = df[MAXDEM] - df[EVEPEAK] - df["target_mw"]

    base_ok = ~(df["R2_max_demand_zero"] | df["R3_regional_copy"] | df["R4_supply_gt_demand"]
                | df["R7_missing_target"])
    train_mask = base_ok & (df["Date"] <= TRAIN_END)
    lo, hi = df.loc[train_mask, "national_residual"].quantile([0.005, 0.995]).tolist()
    df["R5_residual_outlier"] = (df["national_residual"] < lo) | (df["national_residual"] > hi)
    df.loc[df["R2_max_demand_zero"] | df["R7_missing_target"], "R5_residual_outlier"] = False

    # R6 shed above same-day max demand
    df["R6_shed_gt_max_demand"] = (df["target_mw"] > df[MAXDEM]) & ~df["R2_max_demand_zero"]

    flag_cols = [c for c in df.columns if c.startswith("R") and c[1].isdigit()]
    # R1 is logged only; every other flag removes the row from training and scoring
    excl_cols = [c for c in flag_cols if c != "R1_weekday_label_mismatch"]
    df["exclude"] = df[excl_cols].any(axis=1)
    df["reasons"] = df[flag_cols].apply(
        lambda r: ";".join(c for c in flag_cols if r[c]), axis=1)
    thresholds = {"R5_residual_lo": float(lo), "R5_residual_hi": float(hi),
                  "R5_fit_rows": int(train_mask.sum())}
    return df, thresholds


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    flagged, thr = flag_rows(raw)
    flagged.to_csv(OUT_DIR / "daily_flagged.csv", index=False)
    clean = flagged[~flagged["exclude"]].copy()
    clean.to_csv(OUT_DIR / "daily_clean.csv", index=False)

    flag_cols = [c for c in flagged.columns if c.startswith("R") and c[1].isdigit()]
    summary = {
        "rows_in": int(len(flagged)),
        "rows_clean": int(len(clean)),
        "rows_excluded": int(flagged["exclude"].sum()),
        "calendar_days_missing": int(len(pd.date_range(flagged.Date.min(), flagged.Date.max())
                                         .difference(flagged.Date))),
        "flag_counts": {c: int(flagged[c].sum()) for c in flag_cols},
        "thresholds": thr,
        "by_period": {
            "train_2019_2024": {"in": int((flagged.Date <= TRAIN_END).sum()),
                                "clean": int(((flagged.Date <= TRAIN_END) & ~flagged.exclude).sum())},
            "test_2025_2026": {"in": int((flagged.Date >= TEST_START).sum()),
                               "clean": int(((flagged.Date >= TEST_START) & ~flagged.exclude).sum())},
        },
    }
    (OUT_DIR / "cleaning_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
