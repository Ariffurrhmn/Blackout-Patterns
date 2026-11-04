"""Load the raw PGCB file and produce a clean, hourly, flagged table.

Cleaning rules (all thresholds live in ``config.py``):

1. Parse timestamps; rows with an unparseable timestamp are dropped and counted.
2. Rows sharing a timestamp are averaged (duplicates are not silently dropped).
3. Half-hourly rows (early 2015) are resampled to hourly means. MW values are
   rates, so the mean over the hour is the right aggregate.
4. Impossible values (negative, or above the plausible ceilings) are set to NaN
   and recorded in a ``flag_bad_<role>`` column. Rows are never deleted for this.
5. Solar and wind stay NaN where missing; ``flag_missing_<role>`` records it.
6. ``supply_mw`` = generation + load shedding. Reported demand is censored while
   shedding is happening (it records what was served), so this is the better
   proxy for what the grid was asked to deliver.

The real column headers have not been inspected yet, so columns are matched to
*roles* by keyword (``infer_roles``). Pass ``overrides`` to pin any role
explicitly once the headers are known.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

# role -> regexes tried (in order) against the lower-cased, de-punctuated header.
# Order matters: more specific roles come first so e.g. "load shedding" is not
# claimed by a generic "load" pattern.
_ROLE_PATTERNS: dict[str, list[str]] = {
    "timestamp": [r"^(date ?time|timestamp|datetime|date and time)$", r"date.?time"],
    "date": [r"^date$", r"^day$"],
    "hour": [r"^(hour|hr|time)$"],
    "load_shedding": [r"shed", r"load ?cut", r"outage"],
    "generation": [r"^(total )?generation", r"^gen\b"],
    "demand": [r"demand"],
    "gas": [r"\bgas\b", r"\blng\b"],
    "liquid_fuel": [r"liquid", r"\boil\b", r"\bfuel oil\b", r"diesel", r"\bhfo\b"],
    "coal": [r"coal"],
    "hydro": [r"hydro"],
    "solar": [r"solar"],
    "wind": [r"wind"],
    "imports": [r"import", r"india", r"tripura", r"adani", r"nepal", r"bhutan"],
}

_FUEL_ROLES = ("gas", "liquid_fuel", "coal", "hydro", "solar", "wind", "imports")
_VALUE_ROLES = ("generation", "demand", "load_shedding") + _FUEL_ROLES


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(name).lower())).strip()


def infer_roles(columns: list[str], overrides: dict[str, str] | None = None) -> dict[str, list[str]]:
    """Map roles to the raw columns that fill them.

    Most roles map to a single column; ``imports`` can map to several (one per
    interconnector) and they are summed during cleaning. A raw column is only
    assigned to one role. ``overrides`` replaces the inference for a role.
    """
    overrides = overrides or {}
    roles: dict[str, list[str]] = {}
    taken: set[str] = set()

    for role, col in overrides.items():
        if col not in columns:
            raise KeyError(f"override for role {role!r} names unknown column {col!r}")
        roles[role] = [col]
        taken.add(col)

    for role, patterns in _ROLE_PATTERNS.items():
        if role in roles:
            continue
        if role == "imports":
            # Imports legitimately span several interconnector columns: collect
            # every column matching any pattern, not just the first pattern.
            hits = [c for c in columns if c not in taken and any(re.search(p, _norm(c)) for p in patterns)]
            if hits:
                roles[role] = hits
                taken.update(hits)
            continue
        for pat in patterns:
            hits = [c for c in columns if c not in taken and re.search(pat, _norm(c))]
            if hits:
                roles[role] = hits[:1]
                taken.update(hits[:1])
                break
    return roles


@dataclass
class CleaningReport:
    """What the cleaning step did. Written next to the output for the data report."""

    rows_in: int = 0
    rows_dropped_bad_timestamp: int = 0
    duplicate_timestamps_merged: int = 0
    halfhourly_rows_resampled: int = 0
    rows_out: int = 0
    first_timestamp: str = ""
    last_timestamp: str = ""
    roles: dict[str, list[str]] = field(default_factory=dict)
    bad_values: dict[str, int] = field(default_factory=dict)
    missing_share: dict[str, float] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# Cleaning report",
            "",
            f"- rows in: {self.rows_in:,}",
            f"- dropped (unparseable timestamp): {self.rows_dropped_bad_timestamp:,}",
            f"- duplicate timestamps merged: {self.duplicate_timestamps_merged:,}",
            f"- sub-hourly rows folded into hours: {self.halfhourly_rows_resampled:,}",
            f"- hourly rows out: {self.rows_out:,} ({self.first_timestamp} to {self.last_timestamp})",
            "",
            "## Column roles",
            "",
            *[f"- `{role}`: {', '.join(f'`{c}`' for c in cols)}" for role, cols in self.roles.items()],
            "",
            "## Impossible values set to NaN",
            "",
            *([f"- `{r}`: {n:,}" for r, n in self.bad_values.items()] or ["- none"]),
            "",
            "## Missing share after cleaning",
            "",
            *[f"- `{r}`: {s:.1%}" for r, s in self.missing_share.items()],
            "",
        ]
        return "\n".join(lines)


def _parse_timestamp(df: pd.DataFrame, roles: dict[str, list[str]]) -> pd.Series:
    if "timestamp" in roles:
        return pd.to_datetime(df[roles["timestamp"][0]], errors="coerce")
    if "date" in roles and "hour" in roles:
        date = pd.to_datetime(df[roles["date"][0]], errors="coerce")
        hour = df[roles["hour"][0]]
        if not pd.api.types.is_numeric_dtype(hour):
            # accepts "13:00" style strings as well as 0-23 integers
            hour = pd.to_timedelta(hour.astype(str), errors="coerce").dt.total_seconds() / 3600
        return date + pd.to_timedelta(hour, unit="h")
    if "date" in roles:
        return pd.to_datetime(df[roles["date"][0]], errors="coerce")
    raise ValueError(
        "could not find a timestamp: expected a datetime column, or a date + hour pair. "
        f"Columns seen: {list(df.columns)}. Pass overrides={{'timestamp': '<column>'}}."
    )


def _plausible_max(role: str, column: str) -> float:
    if role == "imports":
        name = _norm(column)
        for key, ceiling in config.MAX_PLAUSIBLE_IMPORT_MW.items():
            if key in name:
                return ceiling
        return config.MAX_PLAUSIBLE_IMPORT_DEFAULT_MW
    return config.MAX_PLAUSIBLE_MW[role]


def clean(
    raw: pd.DataFrame, overrides: dict[str, str] | None = None
) -> tuple[pd.DataFrame, CleaningReport]:
    """Return ``(hourly_table, report)`` for a raw PGCB frame."""
    roles = infer_roles(list(raw.columns), overrides)
    report = CleaningReport(rows_in=len(raw), roles=roles)

    for needed in ("load_shedding", "generation"):
        if needed not in roles:
            raise ValueError(
                f"no column found for role {needed!r}. Columns seen: {list(raw.columns)}. "
                f"Pass overrides={{'{needed}': '<column>'}}."
            )

    ts = _parse_timestamp(raw, roles)
    ok = ts.notna()
    report.rows_dropped_bad_timestamp = int((~ok).sum())

    # Impossible-value rules come first, per raw column and before any
    # aggregation, so one 64-million MW row cannot poison an hourly mean or an
    # import sum. The offending reading becomes NaN; the row is kept.
    values = pd.DataFrame(index=raw.index[ok])
    bad_roles = pd.DataFrame(index=raw.index[ok])
    for role in _VALUE_ROLES:
        if role not in roles:
            continue
        cols = raw.loc[ok, roles[role]].apply(pd.to_numeric, errors="coerce")
        bad_any = pd.Series(False, index=cols.index)
        for col in cols:
            bad = (cols[col] < config.MIN_PLAUSIBLE_MW) | (cols[col] > _plausible_max(role, col))
            bad_any |= bad.fillna(False)
            cols.loc[bad, col] = np.nan
        if bad_any.any():
            report.bad_values[role] = int(bad_any.sum())
        values[role] = cols.sum(axis=1, min_count=1)  # imports: sum of interconnectors
        bad_roles[f"flag_bad_{role}"] = bad_any
    values.index = pd.DatetimeIndex(ts[ok], name="timestamp")
    bad_roles.index = values.index
    order = values.index.argsort(kind="stable")
    values, bad_roles = values.iloc[order], bad_roles.iloc[order]

    report.duplicate_timestamps_merged = int(values.index.duplicated().sum())
    values = values.groupby(level=0).mean()
    flags = bad_roles.groupby(level=0).max()

    # Sub-hourly rows -> hourly means.
    hour_index = values.index.floor("h")
    report.halfhourly_rows_resampled = int(len(values) - hour_index.nunique())
    hourly = values.groupby(hour_index).mean()
    hourly_flags = flags.groupby(hour_index).max()
    hourly.index.name = "timestamp"
    out = hourly.join(hourly_flags)

    # Renewable missingness is recorded, never imputed here.
    for role in config.RENEWABLE_ROLES:
        if role in out:
            out[f"flag_missing_{role}"] = out[role].isna()

    out["supply_mw"] = out["generation"] + out["load_shedding"].fillna(0.0)
    out["shedding"] = out["load_shedding"].fillna(0.0) > 0
    out["year"] = out.index.year

    report.rows_out = len(out)
    report.first_timestamp = str(out.index.min())
    report.last_timestamp = str(out.index.max())
    report.missing_share = {
        r: float(out[r].isna().mean()) for r in _VALUE_ROLES if r in out
    }
    return out, report


def read_raw(path: Path | str) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python scripts/download_data.py` for download instructions."
        )
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)
