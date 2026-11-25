"""Predict next-day national load shedding (MW) from data known before the day starts.

Train: 2019-11-21 .. 2024-12-31.   Test: 2025-01-01 .. 2026-08-03.
Two models, same features and same learner:
  * RAW     trained on every row as recorded (no exclusions).
  * CLEAN   trained on rows that pass src/clean.py; features that come from
            excluded days are set to NaN.
Both are scored on the SAME test rows: test days that pass the cleaning rules
(the target itself is a value we can only trust on clean days).
Baselines (on the same rows): always 0, yesterday, same weekday last week,
7-day mean.

Features for day t only use days <= t-1 (no same-day report values).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from clean import (ROOT, REGIONS, MAXDEM, EVEPEAK, flag_rows, load_raw, TRAIN_END, TEST_START)  # noqa: E402

REPORT_LAG_COLS = [MAXDEM, EVEPEAK, "Highest Generation (Generation end)",
                   "Gas/LF limitation", "Coal supply Limitation",
                   "Low water level in Kaptai lake",
                   "Plants under shut down/ maintenance", "Maximum Temperature in Dhaka was"]
SEED = 0


def build_table(flagged: pd.DataFrame, clean_mode: bool) -> pd.DataFrame:
    """Daily calendar table with target and lag-only features."""
    t = flagged.set_index("Date").sort_index()
    t = t.asfreq("D")                                    # missing calendar days -> NaN rows
    keep = ~t["exclude"].fillna(True).astype(bool) if clean_mode else pd.Series(True, index=t.index)
    y = t["target_mw"].where(t["target_mw"].notna() & keep)
    out = pd.DataFrame(index=t.index)
    out["y"] = y
    out["y_lag1"] = y.shift(1)
    out["y_lag2"] = y.shift(2)
    out["y_lag7"] = y.shift(7)
    out["y_mean7"] = y.shift(1).rolling(7, min_periods=3).mean()
    out["y_mean28"] = y.shift(1).rolling(28, min_periods=7).mean()
    for c in REPORT_LAG_COLS:
        s = t[c].where(keep)
        out[f"{c}__lag1"] = s.shift(1)
    out["dow"] = t.index.dayofweek
    out["month"] = t.index.month
    return out


FEATS_ORDER = None


def fit_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    feats = [c for c in train.columns if c != "y"]
    m = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300,
                                      learning_rate=0.05, max_leaf_nodes=15,
                                      random_state=SEED)
    m.fit(train[feats], train["y"])
    return m.predict(test[feats])


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    shed_true = y > 0
    shed_pred = p > 0.5          # MW; treat tiny predictions as no shedding
    tp = int((shed_true & shed_pred).sum())
    fp = int((~shed_true & shed_pred).sum())
    fn = int((shed_true & ~shed_pred).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec and rec and not np.isnan(prec + rec) else float("nan")
    return {"n": int(len(y)),
            "MAE_MW": round(float(mean_absolute_error(y, p)), 1),
            "RMSE_MW": round(float(np.sqrt(mean_squared_error(y, p))), 1),
            "shed_day_accuracy": round(float((shed_true == shed_pred).mean()), 3),
            "shed_day_precision": round(prec, 3) if not np.isnan(prec) else None,
            "shed_day_recall": round(rec, 3) if not np.isnan(rec) else None,
            "shed_day_F1": round(f1, 3) if not np.isnan(f1) else None,
            "mean_actual_MW": round(float(y.mean()), 1),
            "mean_pred_MW": round(float(p.mean()), 1)}


def main() -> None:
    raw = load_raw()
    flagged, thr = flag_rows(raw)
    flagged.to_csv(ROOT / "data/processed/daily_flagged.csv", index=False)

    raw_tab = build_table(flagged, clean_mode=False)
    clean_tab = build_table(flagged, clean_mode=True)

    train_end, test_start = TRAIN_END, TEST_START
    raw_train = raw_tab[(raw_tab.index <= train_end) & raw_tab["y"].notna()]
    clean_train = clean_tab[(clean_tab.index <= train_end) & clean_tab["y"].notna()]

    # Evaluation rows: clean test days that have the lags every baseline needs
    ev = clean_tab[(clean_tab.index >= test_start) & clean_tab["y"].notna()
                   & clean_tab["y_lag1"].notna() & clean_tab["y_lag7"].notna()]
    raw_pred = fit_predict(raw_train, raw_tab.loc[ev.index])
    clean_pred = fit_predict(clean_train, clean_tab.loc[ev.index])

    y = ev["y"].to_numpy()
    baselines = {
        "zero (always no shedding)": np.zeros(len(ev)),
        "yesterday": ev["y_lag1"].to_numpy(),
        "same weekday last week": ev["y_lag7"].to_numpy(),
        "7-day mean": ev["y_mean7"].fillna(ev["y_lag1"]).to_numpy(),
    }
    results = {name: metrics(y, p) for name, p in baselines.items()}
    results["ML raw-trained"] = metrics(y, raw_pred)
    results["ML clean-trained"] = metrics(y, clean_pred)

    # Split by year (2025 vs 2026)
    by_year = {}
    for yr in (2025, 2026):
        mask = ev.index.year == yr
        if mask.sum() == 0:
            continue
        by_year[str(yr)] = {
            "ML raw-trained": metrics(y[mask], raw_pred[mask]),
            "ML clean-trained": metrics(y[mask], clean_pred[mask]),
            "yesterday": metrics(y[mask], ev["y_lag1"].to_numpy()[mask]),
        }

    # Same model on the raw, uncleaned test days (shows what cleaning does to the score)
    raw_test = raw_tab[(raw_tab.index >= test_start) & raw_tab["y"].notna()]
    raw_test_pred_rawmodel = fit_predict(raw_train, raw_test)
    raw_test_pred_cleanmodel = fit_predict(clean_train, clean_tab.loc[raw_test.index])
    uncleaned = {
        "ML raw-trained, all test days": metrics(raw_test["y"].to_numpy(), raw_test_pred_rawmodel),
        "ML clean-trained, all test days": metrics(raw_test["y"].to_numpy(), raw_test_pred_cleanmodel),
    }

    out = {
        "train_rows": {"raw": int(len(raw_train)), "clean": int(len(clean_train))},
        "eval_rows": int(len(ev)),
        "thresholds": thr,
        "clean_scoring": results,
        "by_year": by_year,
        "uncleaned_test_days": uncleaned,
    }
    out_dir = ROOT / "docs"
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed/model_results.json").write_text(json.dumps(out, indent=2))
    pd.DataFrame({"date": ev.index, "actual_mw": y, "pred_raw": raw_pred,
                  "pred_clean": clean_pred, "lag1": ev["y_lag1"].to_numpy()}
                 ).to_csv(ROOT / "data/processed/predictions_2025_2026.csv", index=False)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
