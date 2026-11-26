# B40 → M40 layer: Power BI guide (for Apipi)

Everything is precomputed in Python. Power BI only loads, relates, filters and formats. Rebuild the tables with
`python export_mobility.py` (after `export_powerbi.py` and `build_map.py`). Column meanings: `data/data_dictionary.csv`.

## 1. Load and relate

Get Data → Text/CSV, from `powerbi_tables/`:

| Table | Relationship | Notes |
|---|---|---|
| `fact_mobility` | `dim_district[district_id]` 1 → * `fact_mobility[district_id]` | One row per district and year (2019, 2022, 2024). Growth and 2030 columns are filled on **2024 rows only** |
| `fact_map_mobility` | `fact_map[shape_key]` 1 → 1 `fact_map_mobility[shape_key]` | Same 166 shapes as the map. Split parents show 2022, like the poverty map |
| `fact_lines` | none (stand-alone) | B40/M40/T20 lines by year, national and state |
| `fact_scenarios` | none (stand-alone) | Planner paths 2024–2030 |
| `fact_income_bands` | none (stand-alone) | Penang 2024 published income bands |
| `fact_state_wages` | none (stand-alone) | Formal wages by state, monthly to Jun 2026 |

**Formatting:** columns named `share_*`, `attainment`, `expenditure_share`, `income_growth_*`, `line_growth_*` and
`required_growth_2030_*` are **fractions** (0.42 = 42%). Set them to Percentage format. In `fact_scenarios`, the `*_pct`
columns are already percentages.

**Colours** (handbook palette): below near-M40 band `#B94539` · near M40 (B21-B40) `#D8AD6C` · at or above M40 line
`#377B78` · falling behind `#B94539` · about level `#D8AD6C` · closing `#377B78` · not compared `#8C8C8C`.

## 2. Measures (paste into a "Measures" table)

```DAX
Districts below M40 line =
CALCULATE(COUNTROWS(fact_mobility), fact_mobility[year] = 2024, fact_mobility[gap_rm] > 0)

Districts falling behind =
CALCULATE(COUNTROWS(fact_mobility), fact_mobility[catch_up_status_1924] = "falling behind")

Districts compared =
CALCULATE(COUNTROWS(fact_mobility), NOT ISBLANK(fact_mobility[catch_up_status_1924]))

Households below M40 line (est.) =
SUMX(FILTER(fact_mobility, fact_mobility[year] = 2024), fact_mobility[households] * fact_mobility[share_below_m40])

Near-M40 households (est.) =
SUMX(FILTER(fact_mobility, fact_mobility[year] = 2024), fact_mobility[households] * fact_mobility[share_near_m40])

Selected growth needed (moving line) =
CALCULATE(SELECTEDVALUE(fact_mobility[required_growth_2030_moving]), fact_mobility[year] = 2024)

Scenario growth needed % =
SELECTEDVALUE(fact_scenarios[required_growth_pct])
```

**Check these numbers with no slicers applied** (tell Hamood if any differ):

| Measure | Expected |
|---|---|
| Districts below M40 line | 123 |
| Districts falling behind | 94 |
| Districts compared | 153 |
| Households below M40 line (est.) | about 3.84 million (42% of 9.15 million) |
| Near-M40 households (est.) | about 1.87 million |

Count KPIs from `fact_mobility`, **never from the map table**: split parents on the map show 2022 values.

## 3. What to add on each page

**Page 1 – Atlas: "How far is each district from the middle?"**
- Second Shape Map (or a toggle with bookmarks): Location `fact_map[shape_key]`, Legend
  `fact_map_mobility[income_band_shown]`. Expected split: 33 below near-M40 band, 90 near M40, 43 at or above.
- Cards: *Districts below M40 line*, *Households below M40 line (est.)*.
- Tooltip: `income_median`, `gap_rm`, `share_below_m40`, `state_m40_line`.
- Legend note: *"National M40 line RM5,860 (2024). Shares are estimates from median and mean income."*

**Page 2 – Risk Outlook: "Is it catching up?"**
- Table or bar: count of districts by `catch_up_status_1924`. Expected 94 falling behind / 9 about level / 50 closing.
- Scatter: X = `income_growth_real_1924`, Y = `catch_up_1924`, Details = `district_id`, filter year = 2024.
- Card: *Districts falling behind* with the sub-label "of 153 compared".
- Note: *"Line rose 3.86% a year in 2019–24; the typical district median rose 3.1% (1.5% after inflation)."*

**Page 3 – Allocation Planner: "What growth would close the gap by 2030?"**
- Slicers (single select) on `fact_scenarios`: `start_income_rm`, `income_growth_pct`, `line_growth_pct`.
- Line chart: X = `year`, values = `income_rm` and `line_rm`. Card: *Scenario growth needed %*.
  Check: RM4,000 start, line growth 0 → 6.57%; line growth 3.85 → 10.67%.
- District card: select a district → *Selected growth needed (moving line)* (filter year 2024).
- Keep the poverty-first allocation chart. The near-M40 view is **beside** it, not a replacement.
- Footer: *"Scenarios on stated assumptions, not forecasts for any household."*

**Optional (only if time):**
- Penang income bands as a column chart (`fact_income_bands`, filter one district), with a text box marking RM5,860.
- Formal wages line chart (`fact_state_wages`, slicer on state), titled "Formal-sector employees only, since the
  2024 survey".

## 4. Don'ts
- Don't SUM or AVERAGE `income_median` across districts. Show it per district only.
- Don't write "X households will become M40". Write "estimated households below the M40 line".
- Don't mix 2025–26 wages into the 2024 survey visuals. Keep them on their own, clearly labelled.
