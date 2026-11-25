"""Validation round 2: the eight pre-registered recipes in docs/validation_round2.md.

Validation folds only (E.FOLDS, 2023-07 .. 2024-12). Same score set, skill and bootstrap as round 1.
Recipes P1..P8 are fixed in the doc before this file was run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R13 = next(r for r in E.RECIPES if r["id"] == "R13")


def score_index(t, cut, vs, ve):
    f, tr, sc, thr = E.fold_table(t, cut, "clean")
    idx = t.index[(t.index >= pd.Timestamp(vs)) & (t.index <= pd.Timestamp(ve))]
    return idx[sc.reindex(idx).fillna(False).to_numpy().astype(bool)]


def intermittent(y: pd.Series, cut: str, idx: pd.DatetimeIndex, method: str, a=0.1, b=0.1) -> pd.Series:
    """One-step-ahead Croston-SBA or TSB. State is learned on the training window, then rolled
    forward with observed values, so the forecast for day t uses only data up to t-1."""
    train = y[y.index <= pd.Timestamp(cut)].dropna()
    pos = train[train > 0]
    z = float(pos.mean()) if len(pos) else 0.0
    if method == "sba":
        gaps = np.diff(np.flatnonzero(train.to_numpy() > 0))
        p = float(gaps.mean()) if len(gaps) else 1.0
        q = int(len(train) - 1 - np.flatnonzero(train.to_numpy() > 0)[-1]) if len(pos) else 0
    else:
        prob = float((train > 0).mean())
    out = {}
    last = pd.Timestamp(idx.max())
    for day in pd.date_range(pd.Timestamp(cut) + pd.Timedelta(days=1), last, freq="D"):
        if method == "sba":
            fc = (1 - a / 2) * z / p if p > 0 else 0.0
        else:
            fc = prob * z
        if day in idx:
            out[day] = max(fc, 0.0)
        v = y.get(day, np.nan)
        if pd.notna(v):
            if method == "sba":
                if v > 0:
                    z += a * (v - z)
                    p += a * ((q + 1) - p)
                    q = 0
                else:
                    q += 1
            else:
                prob += b * ((1.0 if v > 0 else 0.0) - prob)
                if v > 0:
                    z += a * (v - z)
    return pd.Series(out)


def ses_forecasts(y: pd.Series, cut: str, idx: pd.DatetimeIndex) -> pd.Series:
    prev = y.shift(1)
    best, best_sse = 0.5, np.inf
    tr_mask = (y.index <= pd.Timestamp(cut)) & y.notna()
    for alpha in np.linspace(0.05, 0.95, 19):
        ew = prev.ewm(alpha=alpha, ignore_na=True, adjust=False).mean()
        sse = float(((y[tr_mask] - ew[tr_mask]) ** 2).sum())
        if sse < best_sse:
            best, best_sse = alpha, sse
    return prev.ewm(alpha=best, ignore_na=True, adjust=False).mean().reindex(idx)


def fit_gbm(t, cut, feats, rows, target, loss="absolute_error"):
    m = HistGradientBoostingRegressor(loss=loss, max_iter=300, learning_rate=0.05,
                                      max_leaf_nodes=15, random_state=0)
    m.fit(feats.loc[rows], target[rows])
    return m


def fr13_train_pred(t, cut, days):
    """Round-1 R13 model fitted through `cut`, predicting the given (training) days."""
    f, train_mask, _, _ = E.fold_table(t, cut, "clean")
    feats = f[E.feature_list(R13["feats"])]
    y = t["y"]
    base = y.shift(1)
    rows = train_mask & (t.index >= pd.Timestamp("2022-01-01")) & y.notna() & base.notna()
    m = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.05,
                                      max_leaf_nodes=15, random_state=0)
    m.fit(feats.loc[rows], (y - base)[rows])
    pred = base + pd.Series(m.predict(feats.loc[days]), index=days)
    return pred.clip(lower=0)


def run_round2():
    t = E.prepare()
    feats_all = {}
    results, frames_by_recipe = {}, {}
    per_fold = {}
    aci_out = []
    for cut, vs, ve in E.FOLDS:
        f, train_mask, score_mask, _ = E.fold_table(t, cut, "clean")
        idx = score_index(t, cut, vs, ve)
        y = t["y"]
        base = y.shift(1)
        persist = base.reindex(idx)
        actual = y.reindex(idx)

        # R13 reference (round-1 winner), identical to round 1
        fr13 = E.run_recipe(t, R13, (cut, vs, ve), return_frame=True)
        r13 = fr13["pred"].reindex(idx)

        # P1 combo persistence + R13
        p1 = (persist + r13) / 2
        # P2 combo persistence + R13 + SES
        ses = ses_forecasts(y, cut, idx)
        p2 = (persist + r13 + ses) / 3
        # P3 Croston SBA, P4 TSB
        sba = intermittent(y, cut, idx, "sba")
        tsb = intermittent(y, cut, idx, "tsb")
        sba = sba.reindex(idx)
        tsb = tsb.reindex(idx)
        # P5 hurdle: P(shed) x E[MW | shed]
        feats = f[E.feature_list("F0")]
        rows = train_mask & (t.index >= pd.Timestamp("2022-01-01")) & y.notna()
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
        clf.fit(feats.loc[rows], (y[rows] > 0).astype(int))
        reg = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=0)
        shed_rows = rows & (y > 0)
        reg.fit(feats.loc[shed_rows], y[shed_rows])
        p_shed = pd.Series(clf.predict_proba(feats.loc[idx])[:, 1], index=idx)
        size = pd.Series(reg.predict(feats.loc[idx]), index=idx)
        p5 = p_shed * size.clip(lower=0)
        # P6 Poisson HGB on the level
        m6 = fit_gbm(t, cut, feats, rows, y, loss="poisson")
        p6 = pd.Series(m6.predict(feats.loc[idx]), index=idx)
        # P8 median of persistence, R13, SBA
        p8 = pd.concat([persist, r13, sba], axis=1).median(axis=1)

        preds = {"P1": p1, "P2": p2, "P3": sba, "P4": tsb, "P5": p5, "P6": p6, "P8": p8, "R13": r13}
        for k, pr in preds.items():
            fr = pd.DataFrame({"actual": actual, "pred": pr.clip(lower=0), "persist": persist})
            frames_by_recipe.setdefault(k, []).append(fr.dropna())

        # P7 ACI around R13. Calibration: R13 in-sample residuals on the last 180 training days.
        tr_days = t.index[train_mask.to_numpy() & (t.index >= pd.Timestamp(cut) - pd.Timedelta(days=180))]
        # In-sample R13 predictions on the training days (round-1 model, same cutoff)
        tr_pred = fr13_train_pred(t, cut, tr_days)
        scores = list(np.abs(y.reindex(tr_days) - tr_pred).dropna().to_numpy())
        target_miscov, gamma = 0.10, 0.01
        alpha_t = target_miscov
        covered, widths, fixed_cov = [], [], []
        q_fixed = float(np.quantile(scores[-365:], 1 - target_miscov)) if scores else 0.0
        for day in idx:
            pr = float(r13.loc[day])
            yy = float(actual.loc[day])
            qlev = min(max(1 - alpha_t, 0.0), 1.0)
            q = float(np.quantile(scores[-365:], qlev)) if scores else 0.0
            lo, hi = max(pr - q, 0.0), pr + q
            hit = lo <= yy <= hi
            covered.append(hit)
            widths.append(hi - lo)
            fixed_cov.append((max(pr - q_fixed, 0) <= yy <= pr + q_fixed))
            alpha_t = alpha_t + gamma * (target_miscov - (0 if hit else 1))
            scores.append(abs(yy - pr))
        aci_out.append({"fold": f"{vs}..{ve}", "n": int(len(idx)),
                        "coverage_ACI": round(float(np.mean(covered)), 3),
                        "coverage_fixed_split": round(float(np.mean(fixed_cov)), 3),
                        "mean_width_ACI_MW": round(float(np.mean(widths)), 1)})

    for k, frs in frames_by_recipe.items():
        if k == "R13":
            continue
        gains = [E.bootstrap_gain([fr]) for fr in frs]
        mae_skill = []
        for fr in frs:
            em = (fr.actual - fr.pred).abs().mean()
            ep = (fr.actual - fr.persist).abs().mean()
            mae_skill.append(1 - em / ep)
        pooled = E.bootstrap_gain(frs)
        results[k] = {"mean_skill": round(float(np.mean(mae_skill)), 4),
                      "skills": [round(float(s), 4) for s in mae_skill],
                      "pooled_gain_MW": pooled[0], "ci95": [pooled[1], pooled[2]],
                      "n_pooled": pooled[3]}
    r13_frames = frames_by_recipe["R13"]
    r13_skill = np.mean([1 - (fr.actual - fr.pred).abs().mean() / (fr.actual - fr.persist).abs().mean()
                         for fr in r13_frames])
    out = {"R13_reference_mean_skill": round(float(r13_skill), 4), "recipes": results, "aci": aci_out}
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed/validation_round2.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    run_round2()
