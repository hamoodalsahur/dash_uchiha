# Atlas — Team Handbook (Dash Uchiha, MDIT 2026)

> **Read this first. Paste it into your own Claude chat as context before asking it for help.**
> Version: 25 Nov 2026, 22:20 MYT. Decisions below were confirmed by the team in a grilling session and are **locked** unless the whole team agrees to change them.

---

## 0. Instructions for your Claude (copy this block into your chat)

```
You are helping one member of team "Dash Uchiha" build "Atlas" for the MDIT 2026 datathon.
The attached handbook is the source of truth. Rules:
1. Do not change locked decisions (Section 3) or method parameters (Section 6). If you think one is wrong, say so and stop; do not silently change it.
2. Never invent numbers, datasets, URLs or citations. Every number must come from the team pipeline output (powerbi_tables/*.csv or review_checks.py) or a cited source. If you don't have it, write TO COMPUTE.
3. Never claim causation. Use "associated with", "priority signal", "estimated".
4. Fabricated or simulated data is banned by the competition. Call Page 3 the "Allocation Planner" (re-allocation over official data), never a "simulator".
5. Keep my work my own: explain what you suggest so I can rewrite it and defend it in Q&A. I must be able to explain every step without you.
6. Respect the booklet rules in Section 11 (file names, report format, 25-page cap).
```

---

## 1. The project in one minute

**Working title:** Atlas (formerly "Kantung Atlas: Where State Averages Hide Hardship").
**Team:** Dash Uchiha.
**Competition theme:** "Challenge The Data, Shape The Future" — build a data-driven solution that anticipates what comes next.

**Pitch sentence:** Poverty in Malaysia is local and sticky: about half of the differences in district poverty rates sit inside states, the same districts stay at the top from one survey to the next, and a district ranking set on 2022 data would have reached more of 2024's poor households than a state ranking.

**Three parts of the tool:**
1. **Atlas** — where hardship concentrates (district map + Kantung Priority Index, KPX, with weight stability).
2. **Risk Outlook** — which districts are persistent, emerging or easing; tested against the 2024 survey.
3. **Allocation Planner** — which ranking rule reaches the most poor households for a fixed household reach, validated out of sample.

**Who it is for:** place-based programmes (water, electrification, clinics, transport, childcare) and outreach to households not yet registered. It **complements** household targeting (STR, SARA through PADU and eKasih); it does not replace it.

---

## 2. Key numbers (from the pipeline run on 25 Nov 2026)

> Rerun the pipeline yourselves and quote **your** printed numbers. If anything moves, update every place it appears (report, dashboard, video, Q&A).

| Finding | Number | Source |
|---|---|---|
| Units in 2024 | 166 (districts + single-district territories) | `fact_district_year.csv` |
| Within-state share of variance, absolute poverty, 2024 | **47%** unweighted (districts as places); **32%** household-weighted | `fact_headline.csv` |
| Same, log median income, 2024 | 34% unweighted; 16% household-weighted | `fact_headline.csv` |
| 2022 equivalents (poverty) | 47% / 34.5% | `fact_headline.csv` |
| Backtest (rank on 2022, score on 2024), 20% household reach | District ranking **56.4%** of poor households vs state ranking **51.1%** | `fact_allocation.csv` |
| Gain | **+5.3 points**, 95% bootstrap interval **2.2 to 7.7** (districts resampled within states; survey error NOT included) | `review_checks.py` |
| Households | ≈ **25,700** more estimated poor households (274,220 vs 248,529); 1 point ≈ 4,900 households | `fact_allocation.csv` |
| KPX rule, backtest, 20% reach | 55.1% (trades a little poverty coverage for labour/service deprivation) | `fact_allocation.csv` |
| Stickiness | **85%** of 2024's worst fifth (29 of 34) were already worst fifth in 2022 | `fact_district_year.csv` (outlook) |
| Outlook counts 2024 | 29 persistent, 5 emerging, 5 easing, 127 not flagged | `fact_district_year.csv` |
| Forecast holdout (predict 2024) | Persistence MAE **2.4** pts beats trend 3.9, damped trend 3.0, state average 4.3 | `review_checks.py` |
| Regression to the mean | corr(change 2022→24, level 2022) = −0.47 | `review_checks.py` |
| Household-weighted poverty 2019 / 2022 / 2024 | 5.7% / 6.3% / 5.3% (pandemic bump explains why trends fail) | `review_checks.py` |
| KPX weight stability | **25** robust priority, **7** watch, 6 provisional (new districts) | `fact_district_year.csv` |
| Method sensitivity | rank correlation ≥ 0.99; top-fifth overlap 0.91–0.94 | `review_checks.py` |
| Hook | **Pitas 50.0%** vs Sabah 17.7%; Tongod 41.5%, Kota Marudu 40.0%; Daro 26.8% vs Sarawak 8.4% | `fact_district_year.csv` |
| Labour-driven priority example | Selama (Perak): 10.4% poverty but rank 5 on KPX | `fact_district_year.csv` |
| 13MP benchmark | 113 of 162 districts (district table) above 4.7% national 2030 benchmark; mostly Sarawak (36), Sabah (28) | district table |
| Factors associated with poverty (state fixed effects, n=160) | participation −0.24 [−0.43, −0.05]; unemployment +0.28 [0.07, 0.49]; water, electricity, dependency ≈ 0 (not significant) | `review_checks.py` |

**Honest framing:** the hidden pockets are mostly **inside states already known to be poor** (Sabah, Sarawak), not poor districts inside rich states (only Besut and Pekan fit that pattern).

---

## 3. Locked decisions (decision log)

| # | Decision | Choice | Decided |
|---|---|---|---|
| D1 | Project | District-level Atlas (not the original 16-state MyGrowth Atlas) | Team, 25 Nov |
| D2 | Roles | Coder 1 = Data lead; Coder 2 = Modeling lead; Power BI pro = Dashboard lead; Document maker = Report & compliance lead | Team, 25 Nov |
| D3 | Dashboard software | Power BI Desktop (Windows) | Team, 25 Nov |
| D4 | AI use | Use the AI-assisted material and **declare it fully** (pipeline scaffolding, proposal drafts, two external AI reviews, Superpowers + Matt Pocock skill packs) | Team, 25 Nov |
| D5 | Time | No hour cap; Tier 2 stays in scope | Team, 25 Nov |
| D6 | Headline order | Open on Pitas (5 s) → "47% of district differences sit inside states" → "32% when weighted by households" | Team, 25 Nov |
| D7 | Names | Team "Dash Uchiha"; working title "Atlas" | Team, 25 Nov |
| D8 | Map | Real polygons (geoBoundaries ADM2, 2020). Parent polygons of the 6 new districts shaded with the **2022 parent value**; the 6 new districts shown as **dots** with their 2024 values; Putrajaya as a dot. Legend states this | Team, 25 Nov |
| D9 | Method parameters | Locked as in Section 6 | Team, 25 Nov |
| D10 | Audience | Judges assumed familiar with DOSM statistics | Team, 25 Nov |
| D11 | Allocation Planner rules | District poverty, State poverty, KPX, Random (drop "Persistent first" from the chart; outlook status shown as colour in the priority list) | Team, 25 Nov |
| D12 | Video closing ask | "Target outreach and place-based programmes at persistent districts" + "DOSM: publish district standard errors and household counts". Finals ask decided after 5 Dec | Team, 25 Nov |
| D13 | Literature review | Geographic targeting (Elbers et al. 2007; Baker & Grosh 1994) > Malaysian sources > composite-indicator method | Team, 25 Nov |
| D14 | Collaboration | Private GitHub repo for code + .pbix (commit history = evidence of human work); Google Drive for report and video | Team, 25 Nov |

**Add every new decision to this table** (date, who, why). This log goes into the AI declaration evidence.

---

## 4. Timeline (all MYT)

| Date | Milestone |
|---|---|
| **Sun 29 Nov 2026, 11:59 pm** | Preliminary submission deadline (official booklet). One submission only, no resubmission, late not accepted |
| Sun 29 Nov, 6:00 pm | **Our internal upload target** |
| Sat 5 Dec | Top 7 finalists announced |
| Sat 12 Dec | Finals: live pitch + Q&A, UiTM Shah Alam |

**Gate: Thursday 26 Nov, 22:00** — all tables frozen, all numbers frozen, Page 1 working, report sections 1–3 drafted. After this, change code only to fix bugs.

| When | Coder 1 (Data) | Coder 2 (Modeling) | Power BI pro (Dashboard) | Document maker (Report) |
|---|---|---|---|---|
| Wed night | Rerun pipeline from fresh downloads; 166/166 match; commit retrieval log + hashes; boundary join (Section 8) | Read `core.py` + tests line by line; rerun `review_checks.py`; confirm numbers in Section 2 | Install/update Power BI; import `powerbi_tables/*.csv`; build model + Page 1 skeleton | Report skeleton in booklet order (Section 10); start literature review; open AI declaration form |
| Thu | Data dictionary; README.txt draft; map file for Power BI | Precompute any extra tables the dashboard needs; stability + outlook tables final | Page 1 complete; start Page 2 | Intro, literature review, reframed problem statement |
| **Thu 22:00 gate** | Tables frozen | Numbers frozen | Page 1 works | Sections 1–3 drafted |
| Fri | Number-to-source check (every figure in report/dashboard → CSV row) | Factors model + sensitivity table; defence appendix draft | Pages 2 and 3; PDF export test | Methodology + findings |
| Sat | ZIP assembly; README.txt final | Q&A rehearsal; defence appendix final | Polish; test on a 2nd Windows machine | Dashboard output, decision criteria, conclusion; AI form; video script |
| Sun | Final lineage check | — | Record screen demo | Record voice-overs (all four); edit; upload to Drive; submit on mditdatathon.com by 18:00 |

Standups 09:00 and 21:00. One submission owner (Document maker).

---

## 5. Data (all official, open, CC BY 4.0)

**Five core district tables + state context.** Parquet path pattern: `https://storage.dosm.gov.my/<folder>/<id>.parquet` (`download_data.py` does this and logs SHA-256 hashes).

| Role | Dataset ID | Folder | Unit | Years used | Variables |
|---|---|---|---|---|---|
| Core | `hh_poverty_district` | hies | district | 2019, 2022, 2024 | absolute poverty (index + outcome); relative poverty (context only) |
| Core | `hh_income_district` | hies | district | 2019, 2022, 2024 | median household income (logged) |
| Core | `lfs_district` | labour | district | 2022, 2024 | participation rate, unemployment rate (employment-population ratio = context only) |
| Core | `hh_access_amenities` | hies | district | 2022, 2024 | piped water, electricity, sanitation (drop "All Districts" rows) |
| Core | `population_district` | population | district | 2020–2025 | population in **thousands**; use sex=both, age=overall, ethnicity=overall for totals |
| Denominator | `hh_lq_state` | demography | state | 2019–2024 | number of households → state average household size |
| Fill / state rule | `hh_poverty_state`, `hies_state` | hies | state | 2022, 2024 | KL, Labuan, Putrajaya, Perlis 2024 come from these (single-district units) |
| Fill | `lfs_state_sex` | labour | state | 2024 | labour rates for single-district units (sex=both) |

**Traps already handled in code (know them for Q&A):**
- **Spelling variants** across tables: S.P. Tengah/Seberang Perai Tengah, Larut & Matang/Larut dan Matang, Hulu (Terengganu)/Hulu Terengganu, Hulu Langat/Ulu Langat, Cameron Highland(s), Manjung (Dinding), Tanjong/Tanjung Manis, Lubok antu. Handled by `district_key()`.
- **Boundary changes (real, not spelling):** the 2024 survey uses new districts; population only has them from 2025. Splits verified from population drops:
  - Simunjan → Simunjan + **Gedong** + **Sebuyau**
  - Sri Aman → Sri Aman + **Pantu** + **Lingga**
  - Serian → Serian + **Siburan**
  - Beaufort + Papar → **Membakut** (weights 20.8 : 33.7 thousand people)
- 2024 survey uses **2025 population** (first year on new boundaries).
- **Households are estimated:** district population ÷ state average household size. Label as "estimated" everywhere.
- The 6 new districts have **no labour data** → index uses 2 of 3 dimensions → tier "provisional".

---

## 6. Method (LOCKED parameters)

**Three separate objects** (never mix): priority index (where) · factors model (what goes with poverty) · outlook + allocation backtest (what happens next). The index is never an input or outcome of the model.

### 6.1 Variance split (headline)
Between-state share = between-state sum of squares ÷ total sum of squares. Computed unweighted (each district equal) and weighted by households. Within share = 1 − between.

### 6.2 Kantung Priority Index (KPX)
| Dimension | Indicators (direction) |
|---|---|
| A. Economic security | log median household income (+), absolute poverty (−) |
| B. Labour opportunity | participation rate (+), unemployment rate (−) |
| C. Living conditions | piped water (+), electricity (+), sanitation (+) |

- Winsorise at **P1/P99 of 2024** (frozen; also applied to 2022).
- Rescale to **[0.01, 1]**, higher = better (floor avoids zero collapse in the geometric mean).
- Arithmetic mean within dimension; **weighted geometric mean** across dimensions, **equal weights**.
- **KPX = 100 × (1 − I)**, higher = more deprived. It is a relative score, not a poverty rate.
- Units with 2 of 3 dimensions: weights renormalised, tier = **provisional**.

```
I_d = A_d^(1/3) × B_d^(1/3) × C_d^(1/3);   KPX_d = 100 × (1 − I_d)
```

### 6.3 Stability and sensitivity (report separately, never pooled)
- **Weight stability:** Dirichlet(**5, 5, 5**), **5,000** draws, seed **2026**. Report 5th–95th percentile rank. **Robust priority** = in the worst fifth in ≥ 90% of draws; **watch** = 50–90%. This is stability under weights, **not** a probability of true deprivation.
- **Method sensitivity:** P5/P95, no winsorising, arithmetic aggregation, complete cases.
- **Sampling error:** DOSM district standard errors are not in open tables → show tiers and intervals, not exact ranks.

### 6.4 Factors associated with poverty
Outcome: logit of absolute poverty after the Smithson–Verkuilen squeeze `y* = (y(n−1)+0.5)/n`. Predictors (standardised): participation, unemployment, piped water, electricity, dependency ratio. **State fixed effects**, SEs clustered by state (only 16 clusters — say so). Check: fractional logit, same signs. Associations between places, not causes or household facts.

### 6.5 Risk Outlook
Fixed before looking at 2024: persistence vs linear trend vs half-damped trend vs 2022 state average. **Persistence wins.** Status: **persistent** (worst fifth 2022 and 2024), **emerging** (entered in 2024), **easing** (left), **not flagged**, **no history**. No ML/ARIMA with three survey waves.

### 6.6 Allocation Planner
For reach 5%–60% (2.5-pt steps), rules **District poverty, State poverty, KPX, Random**, modes **In-sample 2024** and **Backtest 2022→2024**:
- Household reach = selected households ÷ all households (equal cost per household assumed)
- Poverty coverage = poor households in selected units ÷ all poor households
- Efficiency = coverage ÷ reach; Non-poor share = 1 − poor ÷ selected households (leakage proxy, not improper payments)
- Gain = rule coverage − state-rule coverage at same reach
- Ties are one block; the marginal block is selected proportionally.
- New 2024 districts inherit their parent's 2022 value in the backtest.
- Money: only via an **assumed** equal payment per household, stated on screen. Never claim savings.

---

## 7. Code: how to run (Coders 1 and 2)

Package: `kantung_pipeline.zip` (already tested from a clean unzip: 36 tests pass).

```
pip install pandas pyarrow numpy scipy statsmodels pytest
python3 download_data.py      # refresh ./data, writes data/retrieval_log.csv (URLs, time, SHA-256)
python3 -m pytest -q          # must print 36 passed
python3 export_powerbi.py     # writes powerbi_tables/*.csv + prints headline numbers
python3 review_checks.py      # all checks incl. bootstrap interval + regression (~5 min)
```

| File | Purpose |
|---|---|
| `kantung/core.py` | `district_key`, `SPLITS_2025`, `build_panel`, `variance_split`, `coverage`, `fit_bounds`, `kpx`, `dirichlet_ranks` |
| `kantung/outputs.py` | `outlook_status`, `priority_list`, `allocation_grid`, `map_to_2024` |
| `export_powerbi.py` | builds dashboard tables |
| `review_checks.py` | every check behind the proposal's claims |
| `tests/` | hand-derived unit tests + real-data invariants (166 units, no double-counted population, rates 0–100, split parents exist) |

**Code rules:** test first for any new function (Superpowers `test-driven-development`); run the full suite before every commit; any number you quote must be printed by the pipeline; commit small with clear messages.

**To-dos for the coders**
- [ ] Remove "Persistent first" from `modes` in `export_powerbi.py` (D11), rerun export, rerun tests.
- [ ] Add a `fact_map` table / alias fixes for the boundary join (Section 8).
- [ ] Add bootstrap interval for the variance split (Methodology says so; not yet coded).
- [ ] Write `data_dictionary.csv` (column, meaning, unit, source table, status tag).
- [ ] Defence appendix (1 page): missing values, boundary splits, household estimate, parameters, interval method.

---

## 8. Map (Coder 1 + Power BI pro)

- Boundary file: **geoBoundaries gbOpen MYS ADM2**, boundaryYear 2020, 160 units, licence CC BY 3.0, sources geoBoundaries + citypopulation.de. Simplified GeoJSON:
  `https://www.geoboundaries.org/data/snapshots/1c423398df24ddf6e730b116567d2181c9782778d0459c3f3b76ca2f9f12b6bc/gbOpen/MYS/ADM2/geoBoundaries-MYS-ADM2_simplified.geojson`
- Tested join (`district_key` on `shapeName`): 12 of 166 units unmatched. Fixes:

| Dashboard unit | Polygon name | Action |
|---|---|---|
| Johor – Kulai | Kulaijaya | alias |
| Johor – Tangkak | Ledang | alias |
| Sabah – Nabawan | Nabawan / Persiangan | alias |
| W.P. Kuala Lumpur | Kuala Lumpur | alias |
| W.P. Labuan | Labuan | alias |
| W.P. Putrajaya | (no polygon) | **dot** at Putrajaya centroid |
| Membakut, Gedong, Sebuyau, Pantu, Lingga, Siburan | (not in 2020 file) | **dots**; parent polygons (Beaufort, Papar, Simunjan, Sri Aman, Serian) shaded by **2022 parent value** (D8) |

- Legend text: "Hatched/outlined polygons show 2022 values for districts split in 2024; dots show the new districts' 2024 values."
- Power BI: Shape Map (TopoJSON) or Azure/ArcGIS map — use whatever works offline and in PDF export. Convert GeoJSON to TopoJSON (mapshaper) if needed. Test PDF export early.
- Always show a **ranked table** beside the map (large rural districts dominate visually).
- Cite the boundary file in the report as a map base only.

---

## 9. Dashboard spec (Power BI pro)

**Data model:** `dim_district` (1) → `fact_district_year`, `fact_priority_list` (many) on `district_id` (`"State|districtkey"`). `fact_allocation` and `fact_headline` stand alone. **No scenario logic in DAX** — slicers filter precomputed rows.

**Design rules:** one decision per page; titles state the finding; status tag on every number (observed / estimated / provisional / backtest); missing ≠ low deprivation (hatch); palette navy #132C3B, teal #377B78, amber #D8AD6C, brick #B94539, off-white #F4F7F8; ≤ 6 visuals per page.

| | Page 1: Discover | Page 2: Diagnose & anticipate | Page 3: Prioritise (Allocation Planner) |
|---|---|---|---|
| Decision | Where is hardship concentrated? | What kind, and will it persist? | Which rule should a limited programme use? |
| Title | "Half of district poverty differences sit inside states" | "Hardship pockets are sticky: 85% of 2024's worst fifth were already there in 2022" | "Ranked on 2022 data, district targeting reached 5 points more of 2024's poor" |
| KPI cards | 47% / 32%; robust priority 25; units above 4.7% benchmark; data completeness | persistent / emerging / easing counts; outlook MAE 2.4; strongest associated factor | coverage, gain + interval at chosen reach; non-poor share; est. poor households reached |
| Main visual | Map shaded by KPX tier (D8 rules) | Scatter: 2022 vs 2024 poverty coloured by outlook status | Coverage curves: District, State, KPX, Random |
| Supporting | Ranked table with rank-interval whiskers; within-state dot strips | Dimension profile vs state & national; factor coefficients with CIs | Priority list (colour = outlook status), CSV export; rule trade-off table |
| Controls | Year (2022, 2024), state, tier | state, outlook status | reach slider, rule, mode (In-sample / Backtest), optional payment assumption |

**Before submission:** export all 3 pages to PDF (A4 landscape), map legible, no local file paths, open the .pbix on a second Windows machine.

---

## 10. Report (Document maker)

**Format (booklet):** PDF, Times New Roman 12, 1.5 spacing, justified, **≤ 25 pages** excluding front page, table of contents, references. File: `Dash Uchiha_Datathon2026_Report.pdf` (confirm whether spaces are allowed; otherwise `DashUchiha_Datathon2026_Report.pdf`).

| Section (booklet order) | Pages | Content |
|---|---|---|
| 1 Introduction | 2 | Problem, theme fit, three parts of the tool |
| 2 Literature review | 3 | Geographic targeting (Elbers et al. 2007; Baker & Grosh 1994); Malaysian poverty statistics & 13MP; composite indicators (OECD/JRC) |
| 3 Reframed problem statement | 2 | From "which state" to "which districts, what kind of hardship, and which rule" |
| 4 Methodology | 5 | Data, harmonisation, variance split, KPX, stability, factors model, outlook, allocation backtest |
| 5 Findings | 7 | RO1–RO4 with one number, one chart, one caveat each; report failures (water/electricity, trend forecasts) |
| 6 Dashboard output | 3 | Screenshots of 3 pages with how to read them |
| 7 Decision-making criteria | 2 | How a planner chooses a rule/reach; tiers; outlook status → policy area |
| 8 Conclusion | 1 | Includes limitations and data asks |
| References | — | Not counted |

**Research objectives**
| RO | Objective | Result |
|---|---|---|
| RO1 | Locate disparities hidden by state averages | Supported: 47% / 32% within-state |
| RO2 | Profile hardship and associated factors | Partly: labour associated; water/electricity not |
| RO3 | Anticipate next-survey hardship | Supported: persistence MAE 2.4, recall 0.85 |
| RO4 | Compare allocation rules out of sample | Supported: +5.3 pts (2.2–7.7) at 20% reach |

**Verified references (use full APA in report)**
- Elbers, C., Fujii, T., Lanjouw, P., Özler, B., & Yin, W. (2007). Poverty alleviation through geographic targeting: How much does disaggregation help? *Journal of Development Economics, 83*(1), 198–213. https://doi.org/10.1016/j.jdeveco.2006.02.001 — finds large gains from targeting smaller units; still short of household-level information (supports "complements PADU").
- Baker, J. L., & Grosh, M. E. (1994). Poverty reduction through geographic targeting: How well does it work? *World Development, 22*(7), 983–995. https://doi.org/10.1016/0305-750X(94)90143-0
- OECD/JRC (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide.* OECD Publishing.
- Smithson, M., & Verkuilen, J. (2006). A better lemon squeezer? Maximum-likelihood regression with beta-distributed dependent variables. *Psychological Methods, 11*(1), 54–71. (verify page numbers)
- DOSM datasets (Section 5) with URL + retrieval date; geoBoundaries (CC BY 3.0); 13th Malaysia Plan; STR/SARA/PADU sources (Section 14).

**Limitations (write them plainly):** district averages ≠ household facts; survey sampling error not in open tables (regression to the mean r = −0.47); households estimated; 2024 boundary changes; 6 provisional units; only three waves; 16 clusters; bootstrap excludes survey design; equal cost per household; weights are a value judgement.

**Never claim:** causation; exact ranks; the gain will hold in future; estimated households are counts of people; the tool replaces household targeting.

---

## 11. Submission checklist (booklet + FAQ)

- [ ] Report PDF as Section 10, ≤ 25 pages, booklet section order
- [ ] Dashboard ZIP `…_Datathon2026_dashboard.zip`: `Dashboard.pdf`, `Dashboard.pbix`, data CSVs, `README.txt`
- [ ] README.txt: software name + version, step-by-step navigation, plugins/add-ons, limitations + assumptions
- [ ] Dashboard works with no external dependencies the judges can't access; stays accessible until judging ends
- [ ] Video ≤ 5 min, ≤ 2 GB, live demo of the working dashboard; **all four members speak** (FAQ requires it, booklet doesn't — we play safe)
- [ ] Upload to team Google Drive folder **and** submit on mditdatathon.com before 11:59 pm Sun 29 Nov (target 18:00)
- [ ] AI declaration signed, listing: AI-generated pipeline scaffolding, proposal drafts, two external AI reviews, skill packs; decision log + Git history as evidence
- [ ] Every dataset cited (ID, URL, retrieval date); boundary file cited; libraries cited (pandas, numpy, scipy, statsmodels, pyarrow)
- [ ] Status tags visible; no simulated data; "Allocation Planner" wording
- [ ] Finals prep (if selected): ≤ 2 presenters, 7-min pitch (bells at 5 and 7 min), 15-min Q&A, own HDMI device, formal/university attire

---

## 12. Video script (5:00 max; all four speak)

| Time | Speaker | Screen | Words (bracketed = re-read from your run) |
|---|---|---|---|
| 0:00–0:20 | Document maker | Page 1 map, Sabah, Pitas highlighted | "In Pitas, [half] of households live below the poverty line. Sabah's average is [17.7%]. State averages hide places like this." |
| 0:20–1:10 | Document maker | KPI cards | "[47%] of the differences between districts sit inside states; even weighted by households it's [32%]." Who uses it; complements STR/SARA/PADU |
| 1:10–2:15 | Coder 1 | Data lineage, status tags, 6 new districts | Five DOSM district tables, three waves, boundary changes, estimated households, provisional units |
| 2:15–3:20 | Coder 2 | Page 2 scatter, outlook, rank intervals | "[85%] of the worst-off fifth in 2024 were already there in 2022." Index in plain words; weight stability; associations not causes |
| 3:20–4:35 | Power BI pro | Page 3: reach 20%, backtest mode, compare rules, export list | "Ranked on 2022 data, district targeting reached [56%] of 2024's poor households against [51%] for states — about [25,700] more households for the same reach." |
| 4:35–5:00 | All, one line each | Page 1 | Ask: target outreach and place-based programmes at persistent districts; DOSM, publish district standard errors and household counts |

Record screen first, then each voice in one clean take.

---

## 13. Q&A bank (owners: C1 = Coder 1, C2 = Coder 2, PB = Power BI pro, DM = Document maker)

| # | Question | Short answer | Owner |
|---|---|---|---|
| 1 | Why districts, not states? | 47% of variance in district poverty is within states (32% household-weighted); 16 states can't support the analysis | C2 |
| 2 | Isn't the gain just sorting the data you score on? | That's why we backtest: rules fixed on 2022, scored on 2024 → +5.3 pts (2.2–7.7) | C2 |
| 3 | STR/SARA already use PADU/eKasih. Why this? | Complements them: guides place-based spending and outreach to unregistered households. Elbers et al. (2007): geographic targeting helps but is short of household data — so use both | DM |
| 4 | Different from Kawasanku / MySubNasional? | They describe areas; we rank with stated stability, backtest on a later survey, compare allocation rules, flag persistent risk | DM |
| 5 | Why households, and where are household counts? | Poverty is per household; district counts aren't open, so estimated from population ÷ state household size; population-based result shown as check | C1 |
| 6 | What do you predict, and did it beat a baseline? | Next-survey district poverty; persistence beat trend and state averages (MAE 2.4; 85% of worst fifth already flagged) | C2 |
| 7 | New 2024 districts? | Parents verified from population data; inherit parent values for backtest; index provisional; map shows dots | C1 |
| 8 | Why these weights / geometric mean? | Equal default; 5,000 Dirichlet(5,5,5) draws show stability; geometric so one severe gap isn't averaged away; 0.01 floor avoids zeros | C2 |
| 9 | Why P1/P99? | P95 would clip Pitas from 50% to 26.8%; alternatives shown, rank correlation ≥ 0.99 | C2 |
| 10 | What does the regression show? | Within states, lower participation and higher unemployment go with higher poverty; water/electricity no association; not causal | C2 |
| 11 | Why no sliders to improve water access? | Data doesn't support an effect within states; cross-sectional associations aren't causal | PB |
| 12 | How did you turn reach into money? | Only via a stated equal payment per household; no savings claimed | PB |
| 13 | Sampling error? | Not in open tables; extremes regress to the mean (r = −0.47); we show tiers and intervals | C1 |
| 14 | Link to 13MP? | 4.7% benchmark as reference line; 113 of 162 districts above it | DM |
| 15 | What failed? | Water/electricity associations; trend forecasts. Reported | All |
| 16 | How was AI used? | Ideation, code scaffolding, external review, as declared; every number rerun, every choice logged by us | DM |
| 17 | Why is the map mixing years? | Public boundaries predate the 2024 split; parents show 2022, new districts shown as dots with 2024 values; legend says so | PB |

---

## 14. Sources

- MDIT 2026 booklet: https://mditdatathon.com/assets/MDIT%202026%20booklet-Dhs7B9cO.pdf
- Rules & Regulations: https://mditdatathon.com/assets/RULES%20AND%20REGULATIONS%20MDIT%202026-DC-SB687.pdf
- FAQ: https://mditdatathon.com/assets/FREQUENTLY%20ASKED%20QUESTIONS-n8o-py0q.pdf
- OpenDOSM catalogue: https://open.dosm.gov.my/data-catalogue (dataset pages: `/data-catalogue/<id>`)
- Kawasanku: https://open.dosm.gov.my/dashboard/kawasanku · MySubNasional media statement: https://www.dosm.gov.my/portal-main/downloads-log?id=10447
- STR/SARA 2026: https://bernama.com/en/news.php?id=2477253 · https://sara.gov.my/en/home.html · PADU for targeting: https://mof.gov.my/portal/en/news/press-citations/padu-data-to-be-used-for-ron95-targeted-subsidy-mechanism-amir-hamzah
- 13MP targets: https://www.nst.com.my/amp/business/economy/2025/07/1253327/13mp-malaysia-eyes-55pct-gdp-60pct-private-investment-growths
- geoBoundaries API (MYS ADM2): https://www.geoboundaries.org/api/current/gbOpen/MYS/ADM2/
- Full proposal (shared doc): https://claude.ai/artifact/GJHpz9B4GyhubGm3i2dYcJ
- Meta-prompt + follow-up prompts: https://claude.ai/artifact/16KDePMnEATS9JbU6NdCLm

---

## 15. Useful prompts for your Claude

- **Coder:** "Here is `kantung/core.py` and my failing test. Use test-first development; don't change locked parameters; explain each change so I can defend it."
- **Power BI pro:** "Given these CSV schemas [paste headers], give me step-by-step Power BI Desktop instructions for Page 3 using only slicers over precomputed rows — no scenario DAX."
- **Document maker:** "Using Section 2 numbers only, help me outline the Findings section for RO1–RO4: one number, one chart, one caveat each. Don't write final prose — give me bullet points I'll write up myself."
- **Everyone (Q&A drill):** "Act as a DOSM statistician on the MDIT finals panel. Ask me one hard question at a time about my part [name it], score my answer 1–5, and tell me what a stronger answer contains."
