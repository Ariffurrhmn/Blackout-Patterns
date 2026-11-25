# Literature used for the replication round

Sources were found with Consensus. Only the abstracts and excerpts listed here were read, unless marked "full text".

## Data

- Hossain, Nafs & Yeaser (2025). *Multi-year dataset on daily electricity demand, generation, load shedding, and external conditions in Bangladesh.* Data in Brief. DOI 10.1016/j.dib.2025.112014. Descriptor for the 2019–2024 dataset (version 2 used here). Describes programmatic scraping of BPDB reports and the version history.
- Rahman & Islam (2026). *Extended Bangladesh Electricity Dataset: Daily Demand, Generation, Load Shedding, and Supply Constraints (2019–2026).* Mendeley Data, DOI 10.17632/yp5y4thtfm. The extended file used for 2025–26. The Mendeley record lists these authors; the README inside the file does not name them, so cite from the record.
- Mridha (2026). *Bangladesh Daily Electricity Demand, Generation and Load-Shedding Dataset (2016–2026).* Zenodo, DOI 10.5281/zenodo.21783852. Checked: coverage ends 2026-08-01, so it does not give a fresh holdout. Used as an independent cross-check of our shedding target; see `docs/crosscheck_mridha.md`.

## Bangladesh demand forecasting (protocol to replicate)

- Islam, Turja & Habib (2025). *Enhanced power demand forecasting for Bangladesh: using feature engineering associated with environmental and economic impact.* Full text read. Hourly PGCB demand, 2015–2023. Features: date parts, 24 lagged points, rolling mean, max and standard deviation over several windows, holidays, temperature, humidity, GDP and population. Split: train 2015–2022, validate on 2023. Reported best: Prophet with max-absolute scaling, MAPE 2.3% in the abstract and 2.28% on validation in Table 4. Caveats from the text: the 2024 forecast uses forecasted temperature and humidity, the target is the next hour, and the paper does not compare against a persistence baseline.
- Karmakar et al. (2026). *Daily Peak Demand Forecasting in Bangladesh: A Leakage-Aware Comparison.* Not read: no open-access copy, so the full text is blocked. Nothing is taken from it.

## Forecast combinations

- Makridakis, Spiliotis & Assimakopoulos (2018). *The M4 Competition: Results, findings, conclusion and way forward.* International Journal of Forecasting. DOI 10.1016/j.ijforecast.2018.06.001. Among the 17 most accurate methods, 12 were combinations of mostly statistical approaches.
- Makridakis, Spiliotis & Assimakopoulos (2020). *The M4 Competition: 100,000 time series and 61 forecasting methods.* International Journal of Forecasting. DOI 10.1016/j.ijforecast.2019.04.014.
- Petropoulos & Svetunkov (2019). *A simple combination of univariate models.* International Journal of Forecasting. DOI 10.1016/j.ijforecast.2019.01.006. Median combination of ETS, CES, ARIMA and dynamic optimised theta; ranked 6th for point forecasts in M4.
- Wang, Hyndman et al. (2023). *Forecast combinations: An over 50-year review.* International Journal of Forecasting. DOI 10.1016/j.ijforecast.2022.11.005. Simple averages remain a tough benchmark.

## Intermittent demand and zero-inflated targets

- Babaï, Syntetos & Teunter (2014). *Intermittent demand forecasting: An empirical study on accuracy and the risk of obsolescence.* International Journal of Production Economics. DOI 10.1016/j.ijpe.2014.08.019. TSB reacts faster to falling demand than Croston; Croston and SBA are biased.
- Wang, Kang & Petropoulos (2024). *Combining probabilistic forecasts of intermittent demand.* European Journal of Operational Research. DOI 10.1016/j.ejor.2024.01.032. Combinations beat single methods on intermittent demand.
- Kislinskii & Hameed (2026). *Are gradient boosting models suitable for intermittent demand forecasting?* Preprint, not peer reviewed. Specialised methods beat gradient boosting alone; a combined ensemble improved accuracy by up to 10%.
- Nathan et al. (2026). *Primacy of feature engineering over architectural complexity for intermittent demand forecasting.* Scientific Reports. DOI 10.1038/s41598-026-35197-y. On retail spare-parts data, two-stage hurdle models did not beat a single stage with good features. Different domain.

## Prediction intervals under distribution shift

- Gibbs & Candès (2021). *Adaptive conformal inference under distribution shift.* NeurIPS. DOI 10.48550/arXiv.2106.00170. Online update of the miscoverage level; robust to shifts that a fixed split-conformal interval would miss.
- Gibbs & Candès (2022). *Conformal inference for online prediction with arbitrary distribution shifts.* Preprint. Improves on ACI by tuning the step size over time.
