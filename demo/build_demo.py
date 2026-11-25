"""Build the demo: dataset CSV, exported model JSON, and a check that the exported model reproduces
the Python predictions. Run from the project root:  python3 demo/build_demo.py

Pipeline (each step is a script in src/):
  raw files (data/raw) -> clean.py / experiments.py (flags, cleaned target)
  -> demand.py (lag-only features, holidays, weather) -> forecast_round1.py (day-ahead wind and cloud)
  -> train gradient boosting on 2019-2024 -> export trees -> evaluate on 2025-01 to 2026-08.
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import demand as Dm  # noqa: E402
import experiments as E  # noqa: E402
import forecast_round1 as FR  # noqa: E402

DEMO = ROOT / "demo"
TRAIN_END = pd.Timestamp("2024-12-31")
TEST_START = pd.Timestamp("2025-01-01")
# F3: base features + same-day NASA POWER wind and cloud (four-zone mean). The F1 recipe used Open-Meteo
# forecasts, which could not be re-collected, so this build uses the already-tested F3 recipe.
FEATURES = Dm.feats_for(pd.DataFrame(columns=[]), "none") + ["ra_wind_t", "ra_cloud_t"]


def build_table():
    t = E.prepare()
    f, D = Dm.build(t)
    ra = FR.reanalysis_national4(D.index)
    f["ra_wind_t"], f["ra_cloud_t"] = ra["WS10M"], ra["CLOUD_AMT"]
    bp = pd.read_csv(Dm.RAW / "bpdb_forecast_daily.csv", parse_dates=["date"]).set_index("date")["probable_max_demand_mw"]
    wx = Dm.weather_daily().reindex(D.index)
    df = pd.DataFrame(index=D.index)
    df["demand_mw"] = D
    df["demand_yesterday_mw"] = D.shift(1)
    df["bpdb_forecast_mw"] = bp.reindex(D.index)
    df["shed_mw"] = t["y"].reindex(D.index)
    df["quality_flag"] = np.select(
        [t["R2_max_demand_zero"].reindex(D.index).fillna(False).astype(bool),
         t["R7"].reindex(D.index).fillna(False).astype(bool),
         t["R5_residual_outlier"].reindex(D.index).fillna(False).astype(bool) if "R5_residual_outlier" in t else pd.Series(False, index=D.index)],
        ["max demand recorded as zero", "missing target", "residual outlier (kept)"], default="")
    df["tmax_c_national"] = wx["tmax_c"]
    df["rain_mm_national"] = wx["precip_mm"]
    df["m7_mw"] = f["m7"]
    for c in FEATURES:
        df[c] = f[c]
    df["split"] = np.where(df.index <= TRAIN_END, "train", "test")
    df.index.name = "date"
    return df.reset_index()


def export_model(df: pd.DataFrame):
    train = df[(pd.to_datetime(df["date"]) <= TRAIN_END)].copy()
    d = pd.to_datetime(df["date"])
    target = np.log(df["demand_mw"] / df["m7_mw"])
    ok = (d <= TRAIN_END) & target.notna() & df[FEATURES].notna().all(axis=1)
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
    m.fit(df.loc[ok, FEATURES], target[ok])
    trees = []
    for pred in m._predictors:
        nodes = pred[0].nodes
        assert not nodes["is_categorical"].any(), "categorical splits not supported by the JS port"
        trees.append([
            {"v": float(n["value"]), "f": int(n["feature_idx"]), "t": float(n["num_threshold"]),
             "l": int(n["left"]), "r": int(n["right"]), "leaf": bool(n["is_leaf"]),
             "mgl": bool(n["missing_go_to_left"])}
            for n in nodes])
    model = {"name": "F3: gradient boosting on log(demand / 7-day mean), same-day reanalysis wind and cloud",
             "trained_through": "2024-12-31", "features": FEATURES,
             "baseline": float(m._baseline_prediction.ravel()[0]), "trees": trees,
             "target": "log(demand_t / m7_t)", "output": "exp(prediction) * m7_t"}
    return m, model


def walk(model, x):
    total = model["baseline"]
    for tree in model["trees"]:
        i = 0
        while True:
            n = tree[i]
            if n["leaf"]:
                total += n["v"]
                break
            v = x[n["f"]]
            if v is None or (isinstance(v, float) and math.isnan(v)):
                i = n["l"] if n["mgl"] else n["r"]
            else:
                i = n["l"] if v <= n["t"] else n["r"]
    return total


def main():
    (DEMO / "data").mkdir(parents=True, exist_ok=True)
    (DEMO / "model").mkdir(parents=True, exist_ok=True)
    df = build_table()
    m, model = export_model(df)
    py = m.predict(df[FEATURES]) if False else None
    mask = df[FEATURES].notna().all(axis=1)
    py_log = pd.Series(np.nan, index=df.index)
    py_log[mask] = m.predict(df.loc[mask, FEATURES])
    js_log = pd.Series(np.nan, index=df.index)
    for i in df.index[mask]:
        js_log[i] = walk(model, df.loc[i, FEATURES].tolist())
    max_diff = float(np.nanmax(np.abs(py_log - js_log)))
    df["pred_mw"] = np.where(mask, np.exp(js_log) * df["m7_mw"], np.nan)
    # Features stay at full precision: rounding them can move a row across a split threshold and
    # change the prediction by tens of MW. Only MW and weather display columns are rounded.
    for c in [c for c in df.columns if c != "m7_mw" and (c.endswith("_mw") or c.endswith("_c_national"))]:
        df[c] = df[c].round(2)
    df.to_csv(DEMO / "data" / "daily_demo.csv", index=False)
    (DEMO / "model" / "model_f3.json").write_text(json.dumps(model))
    check = {"max_abs_diff_log_scale": max_diff, "rows_checked": int(mask.sum()),
             "trees": len(model["trees"]), "features": FEATURES}
    (DEMO / "model" / "export_check.json").write_text(json.dumps(check, indent=2))
    print(json.dumps(check, indent=2))
    print("rows:", len(df), "test rows with prediction:",
          int(((pd.to_datetime(df["date"]) >= TEST_START) & df["pred_mw"].notna()).sum()))


if __name__ == "__main__":
    main()
