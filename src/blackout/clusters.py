"""Archetype days: cluster 23-hour load-shedding profiles of crisis days.

Three methods on the same days:
  kmeans  : baseline, k-means on raw MW (captures level *and* shape)
  dtw     : tslearn TimeSeriesKMeans with DTW on z-normalised profiles (shape, tolerant to shifts)
  kshape  : tslearn KShape on z-normalised profiles (shape, shift-invariant correlation)
Evaluation: silhouette, Davies-Bouldin, and bootstrap ARI stability (fit on 80% of days,
assign all days to the nearest fitted centre, compare with the full-data labelling).
Only days with some shedding are clustered; shedding-free days are one trivial archetype.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from tslearn.clustering import KShape, TimeSeriesKMeans
from tslearn.metrics import cdist_dtw
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

from . import config

warnings.filterwarnings("ignore", category=FutureWarning)


def crisis_profiles(matrix: pd.DataFrame, start: str = config.CRISIS_START, min_total_mw: float = 50.0) -> pd.DataFrame:
    """Days from ``start`` on whose summed shedding over the 23 hours exceeds ``min_total_mw``."""
    m = matrix.loc[start:]
    return m[m.sum(axis=1) > min_total_mw]


def _znorm(x: np.ndarray) -> np.ndarray:
    return TimeSeriesScalerMeanVariance().fit_transform(x[:, :, None])  # (n, t, 1)


class Model:
    """Thin wrapper giving the three methods one interface: fit, predict, features, centers."""

    def __init__(self, name: str, k: int, seed: int = config.RANDOM_SEED):
        self.name, self.k, self.seed = name, k, seed

    def _repr(self, x: np.ndarray):
        return x if self.name == "kmeans" else _znorm(x)

    def fit(self, x: np.ndarray) -> "Model":
        r = self._repr(x)
        if self.name == "kmeans":
            self.m = KMeans(self.k, n_init=10, random_state=self.seed).fit(r)
        elif self.name == "dtw":
            # DTW k-means is the expensive one: one initialisation and short DBA averaging
            self.m = TimeSeriesKMeans(self.k, metric="dtw", max_iter=10, max_iter_barycenter=5,
                                      n_init=1, random_state=self.seed, n_jobs=-1).fit(r)
        elif self.name == "kshape":
            self.m = KShape(self.k, n_init=3, random_state=self.seed).fit(r)
        else:
            raise ValueError(self.name)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.m.predict(self._repr(x))

    @property
    def centers(self) -> np.ndarray:
        c = self.m.cluster_centers_
        return c if c.ndim == 2 else c[:, :, 0]


def _scores(name: str, x: np.ndarray, labels: np.ndarray, dtw_dist: np.ndarray | None) -> dict:
    if len(set(labels)) < 2:
        return {"silhouette": np.nan, "davies_bouldin": np.nan}
    if name == "dtw":
        sil = silhouette_score(dtw_dist, labels, metric="precomputed")
        db = davies_bouldin_score(_znorm(x)[:, :, 0], labels)
    elif name == "kshape":
        z = _znorm(x)[:, :, 0]
        sil, db = silhouette_score(z, labels), davies_bouldin_score(z, labels)
    else:
        sil, db = silhouette_score(x, labels), davies_bouldin_score(x, labels)
    return {"silhouette": float(sil), "davies_bouldin": float(db)}


def stability(name: str, k: int, x: np.ndarray, full_labels: np.ndarray, reps: int = 5, frac: float = 0.8) -> float:
    rng = np.random.default_rng(config.RANDOM_SEED)
    aris = []
    for r in range(reps):
        idx = rng.choice(len(x), int(frac * len(x)), replace=False)
        m = Model(name, k, seed=config.RANDOM_SEED + r).fit(x[idx])
        aris.append(adjusted_rand_score(full_labels, m.predict(x)))
    return float(np.mean(aris))


def compare(profiles: pd.DataFrame, ks=(2, 3, 4, 5), methods=("kmeans", "kshape", "dtw"), stab_reps: int = 5,
            dtw_ks=(3, 4, 5), dtw_stab_reps: int = 2, log=print):
    """Return (scores table, dict of fitted models keyed by (method, k)).

    DTW k-means is ~100x slower than the others, so it gets fewer ``k`` values and fewer
    stability repeats (``dtw_ks``, ``dtw_stab_reps``).
    """
    x = profiles.to_numpy(float)
    dtw_dist = cdist_dtw(_znorm(x)[:, :, 0], n_jobs=-1) if "dtw" in methods else None
    rows, models = [], {}
    for name in methods:
        for k in (dtw_ks if name == "dtw" else ks):
            m = Model(name, k).fit(x)
            labels = m.predict(x)
            models[(name, k)] = (m, labels)
            reps = dtw_stab_reps if name == "dtw" else stab_reps
            rows.append({"method": name, "k": k, **_scores(name, x, labels, dtw_dist),
                         "stability_ari": stability(name, k, x, labels, reps),
                         "stability_reps": reps,
                         "smallest_cluster": int(np.bincount(labels, minlength=k).min())})
            log(f"{name} k={k} done: {rows[-1]}")
    return pd.DataFrame(rows), models


def describe(profiles: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Per-cluster size, mean MW over the day, peak hour, and year mix."""
    df = profiles.copy()
    df["cluster"] = labels
    out = []
    for c, g in df.groupby("cluster"):
        mean_profile = g.drop(columns="cluster").mean()
        years = g.index.year.value_counts(normalize=True).sort_index()
        out.append({"cluster": c, "days": len(g), "mean_mw_per_hour": mean_profile.mean(),
                    "peak_hour": int(mean_profile.idxmax()), "peak_mw": mean_profile.max(),
                    "night_share": mean_profile.loc[[22, 23, 1, 2, 3, 4, 5]].sum() / mean_profile.sum(),
                    "year_mix": {int(y): round(float(s), 2) for y, s in years.items()}})
    return pd.DataFrame(out)
