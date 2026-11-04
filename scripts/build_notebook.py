#!/usr/bin/env python3
"""Build notebooks/blackout_patterns_demo.ipynb from the package source.

The notebook is self-contained: one cell per module writes that module's source into
``notebooks/_nb_pkg/blackout/`` (``%%writefile``), then the analysis cells import it and run
every stage. So *all* project code is visible in the notebook and running it top to bottom
rebuilds and executes the whole pipeline. The source files in ``src/`` stay the single source
of truth; this script just copies them in. Re-run it after changing any module:

    python scripts/build_notebook.py [--execute]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "blackout"
NB = ROOT / "notebooks" / "blackout_patterns_demo.ipynb"

# order matters: each module may import the ones before it
MODULES = [
    ("config", "Paths, data sources, cleaning ceilings, mining settings and event dates."),
    ("clean", "Raw CSV -> hourly table: column roles, half-hourly folding, impossible-value rules, explicit missing hours."),
    ("profile", "Reproduces the README's first profile (yearly shedding hours, liquid-fuel correlation)."),
    ("features", "Daily table, 23-hour day matrix (midnight dropped), discretisation for rule mining."),
    ("eda", "Exploratory figures for the data report."),
    ("regimes", "Change-point detection: PELT on daily series, calendar-split baseline, event alignment."),
    ("clusters", "Archetype days: k-means baseline vs DTW k-means vs k-Shape, silhouette / Davies-Bouldin / bootstrap ARI."),
    ("motifs", "Matrix profile (STUMPY): motifs and discords."),
    ("rules", "Apriori baseline, FP-Growth, emerging patterns, temporal hold-out."),
    ("episodes", "PrefixSpan (own implementation) on the days before shedding onsets, with a permutation null."),
    ("anomalies", "STL residuals, Isolation Forest vs z-score, injected-glitch benchmark."),
    ("mine", "Driver: runs every stage, writes tables and figures to docs/results."),
    ("cli", "Command-line entry point (`blackout inspect | clean | profile | eda | mine`)."),
]


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip("\n"))


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    cells = [
        md("""
# Blackout Patterns: the whole project in one notebook

Mining the regimes, motifs and precursors of load shedding in Bangladesh's hourly grid data (PGCB, 2015-2026).

**How this notebook works.** Part 1 contains *every line of project code*, one cell per module. Each
code cell writes its module into `notebooks/_nb_pkg/blackout/` with `%%writefile`. Part 2 imports that
freshly written package and runs the whole pipeline: cleaning, exploratory analysis, regimes, clusters,
motifs, rules, episodes and anomalies. The same code lives in `src/blackout/` (the notebook is
generated from it by `scripts/build_notebook.py`).

**Requirements.** The raw file at `data/raw/pgcb_hourly_mendeley.csv` (not stored in git, see the README)
and the packages in `pyproject.toml` (`pip install -e ".[dev,mining,viz]"`).

**The slow step.** Comparing clustering methods with DTW takes about 15 minutes, so the notebook reuses
`docs/results/cluster_comparison.csv`. Set `RUN_CLUSTER_SEARCH = True` in the first cell of Part 2 to redo it.

Contents: [Part 1: code](#part-1) · [Part 2: run it](#part-2)
"""),
        md('<a id="part-1"></a>\n## Part 1. The code'),
        code('''
import os, sys
from pathlib import Path

# Find the repository root (the folder with pyproject.toml) from wherever the notebook is run.
REPO = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists())
os.environ["BLACKOUT_ROOT"] = str(REPO)
BUILD = REPO / "notebooks" / "_nb_pkg"
(BUILD / "blackout").mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(BUILD))           # use the notebook's copy of the package, not an installed one
sys.modules.pop("blackout", None)
print("repo:", REPO)
'''),
        code(f'%%writefile ../notebooks/_nb_pkg/blackout/__init__.py\n{(SRC / "__init__.py").read_text().strip()}'),
    ]
    for name, blurb in MODULES:
        cells.append(md(f"### `{name}.py`\n{blurb}"))
        cells.append(code(f"%%writefile ../notebooks/_nb_pkg/blackout/{name}.py\n{(SRC / f'{name}.py').read_text().rstrip()}"))
    nb.cells = cells
    return nb


PART2 = [
    md('<a id="part-2"></a>\n## Part 2. Run the pipeline'),
    code('''
RUN_CLUSTER_SEARCH = False   # True: redo the DTW / k-Shape comparison (~15 min)

import warnings; warnings.filterwarnings("ignore")
import pandas as pd
from IPython.display import Image, display, Markdown
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_columns", 30)

from blackout import config, clean as C, profile, features, eda, regimes, clusters, motifs, rules, episodes, anomalies, mine
print("package built from the notebook:", C.__file__)
'''),
    md("### 1. Raw data and cleaning"),
    code('''
raw = C.read_raw(config.MAIN_DATASET_PATH)
print(raw.shape); display(raw.head(3))
print("column roles inferred:", C.infer_roles(list(raw.columns)))
hourly, report = C.clean(raw)
display(Markdown(report.to_markdown()))
'''),
    md("README's first profile versus the cleaned table (hours, not raw rows):"),
    code('''
display(profile.compare_with_readme(hourly))
print(profile.liquid_fuel_change_correlation(hourly))
'''),
    md("### 2. Exploratory analysis (data report figures)"),
    code('''
config.DATA_INTERIM.mkdir(parents=True, exist_ok=True)
hourly.to_parquet(config.CLEAN_HOURLY_PATH)      # the later stages read this file
tables = eda.run()
for f in ["fingerprint", "fuel-mix", "hour-profile", "shedding-size"]:
    display(Image(filename=str(eda.FIG_DIR / f"{f}.png"), width=900))
print(tables[:1500])
'''),
    md("### 3. Run every mining stage"),
    code('''
R = mine.run(config.CLEAN_HOURLY_PATH, skip_cluster_search=not RUN_CLUSTER_SEARCH)
daily = R["daily"]
'''),
    md("#### 3a. Regimes (PELT change points vs calendar split)"),
    code('''
sweep = pd.read_csv(config.RESULTS / "regime_sweep.csv"); display(sweep[["signals", "c", "n_breaks", "cost", "calendar_cost", "events_within_7d", "breaks"]])
print("best single break:", R["regimes"]["best_single_break"])
display(pd.read_csv(config.RESULTS / "regime_event_alignment.csv"))
display(Image(filename=str(mine.FIG / "regimes.png"), width=900))
'''),
    md("#### 3b. Archetype days (k-means vs DTW k-means vs k-Shape)"),
    code('''
display(R["cluster_scores"].round(3))
print("chosen:", R["cluster_cfg"], "| days with usable profiles:", R["day_info"])
display(pd.read_csv(config.RESULTS / "cluster_archetypes.csv"))
display(Image(filename=str(mine.FIG / "archetypes.png"), width=900))
'''),
    md("#### 3c. Motifs and discords (matrix profile)"),
    code('''
display(pd.read_csv(config.RESULTS / "matrix_profile_motifs_discords.csv"))
display(Image(filename=str(mine.FIG / "matrix-profile.png"), width=900))
'''),
    md("#### 3d. Association rules and emerging patterns"),
    code('''
r = R["rules"]
print(f"Apriori baseline (all years): {len(r['base'])} rules in {r['base_s']:.1f}s | FP-Growth (crisis train): {len(r['crisis'])} rules in {r['fp_s']:.2f}s")
cols = ["antecedent", "support", "confidence", "lift", "conviction", "leverage", "lift_vs_calendar"]
print("Baseline: top by confidence"); display(r["base"].head(8)[cols].round(3))
print("FP-Growth, crisis training period: top fuel-involving rules by lift"); display(r["crisis"][~r["crisis"].calendar_only].head(10)[cols].round(3))
print("Calendar-only rules (the 'obvious' ones)"); display(r["crisis"][r["crisis"].calendar_only].head(5)[cols].round(3))
print("Emerging patterns, fuel mix only (none -> high shedding)"); display(r["ep_fuel"].head(10).round(3))
print("Hold-out on 2025"); display(r["hold"].round(3))
display(Image(filename=str(mine.FIG / "rules-holdout.png"), width=800))
'''),
    md("#### 3e. Sequential patterns before shedding onsets (PrefixSpan)"),
    code('''
e = R["episodes"]
display(e["patterns"].head(8).round(3))
print(f"best observed gap {e['best_gap']:.2f} | best-by-chance gap: median {e['null_gap_median']:.2f}, 95th percentile {e['null_gap_95']:.2f}")
'''),
    md("#### 3f. Anomalies"),
    code('''
a = R["anomalies"]
display(a["bench"].round(3))
print("rank of the 2022-10-04 grid failure among", a["n_days"], "days:", a["grid_failure_rank"])
print(a["events"]["tag"].value_counts().to_dict())
display(a["events"].head(10).round(1))
display(Image(filename=str(mine.FIG / "anomaly-benchmark.png"), width=600))
'''),
    md("### 4. Models and algorithms used"),
    code('''
import importlib.metadata as md_
def v(p):
    try: return md_.version(p)
    except Exception: return "n/a"
models = pd.DataFrame([
    ("Change points", "PELT (l2 cost, min segment 14 d, jump 5 d + exact-day refinement)", f"ruptures {v('ruptures')}", "daily shedding + fuel shares"),
    ("Change points (baseline)", "calendar split 2022-01-01; best single break (exhaustive)", "numpy", "same"),
    ("Archetype days (baseline)", "k-means on raw MW", f"scikit-learn {v('scikit-learn')}", "978 crisis days x 23 h"),
    ("Archetype days", "DTW k-means (TimeSeriesKMeans)", f"tslearn {v('tslearn')}", "z-normalised profiles"),
    ("Archetype days", "k-Shape", f"tslearn {v('tslearn')}", "z-normalised profiles"),
    ("Cluster evaluation", "silhouette, Davies-Bouldin, bootstrap ARI", f"scikit-learn {v('scikit-learn')}", ""),
    ("Motifs and discords", "matrix profile (stump), windows 7 and 14 days", f"stumpy {v('stumpy')}", "log daily MW shed"),
    ("Rules (baseline)", "Apriori, ranked by confidence", f"mlxtend {v('mlxtend')}", "hourly discretised states, all years"),
    ("Rules", "FP-Growth + lift / conviction / leverage / lift-vs-calendar", f"mlxtend {v('mlxtend')}", "crisis training period"),
    ("Emerging patterns", "support growth none -> high shedding (Dong & Li)", f"mlxtend {v('mlxtend')}", "crisis training period"),
    ("Episodes", "PrefixSpan (own implementation) + Fisher exact + permutation null", f"scipy {v('scipy')}", "3 days before shedding onsets"),
    ("Anomalies (baseline)", "robust z-score of the STL residual", f"statsmodels {v('statsmodels')}", "daily generation"),
    ("Anomalies", "Isolation Forest on STL residuals (1 feature and 5 features)", f"scikit-learn {v('scikit-learn')}, statsmodels {v('statsmodels')}", "daily residuals"),
], columns=["task", "method", "library", "data"])
display(models)
'''),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="run the notebook and store its outputs")
    args = ap.parse_args()
    nb = build()
    nb.cells += PART2
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    NB.parent.mkdir(exist_ok=True)
    nbf.write(nb, NB)
    print(f"wrote {NB} ({len(nb.cells)} cells)")
    if args.execute:
        subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                        "--ExecutePreprocessor.timeout=3000", str(NB)], check=True, cwd=ROOT / "notebooks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
