"""Anomalies: STL residuals + Isolation Forest, against a z-score baseline.

Daily series -> STL (period 7, robust) residuals. Three detectors are compared:
  zscore      : |robust z| of the generation residual (baseline)
  iforest_1   : Isolation Forest on the generation residual alone
  iforest_all : Isolation Forest on residuals of generation, shed (log1p), gas, coal, liquid shares
Evaluation is on *injected* glitches: at random days we multiply daily generation by a factor
(spike x1.6 or dropout x0.4), so the ground truth is known. Score = precision@K with K = number
injected, averaged over seeds. This is a recall test for data glitches; it says nothing about
how well the detectors find *real* events, which has no ground truth here (see ``real_events``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL

from . import config

FEATURES = {"generation": lambda d: d["generation"], "shed": lambda d: np.log1p(d["shed_mw"]),
            "gas": lambda d: d["gas_share"], "coal": lambda d: d["coal_share"],
            "liquid": lambda d: d["liquid_fuel_share"]}


def stl_residuals(daily: pd.DataFrame, start: str = "2018-01-01") -> pd.DataFrame:
    d = daily.loc[start:]
    res = {}
    for name, fn in FEATURES.items():
        s = fn(d).interpolate(limit=7, limit_direction="both")
        s = s.dropna()
        res[name] = STL(s, period=7, robust=True).fit().resid
    return pd.DataFrame(res).dropna()


def _robust_z(x: pd.Series) -> pd.Series:
    # Floor the scale at 10% of the standard deviation: series that are zero for years (shedding
    # before 2022) have a MAD of ~0, which would turn the smallest change into z = -77,000.
    mad = (x - x.median()).abs().median() * 1.4826
    return (x - x.median()) / max(mad, 0.1 * x.std())


def scores(resid: pd.DataFrame, seed: int = config.RANDOM_SEED) -> pd.DataFrame:
    """Anomaly score per day for each detector (higher = more anomalous)."""
    out = pd.DataFrame(index=resid.index)
    out["zscore"] = _robust_z(resid["generation"]).abs()
    z = resid.apply(_robust_z)
    for name, cols in {"iforest_1": ["generation"], "iforest_all": list(resid.columns)}.items():
        f = IsolationForest(n_estimators=300, random_state=seed).fit(z[cols])
        out[name] = -f.score_samples(z[cols])
    return out


def injected_glitch_test(daily: pd.DataFrame, n_inject: int = 40, seeds: int = 10) -> pd.DataFrame:
    rows = []
    d0 = daily.loc["2018-01-01":].copy()
    for seed in range(seeds):
        rng = np.random.default_rng(config.RANDOM_SEED + seed)
        d = d0.copy()
        valid = d.index[d["generation"].notna()]
        days = rng.choice(valid, n_inject, replace=False)
        factor = rng.choice([1.6, 0.4], n_inject)
        d.loc[days, "generation"] = d.loc[days, "generation"].values * factor
        sc = scores(stl_residuals(d), seed=seed)
        truth = set(pd.DatetimeIndex(days))
        for det in sc.columns:
            top = sc[det].nlargest(n_inject).index
            rows.append({"seed": seed, "detector": det,
                         "precision_at_k": len(truth & set(top)) / n_inject})
    r = pd.DataFrame(rows)
    return r.groupby("detector")["precision_at_k"].agg(["mean", "std"]).reset_index()


def real_events(daily: pd.DataFrame, hourly: pd.DataFrame, top: int = 50) -> pd.DataFrame:
    """Top real-data anomalies with a *heuristic* tag (not a manual label).

    ``data_error_like`` if the day has flagged bad readings or fewer than 20 observed hours;
    ``event_like`` if at least two of generation / shed / gas / coal residuals exceed |z| 3
    together; otherwise ``unclear``.
    """
    resid = stl_residuals(daily)
    sc = scores(resid)
    z = resid.apply(_robust_z)
    flags = hourly.filter(like="flag_bad_").any(axis=1).groupby(hourly.index.normalize()).sum()
    res = sc[["iforest_all"]].join(z.add_prefix("z_")).join(daily[["n_hours"]])
    res["flagged_bad_hours"] = flags.reindex(res.index).fillna(0).astype(int)
    res = res.nlargest(top, "iforest_all")
    n_big = (res[["z_generation", "z_shed", "z_gas", "z_coal"]].abs() > 3).sum(axis=1)
    res["tag"] = np.where((res["flagged_bad_hours"] > 0) | (res["n_hours"] < 20), "data_error_like",
                          np.where(n_big >= 2, "event_like", "unclear"))
    return res
