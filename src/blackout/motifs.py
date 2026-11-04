"""Motifs and discords with the matrix profile (STUMPY).

Series: log1p of the daily mean MW shed, from ``config.CRISIS_START`` on (before that the
series is almost constant zero and every window is a trivial match). Window m in days.
A *motif* is a pair of windows that look alike (low z-normalised distance); a *discord* is
the window whose nearest neighbour is furthest away (an unusual stretch: a real event, or a
data problem). Both lists keep chosen windows from overlapping (exclusion zone = m).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import stumpy

from . import config


MIN_ACTIVE_MW = 200.0  # a window is "active" if a day in it averages at least this many MW shed


def daily_series(daily: pd.DataFrame, start: str = config.CRISIS_START) -> pd.Series:
    s = np.log1p(daily["shed_mw"]).loc[start:]
    return s.interpolate(limit=7, limit_direction="both").dropna()


def matrix_profile(s: pd.Series, m: int) -> pd.DataFrame:
    mp = stumpy.stump(s.to_numpy(float), m)
    v = s.to_numpy(float)
    win = np.lib.stride_tricks.sliding_window_view(v, m)
    # A window is "active" if shedding actually happens in it. Flat zero stretches (the winter
    # lull) match each other at distance 0 and would be reported as meaningless motifs.
    active = (win.max(axis=1) >= np.log1p(MIN_ACTIVE_MW)) & (win.std(axis=1) >= 0.1)
    return pd.DataFrame({"start": s.index[: len(mp)], "distance": mp[:, 0].astype(float),
                         "neighbour": mp[:, 1].astype(int), "active": active[: len(mp)]})


def _pick(mp: pd.DataFrame, m: int, k: int, largest: bool) -> pd.DataFrame:
    order = mp.loc[mp["active"] & mp["neighbour"].map(mp["active"].to_dict()).fillna(False).astype(bool), "distance"] \
        .sort_values(ascending=not largest).index
    chosen: list[int] = []
    for i in order:
        if np.isfinite(mp.loc[i, "distance"]) and all(abs(i - j) >= m for j in chosen):
            chosen.append(i)
        if len(chosen) == k:
            break
    out = mp.loc[chosen].copy()
    out["end"] = out["start"] + pd.Timedelta(days=m - 1)
    out["neighbour_start"] = [mp["start"].iloc[n] for n in out["neighbour"]]
    return out.reset_index(drop=True)


def motifs(mp: pd.DataFrame, m: int, k: int = 3) -> pd.DataFrame:
    """Top-k motif windows. Each pair (i, neighbour) appears once: the mirror is skipped."""
    out = _pick(mp, m, k * 2, largest=False)
    seen, keep = set(), []
    for _, r in out.iterrows():
        pair = frozenset({r["start"], r["neighbour_start"]})
        if pair not in seen:
            seen.add(pair)
            keep.append(r)
    return pd.DataFrame(keep).head(k).reset_index(drop=True)


def discords(mp: pd.DataFrame, m: int, k: int = 5) -> pd.DataFrame:
    return _pick(mp, m, k, largest=True)


def run(daily: pd.DataFrame, windows=(7, 14), k: int = 3) -> dict:
    s = daily_series(daily)
    res = {}
    for m in windows:
        mp = matrix_profile(s, m)
        res[m] = {"series": s, "mp": mp, "motifs": motifs(mp, m, k), "discords": discords(mp, m, 5)}
    return res
