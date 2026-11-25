"""Build the map files for Power BI. Run after export_powerbi.py:  python build_map.py

Writes
  dashboard/map/atlas_map.geojson   polygons + dots, property shape_key = district_id
  dashboard/map/atlas_map.topojson  same, for the Power BI Shape Map visual (object "districts")
  powerbi_tables/fact_map.csv       one row per shape: the value and tier it is shaded by
"""
import json
from pathlib import Path

import topojson as tp
import geopandas  # noqa: F401  (topojson needs it for GeoJSON input)

from kantung.map import build_real_map

ROOT = Path(__file__).resolve().parent
table, geo = build_real_map(ROOT)

out = ROOT / "dashboard" / "map"
(out / "atlas_map.geojson").write_text(json.dumps(geo))
topo = tp.Topology(geo, object_name="districts", prequantize=1e5, toposimplify=0.002)
(out / "atlas_map.topojson").write_text(topo.to_json())
table.to_csv(ROOT / "powerbi_tables" / "fact_map.csv", index=False)

print("shapes:", len(table), "| polygons:", (table.shape_type == "polygon").sum(), "| dots:", (table.shape_type == "dot").sum())
print("parents shaded with 2022 value:", sorted(table.loc[table.value_year == 2022, "shape_key"]))
for f in ("atlas_map.geojson", "atlas_map.topojson"):
    print(f, round((out / f).stat().st_size / 1024), "KB")
