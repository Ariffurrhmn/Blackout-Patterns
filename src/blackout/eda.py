"""Exploratory analysis: the figures and tables for the week-3 data report.

Run ``blackout eda``. Figures go to ``docs/data-report/figures``. Colours follow
the reference palette of the dataviz guidance (categorical slots in fixed order,
one-hue sequential ramp), light surface only.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from . import config  # noqa: E402

FIG_DIR = config.ROOT / "docs" / "data-report" / "figures"

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
MISSING_GREY = "#cfcec6"
# categorical slots, fixed order
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

# stack order = categorical slot order; solar and wind are folded together (tiny, 22% / 74% missing)
FUEL_STACK = [
    ("gas", "Gas", BLUE),
    ("liquid_fuel", "Liquid fuel", ORANGE),
    ("coal", "Coal", AQUA),
    ("imports", "Imports", YELLOW),
    ("hydro", "Hydro", MAGENTA),
    ("renewables", "Solar + wind", GREEN),
]

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "text.color": INK,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    }
)


def _observed(t: pd.DataFrame) -> pd.DataFrame:
    return t[t["observed"]]


# ---------------------------------------------------------------- tables

def hour_profile(t: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Share of observed hours with shedding, by hour of day (rows) and year (columns)."""
    o = _observed(t)
    o = o[o.year.isin(years)]
    return o.groupby([o.index.hour, "year"])["shedding"].mean().unstack("year")


def month_profile(t: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    o = _observed(t)
    o = o[o.year.isin(years)]
    return o.groupby([o.index.month, "year"])["shedding"].mean().unstack("year")


def shedding_size_summary(t: pd.DataFrame) -> pd.DataFrame:
    o = _observed(t)
    o = o[o.shedding]
    g = o.groupby(np.where(o.year >= 2022, "2022 onward", "2015-2021"))["load_shedding"]
    return g.describe(percentiles=[0.1, 0.5, 0.9, 0.99]).round(0)


def monthly_fuel_mix(t: pd.DataFrame) -> pd.DataFrame:
    o = _observed(t).copy()
    o["renewables"] = o[["solar", "wind"]].sum(axis=1, min_count=1)
    cols = [k for k, _, _ in FUEL_STACK]
    return o[cols].resample("MS").mean()


def coverage_by_hour(t: pd.DataFrame) -> pd.Series:
    """Share of calendar days on which each hour of day was observed."""
    days = t.index.normalize().nunique()
    return _observed(t).groupby(_observed(t).index.hour).size() / days


# ---------------------------------------------------------------- figures

def _style_axes(ax):
    ax.tick_params(length=0, labelsize=8)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)


def fig_fingerprint(t: pd.DataFrame, path: Path) -> None:
    """Day-of-year x hour heatmap of mean load shedding, one panel per year."""
    years = sorted(t.year.unique())
    cmap = LinearSegmentedColormap.from_list("shed", SEQ)
    cmap.set_bad(MISSING_GREY)
    vmax = 3000.0
    fig, axes = plt.subplots(len(years), 1, figsize=(11, 1.35 * len(years) + 1.4), sharex=True)
    im = None
    for ax, y in zip(axes, years):
        sub = t[t.year == y]
        grid = np.full((24, 366), np.nan)
        doy = sub.index.dayofyear.values - 1
        grid[sub.index.hour.values, doy] = sub["load_shedding"].where(sub["observed"]).values
        im = ax.imshow(np.ma.masked_invalid(grid), aspect="auto", origin="lower", cmap=cmap,
                       vmin=0, vmax=vmax, interpolation="nearest")
        ax.set_xlim(-0.5, (366 if pd.Timestamp(year=int(y), month=12, day=31).dayofyear == 366 else 365) - 0.5)
        ax.set_ylabel(str(y), rotation=0, labelpad=22, va="center", fontsize=10, color=INK)
        ax.set_yticks([0, 6, 12, 18])
        ax.set_yticklabels(["0", "6", "12", "18"])
        _style_axes(ax)
    month_starts = pd.to_datetime([f"2023-{m:02d}-01" for m in range(1, 13)]).dayofyear - 1
    axes[-1].set_xticks(month_starts)
    axes[-1].set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    fig.suptitle("Crisis fingerprint: mean load shedding by day of year (x) and hour of day (y)",
                 x=0.06, ha="left", fontsize=12, color=INK)
    fig.text(0.06, 0.945, "Grey = hour not in the source file (00:00 is absent on almost every day). "
             "Colour is capped at 3,000 MW.", fontsize=8.5, color=INK2, ha="left")
    cax = fig.add_axes([0.80, 0.955, 0.17, 0.008])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=7.5)
    cb.set_label("MW shed", fontsize=8, color=INK2, labelpad=2)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.91, bottom=0.04, hspace=0.12)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_fuel_mix(t: pd.DataFrame, path: Path) -> None:
    mix = monthly_fuel_mix(t)
    shed = _observed(t)["shedding"].resample("MS").sum()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    series = [mix[k].fillna(0).values for k, _, _ in FUEL_STACK]
    ax.stackplot(mix.index, series, colors=[c for _, _, c in FUEL_STACK], edgecolor=SURFACE,
                 linewidth=1.0, labels=[n for _, n, _ in FUEL_STACK])
    ax.set_ylabel("Mean generation, MW", fontsize=9)
    ax.set_title("Fuel mix by month (observed hours only)", loc="left", fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _style_axes(ax)
    # direct labels on the right edge, positioned at each band's midpoint in the last full month
    last = mix.dropna(how="all").iloc[-2]
    cum = 0.0
    for k, name, color in FUEL_STACK:
        v = float(last[k]) if pd.notna(last[k]) else 0.0
        if v > 350:
            ax.annotate(name, (mix.index[-2], cum + v / 2), xytext=(6, 0), textcoords="offset points",
                        fontsize=8.5, color=INK, va="center", annotation_clip=False)
        cum += v
    ax.legend(loc="upper left", ncol=6, fontsize=8, frameon=False, handlelength=1.2)
    ax2.bar(shed.index, shed.values, width=25, color=INK2)  # neutral: blue already means Gas above
    ax2.set_ylabel("Hours with\nshedding", fontsize=9)
    ax2.grid(axis="y", color=GRID, linewidth=0.7)
    ax2.set_axisbelow(True)
    _style_axes(ax2)
    ax.set_xlim(mix.index[0], mix.index[-1])
    fig.subplots_adjust(left=0.08, right=0.93, top=0.93, bottom=0.07, hspace=0.12)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_hour_profile(t: pd.DataFrame, path: Path) -> None:
    years = [2022, 2023, 2024, 2025]
    prof = hour_profile(t, years)
    colors = [BLUE, ORANGE, AQUA, YELLOW]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for y, c in zip(years, colors):
        s = prof[y]
        ax.plot(s.index, s.values * 100, color=c, linewidth=2, marker="o", markersize=4,
                markeredgecolor=SURFACE, markeredgewidth=1.2)
        last = s.dropna()
        ax.annotate(str(y), (last.index[-1], last.values[-1] * 100), xytext=(6, 0),
                    textcoords="offset points", fontsize=9, color=INK, va="center")
    ax.axvspan(-0.5, 0.5, color=MISSING_GREY, alpha=0.5, linewidth=0)
    ax.text(0, ax.get_ylim()[1] * 0.97, "00:00 not\nin source", fontsize=8, color=INK2, ha="center", va="top")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(-0.5, 24.5)
    ax.set_xlabel("Hour of day", fontsize=9)
    ax.set_ylabel("% of hours with load shedding", fontsize=9)
    ax.set_title("When does shedding happen? Share of hours shedding, by hour of day", loc="left",
                 fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _style_axes(ax)
    ax.legend([plt.Line2D([], [], color=c, linewidth=2) for c in colors], [str(y) for y in years],
              loc="lower right", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(1.0, 0.0))
    fig.subplots_adjust(left=0.09, right=0.95, top=0.9, bottom=0.12)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_size_distribution(t: pd.DataFrame, path: Path) -> None:
    o = _observed(t)
    s = o.loc[o.shedding & (o.year >= 2022), "load_shedding"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    bins = np.arange(0, 3100, 100)
    ax.hist(s, bins=bins, color=BLUE, edgecolor=SURFACE, linewidth=1.0)
    ax.set_xlim(0, 3000)
    n_over = int((s > 3000).sum())
    ax.text(2980, ax.get_ylim()[1] * 0.5, f"{n_over} hours above 3,000 MW\n(max {s.max():,.0f} MW) not shown",
            fontsize=8.5, color=INK2, ha="right")
    med = float(s.median())
    ax.axvline(med, color=INK2, linewidth=1, linestyle=(0, (3, 3)))
    ax.annotate(f"median {med:,.0f} MW", (med, ax.get_ylim()[1] * 0.92), xytext=(6, 0),
                textcoords="offset points", fontsize=9, color=INK)
    ax.set_xlabel("Load shed in an hour, MW (hours with shedding, 2022 onward)", fontsize=9)
    ax.set_ylabel("Hours", fontsize=9)
    ax.set_title("How big is a shedding hour?", loc="left", fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _style_axes(ax)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.14)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run(clean_path: Path = config.CLEAN_HOURLY_PATH, out_dir: Path = FIG_DIR) -> str:
    t = pd.read_parquet(clean_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_fingerprint(t, out_dir / "fingerprint.png")
    fig_fuel_mix(t, out_dir / "fuel-mix.png")
    fig_hour_profile(t, out_dir / "hour-profile.png")
    fig_size_distribution(t, out_dir / "shedding-size.png")

    pd.options.display.float_format = "{:,.3f}".format
    prof = hour_profile(t, [2022, 2023, 2024, 2025])
    mon = month_profile(t, [2022, 2023, 2024, 2025])
    parts = [
        "Share of hours with shedding, by hour of day",
        (prof * 100).round(1).to_string(),
        "",
        "Share of hours with shedding, by month",
        (mon * 100).round(1).to_string(),
        "",
        "Size of a shedding hour (MW)",
        shedding_size_summary(t).to_string(),
        "",
        "Share of days on which each hour is observed (full period)",
        (coverage_by_hour(t) * 100).round(1).to_string(),
    ]
    return "\n".join(parts)
