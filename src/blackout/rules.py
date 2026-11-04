"""Association rules and emerging patterns on discretised hourly states (mlxtend).

Items come from ``features.transactions`` (season, hour band, weekday/weekend, and
low/mid/high terciles of gas, liquid-fuel, coal and import shares). The target is
``shed=high`` (an hour with at least 500 MW shed).

* Baseline: Apriori on all years, ranked by confidence.
* Interesting: FP-Growth on the crisis training period (CRISIS_START .. 2024), rules
  ranked by lift / conviction / leverage, with calendar-only rules flagged as obvious.
* Emerging patterns (Dong & Li, 1999): itemsets whose support grows from *no-shedding*
  hours to *high-shedding* hours inside the training period. Growth rate = supp_high / supp_none.
* Temporal hold-out: every mined rule is re-scored on the hold-out year (2025).

Metrics are computed from the frequent-itemset table directly (support is anti-monotone, so
every antecedent of a frequent itemset is itself in the table), which avoids depending on a
particular mlxtend ``association_rules`` signature.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, fpgrowth

from . import config

TARGET = "shed=high"
CALENDAR_ITEMS = ("season=", "hour=", "day=")
CONDITION_COLS = ["season", "hour", "day", "gas", "liquid_fuel", "coal", "imports"]


def onehot(tx: pd.DataFrame) -> pd.DataFrame:
    """Boolean item matrix. Columns look like ``gas=low``; ``shed=high`` is the target."""
    cols = CONDITION_COLS + ["shed"]
    x = pd.get_dummies(tx[cols].astype(str), prefix_sep="=").astype(bool)
    return x[[c for c in x.columns if c != "shed=none" and c != "shed=low"] ]


def _freq(x: pd.DataFrame, miner: str, min_support: float, max_len: int) -> pd.DataFrame:
    fn = {"apriori": apriori, "fpgrowth": fpgrowth}[miner]
    f = fn(x, min_support=min_support, use_colnames=True, max_len=max_len)
    f["itemsets"] = f["itemsets"].apply(frozenset)
    return f.set_index("itemsets")["support"]


def rules_from_itemsets(supp: pd.Series, target: str = TARGET) -> pd.DataFrame:
    rows = []
    t_supp = supp.get(frozenset([target]), np.nan)
    for items, s_xy in supp.items():
        if target not in items or len(items) < 2:
            continue
        ante = items - {target}
        s_x = supp.get(ante)
        if s_x is None:
            continue
        conf = s_xy / s_x
        lift = conf / t_supp
        conviction = (1 - t_supp) / (1 - conf) if conf < 1 else np.inf
        # Does the fuel part add anything beyond the calendar part (season / hour band / day type)?
        cal = frozenset(i for i in ante if i.startswith(CALENDAR_ITEMS))
        if cal and cal != ante:
            s_c, s_cy = supp.get(cal), supp.get(cal | {target})
            lift_vs_cal = conf / (s_cy / s_c) if s_c and s_cy else np.nan
        else:
            lift_vs_cal = np.nan
        rows.append({"antecedent": ", ".join(sorted(ante)), "n_items": len(ante), "support": s_xy,
                     "antecedent_support": s_x, "confidence": conf, "lift": lift,
                     "leverage": s_xy - s_x * t_supp, "conviction": conviction, "lift_vs_calendar": lift_vs_cal,
                     "calendar_only": all(i.startswith(CALENDAR_ITEMS) for i in ante)})
    return pd.DataFrame(rows).sort_values("lift", ascending=False).reset_index(drop=True)


def baseline_apriori(tx: pd.DataFrame, min_support: float = 0.01, max_len: int = 4) -> tuple[pd.DataFrame, float]:
    """Apriori on ALL years, ranked by confidence (the naive baseline)."""
    x = onehot(tx)
    t0 = time.time()
    supp = _freq(x, "apriori", min_support, max_len)
    r = rules_from_itemsets(supp).sort_values("confidence", ascending=False).reset_index(drop=True)
    return r, time.time() - t0


def mine_crisis_rules(tx: pd.DataFrame, min_support: float = 0.01, max_len: int = 4):
    """FP-Growth on the crisis training period; returns (rules, seconds, train transactions)."""
    train = tx[(tx.index >= config.CRISIS_START) & (tx["year"] < config.HOLDOUT_YEAR)]
    x = onehot(train)
    t0 = time.time()
    supp = _freq(x, "fpgrowth", min_support, max_len)
    return rules_from_itemsets(supp), time.time() - t0, train


def emerging_patterns(train: pd.DataFrame, min_support_high: float = 0.03, max_len: int = 3,
                      fuel_only: bool = False) -> pd.DataFrame:
    """Itemsets over the condition columns whose support grows from none -> high shedding.

    ``fuel_only`` drops the calendar items (season, hour band, day type) so that the patterns
    describe the fuel mix alone.
    """
    x = onehot(train[CONDITION_COLS + ["shed"]])
    cond = x.drop(columns=[TARGET])
    if fuel_only:
        cond = cond[[c for c in cond.columns if not c.startswith(CALENDAR_ITEMS)]]
    high, none = cond[x[TARGET].values], cond[(train["shed"] == "none").values]
    s_hi = _freq(high, "fpgrowth", min_support_high, max_len)
    rows = []
    for items, sh in s_hi.items():
        mask = np.logical_and.reduce([none[i].to_numpy() for i in items])
        sn = mask.mean()
        rows.append({"pattern": ", ".join(sorted(items)), "n_items": len(items),
                     "support_high": sh, "support_none": sn,
                     "growth_rate": sh / sn if sn > 0 else np.inf,
                     "calendar_only": all(i.startswith(CALENDAR_ITEMS) for i in items)})
    return pd.DataFrame(rows).sort_values(["growth_rate", "support_high"], ascending=False).reset_index(drop=True)


def holdout_check(rules: pd.DataFrame, tx: pd.DataFrame, year: int = config.HOLDOUT_YEAR) -> pd.DataFrame:
    """Re-score rules on ``year``: confidence and lift there against that year's own base rate."""
    h = tx[tx["year"] == year]
    x = onehot(h)
    base = x[TARGET].mean()
    out = []
    for _, r in rules.iterrows():
        items = r["antecedent"].split(", ")
        mask = np.logical_and.reduce([x[i].to_numpy() if i in x else np.zeros(len(x), bool) for i in items])
        n = int(mask.sum())
        conf = float(x.loc[mask, TARGET].mean()) if n else np.nan
        out.append({"antecedent": r["antecedent"], "train_lift": r["lift"], "train_confidence": r["confidence"],
                    "holdout_n": n, "holdout_confidence": conf,
                    "holdout_lift": conf / base if n and base > 0 else np.nan, "holdout_base_rate": base})
    return pd.DataFrame(out)
