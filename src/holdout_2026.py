"""Hold-out 2026-01-01 .. 2026-07-31 (training cutoff 2025-12-31).

NOTE: these days were already scored in the earlier 2025-26 test runs, so this is a
re-split of data that has been seen, not a fresh holdout. A truly fresh check needs data
after the last date in the file (2026-08-03 onward).
Same recipe (R13), same cleaning definition B, same score-set rules as before.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R13 = next(r for r in E.RECIPES if r["id"] == "R13")
HOLD = ("2025-12-31", "2026-01-01", "2026-07-31")


def summarize(df: pd.DataFrame) -> dict:
    gain, lo, hi, n = E.bootstrap_gain([df])
    em = (df.actual - df.pred).abs().mean()
    ep = (df.actual - df.persist).abs().mean()
    return {"n": int(n), "MAE_model": round(float(em), 2), "MAE_yesterday": round(float(ep), 2),
            "gain_MW": gain, "ci95": [lo, hi], "skill": round(1 - float(em / ep), 4),
            "mean_actual": round(float(df.actual.mean()), 1), "mean_pred": round(float(df.pred.mean()), 1)}


def main() -> None:
    t = E.prepare()
    frozen = E.run_recipe(t, R13, HOLD, return_frame=True)
    parts = []
    for m in pd.date_range("2026-01-01", "2026-07-01", freq="MS"):
        m_end = min(m + pd.offsets.MonthEnd(0), pd.Timestamp("2026-07-31"))
        cut = (m - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        parts.append(E.run_recipe(t, R13, (cut, m.strftime("%Y-%m-%d"), m_end.strftime("%Y-%m-%d")),
                                  return_frame=True))
    walk = pd.concat(parts).sort_index()
    out = {"frozen_train_to_2025-12-31": summarize(frozen),
           "walkforward_monthly_refit": summarize(walk),
           "monthly_walkforward": {str(k.strftime("%Y-%m")): summarize(g)
                                   for k, g in walk.groupby(walk.index.to_period("M"))}}
    (ROOT / "data/processed/holdout_2026.json").write_text(json.dumps(out, indent=2))
    frozen.to_csv(ROOT / "data/processed/holdout_2026_frozen.csv")
    walk.to_csv(ROOT / "data/processed/holdout_2026_walk.csv")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
