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
# A reading outside [MIN, ceiling] is set to NaN and flagged; the row is kept.
# Ceilings are per source and applied to each raw column *before* imports are
# summed. They were set from the upper tail of the real file (v1, 94,934 rows):
# each is roughly 1.2-2x the 99.9th percentile and sits in a visible gap between
# the plausible tail and the glitches (e.g. hydro: 99.9th pct 265 MW, Kaptai is
# ~230 MW, but 32 readings are 1,000-5,600 MW; coal: 7,329 then 11,991 then
# 22,206). Glitches in the file include 64,526,500 MW generation, 29,222,897 MW
# liquid fuel and 65,359 MW shedding. Revisit these if the dataset version changes.
MAX_PLAUSIBLE_MW = {
    "generation": 20_000.0,  # real max 16,794
    "demand": 20_000.0,  # plausible tail ends at 17,200; next value is 20,587
    "load_shedding": 6_000.0,  # 99.9th pct 4,821; values above 6,000 are isolated
    "gas": 12_000.0,
    "liquid_fuel": 12_000.0,
    "coal": 9_000.0,
    "hydro": 500.0,
    "solar": 1_500.0,
    "wind": 200.0,
}
# Imports are checked per interconnector column, matched by keyword in the header.
MAX_PLAUSIBLE_IMPORT_MW = {"bheramara": 1_500.0, "tripura": 400.0, "adani": 2_000.0, "nepal": 100.0}
MAX_PLAUSIBLE_IMPORT_DEFAULT_MW = 2_000.0
MIN_PLAUSIBLE_MW = 0.0  # negative readings are treated as errors

# Solar and wind are 22% / 74% missing. Cleaning leaves them as NaN and adds a
# missing flag; only the fuel-share step may treat them as 0 (see features.py).
RENEWABLE_ROLES = ("solar", "wind")

# Regime boundary used for the calendar-split baseline (README, "Approach").
BASELINE_SPLIT_DATE = "2022-01-01"
