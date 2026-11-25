# Dashboard (owner: Power BI pro)

- `Atlas.pbix` lives here. **Only the Power BI pro edits it** (a .pbix cannot be merged; two editors = one person's work lost).
- Data source: the CSVs in `../powerbi_tables/`. In Power BI, point to them with a **relative folder parameter** or re-point before export so judges' copies don't break.
- `map/` holds the boundary file (geoBoundaries MYS ADM2, 2020, CC BY 3.0) and any TopoJSON conversion.
- Commit the .pbix after each working milestone with a clear message, e.g. `dashboard: page 1 map + KPI cards`.
- Before submission: export `Dashboard.pdf`, open the .pbix on a second Windows machine, check no local paths.
