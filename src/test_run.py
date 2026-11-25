"""Single test run of the validation winner (R13) on 2025-01-01 .. 2026-08-03.

Protocol A (frozen): train through 2024-12-31 once, predict all of 2025-26.
Protocol B (walk-forward): refit at the start of each month using data up to the day before it.
Only the validation winner is run here; nothing is re-selected on the test set.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

RECIPE = next(r for r in E.RECIPES if r["id"] == "R13")
TEST = ("2024-12-31", "2025-01-01", "2026-08-03")


def summarize(df: pd.DataFrame) -> dict:
    err_m = (df.actual - df.pred).abs()
    err_p = (df.actual - df.persist).abs()
    gain, lo, hi, n = E.bootstrap_gain([df])
    return {"n": int(len(df)),
            "MAE_model": round(float(err_m.mean()), 2),
            "MAE_persist": round(float(err_p.mean()), 2),
            "gain_vs_persist_MW": gain, "ci95": [lo, hi],
            "skill": round(1 - float(err_m.mean()) / float(err_p.mean()), 4),
            "mean_actual": round(float(df.actual.mean()), 1),
            "mean_pred": round(float(df.pred.mean()), 1),
            "shed_day_accuracy_model": round(float(((df.actual > 0) == (df.pred > 0.5)).mean()), 3),
            "shed_day_accuracy_persist": round(float(((df.actual > 0) == (df.persist > 0.5)).mean()), 3)}


def main() -> None:
    t = E.prepare()
    frame_a = E.run_recipe(t, RECIPE, TEST, return_frame=True)
    out = {"protocol_A_frozen": {"all": summarize(frame_a)}}
    for yr in (2025, 2026):
        sub = frame_a[frame_a.index.year == yr]
        out["protocol_A_frozen"][str(yr)] = summarize(sub)

    months = pd.date_range("2025-01-01", "2026-08-01", freq="MS")
    parts = []
    for m in months:
        m_end = (m + pd.offsets.MonthEnd(0))
        if m_end > pd.Timestamp(TEST[2]):
            m_end = pd.Timestamp(TEST[2])
        cutoff = (m - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        parts.append(E.run_recipe(t, RECIPE, (cutoff, m.strftime("%Y-%m-%d"), m_end.strftime("%Y-%m-%d")),
                                  return_frame=True))
    frame_b = pd.concat(parts).sort_index()
    out["protocol_B_walkforward"] = {"all": summarize(frame_b)}
    for yr in (2025, 2026):
        sub = frame_b[frame_b.index.year == yr]
        out["protocol_B_walkforward"][str(yr)] = summarize(sub)

    frame_a.to_csv(ROOT_OUT / "test_frozen_predictions.csv")
    frame_b.to_csv(ROOT_OUT / "test_walkforward_predictions.csv")
    (ROOT_OUT / "test_results.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))


ROOT_OUT = Path(__file__).resolve().parents[1] / "data/processed"

if __name__ == "__main__":
    main()
