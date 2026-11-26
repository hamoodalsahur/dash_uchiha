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
python3 download_mobility.py  # optional: refresh the B40 -> M40 source files (own retrieval log)
python3 export_mobility.py    # writes the B40 -> M40 tables and prints their headline numbers
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
| `kantung/mobility.py` | B40 -> M40 layer: lines, gap, share below the line, growth, catch-up, 2030 scenarios |
| `export_mobility.py` | Writes `fact_mobility`, `fact_lines`, `fact_scenarios`, `fact_income_bands`, `fact_state_wages` |
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

## B40 -> M40 layer (added 27 Nov, decision D15)

- Line: national M40 entry line as published by DOSM: RM4,850 (2019), RM5,250 (2022), RM5,860 (2024). Near-M40 band starts at
  the B20 ceiling (RM3,820 in 2024). State lines are percentile-41 minimums, shown as context only.
- Share below the line: lognormal with each district's median and mean income (sigma^2 = 2 ln(mean/median)). Checked two ways:
  household-weighted national total is 40.5% in 2022 (should be 40%; 42% in 2024), and all five Penang districts fall inside
  the published income-band ranges (HIS Pulau Pinang 2024, Table 1.11). Penang rows also carry the observed range.
- Growth and catch-up: compound annual growth; real growth deflated by the state all-items CPI (annual mean). Catch-up = annual
  change in log(median / line); "about level" within 0.25 points a year. Districts whose boundaries changed in 2025 (new
  districts and their parents) are excluded from growth.
- 2030 scenarios: required growth to reach a fixed, inflation-indexed (1.68%/yr) or moving (3.86%/yr) line. Arithmetic on stated
  assumptions, not forecasts.
- School completion: education offices matched to districts by name; a combined office gives its value to each district it
  covers (flagged); offices that split one district are left out.
- Not claimed: following households from B40 to M40, causal effects, or forecasts for individual families.
