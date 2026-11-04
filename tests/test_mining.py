"""Tests for the mining modules, on small SYNTHETIC inputs with known answers."""

import numpy as np
import pandas as pd
import pytest

from blackout import anomalies, episodes, motifs, regimes, rules
from blackout.features import day_matrix, hour_band, tercile_labels


def test_prefixspan_finds_ordered_subsequences_with_gaps():
    db = [["a", "b", "c"], ["a", "c"], ["b", "a", "c"], ["a", "x", "c"]]
    got = {p: c for p, c in episodes.prefixspan(db, min_count=3, max_len=3)}
    assert got[("a",)] == 4 and got[("a", "c")] == 4  # gap allowed
    assert ("c", "a") not in got  # order matters (only 0 sequences have c before a)
    assert ("a", "b") not in got  # only 1 sequence


def test_contains_subsequence_respects_order():
    assert episodes._contains(["a", "x", "b"], ("a", "b"))
    assert not episodes._contains(["b", "a"], ("a", "b"))


def test_pelt_recovers_a_known_step_and_refines_to_the_day():
    idx = pd.date_range("2020-01-01", periods=600, freq="D")
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"a": np.r_[rng.normal(0, 1, 300), rng.normal(6, 1, 300)]}, index=idx)
    (b,) = regimes.pelt(x, c=8)
    assert abs((b - idx[300]).days) <= 2
    best, _ = regimes.best_single_break(x)
    assert abs((best - idx[300]).days) <= 2


def test_rules_metrics_on_a_tiny_itemset_table():
    f = frozenset
    supp = pd.Series({f(["shed=high"]): 0.2, f(["gas=low"]): 0.5, f(["season=monsoon"]): 0.4,
                      f(["gas=low", "shed=high"]): 0.15, f(["gas=low", "season=monsoon"]): 0.3,
                      f(["season=monsoon", "shed=high"]): 0.16,
                      f(["gas=low", "season=monsoon", "shed=high"]): 0.12})
    r = rules.rules_from_itemsets(supp).set_index("antecedent")
    row = r.loc["gas=low"]
    assert row["confidence"] == pytest.approx(0.3) and row["lift"] == pytest.approx(1.5)
    both = r.loc["gas=low, season=monsoon"]
    assert both["confidence"] == pytest.approx(0.4)
    # calendar part "season=monsoon" alone has confidence 0.4, so the fuel part adds nothing
    assert both["lift_vs_calendar"] == pytest.approx(1.0)
    assert not both["calendar_only"] and r.loc["season=monsoon"]["calendar_only"]


def test_matrix_profile_motifs_ignore_flat_zero_windows():
    idx = pd.date_range("2022-07-01", periods=200, freq="D")
    v = np.zeros(200)
    v[40:47] = [5, 6, 7, 6, 5, 4, 3]   # one shape ...
    v[120:127] = [5, 6, 7, 6, 5, 4, 3]  # ... repeated: the real motif
    rng = np.random.default_rng(1)
    v[80:87] = rng.uniform(4, 7, 7)
    s = pd.Series(v, index=idx)
    mp = motifs.matrix_profile(s, 7)
    top = motifs.motifs(mp, 7, k=1).iloc[0]
    # z-normalised matching also accepts a window shifted by a few quiet days, so check that
    # both windows of the pair overlap one planted copy each (not an exact start day).
    starts = sorted([top["start"], top["neighbour_start"]])
    assert abs((starts[0] - idx[40]).days) <= 6 and abs((starts[1] - idx[120]).days) <= 6
    assert top["distance"] < 0.5


def test_robust_z_scale_is_floored_at_a_tenth_of_the_std_when_mad_is_zero():
    x = pd.Series([0.0] * 500 + [0.01, 0.0, 0.5] * 5)  # MAD = 0
    z = anomalies._robust_z(x)
    assert z.iloc[-1] == pytest.approx((0.5 - x.median()) / (0.1 * x.std()))
    # without the floor this would be division by ~0
    assert np.isfinite(z).all()
    y = pd.Series(np.random.default_rng(0).normal(0, 1, 1000))  # normal data: MAD dominates, z ~ N(0,1)
    assert abs(anomalies._robust_z(y).std() - 1) < 0.1


def test_day_matrix_drops_sparse_days_and_interpolates_small_gaps():
    idx = pd.date_range("2023-01-01 01:00", periods=23, freq="h").append(
        pd.date_range("2023-01-02 01:00", periods=10, freq="h"))
    t = pd.DataFrame({"observed": True, "load_shedding": np.arange(33, dtype=float)}, index=idx)
    t = t.drop(index=pd.Timestamp("2023-01-01 05:00"))  # one missing hour on day 1
    m, info = day_matrix(t)
    assert info["days_dropped"] == 1 and info["days_interpolated"] == 1
    assert m.shape == (1, 23) and not m.isna().any().any()


def test_discretisation_helpers():
    assert [hour_band(h) for h in (1, 8, 14, 19, 23)] == ["night", "morning", "afternoon", "evening", "night"]
    lab = tercile_labels(pd.Series(range(9)))
    assert lab.tolist() == ["low"] * 3 + ["mid"] * 3 + ["high"] * 3
