"""Paths, data sources and cleaning thresholds in one place.

Every threshold here is a documented *assumption*. They are starting values
taken from the first profile in docs/research/ideas-round-1.md and must be
reviewed against the real data during EDA (plan, week 3). Change them here,
not inline, so each cleaning rule stays visible and justified.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
REPORTS = ROOT / "reports"

# Expected file name of the main dataset once downloaded (see scripts/download_data.py).
MAIN_DATASET_NAME = "pgcb_hourly_mendeley.csv"
MAIN_DATASET_PATH = DATA_RAW / MAIN_DATASET_NAME
CLEAN_HOURLY_PATH = DATA_INTERIM / "hourly_clean.parquet"

DATASETS = {
    "main": {
        "title": "Hourly electricity generation, demand, load shedding and fuel mix, 2015-2026",
        "landing_page": "https://data.mendeley.com/datasets/vpk8spw2mm/1",
        "licence": "CC BY 4.0",
        "target": MAIN_DATASET_NAME,
    },
    "uci": {
        "title": "PGCB Hourly Generation Dataset (UCI mirror, cross-check)",
        "landing_page": "https://archive.ics.uci.edu/dataset/1175/pgcb+hourly+generation+dataset",
        "licence": "CC BY 4.0",
        "target": "pgcb_hourly_uci.xlsx",
    },
}

# --- Impossible-value rules (MW) ------------------------------------------------
# A reading outside these bounds is set to NaN and flagged; the row is kept.
# Rationale: the first profile found 64,526,500 MW "generation" (2023) and a
# 65,359 MW load-shedding value (2017). Bangladesh's peak generation is in the
# mid-teens of GW and installed capacity in the high twenties, so 30,000 MW is a
# generous ceiling. Shedding of several GW happens; tens of GW does not.
MAX_PLAUSIBLE_GENERATION_MW = 30_000.0
MAX_PLAUSIBLE_SHEDDING_MW = 6_000.0
MAX_PLAUSIBLE_FUEL_MW = 30_000.0  # any single fuel / import column
MIN_PLAUSIBLE_MW = 0.0  # negative readings are treated as errors

# Solar and wind are 22% / 74% missing. Cleaning leaves them as NaN and adds a
# missing flag; only the fuel-share step may treat them as 0 (see features.py).
RENEWABLE_ROLES = ("solar", "wind")

# Regime boundary used for the calendar-split baseline (README, "Approach").
BASELINE_SPLIT_DATE = "2022-01-01"
