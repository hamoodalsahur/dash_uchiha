ATLAS - District hardship, the road to M40, and where to act
Team Dash Uchiha | MDIT 2026 Global Challenge | Preliminary round
DRAFT v0.2 (Coder 1, 27 Nov 2026: B40 -> M40 layer added) - items marked [TO FILL] are completed by the Power BI pro once the pages are final.

=====================================================================
1. WHAT IS IN THIS ZIP
=====================================================================
Dashboard.pdf        Static export of all 3 pages
Dashboard.pbix       Interactive Power BI source file
data/                The CSV tables the dashboard reads (see data_dictionary.csv)
  dim_district.csv, fact_district_year.csv, fact_allocation.csv,
  fact_priority_list.csv, fact_headline.csv, fact_map.csv,
  fact_mobility.csv, fact_map_mobility.csv, fact_lines.csv,
  fact_scenarios.csv, fact_income_bands.csv, fact_state_wages.csv
  data_dictionary.csv  Every column: meaning, unit, source, status tag
map/atlas_map.topojson District shapes used by the map
README.txt           This file

=====================================================================
2. SOFTWARE
=====================================================================
- Microsoft Power BI Desktop, version [TO FILL: Help > About], Windows.
- Visuals used: built-in visuals only, including the Shape Map visual
  (a built-in preview visual). If it does not appear, enable it:
  File > Options and settings > Options > Preview features > Shape map visual,
  then restart Power BI Desktop.
- Plugins / add-ons / custom visuals: none [TO CONFIRM].
- No internet connection, sign-in or external data source is needed.
  All data is stored inside the .pbix.
- The data tables were produced with Python 3 (pandas, numpy, scipy,
  statsmodels) from official DOSM open data. The code is not needed to open
  the dashboard.

=====================================================================
3. HOW TO NAVIGATE (step by step)
=====================================================================
Open Dashboard.pbix. Use the page tabs at the bottom (or the buttons at the
top of each page [TO CONFIRM]).

PAGE 1 - DISCOVER: Where is hardship concentrated?
  1. Read the KPI cards: share of district poverty differences that sit
     within states (unweighted and household-weighted), number of robust
     priority districts, districts above the 13MP 4.7% poverty benchmark.
  2. The map colours each district by priority tier.
     Dots = districts created in 2024 and Putrajaya.
     Grey = districts split in 2024; their shapes show 2022 values.
  3. Hover over a district to see its indicators. Click it to filter the page.
  4. The ranked table shows each district's rank and its 5th-95th percentile
     rank range under different weightings.
  5. Slicers: year (2022 / 2024), state, tier.
  6. B40 -> M40 view: switch the map to "income band" to see where each
     district's median sits against the national lines (below the near-M40
     band, near M40, at or above the M40 line of RM5,860). Cards show the
     districts and estimated households below the line. [TO CONFIRM toggle]

PAGE 2 - DIAGNOSE AND ANTICIPATE: What kind of hardship, and will it persist?
  1. The scatter compares 2022 and 2024 poverty for each district,
     coloured by outlook: persistent, emerging, easing, not flagged.
  2. Select a district to see its three dimension scores against its state
     and the national figure.
  3. The coefficient chart shows factors associated with poverty within
     states (associations, not causes).
  4. Slicers: state, outlook status.
  5. Catch-up: districts tagged closing, about level or falling behind,
     comparing their 2019-2024 income growth with the growth of the M40
     line itself. Districts whose boundaries changed in 2025 are not compared.

PAGE 3 - PRIORITISE (Allocation Planner): Which rule should a limited
programme use?
  1. Choose a household reach with the slider (5% to 60%).
  2. Choose the mode: "Backtest 2022 to 2024" (rules set on 2022 data,
     scored on 2024) or "In-sample 2024".
  3. Compare the coverage curves for District poverty, State poverty, KPX
     and Random, and read the gain over the state rule at your reach.
  4. The priority list shows which districts each rule selects
     (available at 10%, 20% and 30% reach). [TO CONFIRM export button]
  5. Optional: enter a payment per household to translate reach into an
     illustrative budget (assumption shown on screen) [TO CONFIRM].
  6. Growth to M40 by 2030: pick an example starting income, an income
     growth rate and how fast the M40 line rises (fixed, 2%, or the
     2019-2024 pace of 3.85%). The chart shows income and line paths and the
     yearly growth needed. Selecting a district shows the growth its 2024
     median would need. These are scenarios, not forecasts.

=====================================================================
4. DATA SOURCES
=====================================================================
Department of Statistics Malaysia (OpenDOSM / data.gov.my), CC BY 4.0,
retrieved 25 Nov 2026 (exact URLs, times and SHA-256 hashes in the project's
retrieval_log.csv):
  hh_poverty_district, hh_income_district, lfs_district,
  hh_access_amenities, population_district, hh_lq_state,
  hh_poverty_state, hies_state, lfs_state_sex.
B40 -> M40 layer, retrieved 27 Nov 2026 (retrieval_log_mobility.csv):
  hies_malaysia_percentile, hies_state_percentile, hies_district,
  hh_inequality_district, cpi_2d_state, formal_wages_state,
  completion_school_district (Ministry of Education, via data.gov.my).
Penang district income bands: DOSM Household Income Survey Report,
  Pulau Pinang 2024, Table 1.11 (typed from the published report).
Map: geoBoundaries gbOpen MYS ADM2 (2020), CC BY 3.0.
Dot locations: OpenStreetMap Nominatim (c) OpenStreetMap contributors, ODbL.
No fabricated or simulated data is used.

=====================================================================
5. ASSUMPTIONS
=====================================================================
- Unit: 166 districts and single-district territories on the 2024 survey
  boundaries. KL, Labuan, Putrajaya and Perlis 2024 values come from state
  tables.
- The 2024 survey uses 2025 population, the first year published on the
  new district boundaries.
- Households are estimated: district population / state average household
  size. Poor households = poverty rate x estimated households.
- Reach assumes an equal cost per household. Partly selected districts are
  assumed to be selected representatively.
- Six districts created in 2024 inherit their parent district's 2022 value
  in the backtest.
- Priority index (KPX): 7 indicators in 3 equally weighted dimensions;
  winsorised at the 2024 1st/99th percentiles; rescaled to 0.01-1;
  geometric mean across dimensions. Stability: 5,000 Dirichlet(5,5,5) weight
  draws, seed 2026.
- M40 line: DOSM's published national line, RM4,850 (2019), RM5,250 (2022),
  RM5,860 (2024). Near-M40 band starts at the B20 ceiling (RM3,820 in 2024).
- Share of households below the line: estimated from each district's median
  and mean income (lognormal). Checked against the 40% national total
  (40.5% in 2022) and the published Penang income bands.
- Real growth uses the state consumer price index (annual average).
- 2030 growth needed: arithmetic on stated assumptions (fixed line,
  inflation-indexed line at 1.68% a year, or line rising 3.86% a year).

=====================================================================
6. LIMITATIONS
=====================================================================
- District figures are survey estimates; their standard errors are not in
  the open tables, so we show tiers and rank ranges, not exact ranks.
- District averages describe places, not individual households.
- Only three survey waves (2019, 2022, 2024); the outlook carries the latest
  value forward rather than using a learned forecast.
- Six new 2024 districts have no labour-force data; their index uses two of
  three dimensions and is marked provisional.
- Factor results are associations between places, not causal effects.
- The backtest gain interval reflects variation across districts, not survey
  sampling error.
- B40/M40 are relative groups: 40% of households are always B40 nationally.
  We measure districts' distance to the line, not families moving between
  groups; Malaysia has no public household panel data.
- Shares below the line are estimates (about 2 points high nationally in
  2024). Observed ranges exist only for Penang.
- Formal wage data covers formal employees only and is shown as context
  after the 2024 survey, not as household income.
