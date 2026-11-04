# Blackout Patterns: demo write-up

Everything built so far on the `Demo` branch, every model used, what each one found, the decisions made along the way, and what is still open. The same code and all results are in one notebook: [`notebooks/blackout_patterns_demo.ipynb`](notebooks/blackout_patterns_demo.ipynb).

**One-paragraph summary.** Bangladesh's load shedding is a clean natural experiment: almost none until mid-2022, then thousands of hours a year. The data (PGCB hourly, 94,934 rows, 2015-04 to 2026-03) was cleaned and profiled; change-point detection puts the break at **2022-07-19**; crisis days fall into three *intensity* tiers rather than distinct daily shapes; shedding rules mined on 2022–2024 keep their direction but lose most of their precision in 2025; and no sequence of fuel-mix moves reliably precedes a shedding onset. Several of the README's original hypotheses did not survive the first look (section 5).

## 1. How to run it

```bash
pip install -e ".[dev,mining,viz,notebook]"
# put the raw file at data/raw/pgcb_hourly_mendeley.csv (not stored in git)
blackout clean && blackout profile     # cleaning + first profile
blackout eda                           # data-report figures
blackout mine                          # all mining stages -> docs/results/ (about 15 min the first time, 75 s after)
pytest                                 # 21 tests, synthetic data
python scripts/build_notebook.py --execute   # rebuild the notebook from src/ and run it
```

`blackout mine` re-uses `docs/results/cluster_comparison.csv` with `--skip-cluster-search`. The DTW / k-Shape comparison is the only slow step (about 13 minutes).

## 2. What was done, in order

| # | Step | Where | Outcome |
|---|---|---|---|
| 1 | Read the plan and research notes; found the repo had no code | README, `docs/research/` | Project scaffold: `pyproject.toml`, `src/blackout/`, CLI, tests |
| 2 | Cleaning pipeline | `clean.py`, `config.py` | Column roles matched by keyword (all 15 real columns matched), half-hourly folded to hourly, impossible values set to NaN and flagged |
| 3 | First run on the real file | `profile.py` | Raw yearly shedding row counts reproduce the README chart exactly; the cleaned table counts *hours* so is 4–5% lower for 2022–2025 (an extra 19:30 row a day) |
| 4 | Per-source ceilings from the real data | `config.py` | Glitches were far wider than first thought (liquid fuel 29 million MW; dozens of hydro readings above 1,000 MW): one global ceiling replaced with per-source ceilings applied before imports are summed. About 210 readings set to NaN; no rows removed |
| 5 | Found that midnight is missing | `clean.py` | 00:00 exists on 0.1% of days. Missing hours become explicit `observed = False` rows; nothing imputed |
| 6 | Exploratory analysis and data report | `eda.py`, `docs/data-report/` | 4 figures, the report, and updated hypotheses |
| 7 | Features | `features.py` | Daily table, 23-hour day matrix, discretised hourly "transactions" for rule mining |
| 8 | Regimes | `regimes.py` | PELT change points, calendar baseline, event alignment |
| 9 | Archetype days | `clusters.py` | k-means vs DTW k-means vs k-Shape, three evaluation measures |
| 10 | Matrix profile | `motifs.py` | Motifs and discords, windows of 7 and 14 days |
| 11 | Rules | `rules.py` | Apriori baseline, FP-Growth, emerging patterns, 2025 hold-out |
| 12 | Sequential patterns | `episodes.py` | PrefixSpan (own implementation) with a permutation test |
| 13 | Anomalies | `anomalies.py` | STL + Isolation Forest vs z-score, tested on injected glitches |
| 14 | Pipeline, notebook, tests, docs | `mine.py`, `scripts/build_notebook.py`, `tests/`, this file | One command runs everything; the notebook contains all code |

## 3. Every model and algorithm used

| Task | Method | Library (version) | Settings | Data |
|---|---|---|---|---|
| Change points | **PELT**, l2 cost | ruptures 1.1.10 | min segment 14 days; penalty `c·log(n)·d` swept over c = 0.5 to 32; searched on a 5-day grid then each break moved to the exact day within ±5 days | daily log(1+MW shed), liquid, imports, coal and gas shares, standardised |
| Change points (baselines) | Calendar split at 2022-01-01; best single break by exhaustive search | numpy | min segment 30 days | same |
| Archetype days (baseline) | **k-means** on raw MW | scikit-learn 1.9.1 | k = 2–5, 10 inits | 978 crisis days × 23 hours |
| Archetype days | **DTW k-means** (`TimeSeriesKMeans`) | tslearn 0.10.0 | k = 3–5, 1 init, max 10 iterations, DBA 5 iterations | z-normalised profiles |
| Archetype days | **k-Shape** | tslearn 0.10.0 | k = 2–5, 3 inits | z-normalised profiles |
| Cluster evaluation | Silhouette, Davies–Bouldin, bootstrap ARI | scikit-learn | ARI: fit on 80% of days, assign all days, 4 repeats (DTW: 2) | |
| Motifs and discords | **Matrix profile** (`stump`) | stumpy 1.14.1 (numba 0.68.1) | windows 7 and 14 days; only "active" windows (a day ≥ 200 MW) | log daily MW shed from July 2022 |
| Rules (baseline) | **Apriori**, ranked by confidence | mlxtend 0.25.0 | min support 1%, up to 4 items | all years, 90,452 hourly states |
| Rules | **FP-Growth**; lift, conviction, leverage, and lift-versus-calendar-part | mlxtend 0.25.0 | min support 1%, up to 4 items; target = ≥ 500 MW shed | crisis training period (Jul 2022 – 2024, 20,995 hours) |
| Emerging patterns | Support growth from no-shedding to high-shedding hours (Dong & Li, 1999) | mlxtend 0.25.0 | min support 3% in the high group, up to 3 items; with and without calendar items | crisis training period |
| Rule validation | Temporal hold-out | pandas | re-score each rule on 2025 against that year's own base rate | 2025 |
| Sequential patterns | **PrefixSpan**, own implementation (the PyPI package would not build on Python 3.13) | pure Python; scipy 1.18.1 for Fisher exact | min support 10%, up to 3 items; 3-day look-back; 50 onsets vs 50 controls | daily fuel-mix moves (top/bottom quintile) |
| Sequence significance | Fisher exact test and a **label-permutation null** (200 shuffles) | scipy, numpy | | |
| Anomalies (baseline) | Robust z-score of the STL residual | statsmodels 0.15.0 | STL period 7, robust; scale floored at 10% of the std | daily generation, from 2018 |
| Anomalies | **Isolation Forest** on STL residuals | scikit-learn 1.9.1 | 300 trees; one feature (generation) and five features | daily residuals |
| Anomaly evaluation | Precision@40 on **injected glitches** (generation × 1.6 or × 0.4 on random days) | numpy | 10 seeds | |

## 4. Results

### Regimes
- **Every setting finds a break at 2022-07-19**, four days after the (approximate) mid-July 2022 spot-LNG halt, and it is the only break that survives all penalties and both signal sets.
- The best single break is also 2022-07-19, and it beats the calendar split at 2022-01-01 on within-segment cost: 11,143 vs 12,214 on the multivariate signal (−9%) and 1,780 vs 2,214 on shedding alone (−20%).
- With c = 16 the multivariate segmentation is 2020-06-07, **2022-07-19**, 2023-08-07, 2024-08-28; on shedding alone it is **2022-07-19** and 2024-11-05. The 2020, 2023 and 2024 breaks mostly track the coal and import build-out, not shedding.
- With smaller penalties (more breaks), shedding-only segmentations pick out the winter lull each year, so they find seasons, not regimes.
- The 4 Oct 2022 grid failure is a one-day event; a 14-day minimum segment cannot represent it, so no change point aligns with it (nearest is 77 days away). It belongs to the anomaly step.
- Figure: [`docs/results/figures/regimes.png`](docs/results/figures/regimes.png)

### Archetype days
- **Day shapes do not form distinct archetypes; intensity does.** k-means on raw MW is stable and well separated (silhouette 0.65 at k = 2, 0.58 at k = 3, bootstrap ARI 0.99 and 0.96). Shape-only methods are weak: k-Shape silhouette 0.06–0.16 and ARI 0.39–0.64; DTW k-means silhouette 0.21–0.30.
- Selection rule: highest silhouette × stability among k ≥ 3 with no cluster under 5% of days. That picks **k-means, k = 3**:

| Tier | Days | Mean MW shed per hour | Years |
|---|---|---|---|
| Light | 727 | 105 | spread over 2022–2026; 35% are 2025 |
| Medium | 185 | 670 | 2022–2024 (31 / 31 / 36%) |
| Heavy | 66 | 1,455 | **2022–2024 only** |

- All three tiers share one shape: high after midnight, a trough around 06:00–07:00, a second bump mid-afternoon. No heavy days occur in 2025 or 2026.
- Figure: [`docs/results/figures/archetypes.png`](docs/results/figures/archetypes.png)

### Motifs and discords
- The motif finder mostly returns "several quiet days, then shedding starts" (z-normalisation ignores size). Examples at window 7: 2023-01-04 ↔ 2026-01-16 (distance 0.10), 2023-10-06 ↔ 2023-05-29 (0.18).
- The top discords (unusual weeks) include 2022-07-31 and 2022-09-26 (just before the grid failure) at window 7, and 2022-07-30 at window 14.
- Weak result: the series is mostly an on/off seasonal signal, so there is little repeated structure beyond that. Tables: `docs/results/matrix_profile_motifs_discords.csv`.

### Rules and emerging patterns
- **Baseline (Apriori, all years, by confidence):** the top three rules combine low gas share with a season or low imports, with lift 4.7–5.3 but confidence only 24–27%.
- **FP-Growth on the crisis period:** the strongest fuel-involving rules are "monsoon + high liquid-fuel share + a time band", confidence about 53–56%, lift about 2.5. Calendar-only rules (monsoon night, lift 2.3) are nearly as strong.
- **Does the fuel mix add anything beyond the calendar?** Yes, modestly. Across the 155 fuel-involving rules the lift over their own calendar part has median 1.38 (range 0.8 to 2.5). High imports add the most (1.47×); high liquid fuel about 1.2–1.4×.
- **Emerging patterns, fuel mix only** (more common in high-shedding hours than in no-shedding hours): low gas + high imports is 7× more common (6.6% vs 1.0% of hours), low gas + high imports + mid coal 7.9×.
- **Hold-out on 2025:** of the top 15 fuel-involving rules, 14 still had matching hours in 2025. Ten of those 14 kept a lift above 1 against 2025's own base rate, but **precision collapsed**: training confidence 49–56% against 0–18% in 2025. The rules containing high liquid-fuel share held their direction best (lift 5–21 in 2025, except one rule that matched a single hour); the coal / gas / import combinations mostly did not. Only 0.8% of 2025 hours had ≥ 500 MW shed, so lift is large while confidence is small.
- Figure: [`docs/results/figures/rules-holdout.png`](docs/results/figures/rules-holdout.png)

### Sequential patterns before shedding onsets
- **Null result.** The best sequence pattern appears in 16 percentage points more onsets than controls; shuffling the labels, the best pattern you would find by chance has a median gap of 0.18 and a 95th percentile of 0.28. Of the 179 candidate patterns only two have a Fisher p-value below 0.05 (the smallest is 0.027, each seen in 12% of onsets and 0% of controls), against about 9 expected by chance, so nothing survives any multiple-testing correction.

### Anomalies
- **Injected-glitch test (precision@40, 10 seeds):** Isolation Forest on generation only **0.885 ± 0.039**, robust z-score **0.872 ± 0.036** (a tie), Isolation Forest on all five features **0.090 ± 0.046** (extra features that the glitch does not touch drown the signal).
- **Real data:** the 4 Oct 2022 grid failure ranks 37th (z-score), 61st (Isolation Forest, generation) and 120th (Isolation Forest, all features) of 2,989 days.
- The top 50 real anomalous days are dominated by sharp drops in generation. Several fall near holidays or storms (for example late October 2022, mid-June 2024, February 2026), which is an unverified guess, not a finding.
- The "data error vs real event" tag is a crude rule (flagged readings or under 20 observed hours = error-like; two or more fuel residuals beyond 3 = event-like). It tagged 48 of 50 as event-like, so it is not informative.
- Figure: [`docs/results/figures/anomaly-benchmark.png`](docs/results/figures/anomaly-benchmark.png)

## 5. How the README's hypotheses fared

| Hypothesis | After the full run |
|---|---|
| Sharp regime break in mid-2022 | **Supported**: 2022-07-19, robust to every setting |
| Partial recovery in 2025 | **Supported, mostly in amount**: shedding energy −83% vs 2024, shedding days −3%; no heavy days in 2025 |
| Evening-peak and late-night concentration | **Not supported for 2023–24** (all day); partly true for 2025; midnight cannot be checked |
| Low gas + high liquid fuel precede shedding | **Partly**: the direction held in 2025, but liquid-fuel share peaked in 2022 and fell afterwards; precision collapsed; the effect is modest beyond the calendar |
| A cluster of data glitches | **Supported**, and larger than first thought |

## 6. Decisions made on your behalf

You asked me to act as your delegate, so these were my calls. Each is easy to change.

1. **Drop midnight** (23-point days) instead of interpolating it. Interpolating would put guesses into the exact hour the "late night" question depends on.
2. **Crisis start = 2022-07-01** for crisis-relative terciles and train/test splits (confirmed by PELT at 2022-07-19).
3. **Hold out 2025**: rules are mined on Jul 2022 – 2024 and re-scored on 2025.
4. **"High shedding" = at least 500 MW in the hour** (about 4,700 hours).
5. **Emerging patterns are computed inside the crisis** (high-shedding vs no-shedding hours), not between pre-crisis and crisis, because the pre-crisis years have almost no shedding to compare.
6. **Cluster selection:** k ≥ 3, no cluster under 5% of days, maximise silhouette × stability.
7. **DTW k-means was run with reduced settings** (1 initialisation, 2 stability repeats, k = 3–5) because the full version had not finished after 20 minutes.
8. **PrefixSpan was written by hand** because the PyPI package would not build here.

## 7. Caveats and things not done

- **Event dates are unverified.** The two used (about 2022-07-15 spot-LNG halt, 2022-10-04 grid failure) are from memory. The research notes give the LNG halt only as "mid-2022". Check them before quoting. The alignment result (4 days) depends on the first one.
- **No manual labelling.** The plan's "precision@50 by manual labelling" is not done; the injected-glitch test and the crude tags stand in for it.
- **Cleaning ceilings are judgement calls** (config.py), particularly shedding (6,000 MW) and liquid fuel (12,000 MW). Fourteen hours above 3,000 MW remain and should be checked by hand.
- **Correlation, not causation.** Alignments with events and fuel-mix conditions are associations.
- **Multiple testing.** Hundreds of rules and patterns were scored; no correction was applied except through the permutation null for sequences.
- **Weak spots:** shape clustering found little; the matrix profile mostly shows the on/off seasonal pattern; fuel-mix rules add only modest lift beyond season and hour.
- **Not built yet:** the Streamlit dashboard, the UCI cross-check merge, the solar/wind policy for fuel shares beyond "treat as 0", the stretch goals (air quality, dependency structure), and the paper.
- **Data version:** one file, v1 (March 2026). Prior-work check on Google Scholar still to do.

## 8. File map

```
src/blackout/       config, clean, profile, features, eda, regimes, clusters, motifs, rules, episodes, anomalies, mine, cli
tests/              test_clean.py, test_mining.py (21 tests, synthetic data)
notebooks/          blackout_patterns_demo.ipynb (all code + outputs; _nb_pkg/ is a git-ignored build folder)
scripts/            download_data.py, build_notebook.py
docs/data-report/   week-3 data report and its 4 figures
docs/results/       13 CSV tables and 5 figures from `blackout mine`
DEMO.md             this file
```
