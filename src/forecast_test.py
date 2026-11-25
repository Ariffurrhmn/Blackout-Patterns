"""Single test run, frozen recipes from docs/forecast_round1.md. Train through 2024-12-31,
test 2025-01-01 to 2026-08-03. Run once. Same 4-zone deviation as the validation round."""
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
import forecast_round1 as FR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAIN_END, TEST_START, TEST_END = "2024-12-31", "2025-01-01", "2026-08-03"


def main() -> None:
    t = E.prepare()
    f, D = Dm.build(t)
    fc = FR.forecast_national(D.index)
    ra = FR.reanalysis_national4(D.index)
    f["fc_wind_t"], f["fc_cloud_t"] = fc["fc_wind"], fc["fc_cloud"]
    f["ra_wind_t"], f["ra_cloud_t"] = ra["WS10M"], ra["CLOUD_AMT"]
    base = Dm.feats_for(f, "none")
    sets = {"F0": base, "F1": base + ["fc_wind_t", "fc_cloud_t"], "F3": base + ["ra_wind_t", "ra_cloud_t"]}
    m7 = f["m7"]
    target = np.log(D / m7)
    idx = Dm.score_index(D, TEST_START, TEST_END)
    out, frames = {}, {}
    for k, cols in sets.items():
        tr = (D.index <= pd.Timestamp(TRAIN_END)) & target.notna() & f[cols].notna().all(axis=1)
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
        m.fit(f.loc[tr, cols], target[tr])
        fr = pd.DataFrame({"actual": D.reindex(idx),
                           "pred": pd.Series(np.exp(m.predict(f.loc[idx, cols])) * m7.loc[idx], index=idx),
                           "persist": D.shift(1).reindex(idx)})
        frames[k] = fr
        out[k] = Dm.summarize(fr)
    bp = pd.read_csv(Dm.RAW / "bpdb_forecast_daily.csv", parse_dates=["date"]).set_index("date")["probable_max_demand_mw"]
    frames["BPDB"] = pd.DataFrame({"actual": D.reindex(idx), "pred": bp.reindex(idx), "persist": D.shift(1).reindex(idx)})
    out["BPDB"] = Dm.summarize(frames["BPDB"])
    out["persistence"] = {"MAPE_pct": round(float(((D.reindex(idx) - D.shift(1).reindex(idx)).abs() / D.reindex(idx)).mean() * 100), 2)}
    yearly = {}
    for yr in (2025, 2026):
        sub = {k: Dm.summarize(v[v.index.year == yr]) for k, v in frames.items() if k != "persistence"}
        yearly[str(yr)] = sub
    out["by_year"] = yearly
    print(json.dumps({k: out[k] for k in ["F0", "F1", "F3", "BPDB", "persistence"]}, indent=2, default=float))
    print(json.dumps(out["by_year"], indent=2, default=float))
    (ROOT / "data/processed/forecast_test.json").write_text(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
