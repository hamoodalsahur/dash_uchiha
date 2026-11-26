# Team updates

Read this first. Newest entry at the top. If an update changes your work, it says so under **What you need to do**.

How to add an entry: copy the template at the bottom, put it above the last entry, and keep it short. If it locks a method or a number, also add a row to [`docs/decision_log.md`](docs/decision_log.md) and link it.

---

## 26 Nov 2026: B40 → M40 direction (Hamood)

**What changed:** Atlas keeps its poverty work and adds a second question: how far each district is from the M40 entry line, whether it is catching up, and what income growth would close the gap by 2030. See decision [D15](docs/decision_log.md).

**New datasets (all official DOSM open data, checked on 26 Nov):**
- Income percentiles, national and state (`hies_malaysia_percentile`, `hies_state_percentile`): the actual B40/M40/T20 lines. M40 entry was RM4,850 in 2019, RM5,250 in 2022 and RM5,860 in 2024.
- District income, expenditure and Gini (`hies_district`, `hh_inequality_district`): spending share and whether gains are shared.
- State prices (`cpi_2d_state`, to Oct 2026): turns nominal income into real income.
- Population by age (`population_district`, 2020–2026): dependency ratio.
- School completion (`completion_school_district`, 2021–2025): skills pipeline. Uses education districts, so it needs a mapping table.
- Formal wages by state (`formal_wages_state`, to Jun 2026): most recent pay signal, kept separate from the 2024 survey.
- District income-band tables (state HIS 2024 reports, Table 1.11): observed share below RM5,860. Penang done first.

**Early findings (from a quick analysis, not yet in the pipeline):**
- 94 of 148 comparable districts had median income grow slower than the M40 line in 2019–2024 (about 3.1% vs 3.85% a year).
- Our estimate of the share of households below RM5,860 falls inside DOSM's published range for the 4 Penang districts checked, and adds up to 40.4% nationally in 2022 (it should be 40%).

**Rules:**
- The 2024 survey stays the ground truth. 2025–26 wages and prices are a separately labelled layer.
- We describe districts, not families, and show links, not causes. No "X households will become M40".
- The near-M40 view sits beside the poverty-first ranking. It never replaces it.

**What you need to do:**
- **Hamood:** add the datasets, gap and catch-up tables, and tests on a new branch.
- **Aiman:** 2030 required-growth scenarios (fixed, real and moving line) and a 2022→2024 check against simple baselines.
- **Apipi:** plan one new layer per page: gap-to-M40 map (Atlas), closing/falling-behind tag (Risk Outlook), growth-needed card (Allocation Planner). Wait for the new tables before building.
- **Boboi:** add the B40/M40 caveats to the report and cite the World Bank 2024 mobility paper (no household panel data in Malaysia) and the KRI 2024 paper (B40/M40 labels are imperfect).

**Links:** slides "Atlas – From B40 to M40" (shared in the group chat).

---

## Template

```markdown
## DD Mon YYYY: short title (your name)

**What changed:**
**Why:**
**What you need to do:**
- Name: task
**Links:**
```
