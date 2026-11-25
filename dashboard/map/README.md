# Map files (built by Coder 1, used by the Power BI pro)

| File | Use |
|---|---|
| `atlas_map.topojson` | **Load this in Power BI's Shape Map** (object name `districts`, key property `shape_key`) |
| `atlas_map.geojson` | Same shapes as GeoJSON (for other tools / checks) |
| `../../powerbi_tables/fact_map.csv` | One row per shape: `shape_key`, `shape_type` (polygon/dot), `value_year`, `KPX_shown`, `poverty_shown`, `tier_shown` |
| `preview.png` | What the map should look like, for checking |
| `source/` | The original geoBoundaries file (do not edit) |

## How the map follows decision D8
- 159 polygons from geoBoundaries (MYS ADM2, boundary year 2020) + 7 dots = **166 shapes = every 2024 unit once**.
- Five name fixes: Kulaijaya→Kulai, Ledang→Tangkak, Nabawan / Persiangan→Nabawan, Kuala Lumpur→W.P. Kuala Lumpur, Labuan→W.P. Labuan.
- **Dots:** the six districts created in 2024 (Membakut, Gedong, Sebuyau, Pantu, Lingga, Siburan) and Putrajaya, coloured by their 2024 values.
- **Grey parents:** Simunjan, Sri Aman, Serian, Beaufort and Papar still have their pre-split 2020 shape, so they show their **2022** value and the tier label `split in 2024 (2022 value)`.
- Legend note to use: *"Grey districts were split in 2024; their shapes show 2022 values. Dots show the new districts' 2024 values."*

## Important for KPI cards
The map shows 24 robust / 6 watch because one robust and one watch district are split parents shown with 2022 values. **KPI cards and tables must count from `fact_district_year` (25 robust / 7 watch), never from `fact_map`.**

## Power BI steps (Shape Map)
1. If Shape Map isn't in the visuals pane: File → Options and settings → Options → Preview features → tick **Shape map visual** → restart.
2. Load `powerbi_tables/fact_map.csv`; relate `fact_map[district_id]` → `dim_district[district_id]` (one-to-one).
3. Add a Shape Map. **Location** = `fact_map[shape_key]`, **Legend** = `fact_map[tier_shown]`.
4. Format → Map settings → Map type **Custom map** → add `atlas_map.topojson`. Use **View map keys** to confirm keys match `shape_key`.
5. Colours (handbook palette): robust priority #B94539, watch #D8AD6C, not flagged #C9D6DA, provisional #377B78, split parent #8C8C8C.
(Menu names can differ slightly between Power BI versions.)

## Rebuild
```
pip install -r requirements-map.txt
python export_powerbi.py
python build_map.py      # expect: shapes 166 | polygons 159 | dots 7
```

## Credits (put in the report and README.txt)
- Boundaries: geoBoundaries gbOpen MYS ADM2 (2020), CC BY 3.0, sources geoBoundaries and citypopulation.de.
- Dot locations: OpenStreetMap Nominatim, retrieved 25 Nov 2026, © OpenStreetMap contributors (ODbL).
