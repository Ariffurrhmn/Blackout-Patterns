# Data Mining Semester Project: Ideas, Datasets and Research Angles (Bangladesh focus)

*Prepared 7 October 2026. Every dataset in the shortlist was opened and checked: page metadata through the Mendeley / Kaggle / Zenodo / HDX / Hugging Face APIs, plus for most of them a direct look at the actual columns. Small files (≤7 MB) were downloaded; for larger files I read only a few MB using byte-range reads. Paper metadata was checked against Crossref, arXiv or PubMed. Anything I could not confirm is marked **unverified**. All URLs are in [`sources.md`](sources.md).*

---

## 1. TL;DR: top 3 recommendations

1. **Mining Bangladesh's load-shedding crisis from 11 years of hourly grid data** (PGCB, 2015–2026, ~95k hourly rows, CC BY 4.0, 6.5 MB).
   The data has a natural experiment built in. Hours with load shedding: about 3–46 per year in 2015–2021. Then 2,287 in 2022, 5,012 in 2023, 5,034 in 2024 and 3,316 in 2025 (my count from the file). All published work on this data does **forecasting** or **prediction**. Nobody has mined the *patterns* of the crisis. That means regimes (change points), recurring daily shapes (motif discovery, k-Shape clustering), fuel-mix conditions that come before shedding (association and emerging-pattern mining), and data glitches versus real events (anomaly detection). It is small, clean enough, and runs on a laptop. A stretch goal links it to hourly air-quality data (Idea 4).

2. **Who jams first? Congestion propagation across 81 Dhaka junctions** (Google-Maps-derived congestion index, 10-minute resolution, 7 Apr – 6 Jun 2026, 0% missing, CC BY 4.0, 7.7 MB).
   The data includes an 81×81 travel-time adjacency matrix, and the window covers the **Eid-ul-Adha 2026 exodus**. In my check, the city-wide daily mean index fell from ~1.5–1.6 to ~1.17–1.27 during 27 May – 2 Jun. Possible methods: time-series clustering of junctions, frequent "co-jam" itemsets (FP-Growth), lagged Granger-style propagation graphs with centrality analysis, and Eid change-point and contrast analysis. Recent Dhaka papers cluster divisions or find static bottlenecks; none look at lagged, directed propagation or Eid. It also gives the best demo of the three: an animated congestion map.

3. **When does Bangladesh eat? Weekly popularity rhythms of ~20k restaurants** (BanglaDine2024, 58,376 Google Maps restaurants, 221 columns incl. 168 "popular times" columns, CC BY 4.0).
   About 40% of rows have the 7×24 popularity curve, which by my sample estimate means ~23k restaurants. Planned methods: shape-based clustering of the curves into archetypes (late-night, Friday brunch, office lunch), spatial hotspots of each archetype (HDBSCAN, Gi\*), association rules from amenities and service options to archetype and rating, and outlier detection for suspicious ratings. Popular Times has been mined for Curitiba and Chicago (2016) and in a 2025 European study. I found no South Asian study.

*Runners-up:* **load shedding × air quality** (Idea 4) is the most novel research question but the hardest. **Dengue spatiotemporal mining** (Idea 5) is very locally relevant but crowded.

---

## 2. How the search was done (and what was covered)

| Source | What I did | Useful finds |
|---|---|---|
| **Mendeley Data** | ~35 records read through the public API (title, version, publish date, file list and sizes, license) | Most of the shortlist: PGCB, CAMS-BD, Dhaka traffic, BanglaDine, BDFoodSent, retail network, DSE, dengue, prices |
| **Kaggle** | 22 keyword searches through the public API, recording **notebook counts** to judge overuse; 10 dataset pages read in detail | Daily dengue 2022–2025; flagged synthetic datasets |
| **UCI ML Repository** | Site search for "bangladesh" returned 0; found PGCB (#1175) and garment productivity (#597) by web search | PGCB hourly mirror |
| **OpenML** | Name search for "bangladesh": no results | – |
| **Hugging Face** | API listing of 40 Bangladesh datasets; read the bangladeshi-jobs card and the first rows of the BNAD news corpus | BNAD news (1.9M articles); jobs dataset too small |
| **Zenodo** | 3 API searches (bangladesh / dhaka / bangla) | DhaTraX trajectories, BNAD, EComReviews-BD |
| **Google Dataset Search** | Dengue query | Confirmed the dengue dataset landscape |
| **Harvard Dataverse** | API search (1,152 Bangladesh datasets, mostly survey and replication packages) | Nothing better than the shortlist for DM |
| **HDX (humdata)** | API metadata + full CSV (4.6 MB) | WFP food prices, 110 markets, 1998–2026 |
| **data.gov.bd** | Opened the "Daily Water Levels" dataset | Created 2018, never updated, "License Not Specified": rejected |
| **BBS / DGHS / IEDCR** | BBS Agricultural Yearbook exists as PDF tables; the DGHS dengue press-release URL I tried returned 404, and the data is reachable via Kaggle compilations of DGHS bulletins | Used indirectly |
| **World Bank / data.gov** | WDI-style South Asia panels (Kaggle mirrors with 7+ notebooks) were judged overdone; the catalog.data.gov API query failed and it is US-centric, so not pursued | – |
| **Literature** | Semantic Scholar API (rate-limited, partial), arXiv API, Crossref, PubMed E-utilities, web search | 40+ papers verified |

In total I logged about **50 candidate datasets and topics** (Section 7 lists the rejected ones).

**Data checks that changed the ranking** (all from my own inspection of the files):
- The headline **"Bangladesh Road Traffic Accident Dataset 2007–2024" (49,566 rows)** looks **largely synthetic**. Severity classes are ~25% each. The two weather columns are statistically independent of each other, and so are the two lighting columns. Death count is ~1.0 for every severity class, including "Minor Injury". 99.3% of narratives are duplicates, and 96% of victims are "Motorcyclist". Any association rules mined from it would be noise, so it is **rejected** even though it looks like an ideal ARM dataset.
- **BanglaDine** includes ~12% rows labelled `division = India` (border-area coordinates), and only ~40% of rows have popular-times data. Both are manageable, but they are noted.
- **DSE floor price** is visible in the raw data. ACI Ltd had **82.8% zero-return trading days** from Aug 2022 to Dec 2023, versus 0% the year before and 0.4% after Feb 2024.

---

## 3. Shortlist: 12 ideas

Scores are out of 5: **N**ovelty, **F**easibility, **D**ata quality, **Demo** appeal, **P**ublishability.

---

### Idea 1 ★ Mining the load-shedding crisis in Bangladesh's hourly grid data (2015–2026)

**Pitch.** Bangladesh went from almost no load shedding (2015–2021) to thousands of shedding hours a year (2022–2025) after the LNG/forex crisis. The Power Grid Company of Bangladesh (PGCB) publishes hourly generation, demand, load shedding and fuel mix, and two groups have already scraped it into clean files. Published work uses it only to *forecast demand* or *predict* shedding. This project mines the structure of the crisis instead: when did regimes change, what does a typical crisis day look like, which fuel-mix conditions come before shedding, and how do recurring motifs and rare discords (including data glitches) show up?

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Hourly Electricity Generation, Demand, Load Shedding & Fuel Mix (2015–2026), BUET authors | https://data.mendeley.com/datasets/vpk8spw2mm/1 | 6.55 MB CSV; **94,934 rows × 15 cols, 2015-04-17 → 2026-03-08** (my check; half-hourly rows in early 2015) | CC BY 4.0 | v1, 30 Mar 2026 |
| PGCB Hourly Generation Dataset (UCI mirror) | https://archive.ics.uci.edu/dataset/1175/pgcb+hourly+generation+dataset | 6.8 MB XLSX, 92,650 × 14 | CC BY 4.0 | donated 17 Jun 2025 |
| Daily electricity incl. **division-level** load shedding (BPDB PDFs, 2019-11-21 → 2024-12-30) | https://data.mendeley.com/datasets/x7r7wdb39k/1 | 2.07 MB, 5 XLSX versions + README | CC BY 4.0 | v1, 19 Jun 2025 |
| (optional) BMD daily weather, 35 stations, to 2023 | https://data.mendeley.com/datasets/tbrhznpwg9/1 | 42 MB CSVs | CC BY 4.0 | 27 Jun 2024 |

My profile of the Mendeley file: load-shedding>0 hours per year were 22, 46, 7, 12, 12, 6, 3 (2015–2021), then 2,287 / 5,012 / 5,034 / 3,316 (2022–2025). Mean liquid-fuel generation jumped to 6,391 MW in 2022. There are obvious glitches (max "generation" 64,526,500 MW in 2023; a load-shedding value of 65,359 MW in 2017). Solar is 22% missing and wind 74% missing.

**Techniques.** Change-point detection (PELT) on daily shedding energy and fuel shares. Matrix profile motif and discord discovery (STUMPY). k-Shape / DTW clustering of 24-hour profiles per regime. Association rules and **emerging patterns** (FP-Growth; rules whose support jumps between regimes) on discretised hourly states such as {season, hour-band, gas share low, liquid share high, import level} → {shedding high}. Sequential patterns (PrefixSpan) over shedding episodes. Isolation Forest / STL-residual anomaly detection to separate data errors from real events.

**Research question and novelty.** *What operating regimes and recurring patterns characterise Bangladesh's 2022–2025 load-shedding crisis, and which fuel-mix conditions systematically come before shedding?* Prior work on these exact data is forecasting or prediction:
- Islam, Turja & Habib (2025), *Enhanced power demand forecasting for Bangladesh…*, J. Data, Information & Management. https://doi.org/10.1007/s42488-025-00140-9
- Yeaser, Nafs & Hossain (2025), *Comparative Analysis of Deep Learning Models for Long-Term Electricity Demand Forecasting in Bangladesh Using Web-Scraped Data*, ECAI 2025. https://doi.org/10.1109/ECAI65401.2025.11095479
- Arifuzzaman (2026), *An Intelligent ML Based Load Shedding Prediction and Smart Energy Management Framework…*, IEEE SPICSCON 2026 (RF/XGBoost prediction). https://vu.edu.bd/publications/3168/an-intelligent-machine-learning-based-load-shedding-prediction-and-smart-energy-management-framework-for-power-grid-optimization-in-bangladesh
- Method anchor: Yeh et al. (2016), *Matrix Profile I*, IEEE ICDM. https://doi.org/10.1109/ICDM.2016.0179

The gap is unsupervised and pattern-level analysis of the crisis: regimes, archetypal days, emerging fuel-mix rules, and discord-based data auditing.

**Difficulty:** Medium. **Cleaning:** Medium (half-hourly to hourly, glitch removal, censored demand). **Compute:** laptop.

**Risks.** "Demand" is censored during shedding (the dataset author says so), so use generation plus shedding. Some rules will be obvious ("summer evening → shedding"), so rank by lift, conviction and emerging-pattern growth rate, not confidence. Regime causes are policy events, so only claim alignment with them, not causation.

**Scores:** N 4 · F 5 · D 4 · Demo 4 · P 4

---

### Idea 2 ★ Congestion propagation and "co-jam" patterns across 81 Dhaka junctions, with an Eid-ul-Adha natural experiment

**Pitch.** A University of Dhaka group published 60 days of Google-Maps-derived congestion at 81 named locations (Abdullahpur, Uttara, Airport, Mirpur-12, …) every 10 minutes. It comes with an 81×81 travel-time adjacency matrix. The window covers the Eid-ul-Adha 2026 holiday exodus. This project asks where congestion starts, how it spreads, which junctions jam together, and how Eid changes the network.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Dhaka_Traffic_Data (Sadia Tabassum, Univ. of Dhaka) | https://data.mendeley.com/datasets/phkvy2xwrt/1 | 7.70 MB. `traffic_mci_2026.csv` (8,640 × 84: timestamp, time, day + 81 locations), `traffic_class_2026.csv` (ordinal class), `adjacency_matrix.csv` (81×81 travel time), `connectivity_matrix.csv`, `sample_points.json`, 3 PNGs | CC BY 4.0 | v1, 1 Jul 2026 |
| (join) hourly rainfall from Open-Meteo historical API | https://open-meteo.com/ | API | Open-Meteo terms (believed CC BY 4.0, **unverified**) | live |

My check: 2026-04-07 14:39 → 2026-06-06 14:29, exactly 10-minute steps, **0% missing**. The daily mean index is ~1.45–1.64 on weekdays, ~1.30–1.36 on Fridays, peaks at 1.638 on 21 May (pre-Eid), and drops to 1.17–1.27 on 27 May – 2 Jun. The dataset description is a single sentence. The **congestion index (MCI) definition is not documented**, which is a risk.

**Techniques.** Time-series clustering of junction profiles (k-Shape, DTW-hierarchical). Lagged cross-correlation plus Granger tests restricted to adjacency-matrix neighbours, giving a **directed propagation graph**, then centrality (PageRank, out-strength) to find "source" junctions. Frequent **co-jam itemsets** (FP-Growth; transactions are 10-minute windows, items are junctions in a heavy class). Sequential patterns of jam onset order in the morning peak (PrefixSpan). Change-point detection and contrast mining for pre-Eid, Eid and recovery. Rain-linked anomaly detection.

**Research question and novelty.** *Which Dhaka junctions lead congestion and which follow, which jam together, and how did the Eid-ul-Adha exodus restructure these patterns?* Prior work:
- Rahman & Nower (2024), *Inferring Traffic Patterns of Dhaka City: A Spatio-Temporal Analysis Over a Year*, Transport & Telecommunication J. (10 zones, temporal patterns). https://doi.org/10.2478/ttj-2024-0030
- Sarker, Sakib & Nower (2025), *Identification of Traffic Bottlenecks in Central Dhaka Through Spreading Graph-Based Congestion Analysis*, VEHITS 2025 (spreading graphs + MST; **no lagged/Granger or Eid analysis** in abstract). https://doi.org/10.5220/0013296200003941
- Hasan & Sarker (2025), *Unraveling Urban Traffic Congestion Patterns in Bangladesh*, VEHITS 2025 (DTW hierarchical clustering of **8 divisions**, Jan–Jun 2023). https://scitepress.org/publishedPapers/2025/131936/pdf/index.html
- Pramanik et al. (2020), *Modeling Traffic Congestion in Developing Countries using Google Maps Data*, arXiv. https://arxiv.org/abs/2011.02359

The gap is junction-level (81 nodes) **directed, lagged** propagation, co-jam itemsets, and an Eid natural experiment. Clustering by itself is *not* novel here, so it has to stay a supporting step.

**Difficulty:** Medium. **Cleaning:** Low. **Compute:** laptop.

**Risks.** Only 60 days. The MCI is undocumented and derived from Google typical-traffic colours. The same research group (Nower and co-authors) has published two related papers, so there is a **scoop risk**: move fast and cite them. Granger on 10-minute data is sensitive to lag choice, so validate out of sample.

**Scores:** N 3 · F 5 · D 4 · Demo 5 · P 4

---

### Idea 3 ★ Weekly popularity rhythms of Bangladeshi restaurants (Google Maps "popular times")

**Pitch.** BanglaDine2024 scraped 58,376 restaurants from Google Maps in Nov 2024. Columns include the hourly "popular times" curve for each day of the week (168 columns), ratings, review counts, and comma-list attributes (service options, amenities, payments, crowd, …). The curves show how cities live: late-night Old Dhaka, Friday family brunches, office-lunch spots in Motijheel. This project clusters the rhythms, maps them, explains them with association rules, and flags suspicious rating profiles.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| BanglaDine2024 (UIU) | https://data.mendeley.com/datasets/hxrmzggw5b/1 | 179.76 MB total: `Restaurant_Spatial-Analytical.csv` 62.05 MB, JSON 117.71 MB; 58,376 × 221 | CC BY 4.0 | v1, 8 Apr 2025 (scrape dates 14–21 Nov 2024 in `current_date`) |

My check (11,073-row sample from 3 parts of the file): 168 popular-times columns present (`Sunday.12 AM` … `Saturday.11 PM`). **~40% of rows have popular times**, about 23k restaurants if that holds across the file. Rating present in 76.5% of rows, median 6 reviews. `division` includes **"India" for ~12%** of sampled rows, so filter with a Bangladesh boundary polygon. Two of the first rows have Indian coordinates (Coimbatore, Mumbai).

**Techniques.** Shape-based clustering (k-Shape / DTW) of z-normalised weekly curves into archetypes. Spatial hotspots per archetype (HDBSCAN, Getis-Ord Gi\*, Moran's I). FP-Growth association rules with archetype or "high rating" as consequent and attributes as antecedents. Outlier detection (LOF / Isolation Forest on rating, review count and category) for suspicious ratings. Cross-city comparison (Dhaka, Chattogram, Sylhet, Rangpur).

**Research question and novelty.** *What weekly activity archetypes exist among Bangladeshi restaurants, where are they located, and what attributes explain them?* Prior work:
- Barrena-Herrán, Modrego-Monforte & Grijalba (2025), *Revealing Spatiotemporal Urban Activity Patterns: A Machine Learning Study Using Google Popular Times*, ISPRS IJGI 14(6):221. https://doi.org/10.3390/ijgi14060221
- Neves et al. (2016), *Study of Google Popularity Times Series for Commercial Establishments of Curitiba and Chicago*, WebMedia '16. https://doi.org/10.1145/2976796.2976862
- Paparrizos & Gravano (2015), *k-Shape*, SIGMOD (method). https://doi.org/10.1145/2723372.2737793

The gap: no Popular-Times study for any South Asian city, and the dataset has no analysis paper yet (I found none). The Friday-weekend rhythm is a culturally distinct contrast to Western results.

**Difficulty:** Medium. **Cleaning:** Medium (list-valued attributes, India rows, sparse curves). **Compute:** laptop / Colab.

**Risks.** Popular times are relative (0–100 per venue), not absolute counts. It is one snapshot (Nov 2024). The ~60% of restaurants without curves are likely less popular, which biases the sample. It is scraped data, so check Google's ToS before redistributing derived data (the dataset itself is CC BY on Mendeley).

**Scores:** N 4 · F 4 · D 3 · Demo 5 · P 4

---

### Idea 4 Does load shedding make the air dirtier? Joining grid outages with hourly air quality

**Pitch.** When the grid sheds load, Dhaka switches on diesel generators. This is well documented in Beirut and India, but I found no study for Bangladesh. Join hourly PGCB load shedding with the Department of Environment's continuous air monitoring (CAMS) stations for 2022–2024. Then test whether shedding hours carry higher NOx, CO and PM2.5 than matched non-shedding hours (same station, month, hour and day-type, similar weather).

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| CAMS-BD hourly air quality + meteorology, 15–16 stations, Nov 2012 → Jan 2025, >1.37M rows | https://data.mendeley.com/datasets/hwmzyh5w4w/1 | 108.12 MB ZIP of 4 Excel files | CC BY 4.0 | v1, 23 Jul 2026 |
| PGCB hourly (Idea 1) | https://data.mendeley.com/datasets/vpk8spw2mm/1 | 6.55 MB CSV | CC BY 4.0 | 30 Mar 2026 |
| BPDB daily division-level shedding (to match regional stations) | https://data.mendeley.com/datasets/x7r7wdb39k/1 | 2.07 MB | CC BY 4.0 | 19 Jun 2025 |

The CAMS description warns of embedded header and unit rows inside station blocks, inconsistent station names, a confirmed solar-radiation/pressure column swap for Savar (2012–2021), and missing dates. I did **not** download it (108 MB).

**Techniques.** Matched contrast mining and subgroup discovery (which station × season × hour subgroups show the largest pollution lift during shedding). Emerging-pattern mining. Event-window analysis around shedding onsets. Anomaly detection on pollutant ratios such as NOx/PM (a diesel signature). Distributed-lag association.

**Research question and novelty.** *Are grid load-shedding hours associated with measurable increases in diesel-related pollutants at Bangladeshi monitoring stations?* Prior work:
- Al Hallak et al. (2024), *When do science recommendations stop being effective? The case of the sprawl of diesel electricity generators in Beirut*, PLOS ONE. https://doi.org/10.1371/journal.pone.0313341
- *Identifying urban air pollution hot-spots by dispersion modeling when data are scarce: application to diesel generators in Beirut, Lebanon*, arXiv 2111.07635. https://arxiv.org/abs/2111.07635
- Khan et al. (2023), *A quantitative assessment of natural and anthropogenic effects on the occurrence of high air pollution loading in Dhaka…*, Environ. Monit. Assess. https://doi.org/10.1007/s10661-023-12046-3

The gap: no Bangladesh study links grid shedding to ambient air quality (I found only news reports).

**Difficulty:** Hard. **Cleaning:** High (CAMS format). **Compute:** Colab (108 MB is fine).

**Risks.** Strong confounding: shedding peaks in hot, rainy months when PM is lowest, so careful matching is essential. Shedding is national while pollution is local. The effect may be small or null (a null result is still publishable if well designed). Heavy cleaning.

**Scores:** N 5 · F 3 · D 3 · Demo 4 · P 5

---

### Idea 5 Dengue onset rules and epidemic-curve clustering across 8 divisions (2022–2025 daily)

**Pitch.** 2023 was Bangladesh's worst dengue year on record. Daily division-level case counts from DGHS bulletins (2022–2025) now exist in clean form with weather. This project mines when and where seasons start, which climate conditions come before surges (lagged temporal rules), and whether divisions cluster into distinct epidemic-curve shapes.

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Daily Dengue Data of Bangladesh 2022–2025 (DGHS + Open-Meteo/ERA5, 8 divisions, Jan 2022 → Oct 2025) | https://www.kaggle.com/datasets/brownsugar297/dengue-and-weather-data-bangladesh-20222025 | 0.42 MB | CC BY 4.0 | 11 May 2026 (3 notebooks) |
| Bangladesh Daily & Monthly Dengue Cases (DGHS daily Jan 2024 → Mar 2026 + OpenDengue monthly) | https://www.kaggle.com/datasets/jisangain/bangladesh-daily-and-searo-monthly-dengue-cases | 0.03 MB | CC BY-SA 4.0 | 19 May 2026 (1 notebook) |
| Division-wise daily dengue + weather 2022–2024 | https://data.mendeley.com/datasets/z5mvwrfgsz/1 | 1.17 MB, 8 CSVs (+ a PDF receipt); Dhaka file = 1,096 rows, cols `effected, Rainfall, Humidity, Temparature, Windspeed, Sunshine` (my check) | CC BY 4.0 | 26 May 2026 |
| Monthly division dengue + climate 2020–2025 | https://data.mendeley.com/datasets/cgwjshkx5k | 0.04 MB XLSX, 576 rows; messy (forward-filled division, "19 °C" strings) | CC BY 4.0 | v2, 11 Dec 2025 |

**Techniques.** DTW / k-Shape clustering of division-season curves. Change-point detection of season onset. Lagged temporal association rules on discretised weather windows (e.g., "≥3 rainy days in week t−3 and mean T 27–30 °C → cases ×1.5 by week t"). Outbreak anomaly detection (CUSUM / EARS-style vs Isolation Forest). Optional visibility-graph features.

**Research question and novelty.** *Which multi-week weather patterns reliably come before dengue onset in each division, and do divisions follow distinct epidemic shapes?* Prior work:
- Alam et al. (2025), *Time series analysis of dengue incidence and its association with meteorological risk factors in Bangladesh*, PLOS ONE. https://doi.org/10.1371/journal.pone.0323238
- Hasan et al. (2024), *Shifting Geographical Transmission Patterns: Characterizing the 2023 Fatal Dengue Outbreak in Bangladesh*, medRxiv. https://doi.org/10.1101/2024.03.24.24304789
- Tasnim et al. (2021), *Observing the Unobserved: A Newspaper Based Dengue Surveillance System…*, FLAIRS-34. https://doi.org/10.32473/flairs.v34i1.128552

The gap is interpretable onset rules at daily resolution through 2025. Climate-correlation studies are **crowded**.

**Difficulty:** Easy–Medium. **Cleaning:** Low–Medium. **Compute:** laptop.

**Risks.** Crowded topic. Only 8 series. Counts are hospitalisations (Dhaka-hospital bias). Rules may restate known lags.

**Scores:** N 3 · F 5 · D 4 · Demo 4 · P 4

---

### Idea 6 Food-price shock networks across 100+ markets (incl. the Aug-2024 eastern floods)

**Pitch.** WFP's Bangladesh price database became dense in 2024–2026: 104 markets, 63 districts and 70 commodities, monthly. Build market co-movement networks per commodity, find communities and "leader" markets, detect price spikes, and test how shocks from the August 2024 Feni/Noakhali/Cumilla floods showed up across the network.

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| WFP Bangladesh – Food Prices (HDX) | https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh | 4.63 MB CSV; 35,326 rows, 1998-07 → 2026-08, 110 markets, 73 commodities, with lat/lon (my check) | CC BY-IGO | 4 Oct 2026 (updated weekly) |
| Food Commodity Price (OHLC) Dataset of Bangladesh (76 markets, 4 staples, 2007–2024, + weather) | https://data.mendeley.com/datasets/dd58ks2p5y | 5.84 MB CSV, 68,096 rows | CC BY 4.0 | 24 Sep 2026 |
| Retail Wheat Flour Price + macro indicators 2007–2025 | https://data.mendeley.com/datasets/5m4d33mxrs | 1.97 MB CSV, 17,099 obs | CC BY 4.0 | 26 Jun 2026 |
| AgriPriceBD daily prices, 5 commodities (garlic 2020-07-22 → 2025-06-04) | https://data.mendeley.com/datasets/bkmxnrn3hn | 0.41 MB, 5 CSVs | CC BY 4.0 | 27 Mar 2026 |

My check: 2024+ data has 32 monthly observations (15th of each month). Coarse-rice completeness across 80 markets is 54%. Flood districts have 1–3 markets each.

**Techniques.** Correlation / co-movement networks with Louvain communities. Lead–lag (cross-correlation, Granger) for "price leader" detection. STL + robust z / Isolation Forest spike detection. Frequent **co-spike itemsets** (which commodities spike together). Event-window contrast for the floods.

**Research question and novelty.** *How are Bangladesh's food markets connected, which markets lead price movements, and how did the 2024 flood shock propagate?* Prior work:
- Siddique, Raha & Alam (2010), *Market Integration: … Rice Markets in Bangladesh*, The Agriculturists. https://doi.org/10.3329/agric.v6i1.5219
- Alam, McKenzie & Begum (2022), *Spatial market integration of rice in Bangladesh in the presence of transaction cost*, Agric. & Food Econ. https://doi.org/10.1186/s40100-022-00228-5
- Hossain et al. (2026), *GRU-Based Time-Series Forecasting of Agricultural Commodity Prices Using Market and Climate Data*, IEEE QPAIN 2026 (linked from the OHLC dataset). https://doi.org/10.1109/QPAIN69676.2026.11546003

The gap: an econometric literature on rice in a few markets, versus a network / pattern-mining view across 100+ markets and 70 commodities after 2024.

**Difficulty:** Medium. **Cleaning:** Medium (gaps, units, unbalanced panel). **Compute:** laptop.

**Risks.** Monthly data with only ~32 dense months, so correlation networks are noisy (use bootstrapped edges). Economists may expect cointegration tests. Flood attribution is confounded with the Jul–Aug 2024 political transition.

**Scores:** N 4 · F 4 · D 3 · Demo 3 · P 4

---

### Idea 7 What do Bangladeshi food-delivery customers complain about? Aspect, time and reviewer-graph mining of 334k Foodpanda reviews

**Pitch.** BDFoodSent has 334k Foodpanda Bangladesh reviews with *separate food and rider ratings*, timestamps (Nov 2022 → Nov 2023, which covers Ramadan 2023), city and cuisine. All prior work does sentiment classification. This project mines the complaint structure instead: topics, food-vs-rider discrepancy rules, Ramadan and weather effects, and suspicious reviewer clusters.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| BDFoodSent (BRAC Univ.) | https://data.mendeley.com/datasets/532fxhnwbb/2 (also https://zenodo.org/records/14259962) | 132.54 MB CSV, 334,119 × 19 | CC BY 4.0 | v2, 2 Dec 2024 |

My check (30.6k-row sample): `createdAt` 2022-11-10 → 2023-11-10. Dhaka is 82% of rows, then Chittagong, Sylhet, Narayanganj, Savar and Gazipur. Restaurant names and reviewers are anonymised ("Restaurant 2914", "User 12585"). `ratings` holds aspect scores (`overall`, `restaurant_food`, and `rider` in ~60% of rows). Ratings are bimodal (1★ 37%, 5★ 30%). Text is mostly English/Banglish; the description says it was translated to English, but much of it is not.

**Techniques.** NMF/LDA topic mining on TF-IDF after Banglish normalisation. Association rules {city, cuisine, hour, Ramadan, rainy day} → {rider ≤ 2, food ≥ 4}. Temporal pattern and burst mining. Reviewer–restaurant bipartite graph communities, plus LOF on reviewer behaviour for suspicious bursts. Rating–text mismatch outliers.

**Research question and novelty.** *Which service failures (food vs delivery) dominate, and when and where do they cluster?* Prior work:
- BDFoodSent dataset (above).
- Amin et al. (2024), *Sentiment Polarity Analysis of Bangla Food Reviews Using Machine and Deep Learning Algorithms*, ICAEEE 2024. https://doi.org/10.1109/icaeee62219.2024.10561876
- BRAC Univ. thesis, *Sentiment analysis of restaurant reviews from Bangladeshi food delivery apps*. https://dspace.bracu.ac.bd/items/3a557973-d4a5-4df7-b641-33f390f832f0

The gap: no aspect-discrepancy, temporal or reviewer-graph mining.

**Difficulty:** Medium. **Cleaning:** Medium–High (Banglish). **Compute:** Colab.

**Risks.** Graders may see it as "sentiment analysis again". Anonymisation limits interpretation. Only one year of data.

**Scores:** N 3 · F 4 · D 3 · Demo 4 · P 3

---

### Idea 8 When prices can't fall: network and regime mining of the Dhaka Stock Exchange floor-price period (2022–2024)

**Pitch.** From July 2022 to January 2024 the regulator imposed floor prices. Most stocks stopped moving, which breaks standard correlation-network analysis. Detect the regime from data, mine "frozen-stock" run patterns, and compare how network structure (MST communities) changed before, during and after. *Analysis only; no investment advice.*

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Dhaka Stock Exchange Historical Data (1999–2025) | https://data.mendeley.com/datasets/5mww8rb9td/1 | 153.53 MB across 531 per-ticker CSVs (0.02–0.3 MB each); 1,684,249 rows; Jan 1999 → Apr 2025; code, date, OHLC, volume | CC BY 4.0 | v1, 9 Apr 2025 |
| (alt.) DSE historical data v3 | https://data.mendeley.com/datasets/23553sm4tn | – | **unverified** | 8 Mar 2024 (v1) |

My check (ACI): share of zero-return days was 0.0% (Jul 2021–Jun 2022), **82.8% (Aug 2022–Dec 2023)** and 0.4% (Feb 2024–Apr 2025).

**Techniques.** Change points on market-wide zero-return share and turnover. Run-length / sequential patterns of frozen days. MST and PMFG networks plus Louvain per regime, comparing similarity measures that survive zero returns (rank-based, volume-based). Anomaly detection on volume.

**Research question and novelty.** *How did the floor-price policy reshape trading-activity patterns and the co-movement network of DSE stocks?* Prior work:
- Rakib et al. (2024), *Change in hierarchy of the financial networks: A study on firms of an emerging market in Bangladesh*, PLOS ONE (2008–2020). https://doi.org/10.1371/journal.pone.0301725
- Muhammad et al. (2023), *Utilizing Technical Data to Discover Similar Companies in Dhaka Stock Exchange*, arXiv. https://arxiv.org/abs/2301.04455
- Mantegna (1999), *Hierarchical structure in financial markets*, EPJ B. https://doi.org/10.1007/s100510050929

The gap: the network literature stops at 2020, and nothing covers the floor-price regime or the methodological problem of zero returns.

**Difficulty:** Medium. **Cleaning:** Medium (ticker changes, halts; sector labels must be added). **Compute:** laptop.

**Risks.** No sector labels (they need to be collected manually). Survivorship. Finance framing must stay descriptive.

**Scores:** N 4 · F 4 · D 4 · Demo 3 · P 4

---

### Idea 9 Trajectory mining at Dhaka intersections (DhaTraX vehicle tracks)

**Pitch.** DhaTraX (Sept 2026) releases tracked vehicle trajectories with class labels and metric ground-plane coordinates from fixed cameras at three Dhaka sites. It is non-lane-based, mixed traffic with rickshaws, CNGs and buses. Cluster movement patterns, find abnormal trajectories (wrong-way, U-turns, long stops), and mine class-wise interaction patterns.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| DhaTraX (Arnob Roy) | https://zenodo.org/records/22157752 | CSV in ZIPs: `INT_realXY.zip` 438 MB, `BS_realXY.zip` 456 MB, `BM_realXY.zip` 553 MB, raw 1,099 MB, homography 5 MB, analysis 6.8 MB | CC BY 4.0 | Sept 2026 (14 downloads when checked) |

**Techniques.** TRACLUS / DBSCAN on Fréchet or DTW distances. Isolation Forest / LOF on trajectory features. PrefixSpan over zone-transition sequences. Interaction (near-miss) pattern mining by vehicle class.

**Research question and novelty.** *What movement patterns and anomalies characterise non-lane-based traffic at Dhaka intersections, by vehicle class?* Prior work:
- Lee, Han & Whang (2007), *Trajectory clustering: a partition-and-group framework*, SIGMOD. https://doi.org/10.1145/1247480.1247546
- Ali, Rao & Bhaskar (2025), *Microscopic Vehicle Trajectory Datasets from UAV-collected Video for Heterogeneous, Area-Based Urban Traffic*, arXiv. https://arxiv.org/abs/2512.11898
- Airport Highway (Dhaka) trajectory dataset, IEEE DataPort (7,146 vehicle trajectories). https://ieee-dataport.org/documents/airport-dataset (login likely needed to download: **unverified**)

The gap: brand-new Dhaka intersection data with no analysis published yet.

**Difficulty:** Hard. **Cleaning:** Medium. **Compute:** Colab (1.5 GB of downloads).

**Risks.** Large files. Sparse documentation (video durations unknown). Only 3 sites. Tracker noise.

**Scores:** N 5 · F 2 · D 4 · Demo 5 · P 4

---

### Idea 10 News as a sensor: burst and topic mining of 1.9M Bangla news articles against dengue and disaster records

**Pitch.** Use a very large Bangla news corpus to detect bursts of dengue, flood, heatwave and fire coverage. Check whether news bursts lead or lag official counts (e.g., DGHS dengue, Idea 5), extending a 2021 SUST study to a multi-year, multi-outlet setting.

**Datasets**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| BNAD: Bangla News Article Dataset (9 outlets) | https://zenodo.org/records/11111869 / https://huggingface.co/datasets/Asif-Saad/Bangla_News_Article | JSONL per outlet (e.g., DhakaTribuneBangla 387 MB, ekattorTv 297 MB, Ittefaq 4.3 GB); fields `Title, Category, Time, Content, Meta, Tags` (Bangla date strings) | CC BY 4.0 (Zenodo) / Apache-2.0 (HF) | 2024 (HF last modified 24 Apr 2024) |
| (smaller alt.) Bangla Daily News Corpus | https://www.kaggle.com/datasets/shafin11027/bangla-daily-news-corpus | 28.8 MB | CC0 | 6 Oct 2026 (3 notebooks) |

**Techniques.** Kleinberg burst detection. Per-month NMF/LDA. Keyword co-occurrence networks. Cross-correlation of burst series with official counts.

**Research question and novelty.** *Do Bangla news bursts provide early signals of dengue and disaster events?* Prior work:
- Tasnim et al. (2021), arXiv 2107.14095 / FLAIRS. https://arxiv.org/abs/2107.14095
- Alam et al. (2020), *Bangla News Trend Observation using LDA Based Topic Modeling*, ICCIT 2020. https://doi.org/10.1109/iccit51783.2020.9392719
- *GHTM: A Graph-based Hybrid Topic Modeling Approach… Bengali*, arXiv 2508.00605. https://arxiv.org/abs/2508.00605

**Difficulty:** Medium–Hard. **Cleaning:** High (Bangla dates and text). **Compute:** Colab (choose 1–2 outlets).

**Risks.** BNAD coverage dates are unclear and may stop in 2024. Bangla NLP preprocessing takes effort. The corpus is large.

**Scores:** N 3 · F 3 · D 3 · Demo 4 · P 3

---

### Idea 11 Spatial structure of a 600k-shop retail distribution network

**Pitch.** A national FMCG distributor's outlet census: 719,817 outlets with GPS (per the Data in Brief paper) and per-shop targets for 17 products across 613,656 shops. Mine spatial clusters, co-location patterns of shop types, product-portfolio itemsets, and outlier shops.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Comprehensive Retail Network Dataset of Bangladesh (UIU) | https://data.mendeley.com/datasets/mgzvngzng2/1 | 205.87 MB: `shop_info_with_geo.csv` 116.97 MB, `product_target_for_shop.csv` 88.89 MB, `product_info.csv` | CC BY 4.0 | v1, 7 Apr 2025 |

Paper: Shahin, Swarna & Farid (2026), *Data in Brief* 112326. https://doi.org/10.1016/j.dib.2025.112326

My check of the headers: categorical fields are **anonymised codes** (`shpt_1`, `plc_1`, `freq_1`, `shpi_1`). Targets are fractional per product (`prod_1…prod_17`, `Total`). The sample has duplicate coordinates.

**Techniques.** HDBSCAN. Co-location mining (Huang, Shekhar & Xiong 2004, https://doi.org/10.1109/TKDE.2004.90). FP-Growth on products with target > 0. LOF for shops whose targets are out of line with their neighbourhood. k-prototypes segmentation.

**Novelty.** Only the dataset paper exists. **Difficulty:** Medium. **Cleaning:** Medium. **Compute:** Colab.

**Risks.** Anonymised codes make findings hard to interpret. "Targets" are not sales. The company is unknown.

**Scores:** N 3 · F 4 · D 2 · Demo 3 · P 3

---

### Idea 12 Sequential pattern mining of Bangladesh Premier League ball-by-ball data

**Pitch.** Cricsheet has ball-by-ball data for 469 BPL matches. Mine sequential patterns of deliveries (pressure build-up leading to a wicket), phase-wise rules, and batter archetypes, and compare BPL with IPL and PSL.

**Dataset**
| Dataset | Link | Size / format | License | Last updated |
|---|---|---|---|---|
| Cricsheet, Bangladesh Premier League | https://cricsheet.org/downloads/ | JSON (CSV "experimental"); 469 matches | ODC-BY 1.0 (per Cricsheet register page / library guide: https://cricsheet.org/register , https://library.mcmaster.ca/data/cricsheet) | site updated continuously (last blog post 10 Jun 2026) |

**Techniques.** GSP / PrefixSpan (Srikant & Agrawal 1996, https://doi.org/10.1007/BFb0014140). Association rules by match phase. k-means batter profiles. Anomalous-over detection.

**Prior work.** NCI technical report on IPL data mining (https://norma.ncirl.ie/3475/1/kuldeeprawat.pdf). Sports analytics is broad.

**Difficulty:** Easy. **Cleaning:** Low. **Compute:** laptop.

**Risks.** Findings may be obvious. Low research impact and few suitable venues. Weak local-development relevance.

**Scores:** N 2 · F 5 · D 5 · Demo 5 · P 2

---

## 4. Comparison table

| # | Idea | Main DM techniques | N | F | D | Demo | P | Sum | Difficulty |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Load-shedding crisis mining (PGCB)** | change points, matrix profile, k-Shape, emerging patterns / ARM | 4 | 5 | 4 | 4 | 4 | **21** | Medium |
| **2** | **Dhaka congestion propagation (81 junctions)** | TS clustering, Granger graph + centrality, co-jam itemsets, Eid contrast | 3 | 5 | 4 | 5 | 4 | **21** | Medium |
| **3** | **Restaurant popularity rhythms (BanglaDine)** | k-Shape, HDBSCAN / Gi\*, FP-Growth, LOF | 4 | 4 | 3 | 5 | 4 | **20** | Medium |
| 4 | Load shedding × air quality | contrast / subgroup mining, event windows | 5 | 3 | 3 | 4 | 5 | 20 | Hard |
| 5 | Dengue onset rules & curve clustering | DTW clustering, temporal rules, CUSUM | 3 | 5 | 4 | 4 | 4 | 20 | Easy–Med |
| 6 | Food-price shock networks (WFP) | correlation networks, Louvain, lead–lag, co-spike itemsets | 4 | 4 | 3 | 3 | 4 | 18 | Medium |
| 7 | Food-delivery complaint mining | NMF/LDA, ARM, bipartite graph, LOF | 3 | 4 | 3 | 4 | 3 | 17 | Medium |
| 8 | DSE floor-price regime & networks | change points, MST/PMFG, run patterns | 4 | 4 | 4 | 3 | 4 | 19 | Medium |
| 9 | DhaTraX trajectory mining | TRACLUS, trajectory outliers, PrefixSpan | 5 | 2 | 4 | 5 | 4 | 20 | Hard |
| 10 | Bangla news burst mining | Kleinberg bursts, NMF/LDA, co-occurrence networks | 3 | 3 | 3 | 4 | 3 | 16 | Med–Hard |
| 11 | Retail network spatial mining | HDBSCAN, co-location, FP-Growth, LOF | 3 | 4 | 2 | 3 | 3 | 15 | Medium |
| 12 | BPL cricket sequential patterns | PrefixSpan, ARM, k-means | 2 | 5 | 5 | 5 | 2 | 19 | Easy |

*Why the top 3 are not simply the three highest sums.* Ideas 1 and 2 tie. Idea 3 beats the other 20-pointers because: Idea 4 is better used as Idea 1's stretch goal; Idea 5 is in a crowded area; Idea 9 is hard to finish in 14 weeks; Idea 12 has low publishability. The top 3 also cover three different technique families (time-series, spatiotemporal/graph, clustering/ARM/spatial), so you can choose by interest.

---

## 5. Deep dives on the top 3

Shared toolkit (all free): `pandas`, `scikit-learn`, `mlxtend` (Apriori / FP-Growth), `tslearn` (k-Shape, DTW), `stumpy` (matrix profile), `ruptures` (PELT), `statsmodels` (Granger, STL), `networkx` + `python-louvain`, `hdbscan`, `geopandas` / `folium` / `pydeck`, and `streamlit` for the demo.

### 5.1 Idea 1: Mining the load-shedding crisis (PGCB 2015–2026)

**Baselines vs the interesting method**
| Task | Baseline | Interesting method |
|---|---|---|
| Regimes | Calendar split (pre-2022 vs 2022+) | PELT change points on daily shedding energy, liquid-fuel share and import share; compare to known events (e.g., spot-LNG halt mid-2022) |
| Typical days | k-means on raw 24-h vectors | k-Shape / DTW clustering per regime; matrix-profile motifs (recurring multi-day patterns) |
| Rules | Apriori support/confidence on all years | FP-Growth + **emerging patterns** (Dong & Li 1999, https://doi.org/10.1145/312129.312191): rules whose support grows ≥k× between regimes, ranked by lift / conviction |
| Episodes | Count of shedding hours | PrefixSpan on episode sequences (e.g., gas↓ → liquid↑ → evening peak → shedding) |
| Glitches / events | Z-score outliers | Matrix-profile discords + Isolation Forest on STL residuals; label top-50 as *data error* vs *real event* |

**Evaluation.** Silhouette / Davies–Bouldin plus bootstrap ARI stability for clusters. For rules: lift, conviction, leverage, and a **temporal hold-out** (mine on 2022–2024, check whether the rules still hold in 2025). For change points: alignment with documented events within ±7 days. For anomalies: precision@50 by manual labelling, and recall on **synthetic glitches you inject** at known positions.

**Expected figures.**
- Day-of-year × hour heatmap of shedding for every year (the "crisis fingerprint").
- Regime timeline with change points over a stacked fuel-mix area chart.
- Cluster centroids of daily profiles per regime.
- Matrix profile with motifs and discords marked.
- Table of the top emerging rules.
- (Stretch) matched NOx / PM2.5 contrast during shedding hours (Idea 4).

**What I expect to find (hypotheses, not results).** A sharp regime break in mid-2022 and a partial recovery in 2025. Shedding concentrated in the evening peak and late night (Prothom Alo has reported midnight peaks). High-lift rules linking low gas share and high liquid-fuel generation to shedding. A cluster of obvious data-entry glitches (my check found multiple impossible values).

**14-week plan**
| Week | Work |
|---|---|
| 1 | Read the 4 related papers; download both PGCB versions; reproduce my profile; set up repo + notebook template |
| 2 | Cleaning: half-hourly → hourly, impossible-value rules, merge UCI/Mendeley, missing solar/wind policy, document everything |
| 3 | EDA: yearly heatmaps, fuel-mix trends, shedding distributions. **Checkpoint: data report** |
| 4 | Change-point detection (PELT, several penalties) → regimes; event alignment table |
| 5 | Daily-profile clustering: k-means baseline vs k-Shape/DTW; choose k; stability |
| 6 | Matrix profile (STUMPY): motifs and discords; start labelling discords |
| 7 | Discretisation design for ARM (season, hour-band, fuel-share terciles, import levels); Apriori baseline |
| 8 | FP-Growth + emerging-pattern mining across regimes; interestingness ranking. **Mid-term demo** |
| 9 | PrefixSpan on shedding episodes; temporal hold-out validation of rules on 2025 |
| 10 | Anomaly detection evaluation (injected glitches + labelled discords). *Optional:* division-level BPDB data for spatial shedding patterns |
| 11 | (Stretch) Download CAMS-BD, clean one Dhaka station, run the matched shedding / no-shedding contrast |
| 12 | Build Streamlit dashboard (year slider, regime view, rule explorer) |
| 13 | Write paper (IEEE 6-page template): intro, related work, method, results |
| 14 | Final figures, limitations, polish demo, submit course report; prepare conference version |

**Paper title:** *"Mining the Dark Hours: Regimes, Motifs and Emerging Fuel-Mix Rules in Bangladesh's Hourly Grid Data, 2015–2026"*
**Target venues:**
- **ICCIT 2027**. ICCIT 2026 runs 18–20 Dec 2026 with its deadline already passed in Aug 2026, so 2027 is the realistic target. https://iccit.org.bd/
- IEEE Region 10 events (TENSYMP / R10-HTC 2027; check current CFPs).
- *Tackling Climate Change with ML* workshop (NeurIPS 2026 edition announced; a 2027 edition is likely but unverified): https://www.climatechange.ai/events/neurips2026
- ICECE is biennial (14th edition 10–12 Dec 2026, deadline likely passed), so the next is 2028: https://icece.buet.ac.bd/

---

### 5.2 Idea 2: Congestion propagation across 81 Dhaka junctions

**Baselines vs the interesting method**
| Task | Baseline | Interesting method |
|---|---|---|
| Junction typology | k-means on mean daily profiles | k-Shape / DTW-hierarchical on weekday vs Friday profiles (Hasan & Sarker 2025 did this at *division* level, so here it is a supporting step) |
| Spread | Zero-lag Pearson network | Lagged cross-correlation + Granger tests only between adjacency-neighbours (travel time < τ) → **directed propagation graph**; PageRank / out-strength "sources" |
| Co-occurrence | Pairwise correlation | FP-Growth **co-jam itemsets** over 10-min windows (heavy class), maximal sets, lift vs independence |
| Order | – | PrefixSpan on jam-onset order 7–11 am |
| Events | Daily averages | PELT change points + contrast mining of pre-Eid (≈20–26 May), Eid (27 May–2 Jun) and recovery; rain-day anomalies (Open-Meteo join) |

**Evaluation.**
- *Predictive check of the propagation graph:* for each junction, does adding its graph-parents' lagged values improve a 10–30-min-ahead AR model over persistence and over AR alone? Train weeks 1–5, test weeks 6–8; report MAE and the percentage of junctions improved.
- Compare the identified sources with the bottlenecks named by Sarker et al. 2025 (Kawran Bazar, Mohammadpur Bus Stand, Dhanmondi 32) where those locations exist in the 81.
- Itemsets: lift and temporal hold-out. Clusters: silhouette and stability. Eid: effect sizes with bootstrap CIs.

**Expected figures.**
- Map of the 81 points coloured by cluster.
- **Animated congestion map** (the demo centrepiece).
- Directed propagation graph drawn on the map, with node size = PageRank.
- Time × junction heatmap with the Eid band.
- Top co-jam sets table.
- Before / during / after Eid propagation-graph comparison.

**Hypotheses.** North-corridor nodes (Abdullahpur–Uttara–Airport) act as morning sources toward the centre. Co-jam sets follow corridors more than geographic proximity. During Eid the graph thins out and loses most long-range edges, and pre-Eid days show the year's highest congestion (consistent with the 21 May peak in my check).

**14-week plan**
| Week | Work |
|---|---|
| 1 | Read the 4 Dhaka papers; download dataset; reproduce my profile; geocode the 81 locations from `sample_points.json` |
| 2 | Understand MCI vs class files (and email the dataset author via the Mendeley contact for the MCI definition: **you** should do this, I did not contact anyone); build calendar features (Friday, Eid, holidays) |
| 3 | EDA: heatmaps, weekday / Friday curves, map. **Checkpoint: data report** |
| 4 | Junction clustering (baseline vs k-Shape / DTW); interpret clusters on the map |
| 5 | Pull Open-Meteo hourly rain for Dhaka; rain-day anomaly analysis |
| 6 | Lag analysis: cross-correlation per neighbour pair; choose lag window |
| 7 | Granger tests (with false-discovery-rate control) → propagation graph; centrality |
| 8 | Out-of-sample predictive validation of the graph. **Mid-term demo** |
| 9 | Co-jam itemsets (FP-Growth) + PrefixSpan on onset order |
| 10 | Eid natural experiment: change points, contrast, graph-before/after comparison |
| 11 | Robustness: different thresholds / lags; weekday-only graphs |
| 12 | Streamlit / pydeck animated map + graph explorer |
| 13 | Paper writing |
| 14 | Final polish; course submission; conference version |

**Paper title:** *"Who Jams First? Mining Congestion Propagation and Co-Jam Patterns Across 81 Dhaka Junctions, with an Eid-ul-Adha Natural Experiment"*
**Target venues:**
- **ICCIT 2027**.
- **VEHITS** (where the two 2025 Dhaka papers appeared; check the 2027 CFP).
- IEEE TENSYMP / R10-HTC.
- ACM SIGSPATIAL student research competition (check CFP).

---

### 5.3 Idea 3: Weekly popularity rhythms of Bangladeshi restaurants

**Baselines vs the interesting method**
| Task | Baseline | Interesting method |
|---|---|---|
| Rhythm types | k-means on raw 168-d vectors | z-normalise per venue → k-Shape / DTW clustering; also cluster day-of-week shape separately (Friday vs other days) |
| Where | Density map | HDBSCAN per archetype + Getis-Ord Gi\* hotspots (Dhaka thana level); Moran's I |
| Why | Apriori on all attributes | FP-Growth with consequent constraints (archetype = X, rating ≥ 4.5); significance via Fisher's exact test + Benjamini–Hochberg |
| Suspicious ratings | Rating > 4.8 & reviews < 5 | LOF / Isolation Forest on (rating, log reviews, category, archetype, attribute richness) |
| Cities | – | Archetype mix per division; chi-square + contrast sets |

**Evaluation.** Silhouette and bootstrap stability. A small human evaluation: classmates label 50 curves into proposed archetypes, and you report agreement (Cohen's κ) with the clusters. Rule lift, conviction and adjusted p-values. Spatial autocorrelation significance. Manual inspection of the top-30 outliers.

**Expected figures.**
- Archetype centroids as 7×24 heatmaps.
- Dhaka map of archetypes.
- Friday vs weekday curve comparison.
- Rule table.
- City-mix bar chart.
- Outlier gallery.

**Hypotheses.** Distinct late-night (21:00–01:00) archetypes in Old Dhaka and Chattogram, Friday-lunch and evening family archetypes in Gulshan / Dhanmondi, office-lunch weekday archetypes near Motijheel / Karwan Bazar. Rules linking "Delivery / Takeaway only" to late-night profiles.

**14-week plan**
| Week | Work |
|---|---|
| 1 | Read related papers; download CSV (62 MB); load in chunks |
| 2 | Cleaning: filter to a Bangladesh polygon (drop "India" rows), parse list attributes into items, keep rows with popular times |
| 3 | EDA (coverage, ratings, city counts, missingness bias check: with vs without curves). **Checkpoint** |
| 4 | Baseline k-means; normalisation choices |
| 5 | k-Shape / DTW clustering; choose k; name archetypes |
| 6 | Human-label agreement study (50 curves) |
| 7 | Spatial: HDBSCAN, Gi\* hotspots, Moran's I (Dhaka focus, then other cities) |
| 8 | **Mid-term demo** (map + archetypes) |
| 9 | Transaction encoding; FP-Growth with archetype consequents; significance testing |
| 10 | Outlier detection for suspicious ratings; manual inspection |
| 11 | Cross-city contrast; Friday-weekend comparison with Western studies |
| 12 | Streamlit / folium dashboard (filter by archetype, hour slider) |
| 13 | Paper writing |
| 14 | Polish; submissions |

**Paper title:** *"When Does Bangladesh Eat? Mining Weekly Popularity Rhythms of 20,000+ Restaurants from Google Maps"*
**Target venues:**
- **ICCIT 2027**.
- ACM COMPASS (poster / short paper; 2027 CFP not yet seen): https://compass.acm.org/
- IEEE R10 events.
- Urban-computing workshops at KDD / SIGSPATIAL (check current CFPs).

---

## 6. Things to do before committing (for any idea)

1. Download the dataset and re-run my quick checks (row counts, date range, missingness). Datasets get new versions.
2. Search Google Scholar for the dataset DOI to see whether a paper using it appeared after 7 Oct 2026.
3. Confirm with your instructor that unsupervised and pattern mining (not just classification) meets the course requirements.
4. For conference submission: check the current CFP and deadline. I could verify ICCIT 2026's dates (deadline passed) and ICECE 2026's (biennial), but not the 2027 calls.

---

## 7. Ideas I rejected (and why)

| Candidate | Source | Why rejected |
|---|---|---|
| Bangladesh Road Traffic Accident Dataset 2007–2024 (49,566 rows) | https://data.mendeley.com/datasets/p2kgkb5cd2 | **Appears largely synthetic / randomised** (my checks: independent duplicate weather and light columns, uniform severity, death ≈1 for all severities, 99.3% duplicate narratives, 96% motorcyclists, 99.9% "Urban"). Narratives also contain personal names. The file itself has 47,680 rows covering 2007–2021, not 2024 |
| Motorbike Accident Severity dataset | https://data.mendeley.com/datasets/rm8t8kmhpj/3 | Survey-based, small; classification-only use case |
| Flight Price Dataset of Bangladesh (Kaggle, 12 notebooks) | https://www.kaggle.com/datasets/mahatiratusher/flight-price-dataset-of-bangladesh | Self-described **synthetic** |
| "Dhaka Air Quality 2000–2025 – Synthetic" | https://www.kaggle.com/datasets/shakil10945/dhaka-air-quality-2000-2025-synthetic-dataset | Synthetic |
| Hourly AQI of Bangladesh, 103 cities (Kaggle, 359 MB) | https://www.kaggle.com/datasets/shakilofficial0/hourly-air-quality-index-aqi-of-bangladesh | Values going back to 2000 for 103 cities, including CO₂, indicate modelled (reanalysis-type) data, not measured (**unverified** source); CC BY-NC. CAMS-BD is the measured alternative |
| Diabetes datasets (DiaHealth, DiaBD) | https://data.mendeley.com/datasets/7m7555vgrn , https://data.mendeley.com/datasets/m8cgwxs9s6/3 | Generic binary classification; heavily overdone genre |
| Student Performance Bangladesh (SSC/HSC) | https://data.mendeley.com/datasets/5nvsv7ypg4 | Generic prediction survey; little novelty |
| University student mental health (USDI-30, BDI/PHQ, ONUBHOB-BD) | https://data.mendeley.com/datasets/57yvy3gx8f , https://data.mendeley.com/datasets/f4z2bfv7vk | Small surveys; ML risk-factor studies on Bangladeshi students are **already published** (JHPN 2025: https://jhpn.biomedcentral.com/articles/10.1186/s41043-025-01095-8 ; QPAIN 2025: https://research.daffodilvarsity.edu.bd/scopus-article/6581). A search snippet also described a regression + Apriori hybrid study on this topic (**unverified**) |
| Bangla cyberbullying / hate speech (multilabel, BOISHOMMO, BanCyB) | https://data.mendeley.com/datasets/sz5558wrd4/3 , https://data.mendeley.com/datasets/4tsb6tg9b2 | NLP classification, crowded; little classic DM |
| July-2024 uprising sentiment (4,200 comments) | https://arxiv.org/abs/2507.11084 (dataset DOI 10.5281/zenodo.15342899, **unverified**) | Generic sentiment; small; politically sensitive |
| Daraz review sentiment (EComReviews-BD, DarazMM, BECS, RevBangla) | https://zenodo.org/records/22733565 | Generic sentiment / ABSA (NLP-heavy). BDFoodSent (Idea 7) is the better review dataset |
| Bangladeshi tech jobs (HF, weekly) | https://huggingface.co/datasets/swadhinbiswas/bangladeshi-jobs | Only 474 open postings (snapshot 4 Oct 2026), too small for skill-association mining today. Worth revisiting in a year |
| Medicinal products in Bangladesh | https://data.mendeley.com/datasets/zhtvkny53n/1 | Designed for LLM fine-tuning; a flat brand/generic list with weak mining potential |
| AgriClimateBD (4,607 rows, 2022 only) | https://data.mendeley.com/datasets/tb5x9gw2pt/2 | Single year, small; fine as a side dataset, not a project |
| Bangladesh Agroclimatic Crop Yield 2000–2024 (Kaggle) | https://www.kaggle.com/datasets/firozemaliha/bangladesh-agroclimatic-crop-yield-2000-2024 | 150 rows |
| BMD 35-station daily weather / 1901–2023 Kaggle weather | https://data.mendeley.com/datasets/tbrhznpwg9/1 , https://www.kaggle.com/datasets/yakinrubaiat/bangladesh-weather-dataset | Heavily explored (20 notebooks on the Kaggle version); useful only as a join table |
| IBTrACS Bay-of-Bengal cyclone track clustering | https://www.ncei.noaa.gov/products/international-best-track-archive | Good data, but track clustering already done (FCM-firefly, standard-deviational-ellipse papers) |
| Arsenic (BGS/DPHE national survey) | https://www.bgs.ac.uk/groundwater/?p=3986 | 1998–99 data; extensively studied |
| Ganges hydrology (3 stations) | https://data.mendeley.com/datasets/sx4m6tdwb7 | Too narrow for DM |
| data.gov.bd "Daily Water Levels" | https://data.gov.bd/dataset/daily-water-levels-data | Created 2018, never updated, "License Not Specified" |
| Lightning fatalities | (papers only, e.g., https://doi.org/10.1016/j.heliyon.2024.e28708) | No open event-level dataset |
| Woman Harassment 2001–21 / crime statistics 2010–19 (Kaggle) | https://www.kaggle.com/datasets/azminetoushikwasi/woman-harassment-dataset-200121-bangladesh | Yearly aggregates, tiny, sensitive |
| Garment worker productivity (UCI #597) | https://archive.ics.uci.edu/dataset/597/productivity+prediction+of+garment+employees | 1,197 rows (2020), 66k page views; overused |
| Mapped in Bangladesh / Open Supply Hub factories | https://www.fibre2fashion.com/news/apparel-news/over-3-600-rmg-factories-in-bangladesh-now-digitally-mapped-278976-newsdetails.htm | Bulk download / licence not verified; may need an account |
| DHS / BDHS, MICS, ACLED | – | Require registration or approval (against the "no special approval" rule) |
| Image datasets (crop/leaf disease, license plates, rickshaw video) | various Kaggle / HF | Deep-learning CV, not data mining |
| KrishiGyan / KrishokChat agricultural QA | https://arxiv.org/pdf/2510.18355 | LLM / RAG resources, not DM |
| House rent / real estate (bproperty, Kaggle 12 notebooks) | https://www.kaggle.com/datasets/durjoychandrapaul/house-price-bangladesh | Regression genre; overdone |
| South Asia WDI panels (World Bank) | https://www.kaggle.com/datasets/rezwananik/south-asia-growth-and-development-data-2000-23 | Country-level, tiny n; overdone clustering exercise |
| Dhaka local bus routes (Kaggle, 0.05 MB) | https://www.kaggle.com/datasets/mahabub001cs/dhaka-local-bus-route | Interesting for graph mining but too small alone; a possible add-on to Idea 2 |
| PreEnvBD preterm birth (Zenodo) | https://zenodo.org/records/19684670 | No files visible in the record when checked; BDHS-derived |
| Net-Edu-BD (Zenodo, 4 Oct 2026) | https://zenodo.org/records/23134442 | No files visible in the record when checked |
| Dengue clinical / hematology datasets | https://data.mendeley.com/datasets/673swz9tb4 , https://www.kaggle.com/datasets/kawsarahmad/dengue-dataset-bangladesh | Small diagnostic classification (11 Kaggle notebooks on the latter) |

---

## 8. Assumptions I made

- **Timing:** the semester runs roughly mid-October 2026 → late January 2027 (14 weeks), with ~8–10 hours/week for the project. You work alone or in a pair.
- **Course scope:** unsupervised learning, pattern mining, graph mining and anomaly detection all count as data mining. A small supervised component (e.g., predictive validation) is fine.
- **"Publishable"** means a student / regional IEEE conference (ICCIT, TENSYMP, R10-HTC) or a workshop, not a top-tier venue.
- **Compute:** Python on a laptop, with Colab for files over ~100 MB. No GPU training is needed for any shortlisted idea.
- **Licences** are as stated on the dataset pages on 7 Oct 2026. CC BY 4.0 / CC BY-IGO / ODC-BY require attribution, and CC BY-SA requires share-alike for derived data. This is not legal advice, especially for scraped sources (BanglaDine, Dhaka traffic).
- **Verification method:** I did not sign in or create any account. I downloaded only small files (≤7 MB: PGCB, accident ZIP, dengue CSVs, OHLC, WFP CSV, Dhaka traffic CSVs, one DSE ticker) and used byte-range reads (≤12 MB per file) for the large files (BanglaDine, BDFoodSent, retail). I did not download CAMS-BD (108 MB), DhaTraX (1.5 GB) or BNAD (GBs). Their descriptions come from the repository pages.
- **Scores** are my judgement, explained in each idea. Dates such as "last updated" are the repository's publish / modified dates.
- **Literature search:** the Semantic Scholar API was rate-limited, so related-work searches relied mainly on web search plus Crossref / arXiv / PubMed verification. The related-work lists are representative, not exhaustive. Do a Google Scholar pass on your chosen idea before writing.
- I am not giving financial advice. Idea 8 is descriptive market-structure analysis only.
