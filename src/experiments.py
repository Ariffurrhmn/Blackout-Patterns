"""Recipe search on VALIDATION folds only (2023-07 .. 2024-12). Test 2025-26 is NOT touched here.

Protocol (fixed before running):
  folds: (train_end, val_start, val_end)
    F1: 2023-06-30 | 2023-07-01..2023-12-31
    F2: 2023-12-31 | 2024-01-01..2024-06-30
    F3: 2024-06-30 | 2024-07-01..2024-12-31
  Score set (same for every recipe): days t with a recorded target, not a full-row
  duplicate of the previous day, and an observed target on t-1.
  Skill per fold = 1 - MAE_model / MAE_persistence. Recipe score = mean skill over folds.
  Cleaning variants change only training rows and feature masks, never the score set.
    raw   : training excludes missing target and full-row duplicates only.
    clean : training also excludes R2 (max demand = 0), R4 (supply > demand),
            R5 (residual outlier, thresholds fitted on rows up to the fold's train_end).
            R3 (regional copy) masks regional-load features only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clean import ROOT, REGIONS, MAXDEM, EVEPEAK, load_raw, flag_rows  # noqa: E402

FOLDS = [
    ("2023-06-30", "2023-07-01", "2023-12-31"),
    ("2023-12-31", "2024-01-01", "2024-06-30"),
    ("2024-06-30", "2024-07-01", "2024-12-31"),
]
REPORT = [MAXDEM, EVEPEAK, "Highest Generation (Generation end)", "Gas/LF limitation",
          "Coal supply Limitation", "Low water level in Kaptai lake",
          "Plants under shut down/ maintenance", "Maximum Temperature in Dhaka was"]
LOAD = [f"{r}_load" for r in REGIONS]

# Recipe grid, fixed before any run.
# kind: persist | ewma | ridge | hgb ; target: level | diff ; feats: F0 | F1 ; train: all | 2022 ; clean: clean | raw
RECIPES = [
    dict(id="R01", name="persistence (yesterday)", kind="persist"),
    dict(id="R02", name="EWMA alpha=0.2", kind="ewma", alpha=0.2),
    dict(id="R03", name="EWMA alpha=0.4", kind="ewma", alpha=0.4),
    dict(id="R04", name="EWMA alpha=0.6", kind="ewma", alpha=0.6),
    dict(id="R05", name="Ridge level F0 all clean", kind="ridge", target="level", feats="F0", train="all", clean="clean"),
    dict(id="R06", name="Ridge level F0 2022+ clean", kind="ridge", target="level", feats="F0", train="2022", clean="clean"),
    dict(id="R07", name="Ridge diff F1 2022+ clean", kind="ridge", target="diff", feats="F1", train="2022", clean="clean"),
    dict(id="R08", name="Ridge diff F1 all clean", kind="ridge", target="diff", feats="F1", train="all", clean="clean"),
    dict(id="R09", name="HGB level F0 all raw", kind="hgb", target="level", feats="F0", train="all", clean="raw"),
    dict(id="R10", name="HGB level F0 all clean", kind="hgb", target="level", feats="F0", train="all", clean="clean"),
    dict(id="R11", name="HGB level F0 2022+ clean", kind="hgb", target="level", feats="F0", train="2022", clean="clean"),
    dict(id="R12", name="HGB diff F0 all clean", kind="hgb", target="diff", feats="F0", train="all", clean="clean"),
    dict(id="R13", name="HGB diff F0 2022+ clean", kind="hgb", target="diff", feats="F0", train="2022", clean="clean"),
    dict(id="R14", name="HGB diff F1 2022+ clean", kind="hgb", target="diff", feats="F1", train="2022", clean="clean"),
    dict(id="R15", name="HGB diff F1 2022+ raw", kind="hgb", target="diff", feats="F1", train="2022", clean="raw"),
    dict(id="R16", name="HGB diff F1 all clean", kind="hgb", target="diff", feats="F1", train="all", clean="clean"),
    dict(id="R17", name="HGB level F1 2022+ clean", kind="hgb", target="level", feats="F1", train="2022", clean="clean"),
]


def prepare() -> pd.DataFrame:
    raw = load_raw()
    flagged, _ = flag_rows(raw)
    num = [c for c in raw.columns if c not in ("Date", "source") and raw[c].dtype.kind in "if"]
    prev = raw[num].shift(1)
    same = ((raw[num].fillna(-999) == prev.fillna(-999)).all(axis=1)) & prev.notna().any(axis=1)
    t = flagged.set_index("Date").sort_index().asfreq("D")
    t["dup"] = same.reindex(t.index).fillna(False).astype(bool).to_numpy()
    t["R7"] = t["target_mw"].isna()
    t["y"] = t["target_mw"]
    return t


def fold_table(t: pd.DataFrame, cutoff: str, clean: str) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Features for every day plus training mask and scoring mask for this fold."""
    cut = pd.Timestamp(cutoff)
    base_ok = ~(t["R2_max_demand_zero"] | t["R4_supply_gt_demand"] | t["R7"] | t["dup"]).astype(bool)
    fit_rows = base_ok & (t.index <= cut)
    lo, hi = t.loc[fit_rows, "national_residual"].quantile([0.005, 0.995]).tolist()
    r5 = ((t["national_residual"] < lo) | (t["national_residual"] > hi)).fillna(False).astype(bool)
    r2 = t["R2_max_demand_zero"].fillna(False).astype(bool)
    r4 = t["R4_supply_gt_demand"].fillna(False).astype(bool)
    r3 = t["R3_regional_copy"].fillna(False).astype(bool)
    r7 = t["R7"].astype(bool)
    dup = t["dup"].astype(bool)

    if clean == "clean":
        bad_report = r2 | r4 | r5
        train_ok = ~(bad_report | dup | r7)
        mask_load = r3
    else:
        bad_report = pd.Series(False, index=t.index)
        train_ok = ~(dup | r7)
        mask_load = pd.Series(False, index=t.index)

    y = t["y"]
    f = pd.DataFrame(index=t.index)
    f["y_lag1"] = y.shift(1)
    f["y_lag2"] = y.shift(2)
    f["y_lag7"] = y.shift(7)
    f["y_mean7"] = y.shift(1).rolling(7, min_periods=3).mean()
    f["y_mean28"] = y.shift(1).rolling(28, min_periods=7).mean()
    for c in REPORT:
        s = t[c].where(~bad_report)
        f[f"{c}__l1"] = s.shift(1)
    for c in LOAD:
        f[f"{c}__l1"] = t[c].where(~mask_load).shift(1)
    f["dow"] = t.index.dayofweek
    f["month"] = t.index.month
    # F1 extras, all known before day t
    gas = t["Gas/LF limitation"].where(~bad_report)
    f["d_gas"] = (gas.shift(1) - gas.shift(2))
    plants = t["Plants under shut down/ maintenance"].where(~bad_report)
    f["d_plants"] = plants.shift(1) - plants.shift(2)
    f["gap_l1"] = (t[MAXDEM].where(~bad_report) - t["Highest Generation (Generation end)"].where(~bad_report)).shift(1)
    f["max7_l1"] = y.shift(1).rolling(7, min_periods=3).max()
    count = 0
    days_since = []
    for v in y.shift(1).to_numpy():
        if np.isnan(v):
            days_since.append(np.nan)
            continue
        if v == 0:
            count = 0
        else:
            count += 1
        days_since.append(count)
    f["days_since_zero"] = days_since

    train_mask = train_ok & (t.index <= cut) & y.notna()
    score_mask = (~dup) & y.notna() & (~r7) & y.shift(1).notna()
    return f, train_mask, score_mask, (lo, hi)


F1_EXTRA = ["d_gas", "d_plants", "gap_l1", "max7_l1", "days_since_zero"]


def feature_list(kind: str) -> list[str]:
    base = ["y_lag1", "y_lag2", "y_lag7", "y_mean7", "y_mean28", "dow", "month"]
    base += [f"{c}__l1" for c in REPORT]
    if kind == "F0":
        return base
    return base + F1_EXTRA + [f"{c}__l1" for c in LOAD]


def make_model(recipe: dict):
    if recipe["kind"] == "hgb":
        return HistGradientBoostingRegressor(loss="absolute_error", max_iter=300,
                                             learning_rate=0.05, max_leaf_nodes=15, random_state=0)
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))


def run_recipe(t: pd.DataFrame, recipe: dict, fold: tuple, return_frame: bool = False):
    cut, vs, ve = fold
    vs, ve = pd.Timestamp(vs), pd.Timestamp(ve)
    y = t["y"]
    if recipe["kind"] == "persist":
        pred = y.shift(1)
        f, _, score_mask, _ = fold_table(t, cut, "raw")
    elif recipe["kind"] == "ewma":
        ew = y.shift(1).ewm(alpha=recipe["alpha"], ignore_na=True, adjust=False).mean()
        pred = ew
        _, _, score_mask, _ = fold_table(t, cut, "raw")
    else:
        clean = recipe["clean"]
        f, train_mask, score_mask, _ = fold_table(t, cut, clean)
        feats = feature_list(recipe["feats"])
        if recipe["train"] == "2022":
            train_mask = train_mask & (t.index >= pd.Timestamp("2022-01-01"))
        base = y.shift(1)
        is_diff = recipe["target"] == "diff"
        tgt = (y - base) if is_diff else y
        tr = train_mask & tgt.notna() & base.notna()
        model = make_model(recipe)
        model.fit(f.loc[tr, feats], tgt[tr])
        pred_raw = pd.Series(model.predict(f[feats]), index=f.index)
        pred = (base + pred_raw) if is_diff else pred_raw
    win = (t.index >= vs) & (t.index <= ve) & score_mask
    actual = y[win]
    p = pred[win].clip(lower=0)
    persist = y.shift(1)[win]
    if return_frame:
        return pd.DataFrame({"actual": actual, "pred": p, "persist": persist})
    mae = float(np.mean(np.abs(actual - p)))
    mae_p = float(np.mean(np.abs(actual - persist)))
    return {"n": int(win.sum()), "MAE": round(mae, 2), "MAE_persist": round(mae_p, 2),
            "skill": round(1 - mae / mae_p, 4)}


def bootstrap_gain(frames: list[pd.DataFrame], block: int = 7, B: int = 2000, seed: int = 0) -> tuple:
    """Mean MAE reduction vs persistence over pooled validation days (positive = model better),
    with a 95% moving-block bootstrap interval (blocks of `block` consecutive days)."""
    df = pd.concat(frames).sort_index()
    gain = (df["actual"] - df["persist"]).abs() - (df["actual"] - df["pred"]).abs()
    arr = gain.to_numpy()
    n = len(arr)
    rng = np.random.default_rng(seed)
    means = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, n - block, size=int(np.ceil(n / block)))
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        means[b] = arr[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return round(float(arr.mean()), 2), round(float(lo), 2), round(float(hi), 2), n


def main() -> None:
    t = prepare()
    results = {}
    for rc in RECIPES:
        per = [run_recipe(t, rc, fold) for fold in FOLDS]
        frames = [run_recipe(t, rc, fold, return_frame=True) for fold in FOLDS]
        gain, lo, hi, n = bootstrap_gain(frames)
        results[rc["id"]] = {"name": rc["name"], "folds": per,
                             "mean_skill": round(float(np.mean([p["skill"] for p in per])), 4),
                             "min_skill": round(float(np.min([p["skill"] for p in per])), 4),
                             "pooled_MAE_gain_vs_persist_MW": gain,
                             "ci95_block_bootstrap": [lo, hi], "n_pooled_days": n}
        print(rc["id"], rc["name"], [p["skill"] for p in per], results[rc["id"]]["mean_skill"],
              "gain", gain, "CI", [lo, hi], flush=True)
    out = ROOT / "data/processed/experiments_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print("written", out)


if __name__ == "__main__":
    main()
