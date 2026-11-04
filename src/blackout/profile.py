"""First profile of the cleaned data: reproduces the README's headline numbers.

Run ``blackout profile`` once the data is downloaded. The yearly shedding-hour
counts printed here should be compared with the figures in the README chart
(22, 46, 7, 12, 12, 6, 3, then 2,287 / 5,012 / 5,034 / 3,316 for 2015-2025).
Differences are expected where cleaning removes impossible values or where the
dataset has been revised; they must be explained in the data report.
"""

from __future__ import annotations

import pandas as pd

# Figures recorded in docs/research/ideas-round-1.md (profile of the raw file).
README_SHEDDING_HOURS = {
    2015: 22, 2016: 46, 2017: 7, 2018: 12, 2019: 12, 2020: 6, 2021: 3,
    2022: 2287, 2023: 5012, 2024: 5034, 2025: 3316,
}


def shedding_hours_per_year(clean: pd.DataFrame) -> pd.Series:
    """Hours per calendar year with load shedding > 0 MW."""
    return clean[clean["observed"]].groupby("year")["shedding"].sum().astype(int).rename("shedding_hours")


def compare_with_readme(clean: pd.DataFrame) -> pd.DataFrame:
    got = shedding_hours_per_year(clean)
    expected = pd.Series(README_SHEDDING_HOURS, name="readme")
    out = pd.concat([got, expected], axis=1).sort_index().astype("Int64")
    out.index.name = "year"
    out["difference"] = out["shedding_hours"] - out["readme"]
    return out


def liquid_fuel_change_correlation(clean: pd.DataFrame) -> dict[str, float]:
    """Spearman correlation of daily changes, liquid fuel vs shedding.

    README reports 0.01 for 2018-2021 and 0.43 for Jul 2022-2024.
    """
    if "liquid_fuel" not in clean:
        return {}
    daily = clean[["liquid_fuel", "load_shedding"]].resample("D").mean().diff().dropna()
    windows = {"2018-2021": ("2018-01-01", "2021-12-31"), "2022-07 to 2024": ("2022-07-01", "2024-12-31")}
    return {
        name: float(daily.loc[lo:hi].corr(method="spearman").iloc[0, 1])
        for name, (lo, hi) in windows.items()
    }


def text_profile(clean: pd.DataFrame) -> str:
    parts = [
        "Shedding hours per year (cleaned) vs README figures",
        compare_with_readme(clean).to_string(),
    ]
    corr = liquid_fuel_change_correlation(clean)
    if corr:
        parts += ["", "Spearman, daily change in liquid fuel vs load shedding (README: 0.01 then 0.43)"]
        parts += [f"  {k}: {v:.2f}" for k, v in corr.items()]
    return "\n".join(parts)
