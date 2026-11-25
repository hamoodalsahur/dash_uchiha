"""Integration checks on the real DOSM panel (needs the downloaded parquet files).
Each test names the break: a lost district, a double-counted population, a
mis-scaled rate, or a broken boundary mapping."""
import pytest

from kantung.core import SPLITS_2025, build_panel


@pytest.fixture(scope="module")
def panel():
    return build_panel()


def test_2024_has_all_166_units_once(panel):
    p = panel[panel.year == 2024]
    assert len(p) == 166
    assert not p.duplicated(["state", "dkey"]).any()


def test_every_2024_unit_has_poverty_and_households(panel):
    p = panel[panel.year == 2024]
    assert p.poverty_absolute.notna().all()
    assert (p.households > 0).all()


def test_rates_are_percentages(panel):
    for c in ("poverty_absolute", "p_rate", "u_rate", "piped_water", "electricity"):
        s = panel[c].dropna()
        assert s.between(0, 100).all(), c


def test_population_not_double_counted(panel):
    # Malaysia's population is about 34 million (2025); summing every age and
    # ethnicity row would give several times that.
    total_thousands = panel[panel.year == 2024]["pop"].sum()
    assert 30_000 < total_thousands < 38_000


def test_new_districts_have_parents_in_2022(panel):
    keys22 = set(map(tuple, panel[panel.year == 2022][["state", "dkey"]].values))
    for (state, _), parents in SPLITS_2025.items():
        for p in parents:
            assert (state, p) in keys22, (state, p)
