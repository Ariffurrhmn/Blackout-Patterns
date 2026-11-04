"""Regime detection: PELT change points on daily series (ruptures), against a calendar baseline.

Signals (all standardised, then stacked into one multivariate series):
  shed   : log1p(daily mean MW shed per observed hour)
  liquid : liquid-fuel share of generation
  imports: import share
  coal   : coal share
  gas    : gas share
Model: PELT, l2 cost, min segment 14 days. The penalty is ``c * log(n) * d`` (a BIC-style
scale for d standardised dimensions), swept over several ``c`` because the number of
breakpoints is very sensitive to it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import ruptures as rpt

from . import config

SIGNALS = {
    "shed": lambda d: np.log1p(d["shed_mw"]),
    "liquid": lambda d: d["liquid_fuel_share"],
    "imports": lambda d: d["imports_share"],
    "coal": lambda d: d["coal_share"],
    "gas": lambda d: d["gas_share"],
}


def signal_matrix(daily: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    x = pd.DataFrame({n: SIGNALS[n](daily) for n in names})
    x = x.interpolate(limit=7, limit_direction="both").dropna()  # short gaps only
    return (x - x.mean()) / x.std()


def _refine(x: pd.DataFrame, i: int, lo: int, hi: int, width: int) -> int:
    """Move break ``i`` to the exact day within +-width that minimises the two-segment cost."""
    best, best_cost = i, np.inf
    v = x.values
    for j in range(max(lo + 14, i - width), min(hi - 14, i + width) + 1):
        left, right = v[lo:j], v[j:hi]
        cost = ((left - left.mean(0)) ** 2).sum() + ((right - right.mean(0)) ** 2).sum()
        if cost < best_cost:
            best, best_cost = j, cost
    return best


def pelt(x: pd.DataFrame, c: float, min_size: int = 14, jump: int = 5) -> list[pd.Timestamp]:
    """Change-point dates (the first day of each new segment).

    PELT is searched on a ``jump``-day grid (about 24x faster than jump=1 on this data and
    the same breaks to within two days), then each break is moved to the exact day inside
    its +-``jump`` window.
    """
    pen = c * np.log(len(x)) * x.shape[1]
    ends = rpt.Pelt(model="l2", min_size=min_size, jump=jump).fit(x.values).predict(pen=pen)
    idx = [0] + ends
    refined = [_refine(x, idx[k], idx[k - 1], idx[k + 1], jump) for k in range(1, len(idx) - 1)]
    return [x.index[i] for i in refined]


def calendar_baseline(x: pd.DataFrame) -> list[pd.Timestamp]:
    return [pd.Timestamp(config.BASELINE_SPLIT_DATE)]


def segment_cost(x: pd.DataFrame, breaks: list[pd.Timestamp]) -> float:
    """Total within-segment sum of squares: lower = the segmentation explains more."""
    edges = [x.index[0]] + list(breaks) + [x.index[-1] + pd.Timedelta(days=1)]
    cost = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        seg = x.loc[a: b - pd.Timedelta(days=1)]
        cost += float(((seg - seg.mean()) ** 2).to_numpy().sum())
    return cost


def align_with_events(breaks: list[pd.Timestamp], tol_days: int = 7) -> pd.DataFrame:
    rows = []
    for date, label in config.KNOWN_EVENTS.items():
        ev = pd.Timestamp(date)
        if breaks:
            nearest = min(breaks, key=lambda b: abs((b - ev).days))
            gap = (nearest - ev).days
        else:
            nearest, gap = pd.NaT, np.nan
        rows.append({"event": label, "event_date": ev.date(), "nearest_break": getattr(nearest, "date", lambda: None)(),
                     "gap_days": gap, f"within_{tol_days}d": bool(abs(gap) <= tol_days) if gap == gap else False})
    return pd.DataFrame(rows)


def sweep(daily: pd.DataFrame, names: list[str], cs=(0.5, 1, 2, 4, 8, 16)) -> pd.DataFrame:
    x = signal_matrix(daily, names)
    base_cost = segment_cost(x, calendar_baseline(x))
    rows = []
    for c in cs:
        b = pelt(x, c)
        ev = align_with_events(b)
        rows.append({"signals": "+".join(names), "c": c, "n_breaks": len(b),
                     "cost": segment_cost(x, b), "calendar_cost": base_cost,
                     "events_within_7d": int(ev["within_7d"].sum()), "breaks": [str(d.date()) for d in b]})
    return pd.DataFrame(rows)


def best_single_break(x: pd.DataFrame, min_size: int = 30) -> tuple[pd.Timestamp, float]:
    """The one break date that minimises total within-segment cost (exhaustive search)."""
    v = x.values
    best_j, best_cost = None, np.inf
    for j in range(min_size, len(v) - min_size):
        left, right = v[:j], v[j:]
        cost = ((left - left.mean(0)) ** 2).sum() + ((right - right.mean(0)) ** 2).sum()
        if cost < best_cost:
            best_j, best_cost = j, cost
    return x.index[best_j], float(best_cost)
