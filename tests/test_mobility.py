"""B40 -> M40 layer. Unit tests pin the arithmetic (each names the break it
catches); data tests check the estimates against published DOSM figures."""
import math

import numpy as np
import pandas as pd
import pytest

from kantung import mobility as m


# ---------- arithmetic ----------

def test_required_growth_fixed_line_matches_hand_calculation():
    # RM4,000 -> RM5,860 in six years: (5860/4000)^(1/6) - 1 = 6.57%
    assert m.required_growth(4000, 5860, 0.0, 6) == pytest.approx(0.0657, abs=5e-4)


def test_required_growth_moving_line_is_higher():
    # Break caught: forgetting to grow the line. At 4%/yr the 2030 line is RM7,415.
    assert m.required_growth(4000, 5860, 0.04, 6) == pytest.approx(0.1083, abs=5e-4)


def test_required_growth_needs_positive_years_and_income():
    assert math.isnan(m.required_growth(4000, 5860, 0.0, 0))
    assert math.isnan(m.required_growth(0, 5860, 0.0, 6))


def test_years_to_cross_uses_whole_years():
    # 10%/yr: four years gives RM5,856.40, still short, so five years.
    assert m.years_to_cross(4000, 5860, 0.10, 0.0) == 5


def test_years_to_cross_is_zero_when_already_above_and_none_when_line_runs_away():
    assert m.years_to_cross(6000, 5860, 0.03, 0.0) == 0
    assert m.years_to_cross(4000, 5860, 0.03, 0.04) is None


def test_annual_growth_annualises_unequal_intervals():
    # Break caught: dividing total growth by years instead of compounding.
    assert m.annual_growth(100, 121, 2) == pytest.approx(0.10)


def test_real_growth_divides_rather_than_subtracts_inflation():
    # 5% nominal with 3% inflation is 1.94% real, not 2%.
    assert m.annual_growth(100, 105, 1, cpi_start=100, cpi_end=103) == pytest.approx(0.0194, abs=1e-4)


def test_catch_up_status_from_relative_gap_change():
    s = m.catch_up_status(pd.Series([0.02, -0.02, 0.001]))
    assert s.tolist() == ["closing", "falling behind", "about level"]


# ---------- distribution estimates ----------

def test_share_below_line_is_half_at_the_median():
    assert m.share_below(5000, 6000, 5000) == pytest.approx(0.5)


def test_share_below_rises_with_the_line_and_needs_mean_above_median():
    lo, hi = m.share_below(4000, 5000, 4000), m.share_below(4000, 5000, 6000)
    assert hi > lo
    assert math.isnan(m.share_below(5000, 4900, 5860))  # lognormal needs mean > median


def test_band_bounds_bracket_the_line():
    bands = pd.DataFrame({"band_lower_rm": [0, 5000, 6000], "band_upper_rm": [5000, 6000, np.nan],
                          "household_share_pct": [30.0, 10.0, 60.0]})
    lo, hi, uni = m.band_bounds(bands, 5860)
    assert (lo, hi) == pytest.approx((0.30, 0.40))
    assert uni == pytest.approx(0.30 + 0.10 * 0.86)


# ---------- lines from DOSM percentiles ----------

@pytest.fixture(scope="module")
def lines():
    return m.load_lines()


def test_national_m40_entry_lines_are_the_official_values(lines):
    nat = lines[(lines.geography == "Malaysia") & (lines.line == "m40_entry")].set_index("year").value_rm
    assert nat.to_dict() == {2019: 4850, 2022: 5250, 2024: 5860}


def test_state_lines_are_close_to_published_2024_cutoffs(lines):
    st = lines[(lines.year == 2024) & (lines.line == "m40_entry")].set_index("geography").value_rm
    assert st["Kedah"] == pytest.approx(3940, abs=20)     # DOSM technical notes, Table 5
    assert st["Selangor"] == pytest.approx(9570, abs=20)


def test_near_m40_band_starts_at_b20_ceiling(lines):
    near = lines[(lines.geography == "Malaysia") & (lines.line == "near_m40_floor") & (lines.year == 2024)]
    assert near.value_rm.iloc[0] == 3820


# ---------- estimates against published figures ----------

@pytest.fixture(scope="module")
def mob():
    return m.build_mobility()


def test_national_share_below_line_is_about_40_percent(mob):
    # By definition 40% of households are below the national B40 line. Adding
    # district estimates weighted by households must land close to that.
    d = mob[mob.year == 2022].dropna(subset=["share_below_m40", "households"])
    assert np.average(d.share_below_m40, weights=d.households) == pytest.approx(0.40, abs=0.02)


def test_estimates_fall_inside_published_penang_ranges(mob):
    bands = m.load_penang_bands()
    est = mob[(mob.year == 2024) & (mob.state == "Pulau Pinang")].set_index("dkey").share_below_m40
    checked = 0
    for dkey, b in bands.groupby("dkey"):
        if dkey not in est.index:
            continue
        lo, hi, _ = m.band_bounds(b, 5860)
        assert lo - 0.01 <= est[dkey] <= hi + 0.01, dkey
        checked += 1
    assert checked == 5


def test_growth_skips_districts_whose_boundaries_changed(mob):
    # Parents of the 2025 splits lost area, so 2019->2024 growth is not comparable.
    changed = mob[mob.boundary_changed]
    assert changed.income_growth_real_1924.isna().all()
    assert len(changed) > 0


def test_one_row_per_district_year(mob):
    assert not mob.duplicated(["state", "dkey", "year"]).any()


# ---------- school completion (education districts -> admin districts) ----------

def test_completion_maps_each_admin_district_once_and_keeps_most():
    c = m.load_completion()
    assert not c.duplicated(["state", "dkey", "year"]).any()
    assert c[c.year == 2024].dkey.nunique() >= 125


def test_combined_education_offices_are_flagged_not_hidden():
    c = m.load_completion()
    shared = c[(c.state == "Kedah") & (c.dkey.isin(["kuala muda", "yan"])) & (c.year == 2024)]
    assert len(shared) == 2
    assert (shared.match_note == "shared education office").all()
    assert shared.completion_upper_secondary.nunique() == 1
