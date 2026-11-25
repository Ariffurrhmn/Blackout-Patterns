"""Demand forecasting: national evening-peak demand (MW). Protocol and recipes in docs/demand_round1.md.

Validation folds only in this file's `main()`. The test run is a separate function, called once,
after the validation table has been reviewed.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from hijri_converter import convert
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MD = "Max. Demand at eve. peak (Generation end)"
RAW = ROOT / "data/raw/crosscheck_mridha_zenodo21783853"  # weather_daily.csv and bpdb_forecast_daily.csv
FOLDS = E.FOLDS
TEST = ("2024-12-31", "2025-01-01", "2026-08-03")


def holiday_flags(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Ramadan (Hijri month 9) and Eid windows (+-1 day), from the Hijri calendar, not hand-typed."""
    days = pd.date_range(index.min() - pd.Timedelta(days=5), index.max() + pd.Timedelta(days=5), freq="D")
    hij = {}
    for d in days:
        h = convert.Gregorian(d.year, d.month, d.day).to_hijri()
        hij[d] = (h.month, h.day)
    eid_fitr = [d for d, (m, dd) in hij.items() if m == 10 and dd == 1]
    eid_adha = [d for d, (m, dd) in hij.items() if m == 12 and dd == 10]
    out = pd.DataFrame(index=index)
    out["ramadan"] = [int(hij[d][0] == 9) if d in hij else 0 for d in index]
    out["eid_fitr_win"] = [int(any(abs((d - e).days) <= 1 for e in eid_fitr)) for d in index]
    out["eid_adha_win"] = [int(any(abs((d - e).days) <= 1 for e in eid_adha)) for d in index]
    return out


def weather_daily() -> pd.DataFrame:
    w = pd.read_csv(RAW / "weather_daily.csv", parse_dates=["date"])
    g = w.groupby("date")[["tmax_c", "tmean_c", "precip_mm"]].mean()
    return g


def build(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Demand series D (R2 and missing set to NaN) and a feature table with only past-known inputs,
    except calendar fields and the same-day weather columns, which are labelled."""
    D = t[MD].where(~t["R2_max_demand_zero"].fillna(False).astype(bool) & t["R7"].eq(False))
    D = D.asfreq("D")
    m7 = D.shift(1).rolling(7, min_periods=5).mean()
    f = pd.DataFrame(index=D.index)
    f["lr1"] = np.log(D.shift(1) / m7)
    f["lr7"] = np.log(D.shift(7) / m7)
    f["lm7"] = np.log(m7)
    f["dow"] = D.index.dayofweek
    doy = D.index.dayofyear
    for k in (1, 2):
        f[f"sin{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
        f[f"cos{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
    hf = holiday_flags(D.index)
    for c in hf.columns:
        f[c] = hf[c]
    wx = weather_daily().reindex(D.index)
    for c in ("tmax_c", "tmean_c", "precip_mm"):
        f[f"{c}_l1"] = wx[c].shift(1)
        f[f"{c}_t"] = wx[c]
    f["m7"] = m7
    return f, D


def feats_for(f: pd.DataFrame, weather: str) -> list[str]:
    cal = ["lr1", "lr7", "lm7", "dow", "sin1", "cos1", "sin2", "cos2", "ramadan", "eid_fitr_win", "eid_adha_win"]
    if weather == "none":
        return cal
    if weather == "lagged":
        return cal + ["tmax_c_l1", "tmean_c_l1", "precip_mm_l1"]
    return cal + ["tmax_c_t", "tmean_c_t", "precip_mm_t"]


def hw_onestep(D: pd.Series, cut: str, idx: pd.DatetimeIndex) -> pd.Series:
    """Additive weekly seasonal smoother, one-step ahead. alpha/gamma chosen by grid on training days."""
    prev = D.shift(1)
    tr = (D.index <= pd.Timestamp(cut)) & D.notna()
    best, best_sse = (0.3, 0.1), np.inf
    for a in np.linspace(0.05, 0.9, 10):
        for g in np.linspace(0.02, 0.5, 8):
            lvl, seas = None, np.zeros(7)
            sse = 0.0
            pred_series = pd.Series(np.nan, index=D.index)
            for i, day in enumerate(D.index):
                v = D.iat[i]
                if lvl is None:
                    if pd.notna(v):
                        lvl = v
                    continue
                p = lvl + seas[i % 7]
                pred_series.iat[i] = p
                if pd.notna(v):
                    if tr.iat[i]:
                        sse += (v - p) ** 2
                    e = v - lvl - seas[i % 7]
                    lvl = lvl + a * e
                    seas[i % 7] = seas[i % 7] + g * e
            if sse < best_sse:
                best, best_sse = (a, g), sse
    a, g = best
    lvl, seas = None, np.zeros(7)
    out = {}
    for i, day in enumerate(D.index):
        v = D.iat[i]
        if lvl is None:
            if pd.notna(v):
                lvl = v
            continue
        p = lvl + seas[i % 7]
        if day in idx:
            out[day] = p
        if pd.notna(v):
            e = v - lvl - seas[i % 7]
            lvl = lvl + a * e
            seas[i % 7] = seas[i % 7] + g * e
    return pd.Series(out)


def fit_predict(f: pd.DataFrame, D: pd.Series, cut: str, idx: pd.DatetimeIndex, kind: str, weather: str):
    m7 = f["m7"]
    target = np.log(D / m7)
    cols = feats_for(f, weather)
    tr = (D.index <= pd.Timestamp(cut)) & target.notna() & f[cols].notna().all(axis=1)
    if kind == "ridge":
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
    else:
        model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
    model.fit(f.loc[tr, cols], target[tr])
    pr = np.exp(model.predict(f.loc[idx, cols])) * m7.loc[idx]
    return pd.Series(pr, index=idx)


def score_index(D: pd.Series, lo, hi) -> pd.DatetimeIndex:
    idx = D.index[(D.index >= pd.Timestamp(lo)) & (D.index <= pd.Timestamp(hi))]
    ok = D.reindex(idx).notna() & D.shift(1).reindex(idx).notna() & D.shift(7).reindex(idx).notna()
    return idx[ok.to_numpy()]


def recipe_frames(t: pd.DataFrame, cut: str, lo: str, hi: str) -> dict:
    f, D = build(t)
    idx = score_index(D, lo, hi)
    persist = D.shift(1).reindex(idx)
    seas = D.shift(7).reindex(idx)
    actual = D.reindex(idx)
    frames = {
        "D1": persist,
        "D2": seas,
        "D4": fit_predict(f, D, cut, idx, "ridge", "none"),
        "D5": fit_predict(f, D, cut, idx, "ridge", "lagged"),
        "D6": fit_predict(f, D, cut, idx, "ridge", "same"),
        "D7": fit_predict(f, D, cut, idx, "gbm", "none"),
        "D8": fit_predict(f, D, cut, idx, "gbm", "lagged"),
        "D9": hw_onestep(D, cut, idx),
    }
    out = {}
    for k, p in frames.items():
        out[k] = pd.DataFrame({"actual": actual, "pred": p.reindex(idx), "persist": persist})
    return out


def summarize(fr: pd.DataFrame) -> dict:
    fr = fr.dropna()
    em = (fr.actual - fr.pred).abs().mean()
    ep = (fr.actual - fr.persist).abs().mean()
    mape = float(((fr.actual - fr.pred).abs() / fr.actual).mean() * 100)
    gain, lo, hi, n = E.bootstrap_gain([fr])
    return {"n": int(n), "MAE_MW": round(float(em), 1), "MAPE_pct": round(mape, 2),
            "skill": round(float(1 - em / ep), 4), "gain_MW": gain, "ci95": [lo, hi]}


def main() -> None:
    t = E.prepare()
    per, pooled = {}, {}
    for cut, vs, ve in FOLDS:
        fr = recipe_frames(t, cut, vs, ve)
        for k, v in fr.items():
            pooled.setdefault(k, []).append(v)
            per.setdefault(k, []).append(summarize(v))
    res = {}
    for k in sorted(pooled):
        res[k] = {"folds": per[k], "pooled": summarize(pd.concat(pooled[k]).sort_index()),
                  "mean_skill": round(float(np.mean([p["skill"] for p in per[k]])), 4),
                  "mean_MAPE_pct": round(float(np.mean([p["MAPE_pct"] for p in per[k]])), 2)}
        print(k, res[k]["mean_skill"], res[k]["mean_MAPE_pct"], res[k]["pooled"], flush=True)
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed/demand_validation.json").write_text(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
