"""Day-ahead forecast test (protocol: docs/forecast_round1.md), with a documented deviation:
only 4 of 9 zones downloaded (Dhaka, Chattogram, Rajshahi, Sylhet). National values are means over those 4.
Validation folds only. Forecast source: Open-Meteo historical forecast archive. Reanalysis: NASA POWER.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demand as Dm  # noqa: E402
import experiments as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ZONES4 = ["Dhaka", "Chattogram", "Rajshahi", "Sylhet"]


def forecast_national(D_index):
    frames = []
    for z in ZONES4:
        j = json.load(open(ROOT / f"data/raw/open_meteo_forecast/{z}.json"))["daily"]
        df = pd.DataFrame({"date": pd.to_datetime(j["time"]), "fc_wind": j["wind_speed_10m_max"],
                           "fc_cloud": j["cloud_cover_mean"]})
        frames.append(df.set_index("date"))
    fc = pd.concat(frames, keys=ZONES4).groupby(level=1).mean()
    return fc.reindex(D_index)


def reanalysis_national4(D_index):
    n = pd.read_csv(ROOT / "data/raw/nasa_power/nasa_power_daily_zones.csv", parse_dates=["date"])
    n = n[n["zone"].isin(ZONES4)]
    return n.groupby("date")[["WS10M", "CLOUD_AMT"]].mean().reindex(D_index)


def main() -> None:
    t = E.prepare()
    f, D = Dm.build(t)
    fc = forecast_national(D.index)
    ra = reanalysis_national4(D.index)
    # Forecast accuracy on days with both (validation window only)
    acc_idx = Dm.score_index(D, "2023-07-01", "2024-12-31")
    cloud_mae = float((fc.loc[acc_idx, "fc_cloud"] - ra.loc[acc_idx, "CLOUD_AMT"]).abs().mean())
    cloud_corr = float(fc.loc[acc_idx, "fc_cloud"].corr(ra.loc[acc_idx, "CLOUD_AMT"]))
    wind_corr = float(fc.loc[acc_idx, "fc_wind"].corr(ra.loc[acc_idx, "WS10M"]))
    acc = {"cloud_MAE_pct_points": round(cloud_mae, 2), "cloud_corr": round(cloud_corr, 3),
           "wind_corr_forecast_max_vs_reanalysis_mean": round(wind_corr, 3), "n_days": int(len(acc_idx))}
    # Features: day-t forecast (issued the previous day) and day-t 4-zone reanalysis (upper bound)
    f["fc_wind_t"] = fc["fc_wind"]
    f["fc_cloud_t"] = fc["fc_cloud"]
    f["ra_wind_t"] = ra["WS10M"]
    f["ra_cloud_t"] = ra["CLOUD_AMT"]
    base = Dm.feats_for(f, "none")
    sets = {
        "F0": base,
        "F1": base + ["fc_wind_t", "fc_cloud_t"],
        "F2": base + ["fc_cloud_t"],
        "F3": base + ["ra_wind_t", "ra_cloud_t"],
    }
    m7 = f["m7"]
    target = np.log(D / m7)
    out = {"accuracy_validation": acc, "deviation": "4 of 9 zones (Dhaka, Chattogram, Rajshahi, Sylhet)"}
    for k, cols in sets.items():
        pooled = []
        for cut, vs, ve in E.FOLDS:
            idx = Dm.score_index(D, vs, ve)
            tr = (D.index <= pd.Timestamp(cut)) & target.notna() & f[cols].notna().all(axis=1)
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
            m.fit(f.loc[tr, cols], target[tr])
            pooled.append(pd.DataFrame({"actual": D.reindex(idx),
                                        "pred": pd.Series(np.exp(m.predict(f.loc[idx, cols])) * m7.loc[idx], index=idx),
                                        "persist": D.shift(1).reindex(idx)}))
        out[k] = Dm.summarize(pd.concat(pooled).sort_index())
        print(k, out[k], flush=True)
    print("accuracy", acc)
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed/forecast_validation.json").write_text(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
