"""Map layer for the dashboard (decision D8).

Polygons: geoBoundaries gbOpen MYS ADM2 (boundary year 2020, CC BY 3.0).
The six districts created in 2024 and Putrajaya have no polygon in that file,
so they are drawn as dots. Their parent polygons keep the old (2020) extent and
are shaded with the parent's 2022 value, labelled as such.
Dot coordinates: OpenStreetMap Nominatim, retrieved 25 Nov 2026
(© OpenStreetMap contributors, ODbL).
"""
import pandas as pd

from kantung.core import district_key

# geoBoundaries shapeName (normalised) -> our district key. The five agreed fixes.
MAP_ALIASES = {
    "kulaijaya": "kulai",
    "ledang": "tangkak",
    "nabawan / persiangan": "nabawan",
    "kuala lumpur": "w.p. kuala lumpur",
    "labuan": "w.p. labuan",
}

# district_id -> (lat, lon)
DOTS = {
    "Sabah|membakut": (5.4727, 115.7967),       # Membakut town (station node)
    "Sarawak|gedong": (1.2981, 110.6784),       # Gedong district boundary centre
    "Sarawak|sebuyau": (1.3918, 111.0113),      # Sebuyau district boundary centre
    "Sarawak|pantu": (1.1736, 111.1316),        # Pantu district boundary centre
    "Sarawak|lingga": (1.3519, 111.1701),       # Lingga town
    "Sarawak|siburan": (1.3615, 110.4043),      # Siburan town
    "W.P. Putrajaya|w.p. putrajaya": (2.9384, 101.6922),  # Putrajaya boundary centre
}

# Parent districts whose 2020 polygon still includes land given to a new district
SPLIT_PARENTS = {"Sarawak|simunjan", "Sarawak|sri aman", "Sarawak|serian", "Sabah|beaufort", "Sabah|papar"}

PARENT_LABEL = "split in 2024 (2022 value)"


def polygon_key(shape_name: str, state: str) -> str:
    """district_id for a geoBoundaries polygon, applying the agreed aliases."""
    raw = shape_name.strip().lower()
    key = MAP_ALIASES.get(raw, district_key(shape_name))
    return f"{state}|{key}"


def build_map_table(fact: pd.DataFrame, polygon_keys, dots: dict, parents: set) -> pd.DataFrame:
    """One row per map shape with the value it is shaded by.

    Parent polygons show the 2022 value (D8); every other shape shows 2024.
    `fact` needs district_id, year, KPX, poverty_absolute, tier."""
    f = fact.set_index(["district_id", "year"])
    rows = []
    for key in polygon_keys:
        year = 2022 if key in parents else 2024
        r = f.loc[(key, year)]
        rows.append({"shape_key": key, "district_id": key, "shape_type": "polygon", "value_year": year,
                     "KPX_shown": r.KPX, "poverty_shown": r.poverty_absolute,
                     "tier_shown": PARENT_LABEL if key in parents else r.tier})
    for key, (lat, lon) in dots.items():
        r = f.loc[(key, 2024)]
        rows.append({"shape_key": key, "district_id": key, "shape_type": "dot", "value_year": 2024,
                     "KPX_shown": r.KPX, "poverty_shown": r.poverty_absolute, "tier_shown": r.tier,
                     "lat": lat, "lon": lon})
    return pd.DataFrame(rows)


def _circle(lat: float, lon: float, radius_deg: float = 0.07, n: int = 24) -> list:
    """Small polygon ring so a dot can live in the same shape file as districts."""
    import math
    ring = [[round(lon + radius_deg * math.cos(2 * math.pi * i / n), 5),
             round(lat + radius_deg * math.sin(2 * math.pi * i / n), 5)] for i in range(n)]
    return [ring + [ring[0]]]


def build_real_map(root=None):
    """Join the geoBoundaries file to our 2024 units. Returns (table, geojson).

    Each polygon's state is found by matching its district key to our 2024
    units; a key that matches no unit or more than one raises an error rather
    than guessing."""
    import json
    from pathlib import Path

    root = Path(root or Path(__file__).resolve().parent.parent)
    fact = pd.read_csv(root / "powerbi_tables" / "fact_district_year.csv")
    units = fact.loc[fact.year == 2024, "district_id"]
    by_dkey = {k: [units[i] for i in v] for k, v in units.groupby(units.str.split("|", n=1).str[1]).groups.items()}

    geo = json.loads((root / "dashboard/map/source/geoBoundaries-MYS-ADM2_simplified.geojson").read_text())
    features, poly_keys = [], []
    for f in geo["features"]:
        name = f["properties"]["shapeName"]
        dkey = MAP_ALIASES.get(name.strip().lower(), district_key(name))
        matches = by_dkey.get(dkey, [])
        if len(matches) != 1:
            raise ValueError(f"polygon {name!r} matched {len(matches)} units: {matches}")
        key = matches[0]
        poly_keys.append(key)
        features.append({"type": "Feature", "properties": {"shape_key": key, "shape_type": "polygon"},
                         "geometry": f["geometry"]})
    for key, (lat, lon) in DOTS.items():
        features.append({"type": "Feature", "properties": {"shape_key": key, "shape_type": "dot"},
                         "geometry": {"type": "Polygon", "coordinates": _circle(lat, lon)}})
    table = build_map_table(fact, poly_keys, DOTS, SPLIT_PARENTS)
    return table, {"type": "FeatureCollection", "features": features}
