"""Figures for the write-up. Reads saved predictions; no refitting, no new scoring."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

OUT = ROOT / "docs/figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
COL = {"actual": "#9aa5a0", "persist": "#7f8c86", "frozen": "#c92a3a", "walk": "#0a6b4f", "flag": "#c92a3a"}


def fig_timeline(t: pd.DataFrame) -> None:
    f, train_mask, _, (lo, hi) = E.fold_table(t, "2024-12-31", "clean")
    y = t["y"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(y.index, y.rolling(7, min_periods=3).mean(), color="#0a6b4f", lw=1.4, label="7-day average shedding")
    ax.axvspan(pd.Timestamp("2025-01-01"), y.index.max(), color="#e8efeb", zorder=0, label="test period (2025–26)")
    ex = y.notna() & ~train_mask & (y.index <= pd.Timestamp("2024-12-31"))
    ax.scatter(y.index[ex], y[ex], s=12, color=COL["flag"], zorder=3,
               label="excluded from training (2019–24 rules)")
    ax.set_ylabel("MW shed per day")
    ax.set_title("National daily load shedding, 2019–2026")
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_timeline_shedding.png", dpi=150)
    plt.close(fig)


def fig_test(frozen: pd.DataFrame, walk: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(walk.index, walk.actual.rolling(7, min_periods=3).mean(), color="#1f2a26", lw=1.6,
            label="actual (7-day average)")
    ax.plot(walk.index, walk.persist.rolling(7, min_periods=3).mean(), color=COL["persist"], lw=1.1,
            ls="--", label="yesterday's value (7-day average)")
    ax.plot(frozen.index, frozen.pred.rolling(7, min_periods=3).mean(), color=COL["frozen"], lw=1.2,
            label="model, frozen (trained to 2024)")
    ax.plot(walk.index, walk.pred.rolling(7, min_periods=3).mean(), color=COL["walk"], lw=1.2,
            label="model, walk-forward (monthly refit)")
    ax.set_ylabel("MW shed per day")
    ax.set_title("Test period 2025–26: actual, persistence and both model versions (7-day averages)")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "02_test_predictions.png", dpi=150)
    plt.close(fig)


def fig_monthly(frozen: pd.DataFrame, walk: pd.DataFrame) -> None:
    def mae(df, col):
        return (df.actual - df[col]).abs().groupby(df.index.to_period("M")).mean()
    m = pd.DataFrame({"yesterday": mae(walk, "persist"), "frozen": mae(frozen, "pred"),
                      "walk-forward": mae(walk, "pred")})
    x = np.arange(len(m))
    fig, ax = plt.subplots(figsize=(11, 4))
    w = 0.28
    ax.bar(x - w, m["yesterday"], w, color=COL["persist"], label="yesterday's value")
    ax.bar(x, m["frozen"], w, color=COL["frozen"], label="model, frozen")
    ax.bar(x + w, m["walk-forward"], w, color=COL["walk"], label="model, walk-forward")
    ax.set_xticks(x)
    ax.set_xticklabels([str(p) for p in m.index], rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("mean absolute error (MW)")
    ax.set_title("Monthly error on the test period")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "03_monthly_mae.png", dpi=150)
    plt.close(fig)


def fig_excluded(t: pd.DataFrame) -> None:
    _, train_mask, _, _ = E.fold_table(t, "2024-12-31", "clean")
    w = (t.index <= pd.Timestamp("2024-12-31")) & t["y"].notna()
    counts = {
        "max demand = 0 (R2)": int((w & t["R2_max_demand_zero"].fillna(False).astype(bool)).sum()),
        "supply > demand (R4)": int((w & t["R4_supply_gt_demand"].fillna(False).astype(bool)).sum()),
        "residual outlier (R5)": int((w & ((t.national_residual < -235.8) | (t.national_residual > 112.7))).sum()),
        "regional copy (R3, kept)": int((w & t["R3_regional_copy"].fillna(False).astype(bool)).sum()),
    }
    fig, ax = plt.subplots(figsize=(7, 3.2))
    labels, vals = list(counts.keys()), list(counts.values())
    colors = [COL["flag"]] * 3 + [COL["persist"]]
    ax.barh(labels, vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(v + 1, i, str(v), va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("days with a recorded target, 2019–2024 (reasons can overlap)")
    ax.set_title("Cleaning flags in the training window")
    fig.tight_layout()
    fig.savefig(OUT / "04_cleaning_flags.png", dpi=150)
    plt.close(fig)


def main() -> None:
    t = E.prepare()
    frozen = pd.read_csv(ROOT / "data/processed/test_frozen_predictions.csv", index_col=0, parse_dates=True)
    walk = pd.read_csv(ROOT / "data/processed/test_walkforward_predictions.csv", index_col=0, parse_dates=True)
    fig_timeline(t)
    fig_test(frozen, walk)
    fig_monthly(frozen, walk)
    fig_excluded(t)
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
