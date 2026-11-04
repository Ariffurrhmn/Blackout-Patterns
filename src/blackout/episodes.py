"""Sequential patterns before shedding episodes (PrefixSpan, implemented here).

An *onset* is a crisis day with at least ``ONSET_HOURS`` shedding hours that follows a quiet
day (fewer than ``QUIET_HOURS``). Each day is described by tokens for unusual day-over-day
moves in the fuel mix (bottom / top quintile of the crisis-period changes). The sequence for an
onset is the tokens of the ``LOOKBACK`` days before it. Frequent subsequences are then compared
with control sequences taken before days where the quiet continued: a pattern is only
interesting if it is clearly more common before onsets than before quiet days.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from . import config

ONSET_HOURS, QUIET_HOURS, LOOKBACK = 6, 3, 3
MOVES = {"gas": "gas_mw", "liquid": "liquid_fuel", "coal": "coal", "imports": "imports"}


def prefixspan(db: list[list[str]], min_count: int, max_len: int = 3) -> list[tuple[tuple[str, ...], int]]:
    """Frequent subsequences (order kept, gaps allowed) of single items. Classic PrefixSpan."""
    out: list[tuple[tuple[str, ...], int]] = []

    def grow(prefix: tuple[str, ...], projected: list[list[str]]):
        counts: dict[str, int] = defaultdict(int)
        for seq in projected:
            for item in set(seq):
                counts[item] += 1
        for item, c in sorted(counts.items()):
            if c < min_count:
                continue
            new = prefix + (item,)
            out.append((new, c))
            if len(new) < max_len:
                nxt = [seq[seq.index(item) + 1:] for seq in projected if item in seq]
                grow(new, nxt)

    grow((), db)
    return out


def day_tokens(daily: pd.DataFrame, start: str = config.CRISIS_START, q: float = 0.2) -> pd.Series:
    """Per-day list of tokens such as ``gas_down`` / ``liquid_up`` (extreme day-over-day changes)."""
    d = daily.loc[start:].copy()
    d["gas_mw"] = d["gas"]
    tok = pd.Series([[] for _ in range(len(d))], index=d.index, dtype=object)
    for name, col in MOVES.items():
        chg = d[col].pct_change().replace([np.inf, -np.inf], np.nan)
        lo, hi = chg.quantile([q, 1 - q])
        for i, v in enumerate(chg.values):
            if v == v and v <= lo:
                tok.iloc[i] = tok.iloc[i] + [f"{name}_down"]
            elif v == v and v >= hi:
                tok.iloc[i] = tok.iloc[i] + [f"{name}_up"]
    return tok


def build_sequences(daily: pd.DataFrame, seed: int = config.RANDOM_SEED):
    d = daily.loc[config.CRISIS_START:]
    tok = day_tokens(daily)
    prev_quiet = d["shed_hours"].shift(1) < QUIET_HOURS
    onset = (d["shed_hours"] >= ONSET_HOURS) & prev_quiet
    control = (d["shed_hours"] < QUIET_HOURS) & prev_quiet
    idx = {dt: i for i, dt in enumerate(tok.index)}

    def seqs(mask):
        out = []
        for dt in d.index[mask.fillna(False)]:
            i = idx[dt]
            if i >= LOOKBACK:
                out.append([t for k in range(i - LOOKBACK, i) for t in sorted(tok.iloc[k])])
        return out

    onsets, controls = seqs(onset), seqs(control)
    rng = np.random.default_rng(seed)
    if len(controls) > len(onsets):
        controls = [controls[i] for i in rng.choice(len(controls), len(onsets), replace=False)]
    return onsets, controls


def mine(daily: pd.DataFrame, min_support: float = 0.10, max_len: int = 3) -> pd.DataFrame:
    onsets, controls = build_sequences(daily)
    pats = prefixspan(onsets, max(2, int(np.ceil(min_support * len(onsets)))), max_len)
    rows = []
    for pat, c in pats:
        cc = sum(_contains(s, pat) for s in controls)
        sup_o, sup_c = c / len(onsets), cc / max(len(controls), 1)
        _, p = fisher_exact([[c, len(onsets) - c], [cc, len(controls) - cc]])
        rows.append({"pattern": " -> ".join(pat), "length": len(pat), "support_onset": sup_o,
                     "support_control": sup_c, "gap": sup_o - sup_c, "fisher_p": p,
                     "ratio": sup_o / sup_c if sup_c > 0 else np.inf,
                     "n_onsets": len(onsets), "n_controls": len(controls)})
    df = pd.DataFrame(rows)
    return df.sort_values(["gap", "support_onset"], ascending=False).reset_index(drop=True) if len(df) else df


def permutation_null(daily: pd.DataFrame, n_perm: int = 200, min_support: float = 0.10, max_len: int = 3,
                     seed: int = config.RANDOM_SEED) -> np.ndarray:
    """Largest (support_group_a - support_group_b) over all patterns when onset/control labels are shuffled.

    With hundreds of candidate patterns and only ~50 sequences per group, some pattern always
    looks good by chance; this gives the distribution of that best-by-chance gap.
    """
    onsets, controls = build_sequences(daily)
    pool = onsets + controls
    n = len(onsets)
    rng = np.random.default_rng(seed)
    gaps = []
    for _ in range(n_perm):
        idx = rng.permutation(len(pool))
        a, b = [pool[i] for i in idx[:n]], [pool[i] for i in idx[n:]]
        pats = prefixspan(a, max(2, int(np.ceil(min_support * n))), max_len)
        gaps.append(max((c / n - sum(_contains(s, p) for s in b) / len(b) for p, c in pats), default=0.0))
    return np.array(gaps)


def _contains(seq: list[str], pat: tuple[str, ...]) -> bool:
    it = iter(seq)
    return all(any(x == p for x in it) for p in pat)
