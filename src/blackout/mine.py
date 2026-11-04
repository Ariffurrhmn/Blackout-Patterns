"""Run every mining stage, save tables to docs/results and figures to docs/results/figures.

``blackout mine`` runs all stages. Cluster comparison is the slow one (DTW), so
``--skip-cluster-search`` re-uses docs/results/cluster_comparison.csv.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import anomalies, clusters, config, episodes, motifs, regimes, rules  # noqa: E402
from .eda import AQUA, BLUE, GRID, INK, INK2, MAGENTA, MUTED, ORANGE, SURFACE, YELLOW, GREEN, _style_axes  # noqa: E402
from .features import daily_table, day_matrix, transactions  # noqa: E402

warnings.filterwarnings("ignore")
RES = config.RESULTS
FIG = RES / "figures"
CATEG = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN]


def _save(df: pd.DataFrame, name: str, index: bool = False) -> None:
    df.to_csv(RES / name, index=index)


# ------------------------------------------------------------------ regimes

def run_regimes(daily: pd.DataFrame) -> dict:
    multi = ["shed", "liquid", "imports", "coal", "gas"]
    out = {}
    sweeps = pd.concat([regimes.sweep(daily, multi), regimes.sweep(daily, ["shed"])])
    sweeps["breaks"] = sweeps["breaks"].apply(lambda b: " ".join(b))
    _save(sweeps, "regime_sweep.csv")
    x = regimes.signal_matrix(daily, multi)
    single, cost1 = regimes.best_single_break(x)
    xs = regimes.signal_matrix(daily, ["shed"])
    out["best_single_break"] = {"multi": str(single.date()), "multi_cost": cost1,
                                "calendar_cost": regimes.segment_cost(x, regimes.calendar_baseline(x)),
                                "shed_only": str(regimes.best_single_break(xs)[0].date()),
                                "shed_only_cost": regimes.best_single_break(xs)[1],
                                "shed_only_calendar_cost": regimes.segment_cost(xs, regimes.calendar_baseline(xs))}
    out["breaks_multi_c16"] = regimes.pelt(x, 16)
    out["breaks_shed_c16"] = regimes.pelt(xs, 16)
    ev = regimes.align_with_events(out["breaks_multi_c16"])
    _save(ev, "regime_event_alignment.csv")
    out["x"] = x
    return out


def fig_regimes(daily: pd.DataFrame, reg: dict, path: Path) -> None:
    d = daily.loc["2018-01-01":]
    cols = [("gas", "Gas"), ("liquid_fuel", "Liquid fuel"), ("coal", "Coal"), ("imports", "Imports"),
            ("hydro", "Hydro"), ("renewables", "Solar + wind")]
    smooth = d[[c for c, _ in cols]].rolling(30, min_periods=10, center=True).mean().fillna(0)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.6), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
    ax.stackplot(smooth.index, [smooth[c].values for c, _ in cols], colors=CATEG, edgecolor=SURFACE,
                 linewidth=0.8, labels=[n for _, n in cols])
    ax.set_ylabel("Mean generation (30-day), MW", fontsize=9)
    fig.suptitle("Regimes: PELT change points (daily shedding + fuel shares) over the fuel mix",
                 x=0.08, ha="left", fontsize=12, color=INK)
    ax.legend(loc="upper left", ncol=6, fontsize=8, frameon=True, facecolor=SURFACE, edgecolor="none",
              framealpha=1, handlelength=1.2).set_zorder(10)
    for b in reg["breaks_multi_c16"]:
        for a in (ax, ax2):
            a.axvline(b, color=INK, linewidth=1.1, linestyle="-")
        ax.text(b, 250, f" {b.date()}", fontsize=8, color="#ffffff", rotation=90, va="bottom", ha="right")  # on the blue gas band
    for date in config.KNOWN_EVENTS:
        for a in (ax, ax2):
            a.axvline(pd.Timestamp(date), color=ORANGE, linewidth=1.0, linestyle=(0, (3, 3)))
    fig.text(0.08, 0.905, "Black = PELT change points (c=16). Dashed orange = documented events (dates not yet verified).",
             fontsize=8.5, color=INK2)
    ax2.plot(d.index, d["shed_mw"].rolling(30, min_periods=10, center=True).mean(), color=INK2, linewidth=1.6)
    ax2.set_ylabel("Mean MW shed\n(30-day)", fontsize=9)
    for a in (ax, ax2):
        a.grid(axis="y", color=GRID, linewidth=0.7)
        a.set_axisbelow(True)
        _style_axes(a)
    ax.set_xlim(d.index[0], d.index[-1])
    fig.subplots_adjust(left=0.08, right=0.97, top=0.87, bottom=0.06, hspace=0.1)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ clusters

def choose_config(scores: pd.DataFrame, n_days: int) -> tuple[str, int]:
    ok = scores[(scores.k >= 3) & (scores.smallest_cluster >= 0.05 * n_days)].copy()
    ok["score"] = ok["silhouette"] * ok["stability_ari"]
    best = ok.sort_values("score", ascending=False).iloc[0]
    return best["method"], int(best["k"])


def run_clusters(t: pd.DataFrame, skip_search: bool):
    m, info = day_matrix(t)
    prof = clusters.crisis_profiles(m)
    csv = RES / "cluster_comparison.csv"
    if skip_search and csv.exists():
        scores = pd.read_csv(csv)
    else:
        scores, _ = clusters.compare(prof, ks=(2, 3, 4, 5), stab_reps=4)
        _save(scores, "cluster_comparison.csv")
    method, k = choose_config(scores, len(prof))
    model = clusters.Model(method, k).fit(prof.to_numpy(float))
    labels = model.predict(prof.to_numpy(float))
    desc = clusters.describe(prof, labels)
    desc["year_mix"] = desc["year_mix"].apply(json.dumps)
    _save(desc, "cluster_archetypes.csv")
    return prof, labels, scores, (method, k), info


def fig_archetypes(prof: pd.DataFrame, labels: np.ndarray, cfg: tuple, path: Path) -> None:
    k = cfg[1]
    order = pd.Series(labels).value_counts().index.tolist()
    fig, axes = plt.subplots(1, k, figsize=(3.3 * k, 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, c, color in zip(axes, order, CATEG):
        g = prof[labels == c]
        for _, row in g.sample(min(40, len(g)), random_state=1).iterrows():
            ax.plot(row.index, row.values, color=color, alpha=0.08, linewidth=0.8)
        ax.plot(g.columns, g.mean(), color=color, linewidth=2.4)
        ax.set_title(f"{len(g)} days · mean {g.values.mean():,.0f} MW", fontsize=9.5, color=INK, loc="left")
        ax.set_xticks([1, 6, 12, 18, 23])
        ax.set_xlabel("Hour of day", fontsize=8.5)
        ax.grid(axis="y", color=GRID, linewidth=0.7)
        ax.set_axisbelow(True)
        _style_axes(ax)
    axes[0].set_ylabel("MW shed", fontsize=9)
    fig.suptitle(f"Archetype days ({cfg[0]}, k={cfg[1]}): mean profile (bold) over a sample of days",
                 x=0.01, ha="left", fontsize=11.5, color=INK)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.82, bottom=0.17, wspace=0.08)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ motifs

def run_motifs(daily: pd.DataFrame) -> dict:
    res = motifs.run(daily)
    rows = []
    for m, v in res.items():
        for kind in ("motifs", "discords"):
            df = v[kind].copy()
            df.insert(0, "kind", kind[:-1])
            df.insert(0, "window_days", m)
            rows.append(df[["window_days", "kind", "start", "end", "neighbour_start", "distance"]])
    _save(pd.concat(rows), "matrix_profile_motifs_discords.csv")
    return res


def fig_motifs(res: dict, path: Path, m: int = 7) -> None:
    v = res[m]
    s, mp = v["series"], v["mp"]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax.plot(s.index, s.values, color=INK2, linewidth=1)
    ax.set_ylabel("log(1 + daily mean MW shed)", fontsize=9)
    ax.set_title(f"Matrix profile (window {m} days): motifs (blue) and discords (orange)", loc="left",
                 fontsize=12, color=INK)
    for _, r in v["motifs"].iterrows():
        for st in (r["start"], r["neighbour_start"]):
            ax.axvspan(st, st + pd.Timedelta(days=m - 1), color=BLUE, alpha=0.35, linewidth=0)
    for _, r in v["discords"].iterrows():
        ax.axvspan(r["start"], r["end"], color=ORANGE, alpha=0.45, linewidth=0)
    ax2.plot(mp["start"], mp["distance"].where(mp["active"]), color=INK2, linewidth=1)
    ax2.set_ylabel("Distance to nearest\nneighbour", fontsize=9)
    for a in (ax, ax2):
        a.grid(axis="y", color=GRID, linewidth=0.7)
        a.set_axisbelow(True)
        _style_axes(a)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.07, hspace=0.1)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ rules

def run_rules(t: pd.DataFrame) -> dict:
    tx = transactions(t)
    base, base_s = rules.baseline_apriori(tx)
    crisis, fp_s, train = rules.mine_crisis_rules(tx)
    ep_all = rules.emerging_patterns(train)
    ep_fuel = rules.emerging_patterns(train, fuel_only=True)
    top_fuel = crisis[~crisis.calendar_only].head(15)
    hold = rules.holdout_check(top_fuel, tx)
    _save(base.head(50), "rules_baseline_apriori_all_years.csv")
    _save(crisis.head(200), "rules_fpgrowth_crisis_train.csv")
    _save(ep_all.head(100), "emerging_patterns_with_calendar.csv")
    _save(ep_fuel.head(100), "emerging_patterns_fuel_only.csv")
    _save(hold, "rules_holdout_2025.csv")
    return {"tx": tx, "base": base, "base_s": base_s, "crisis": crisis, "fp_s": fp_s, "train": train,
            "ep_all": ep_all, "ep_fuel": ep_fuel, "hold": hold}


def fig_holdout(hold: pd.DataFrame, path: Path) -> None:
    h = hold.dropna(subset=["holdout_confidence"]).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    y = np.arange(len(h))
    ax.hlines(y, h["holdout_confidence"] * 100, h["train_confidence"] * 100, color=GRID, linewidth=2)
    ax.plot(h["train_confidence"] * 100, y, "o", color=BLUE, markersize=8, markeredgecolor=SURFACE, label="Training (Jul 2022 - 2024)")
    ax.plot(h["holdout_confidence"] * 100, y, "o", color=ORANGE, markersize=8, markeredgecolor=SURFACE, label="Hold-out (2025)")
    ax.set_yticks(y)
    ax.set_yticklabels([a.replace(", ", "\n") if len(a) > 48 else a for a in h["antecedent"]], fontsize=7.5)
    ax.set_xlabel("% of matching hours with >= 500 MW shed (rule confidence)", fontsize=9)
    fig.suptitle("Rules mined on 2022-2024 and re-scored on 2025: precision falls sharply", x=0.01, ha="left",
                 fontsize=12, color=INK)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    ax.tick_params(axis="y", colors=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _style_axes(ax)
    fig.subplots_adjust(left=0.36, right=0.97, top=0.9, bottom=0.22)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ episodes / anomalies

def run_episodes(daily: pd.DataFrame) -> dict:
    e = episodes.mine(daily)
    null = episodes.permutation_null(daily, n_perm=200)
    _save(e.head(50), "episode_patterns_prefixspan.csv")
    return {"patterns": e, "null_gap_95": float(np.quantile(null, 0.95)), "null_gap_median": float(np.median(null)),
            "best_gap": float(e["gap"].max()) if len(e) else float("nan")}


def run_anomalies(daily: pd.DataFrame, t: pd.DataFrame) -> dict:
    bench = anomalies.injected_glitch_test(daily, n_inject=40, seeds=10)
    ev = anomalies.real_events(daily, t, top=50)
    _save(bench, "anomaly_injected_glitch_benchmark.csv")
    _save(ev.reset_index(), "anomaly_top50_real_days.csv")
    sc = anomalies.scores(anomalies.stl_residuals(daily))
    ranks = {c: int(sc[c].rank(ascending=False).loc[pd.Timestamp("2022-10-04")]) for c in sc}
    return {"bench": bench, "events": ev, "grid_failure_rank": ranks, "n_days": len(sc)}


def fig_anomaly(bench: pd.DataFrame, path: Path) -> None:
    b = bench.sort_values("mean")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.barh(b["detector"], b["mean"], xerr=b["std"], color=BLUE, error_kw={"ecolor": INK2, "capsize": 3, "elinewidth": 1})
    ax.set_xlim(0, 1)
    ax.set_xlabel("Precision@40 on injected generation glitches (10 seeds)", fontsize=9)
    ax.set_title("Which detector finds injected glitches?", loc="left", fontsize=12, color=INK)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _style_axes(ax)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.85, bottom=0.2)
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ driver

def run(clean_path: Path = config.CLEAN_HOURLY_PATH, skip_cluster_search: bool = False) -> dict:
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    t = pd.read_parquet(clean_path)
    daily = daily_table(t)
    R = {"daily": daily}
    R["regimes"] = run_regimes(daily)
    fig_regimes(daily, R["regimes"], FIG / "regimes.png")
    prof, labels, scores, cfg, info = run_clusters(t, skip_cluster_search)
    R.update(profiles=prof, labels=labels, cluster_scores=scores, cluster_cfg=cfg, day_info=info)
    fig_archetypes(prof, labels, cfg, FIG / "archetypes.png")
    R["motifs"] = run_motifs(daily)
    fig_motifs(R["motifs"], FIG / "matrix-profile.png")
    R["rules"] = run_rules(t)
    fig_holdout(R["rules"]["hold"], FIG / "rules-holdout.png")
    R["episodes"] = run_episodes(daily)
    R["anomalies"] = run_anomalies(daily, t)
    fig_anomaly(R["anomalies"]["bench"], FIG / "anomaly-benchmark.png")
    return R
