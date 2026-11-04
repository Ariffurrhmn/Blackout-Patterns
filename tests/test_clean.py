"""Tests for the cleaning rules, on SYNTHETIC data only.

The frame below imitates the problems found in the first profile (half-hourly
rows, absurd values, missing solar). Its column names are made up; the real
headers are not known yet, so these tests check behaviour, not the real schema.
"""

import numpy as np
import pandas as pd
import pytest

from blackout.clean import clean, infer_roles
from blackout.profile import shedding_hours_per_year


def make_raw() -> pd.DataFrame:
    half = pd.date_range("2015-04-17 00:00", periods=4, freq="30min")  # 2 hours, half-hourly
    hourly = pd.date_range("2023-06-01 00:00", periods=6, freq="h")
    ts = list(half) + list(hourly)
    n = len(ts)
    df = pd.DataFrame(
        {
            "Date Time": ts,
            "Total Generation (MW)": [5000.0] * n,
            "Demand (MW)": [5200.0] * n,
            "Load Shedding (MW)": [0.0] * n,
            "Gas": [3000.0] * n,
            "Liquid Fuel": [500.0] * n,
            "Coal": [1000.0] * n,
            "Solar": [np.nan] * n,
            "Wind": [np.nan] * n,
            "India Bheramara": [300.0] * n,
            "India Tripura": [100.0] * n,
        }
    )
    df.loc[4, "Total Generation (MW)"] = 64_526_500.0  # the 2023 glitch
    df.loc[5, "Load Shedding (MW)"] = 65_359.0  # the 2017 glitch
    df.loc[6, "Load Shedding (MW)"] = 800.0  # real shedding
    df.loc[7, "Gas"] = -50.0
    return df


def test_role_inference_groups_imports():
    roles = infer_roles(list(make_raw().columns))
    assert roles["timestamp"] == ["Date Time"]
    assert roles["load_shedding"] == ["Load Shedding (MW)"]
    assert roles["generation"] == ["Total Generation (MW)"]
    assert roles["demand"] == ["Demand (MW)"]
    assert roles["imports"] == ["India Bheramara", "India Tripura"]


def test_override_wins_and_unknown_column_errors():
    cols = list(make_raw().columns)
    assert infer_roles(cols, {"gas": "Coal"})["gas"] == ["Coal"]
    with pytest.raises(KeyError):
        infer_roles(cols, {"gas": "nope"})


def test_halfhourly_rows_become_hourly():
    out, report = clean(make_raw())
    assert out.index.is_unique
    assert pd.Timestamp("2015-04-17 00:00") in out.index
    assert pd.Timestamp("2015-04-17 00:30") not in out.index
    assert report.halfhourly_rows_resampled == 2
    assert (out.index == out.index.floor("h")).all()


def test_impossible_values_are_nan_flagged_and_rows_kept():
    out, report = clean(make_raw())
    h4 = pd.Timestamp("2023-06-01 00:00") + pd.Timedelta(hours=0)  # row 4
    assert np.isnan(out.loc[h4, "generation"])
    assert out.loc[h4, "flag_bad_generation"]
    assert out["generation"].max() < 30_000
    assert report.bad_values["generation"] == 1
    assert report.bad_values["load_shedding"] == 1
    assert report.bad_values["gas"] == 1  # negative reading
    assert len(out) == 8  # nothing dropped: 2 half-hourly hours + 6 hourly


def test_glitch_does_not_count_as_shedding_but_real_shedding_does():
    out, _ = clean(make_raw())
    assert out["shedding"].sum() == 1
    assert shedding_hours_per_year(out).loc[2023] == 1


def test_renewables_stay_nan_with_flag_and_imports_are_summed():
    out, report = clean(make_raw())
    assert out["solar"].isna().all() and out["flag_missing_solar"].all()
    assert (out["imports"] == 400.0).all()
    assert report.missing_share["solar"] == 1.0


def test_supply_is_generation_plus_shedding():
    out, _ = clean(make_raw())
    row = out.loc[pd.Timestamp("2023-06-01 02:00")]
    assert row["supply_mw"] == pytest.approx(row["generation"] + row["load_shedding"])


def test_duplicate_timestamps_are_merged_not_dropped_silently():
    raw = make_raw()
    raw = pd.concat([raw, raw.iloc[[8]]], ignore_index=True)
    _, report = clean(raw)
    assert report.duplicate_timestamps_merged == 1


def test_missing_required_role_gives_clear_error():
    raw = make_raw().drop(columns=["Load Shedding (MW)"])
    with pytest.raises(ValueError, match="load_shedding"):
        clean(raw)


def test_date_plus_hour_columns_supported():
    raw = pd.DataFrame(
        {
            "Date": ["2022-01-01"] * 3,
            "Hour": [0, 1, 2],
            "Generation": [5000.0, 5100.0, 5200.0],
            "Load Shedding": [0.0, 0.0, 100.0],
        }
    )
    out, _ = clean(raw)
    assert list(out.index.hour) == [0, 1, 2]
    assert out["shedding"].tolist() == [False, False, True]
