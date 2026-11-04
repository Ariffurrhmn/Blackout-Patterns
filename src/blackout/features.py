"""Feature tables built from the cleaned hourly table.

Decisions (made while acting as the project's delegate; revisit if you disagree):

* **Midnight is dropped.** 00:00 is absent from the source on ~99.9% of days, so a
  day is a 23-point vector for hours 1..23. Days with more than two missing hours
  are discarded; up to two are filled by linear interpolation along the day and
  counted (``day_matrix`` reports how many days were affected).
* **Fuel shares** divide by generation and treat missing solar and wind as 0.
* **Crisis start** is taken from the data (first shedding block, July 2022), see
  ``config.CRISIS_START``; regime detection (regimes.py) tests it independently.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

HOURS = list(range(1, 24))  # 00:00 is not in the source file
FUELS = ["gas", "liquid_fuel", "coal", "imports", "hydro", "renewables"]


def observed_hourly(t: pd.DataFrame) -> pd.DataFrame:
    """Observed rows only, with fuel shares and calendar fields added."""
    o = t[t["observed"]].copy()
    o["renewables"] = o[["solar", "wind"]].sum(axis=1, min_count=1).fillna(0.0)
    for f in FUELS:
        o[f"{f}_share"] = o[f] / o["generation"]
    o["hour"] = o.index.hour
    o["month"] = o.index.month
    o["dow"] = o.index.dayofweek  # Monday=0; Bangladesh's weekend is Friday + Saturday
    return o


def daily_table(t: pd.DataFrame) -> pd.DataFrame:
    """One row per day, from observed hours only (so missing hours do not bias means)."""
    o = observed_hourly(t)
    g = o.groupby(o.index.normalize())
    d = pd.DataFrame(
        {
            "n_hours": g.size(),
            "shed_hours": g["shedding"].sum(),
            "shed_mw": g["load_shedding"].mean(),  # mean MW per observed hour
            "generation": g["generation"].mean(),
            "supply": g["supply_mw"].mean(),
        }
    )
    for f in FUELS:
        d[f"{f}_share"] = g[f"{f}_share"].mean()
        d[f] = g[f].mean()
    d = d[d["n_hours"] >= 18]  # drop days that are mostly missing
    d.index.name = "date"
    return d.asfreq("D")


def day_matrix(t: pd.DataFrame, value: str = "load_shedding", max_missing: int = 2) -> tuple[pd.DataFrame, dict]:
    """Day x hour (1..23) matrix of ``value``; returns (matrix, info)."""
    o = t[t["observed"]]
    m = o.pivot_table(index=o.index.normalize(), columns=o.index.hour, values=value, aggfunc="mean")
    m = m.reindex(columns=HOURS)
    miss = m.isna().sum(axis=1)
    info = {"days_total": len(m), "days_dropped": int((miss > max_missing).sum()),
            "days_interpolated": int(((miss > 0) & (miss <= max_missing)).sum())}
    m = m[miss <= max_missing]
    m = m.interpolate(axis=1, limit_direction="both")
    m.index.name = "date"
    return m, info


# ---------------------------------------------------------------- discretisation for rule mining

SEASONS = {12: "winter", 1: "winter", 2: "winter", 3: "pre-monsoon", 4: "pre-monsoon", 5: "pre-monsoon",
           6: "monsoon", 7: "monsoon", 8: "monsoon", 9: "monsoon", 10: "autumn", 11: "autumn"}


def hour_band(h: int) -> str:
    if h >= 22 or h <= 5:
        return "night"
    if h <= 11:
        return "morning"
    if h <= 17:
        return "afternoon"
    return "evening"  # 18-21, the evening peak


def tercile_labels(s: pd.Series, ref: pd.Series | None = None) -> pd.Series:
    """low / mid / high by terciles of ``ref`` (defaults to ``s``)."""
    ref = s if ref is None else ref
    lo, hi = ref.quantile([1 / 3, 2 / 3])
    return pd.Series(np.where(s <= lo, "low", np.where(s <= hi, "mid", "high")), index=s.index).where(s.notna())


def transactions(t: pd.DataFrame, high_mw: float = 500.0) -> pd.DataFrame:
    """Hourly 'transactions' for association-rule mining: one categorical item per column.

    Terciles of fuel shares are computed over the crisis period so that "low gas" means
    low *for the crisis*, not low compared with the pre-crisis years.
    """
    o = observed_hourly(t)
    o = o[o[["gas_share", "liquid_fuel_share", "coal_share", "imports_share"]].notna().all(axis=1)]
    crisis = o.index >= config.CRISIS_START
    x = pd.DataFrame(index=o.index)
    x["season"] = o["month"].map(SEASONS)
    x["hour"] = o["hour"].map(hour_band)
    x["day"] = np.where(o["dow"].isin([4, 5]), "weekend", "weekday")
    for f in ["gas", "liquid_fuel", "coal", "imports"]:
        x[f] = tercile_labels(o[f"{f}_share"], o.loc[crisis, f"{f}_share"]).values
    x["shed"] = np.where(o["load_shedding"].fillna(0) >= high_mw, "high",
                         np.where(o["load_shedding"].fillna(0) > 0, "low", "none"))
    x["year"] = o["year"].values
    return x
