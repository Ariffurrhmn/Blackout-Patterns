# Sources (visited and found useful), grouped by idea

All URLs below were opened (page, API record, or file header) on 7 Oct 2026 unless marked **unverified**. "API" means metadata was read from the repository's public API for that same record.

---

## Idea 1: Load-shedding crisis mining (PGCB)

**Datasets**
- https://data.mendeley.com/datasets/vpk8spw2mm/1 — Hourly Electricity Generation, Demand, Load Shedding & Fuel Mix (2015–2026). API + full CSV inspected (6.55 MB)
- https://archive.ics.uci.edu/dataset/1175/pgcb+hourly+generation+dataset — UCI mirror (92,650 × 14, XLSX 6.8 MB)
- https://data.mendeley.com/datasets/x7r7wdb39k/1 — Daily electricity incl. division-level load shedding (BPDB, 2019–2024)
- https://data.mendeley.com/datasets/4c5jwjhpns — Daily peak demand 2016–2024 (considered, not needed)
- https://data.mendeley.com/datasets/djdg2d3rbz/1 — Chattogram urban load 2021–2023 (considered)
- https://data.mendeley.com/datasets/tbrhznpwg9/1 — BMD daily weather, 35 stations (join table)

**Papers / context**
- https://doi.org/10.1007/s42488-025-00140-9 — Islam, Turja & Habib 2025, demand forecasting (paper linked from UCI)
- https://doi.org/10.1109/ECAI65401.2025.11095479 — Yeaser, Nafs & Hossain 2025, ECAI
- https://arxiv.org/abs/2406.06651 — Akhter et al. 2024, Dhaka demand forecasting CNN-BiLSTM
- https://vu.edu.bd/publications/3168/an-intelligent-machine-learning-based-load-shedding-prediction-and-smart-energy-management-framework-for-power-grid-optimization-in-bangladesh — SPICSCON 2026 load-shedding prediction
- https://doi.org/10.65405/cv5t9g68 — "LATENT" anomaly tracking on the PGCB grid (2026; low-profile journal)
- https://courses.lsa.umich.edu/urop-symposium/symposium-presentati/left-in-the-dark-regional-variation-in-the-impacts-of-load-shedding-across-bangladesh/ — student symposium on regional load-shedding impacts
- https://en.prothomalo.com/bangladesh/e4s0883p85 — news: load shedding peaks at midnight, rural areas worse
- https://cpd-power-energy-study.com/?p=2296 — 2022 fuel-shortage context
- https://doi.org/10.1109/ICDM.2016.0179 — Matrix Profile I (Yeh et al. 2016)
- https://arxiv.org/abs/1811.03064 — Matrix profile journal version
- https://doi.org/10.1145/312129.312191 — Emerging patterns (Dong & Li 1999)
- https://doi.org/10.1080/01621459.2012.737745 — PELT change points (Killick et al. 2012)
- https://doi.org/10.1109/ICDE.2001.914830 — PrefixSpan
- https://doi.org/10.1145/342009.335372 — FP-Growth
- https://doi.org/10.1109/ICDM.2008.17 — Isolation Forest

## Idea 2: Dhaka congestion propagation

**Datasets**
- https://data.mendeley.com/datasets/phkvy2xwrt/1 — Dhaka_Traffic_Data. API + all CSVs inspected (7.7 MB)
- https://open-meteo.com/ — historical weather API for rainfall join (licence **unverified**)
- https://www.kaggle.com/datasets/mahabub001cs/dhaka-local-bus-route — bus routes (possible add-on)

**Papers**
- https://doi.org/10.2478/ttj-2024-0030 — Rahman & Nower 2024, Transport & Telecommunication
- https://doi.org/10.5220/0013296200003941 — Sarker, Sakib & Nower 2025, VEHITS (spreading graphs)
- https://scitepress.org/publishedPapers/2025/131936/pdf/index.html — Hasan & Sarker 2025, VEHITS (DTW clustering of divisions)
- https://arxiv.org/abs/2011.02359 — Pramanik et al. 2020, Google Maps congestion modelling
- https://sanghani.cs.vt.edu/research/publications/2022/granger-causal-inference-for-interpretable-traffic-prediction.html — Granger causal inference for traffic (ITSC 2022)
- https://doi.org/10.1145/2723372.2737793 — k-Shape

## Idea 3: Restaurant popularity rhythms (BanglaDine2024)

**Dataset**
- https://data.mendeley.com/datasets/hxrmzggw5b/1 — BanglaDine2024. API + byte-range samples of the CSV (≈12 MB)

**Papers**
- https://doi.org/10.3390/ijgi14060221 — Barrena-Herrán et al. 2025, IJGI (Google Popular Times)
- https://ekoizpen-zientifikoa.ehu.eus/documentos/686973d984fff30d95b13d30?lang=en — record of the same paper
- https://doi.org/10.1145/2976796.2976862 — Neves et al. 2016, Curitiba & Chicago popularity time series
- https://doi.org/10.1145/2723372.2737793 — k-Shape
- https://doi.org/10.1007/978-3-642-37456-2_14 — HDBSCAN
- https://doi.org/10.1145/335191.335388 — LOF

## Idea 4: Load shedding × air quality

**Datasets**
- https://data.mendeley.com/datasets/hwmzyh5w4w/1 — CAMS-BD hourly air quality (API; 108 MB ZIP not downloaded)
- https://data.mendeley.com/datasets/vpk8spw2mm/1 — PGCB hourly (as Idea 1)
- https://data.mendeley.com/datasets/cdn2vbvzgr — Dhaka EPZ PM2.5/PM10/CO (considered)
- https://zenodo.org/records/18673791 — Dhaka air quality 2022–2026 from Open-Meteo CAMS-global (modelled; considered)

**Papers / context**
- https://doi.org/10.1371/journal.pone.0313341 — Al Hallak et al. 2024, Beirut diesel generators (PLOS ONE)
- https://arxiv.org/abs/2111.07635 — Beirut generator dispersion modelling
- https://doi.org/10.1007/s10661-023-12046-3 — Khan et al. 2023, Dhaka high pollution loading (PMC10663179)
- https://doi.org/10.1016/j.atmosenv.2023.119587 — Sarwar et al. 2023, US Embassy Dhaka PM2.5 + CMAQ (PMC10581604)
- https://doi.org/10.1016/j.dib.2024.110594 — Dhaka EPZ pollutant dataset paper (PMC11225025)
- https://indiaenvironmentportal.org.in/news-clippings/diesel-gensets-push-air-pollution-up-by-30-in-city-reveals-survey — CSE survey (news): gensets raise PM by ~30%
- https://www.thedailystar.net/tech-startup/news/real-time-air-quality-tracking-launched-across-bangladesh-3474436 — DoE's 16 CAMS stations

## Idea 5: Dengue spatiotemporal mining

**Datasets**
- https://www.kaggle.com/datasets/brownsugar297/dengue-and-weather-data-bangladesh-20222025 — daily, 8 divisions, 2022–Oct 2025 (Kaggle API)
- https://www.kaggle.com/datasets/jisangain/bangladesh-daily-and-searo-monthly-dengue-cases — daily 2024–Mar 2026 + OpenDengue monthly (Kaggle API)
- https://data.mendeley.com/datasets/z5mvwrfgsz/1 — division daily 2022–2024 + weather (API + Dhaka CSV inspected)
- https://data.mendeley.com/datasets/cgwjshkx5k — monthly division 2020–2025 (API + XLSX inspected)
- https://data.mendeley.com/datasets/zdtc3n6xv2 — survey/clinical dengue dataset (considered; Kaggle mirror has 11 notebooks)
- https://data.mendeley.com/datasets/673swz9tb4 — clinical/hematological dengue (considered)
- https://datasetsearch.research.google.com/search?query=Bangladesh%20dengue%20daily — Google Dataset Search results

**Papers**
- https://doi.org/10.1371/journal.pone.0323238 — Alam et al. 2025, PLOS ONE (PMC12360610)
- https://doi.org/10.1101/2024.03.24.24304789 — Hasan et al. 2024, 2023 outbreak, medRxiv
- https://doi.org/10.32473/flairs.v34i1.128552 — Tasnim et al. 2021, FLAIRS
- https://arxiv.org/abs/2107.14095 — Tasnim et al. 2021, arXiv version

## Idea 6: Food-price shock networks

**Datasets**
- https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh — WFP Bangladesh food prices (HDX API + full CSV, 4.6 MB)
- https://data.mendeley.com/datasets/dd58ks2p5y — Food Commodity Price (OHLC), 76 markets (API + CSV inspected)
- https://data.mendeley.com/datasets/5m4d33mxrs — Wheat flour + macro 2007–2025
- https://data.mendeley.com/datasets/bkmxnrn3hn — AgriPriceBD daily (API + garlic CSV inspected)
- https://data.mendeley.com/datasets/867kdtn78c/1 — AgriCast-Sylhet (considered)

**Papers**
- https://doi.org/10.3329/agric.v6i1.5219 — Siddique et al. 2010, rice market integration
- https://doi.org/10.1186/s40100-022-00228-5 — Alam, McKenzie & Begum 2022, threshold cointegration
- https://doi.org/10.2139/ssrn.4325164 — Prince et al. 2023, spatial rice market integration (VECM)
- https://doi.org/10.1109/QPAIN69676.2026.11546003 — Hossain et al. 2026, GRU price forecasting (OHLC dataset paper)
- https://doi.org/10.1088/1742-5468/2008/10/P10008 — Louvain community detection

## Idea 7: Food-delivery complaint mining

**Datasets**
- https://data.mendeley.com/datasets/532fxhnwbb/2 — BDFoodSent (API + byte-range samples)
- https://zenodo.org/records/14259962 — BDFoodSent Zenodo mirror
- https://data.mendeley.com/datasets/wc87kpk6ks — Foodpanda + Hungrynaki reviews (considered)
- https://data.mendeley.com/datasets/2p5cyjwmrx — Foodpanda reviews 43k (considered)

**Papers**
- https://doi.org/10.1109/icaeee62219.2024.10561876 — Amin et al. 2024, Bangla food review sentiment
- https://arxiv.org/html/2405.06667v1 — arXiv version of the above
- https://dspace.bracu.ac.bd/items/3a557973-d4a5-4df7-b641-33f390f832f0 — BRACU thesis, food-delivery review sentiment
- https://shdl.mmu.edu.my/14998/ — Deep hierarchical networks for restaurant reviews from food apps

## Idea 8: DSE floor-price regime & networks

**Datasets**
- https://data.mendeley.com/datasets/5mww8rb9td/1 — DSE 1999–2025 (API + ACI.csv inspected)
- https://data.mendeley.com/datasets/23553sm4tn — DSE historical data (older; licence **unverified**)
- https://www.kaggle.com/datasets/mahmudulhaque/dsebd — Kaggle DSE (CC BY-NC-SA; considered)

**Papers / context**
- https://doi.org/10.1371/journal.pone.0301725 — Rakib et al. 2024, PLOS ONE (PMC11142525)
- https://arxiv.org/abs/2301.04455 — Muhammad et al. 2023, similar DSE companies
- https://doi.org/10.1007/s100510050929 — Mantegna 1999, hierarchical structure in financial markets
- https://www.thedailystar.net/business/economy/news/investors-edge-stocks-end-two-years-inflated-prices-3529781 — floor price lifted Jan 2024
- https://old.thefinancialexpress.com.bd/stock/dse-records-lowest-trade-in-25-years-after-partial-removal-of-floor-1671764664 — turnover collapse under floor

## Idea 9: DhaTraX trajectory mining

- https://zenodo.org/records/22157752 — DhaTraX (Zenodo API)
- https://doi.org/10.1145/1247480.1247546 — TRACLUS (Lee, Han & Whang 2007)
- https://arxiv.org/abs/2512.11898 — UAV trajectory datasets, heterogeneous traffic (Ali et al. 2025)
- https://ieee-dataport.org/documents/airport-dataset — Dhaka Airport Highway trajectories (download access **unverified**)
- https://dl.lib.uom.lk/items/735b8f94-f6a5-472b-8942-891ad2edeeb1 — vehicle detection for non-lane-based Dhaka traffic
- https://huggingface.co/datasets/hamimmahmud0/DRINF — DRINF drone intersection footage (video; considered)

## Idea 10: Bangla news burst mining

- https://zenodo.org/records/11111869 — BNAD (Zenodo API: files and sizes)
- https://huggingface.co/datasets/Asif-Saad/Bangla_News_Article — HF mirror (API + first rows: fields Title/Category/Time/Content/Meta/Tags)
- https://www.kaggle.com/datasets/shafin11027/bangla-daily-news-corpus — smaller CC0 corpus (Kaggle search listing)
- https://doi.org/10.1109/iccit51783.2020.9392719 — Alam et al. 2020, LDA Bangla news trends (ICCIT)
- https://arxiv.org/abs/2508.00605 — GHTM Bengali topic modelling
- https://arxiv.org/abs/2101.09667 — monitoring social dynamics in Bangladesh during COVID-19 via news
- https://doi.org/10.1023/A:1024940629314 — Kleinberg burst detection

## Idea 11: Retail network spatial mining

- https://data.mendeley.com/datasets/mgzvngzng2/1 — Comprehensive Retail Network Dataset (API + header bytes)
- https://doi.org/10.1016/j.dib.2025.112326 — Shahin, Swarna & Farid 2026, Data in Brief (PMC12765268)
- https://doi.org/10.1109/TKDE.2004.90 — co-location pattern mining (Huang, Shekhar & Xiong 2004)

## Idea 12: BPL cricket sequential patterns

- https://cricsheet.org/downloads/ — BPL listed, 469 matches
- https://cricsheet.org/ — site overview (22,983 matches)
- https://cricsheet.org/register — Cricsheet register (ODC-BY reference)
- https://library.mcmaster.ca/data/cricsheet — library guide (licence)
- https://pkg.robjhyndman.com/cricketdata/articles/cricsheet.html — R access to Cricsheet
- https://doi.org/10.1007/BFb0014140 — GSP sequential patterns (Srikant & Agrawal 1996)
- https://norma.ncirl.ie/3475/1/kuldeeprawat.pdf — IPL data-mining report

---

## Venues

- https://iccit.org.bd/ and https://iccit.org.bd/2026/call-for-paper/ — ICCIT 2026 (18–20 Dec 2026, Cox's Bazar; submission closed Aug 2026)
- https://icece.buet.ac.bd/ — ICECE 2026 (10–12 Dec 2026, BUET; biennial)
- https://www.climatechange.ai/events/neurips2026 — Tackling Climate Change with ML, NeurIPS 2026
- https://compass.acm.org/ — ACM COMPASS

## Rejected / considered (selection)

- https://data.mendeley.com/datasets/p2kgkb5cd2 — Road accident 2007–2024 (inspected; appears synthetic)
- https://www.kaggle.com/datasets/mdnahidurrahmankh/bangladesh-road-accident-dataset-2007-2024 — Kaggle copy of the above
- https://data.mendeley.com/datasets/rm8t8kmhpj/3 — Motorbike accident severity
- https://arxiv.org/abs/2409.11929 — Explainable ML for Dhaka traffic fatality prediction (prior accident work)
- https://doi.org/10.1109/qpain66474.2025.11171847 — ML road accident risk in Bangladesh (QPAIN 2025)
- https://iccesd.kuet.ac.bd/Papers/362.pdf — Khulna accident hotspots (KDE / Gi\*)
- https://www.kaggle.com/datasets/mahatiratusher/flight-price-dataset-of-bangladesh — synthetic
- https://www.kaggle.com/datasets/shakil10945/dhaka-air-quality-2000-2025-synthetic-dataset — synthetic
- https://www.kaggle.com/datasets/shakilofficial0/hourly-air-quality-index-aqi-of-bangladesh — modelled AQI, CC BY-NC
- https://data.mendeley.com/datasets/7m7555vgrn — DiaHealth
- https://data.mendeley.com/datasets/m8cgwxs9s6/3 — DiaBD (paper: https://doi.org/10.1016/j.dib.2025.111746)
- https://data.mendeley.com/datasets/5nvsv7ypg4 — Student Performance Bangladesh
- https://data.mendeley.com/datasets/57yvy3gx8f — USDI-30 depression
- https://data.mendeley.com/datasets/f4z2bfv7vk — Undergraduate mental health
- https://jhpn.biomedcentral.com/articles/10.1186/s41043-025-01095-8 — ML prediction of student depression/anxiety/stress (JHPN 2025)
- https://research.daffodilvarsity.edu.bd/scopus-article/6581 — ML mental-health risk factors (QPAIN 2025)
- https://data.mendeley.com/datasets/sz5558wrd4/3 — Bangla multilabel cyberbully
- https://data.mendeley.com/datasets/4tsb6tg9b2 — BOISHOMMO (paper https://arxiv.org/abs/2504.08408)
- https://arxiv.org/abs/2507.11084 — July Revolution sentiment
- https://zenodo.org/records/22733565 — EComReviews-BD
- https://huggingface.co/datasets/swadhinbiswas/bangladeshi-jobs — Bangladeshi tech jobs (474 postings)
- https://data.mendeley.com/datasets/zhtvkny53n/1 — Medicinal products in Bangladesh
- https://data.mendeley.com/datasets/tb5x9gw2pt/2 — AgriClimateBD
- https://www.kaggle.com/datasets/firozemaliha/bangladesh-agroclimatic-crop-yield-2000-2024 — 150-row crop yield
- https://www.kaggle.com/datasets/yakinrubaiat/bangladesh-weather-dataset — weather 1901–2023 (20 notebooks)
- https://www.ncei.noaa.gov/products/international-best-track-archive — IBTrACS
- https://www.journal.bmd.gov.bd/media/research_papers/3.pdf — BoB cyclone track analysis (prior work)
- https://www.bgs.ac.uk/groundwater/?p=3986 — BGS arsenic data
- https://data.mendeley.com/datasets/sx4m6tdwb7 — Ganges hydrology
- https://data.gov.bd/dataset/daily-water-levels-data — data.gov.bd water levels (no licence, 2018)
- https://doi.org/10.1016/j.heliyon.2024.e28708 — lightning GIS study (PMC10998115)
- https://www.kaggle.com/datasets/azminetoushikwasi/woman-harassment-dataset-200121-bangladesh — aggregates
- https://archive.ics.uci.edu/dataset/597/productivity+prediction+of+garment+employees — garment productivity
- https://www.fibre2fashion.com/news/apparel-news/over-3-600-rmg-factories-in-bangladesh-now-digitally-mapped-278976-newsdetails.htm — Mapped in Bangladesh (news)
- https://arxiv.org/pdf/2510.18355 — KrishokBondhu agricultural call-centre RAG
- https://www.kaggle.com/datasets/durjoychandrapaul/house-price-bangladesh — real estate
- https://www.kaggle.com/datasets/rezwananik/south-asia-growth-and-development-data-2000-23 — WDI South Asia panel
- https://zenodo.org/records/19684670 — PreEnvBD (no files visible)
- https://zenodo.org/records/23134442 — Net-Edu-BD (no files visible)
- https://www.kaggle.com/datasets/kawsarahmad/dengue-dataset-bangladesh — dengue survey dataset (11 notebooks)
- https://dataverse.harvard.edu/ — Harvard Dataverse search (API), mostly survey and replication data
- https://bbs.gov.bd/site/page/3e838eb6-30a2-4709-be85-40484b0c16c6/Yearbook-of-Agricultural-Statistics — BBS Agricultural Yearbook (PDF; link from search results, **unverified** page load)
