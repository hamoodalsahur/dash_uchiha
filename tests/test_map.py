"""Tests for the dashboard map layer (decision D8).
Each test names the break: a district missing from the map, a bad alias,
a parent shown with the wrong year, or a dot placed in the wrong state."""
import pandas as pd
import pytest

from kantung.map import DOTS, MAP_ALIASES, build_map_table, polygon_key

# ---------- polygon_key: geoBoundaries names -> our district_id
@pytest.mark.parametrize("shape_name,state_hint,expected", [
    ("Kulaijaya", "Johor", "Johor|kulai"),
    ("Ledang", "Johor", "Johor|tangkak"),
    ("Nabawan / Persiangan", "Sabah", "Sabah|nabawan"),
    ("Kuala Lumpur", "W.P. Kuala Lumpur", "W.P. Kuala Lumpur|w.p. kuala lumpur"),
    ("Labuan", "W.P. Labuan", "W.P. Labuan|w.p. labuan"),
    ("Kota Bharu", "Kelantan", "Kelantan|kota bharu"),  # plain name, no alias
])
def test_polygon_key_applies_aliases(shape_name, state_hint, expected):
    assert polygon_key(shape_name, state_hint) == expected


def test_alias_table_has_exactly_the_five_agreed_fixes():
    # Break caught: an alias silently added or dropped without a team decision
    assert sorted(MAP_ALIASES) == sorted(["kulaijaya", "ledang", "nabawan / persiangan", "kuala lumpur", "labuan"])


# ---------- build_map_table on a small hand-made fixture
FACT = pd.DataFrame([
    # district_id, year, KPX, poverty, tier
    ("Sarawak|simunjan", 2022, 70.0, 20.0, None),
    ("Sarawak|simunjan", 2024, 60.0, 12.0, "watch"),
    ("Sarawak|gedong", 2024, 65.0, 16.7, "provisional"),
    ("Kelantan|kota bharu", 2024, 40.0, 5.0, "not flagged"),
    ("W.P. Putrajaya|w.p. putrajaya", 2024, 2.0, 0.2, "not flagged"),
], columns=["district_id", "year", "KPX", "poverty_absolute", "tier"])
POLYS = ["Sarawak|simunjan", "Kelantan|kota bharu"]
DOTS_FIX = {"Sarawak|gedong": (1.30, 110.68), "W.P. Putrajaya|w.p. putrajaya": (2.94, 101.69)}
PARENTS = {"Sarawak|simunjan"}


def _table():
    return build_map_table(FACT, POLYS, DOTS_FIX, PARENTS).set_index("shape_key")


def test_parent_polygon_shows_2022_value_and_is_labelled():
    t = _table()
    assert t.loc["Sarawak|simunjan", "value_year"] == 2022
    assert t.loc["Sarawak|simunjan", "KPX_shown"] == pytest.approx(70.0)
    assert t.loc["Sarawak|simunjan", "tier_shown"] == "split in 2024 (2022 value)"


def test_normal_polygon_shows_2024_value_and_tier():
    t = _table()
    assert t.loc["Kelantan|kota bharu", "value_year"] == 2024
    assert t.loc["Kelantan|kota bharu", "tier_shown"] == "not flagged"


def test_new_district_and_putrajaya_are_dots_with_2024_values():
    t = _table()
    assert t.loc["Sarawak|gedong", "shape_type"] == "dot"
    assert t.loc["Sarawak|gedong", "KPX_shown"] == pytest.approx(65.0)
    assert t.loc["W.P. Putrajaya|w.p. putrajaya", "shape_type"] == "dot"


def test_every_shape_appears_once():
    t = build_map_table(FACT, POLYS, DOTS_FIX, PARENTS)
    assert t.shape_key.is_unique and len(t) == 4


# ---------- real dot coordinates sit inside the right part of Malaysia
@pytest.mark.parametrize("key", sorted(DOTS))
def test_dot_coordinates_are_in_the_right_region(key):
    lat, lon = DOTS[key]
    if key.startswith("Sarawak"):
        assert 0.8 < lat < 5.0 and 109.5 < lon < 115.7
    elif key.startswith("Sabah"):
        assert 4.0 < lat < 7.5 and 115.3 < lon < 119.5
    else:  # Putrajaya
        assert 2.8 < lat < 3.1 and 101.6 < lon < 101.8


# ---------- integration: the real map covers every 2024 unit exactly once
def test_real_map_covers_every_2024_unit_once():
    from kantung.map import build_real_map
    table, geo = build_real_map()
    fact = pd.read_csv("powerbi_tables/fact_district_year.csv")
    units_2024 = set(fact.loc[fact.year == 2024, "district_id"])
    assert table.shape_key.is_unique
    assert set(table.shape_key) == units_2024          # nothing missing, nothing extra
    assert {f["properties"]["shape_key"] for f in geo["features"]} == units_2024
    assert (table.shape_type == "dot").sum() == 7      # 6 new districts + Putrajaya
