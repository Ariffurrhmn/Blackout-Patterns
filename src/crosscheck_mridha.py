"""Independent cross-check of our national shedding target against Mridha (2026), Zenodo 21783853.

Read-only analysis. Nothing from the archive is executed; only its CSV tables are read.
Their area_demand_wide.csv has per-zone shedding (2016 onward) and a total; system_daily.csv
has a separate system-level load_shed_mw field.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as E  # noqa: E402

RAW = ROOT / "data/raw/crosscheck_mridha_zenodo21783853"
ZONES = {"Dhaka": "Dhaka", "Chattogram": "Chittagong", "Rajshahi": "Rajshahi", "Mymensingh": "Mymensingh",
         "Sylhet": "Sylhet", "Barishal": "Barisal", "Rangpur": "Rangpur", "Cumilla": "Comilla", "Khulna": "Khulna"}


def main() -> None:
    t = E.prepare()
    w = pd.read_csv(RAW / "area_demand_wide.csv", parse_dates=["date"]).set_index("date")
    s = pd.read_csv(RAW / "system_daily.csv", parse_dates=["date"]).set_index("date")["load_shed_mw"]
    idx = t.index[(t.index >= "2019-11-21") & (t.index <= "2024-12-30")]
    wz = w.reindex(idx)
    zone_cols = [f"{v}_loadshed_mw" for v in ZONES.values()]
    their_zone_sum = wz[zone_cols].sum(axis=1, min_count=len(zone_cols))
    their_total = wz["total_loadshed_mw"]
    ours = t["y"].reindex(idx)
    sys_field = s.reindex(idx)

    def agree(a, b):
        ok = a.notna() & b.notna()
        return {"days": int(ok.sum()), "exact_agreement": round(float((a[ok] == b[ok]).mean()), 3)}

    by_year = pd.DataFrame({"ours": ours, "theirs_total": their_total}).dropna()
    by_year = by_year.assign(match=lambda d: d.ours == d.theirs_total, year=lambda d: d.index.year)
    out = {
        "ours_vs_their_zone_sum": agree(ours, their_zone_sum),
        "ours_vs_their_total": agree(ours, their_total),
        "their_total_vs_their_zone_sum": agree(their_total, their_zone_sum),
        "their_system_field_vs_their_total": agree(sys_field, their_total),
        "by_year_ours_vs_their_total": {int(k): round(float(v), 3)
                                        for k, v in by_year.groupby("year").match.mean().items()},
        "zone_level_exact_agreement": {
            ours_name: round(float((t[f"{ours_name}_load"].reindex(idx) == wz[f"{theirs}_loadshed_mw"])
                                   [t[f"{ours_name}_load"].reindex(idx).notna() & wz[f"{theirs}_loadshed_mw"].notna()].mean()), 3)
            for ours_name, theirs in ZONES.items()},
    }
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed/crosscheck_mridha.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
