# Kantung Atlas pipeline

Python pipeline behind the Kantung Atlas dashboard (MDIT 2026). It builds a
district-year panel from official DOSM data and writes every table Power BI
reads. Power BI only filters these rows; no scenario logic lives in DAX.

## Run

```
pip install pandas pyarrow numpy scipy statsmodels pytest
python3 download_data.py      # optional: refresh ./data from DOSM and log SHA-256 hashes
python3 -m pytest -q          # 36 tests: maths, edge cases, real-data invariants
python3 export_powerbi.py     # writes ./powerbi_tables/*.csv and prints headline numbers
python3 review_checks.py      # full checks incl. bootstrap interval and regression (slow, ~5 min)
```

`./data` holds the 25 Nov 2026 snapshot; `data/retrieval_log.csv` has URLs and
hashes. Re-download, rerun, and quote only the numbers your own run prints.

## Files

| File | What it does |
| --- | --- |
| `kantung/core.py` | District name keys, 2025 boundary splits, panel build, variance split, coverage, KPX, Dirichlet stability |
| `kantung/outputs.py` | Outlook status, priority list, allocation grid, mapping 2022 values onto 2024 boundaries |
| `export_powerbi.py` | Produces the dashboard tables |
| `review_checks.py` | Every check behind the proposal's claims, incl. the model and backtest interval |
| `tests/` | Unit tests with hand-derived expectations, plus real-data invariants |

## Tables for Power BI

| Table | Grain | Key columns |
| --- | --- | --- |
| `dim_district.csv` | district | district_id, state, region, new_2024_district, src_note |
| `fact_district_year.csv` | district x year (2022, 2024) | raw indicators, dim_A/B/C, KPX, partial, rank_p05/p50/p95, share_top, tier, outlook, households (estimated) |
| `fact_allocation.csv` | mode x rule x reach | coverage, efficiency, nonpoor_share, poor_reached, gain_vs_baseline (vs state rule) |
| `fact_priority_list.csv` | mode x rule x reach x district | selected_share (1 = fully selected) |
| `fact_headline.csv` | metric | within-state variance shares, unweighted and household-weighted |

Relationships: `dim_district[district_id]` 1-to-many to the fact tables.

## Fixed parameters (state these in the Methods appendix)

- Indicators: A = log median income, absolute poverty; B = participation, unemployment; C = piped water, electricity, sanitation.
- Winsorise at P1/P99 of 2024, rescale to [0.01, 1], arithmetic within dimensions, geometric across, equal weights; KPX = 100 x (1 - I).
- Stability: Dirichlet(5, 5, 5), 5,000 draws, seed 2026; robust priority >= 90% of draws in the worst fifth, watch 50-90%.
- Households = district population / state average household size (`hh_lq_state`). Estimated, labelled as such.
- 2024 survey uses 2025 population (first year on the new boundaries). New districts inherit parent 2022 values (see `SPLITS_2025`).
- Factors model: Smithson-Verkuilen squeezed logit of poverty, state fixed effects, standard errors clustered by state.

## Known limits

District values are survey estimates without published standard errors; household counts are estimated; six new 2024
districts lack labour data (provisional); only three survey waves; associations are not causes.
