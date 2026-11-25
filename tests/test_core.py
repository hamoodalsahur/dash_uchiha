"""Tests for kantung.core. Expected values are hand-derived (see comments)."""
import numpy as np
import pandas as pd
import pytest

from kantung.core import coverage, dirichlet_ranks, district_key, kpx, variance_split


# ---------- district_key: catches a missing spelling rule (silent drop in joins)
@pytest.mark.parametrize("a,b", [
    ("S.P.Tengah", "Seberang Perai Tengah"),
    ("S.P. Selatan", "Seberang Perai Selatan"),
    ("Larut & Matang", "Larut Dan Matang"),
    ("Hulu", "Hulu Terengganu"),           # Terengganu 2024 label
    ("Hulu Langat", "Ulu Langat"),
    ("Cameron Highland", "Cameron Highlands"),
    ("Manjung (Dinding)", "Manjung"),
    ("Tanjong Manis", "Tanjung Manis"),
    ("Lubok antu", "Lubok Antu"),
])
def test_spelling_variants_share_a_key(a, b):
    assert district_key(a) == district_key(b)


def test_different_districts_keep_different_keys():
    # Break caught: an over-eager rule that maps every 'Hulu X' to one key
    assert district_key("Hulu Perak") != district_key("Hulu Terengganu")
    assert district_key("Seberang Perai Utara") != district_key("Seberang Perai Tengah")


# ---------- variance_split
# Fixture: state A districts y=0,2 ; state B y=10,12
# Unweighted: mean 6; SST=36+16+16+36=104; SSB=2*25+2*25=100 -> between 100/104
# Weighted w=(1,1,1,3): mean=(0+2+10+36)/6=8; SST=64+36+4+3*16=152;
#   state means A=1 (w=2), B=(10+36)/4=11.5 (w=4); SSB=2*49+4*12.25=147 -> 147/152
VS = pd.DataFrame({"state": ["A", "A", "B", "B"], "y": [0, 2, 10, 12], "w": [1, 1, 1, 3]})


def test_variance_split_unweighted():
    r = variance_split(VS, "y")
    assert r["between"] == pytest.approx(100 / 104)
    assert r["within"] == pytest.approx(4 / 104)


def test_variance_split_weighted_differs_and_is_correct():
    r = variance_split(VS, "y", "w")
    assert r["between"] == pytest.approx(147 / 152)


# ---------- coverage
# A: 100 households at 50% poor (50 poor); B: 100 at 10% (10); C: 200 at 10% (20)
# Totals: 400 households, 80 poor. Score = poverty rate, so B and C tie.
CV = pd.DataFrame({"unit": ["A", "B", "C"], "rate": [50.0, 10.0, 10.0], "hh": [100.0, 100.0, 200.0]})


def test_coverage_takes_highest_score_first():
    # reach 25% = 100 hh -> all of A -> 50/80
    assert coverage(CV, "rate", "hh", "rate", 0.25) == pytest.approx(50 / 80)


def test_coverage_splits_tied_block_proportionally():
    # reach 50% = 200 hh -> A (100) + 100 of the tied B+C block (300 hh, 30 poor)
    # -> 50 + 30/3 = 60 poor -> 60/80
    assert coverage(CV, "rate", "hh", "rate", 0.5) == pytest.approx(60 / 80)


def test_full_reach_covers_everyone():
    assert coverage(CV, "rate", "hh", "rate", 1.0) == pytest.approx(1.0)


def test_zero_reach_covers_no_one():
    assert coverage(CV, "rate", "hh", "rate", 0.0) == pytest.approx(0.0)


# ---------- kpx
# Bounds chosen so each indicator maps to 0 (worst) or 1 (best) before the floor.
BOUNDS = {"log_income": (0, 1), "poverty_absolute": (0, 100), "p_rate": (0, 100),
          "u_rate": (0, 10), "piped_water": (0, 100), "electricity": (0, 100), "sanitation": (0, 100)}
BEST = dict(log_income=1, poverty_absolute=0, p_rate=100, u_rate=0, piped_water=100, electricity=100, sanitation=100)
WORST = dict(log_income=0, poverty_absolute=100, p_rate=0, u_rate=10, piped_water=0, electricity=0, sanitation=0)


def _unit(**over):
    d = dict(BEST); d.update(over); return d


def test_kpx_extremes_and_single_dimension_deprivation():
    df = pd.DataFrame([BEST, WORST, _unit(log_income=0, poverty_absolute=100)])
    k = kpx(df, BOUNDS)
    # best: I=1 -> 0 ; worst: I=0.01 -> 99 ; worst in A only: I=0.01**(1/3)=0.215443 -> 78.4557
    assert k.KPX.tolist() == pytest.approx([0.0, 99.0, 78.4557], abs=1e-3)


def test_kpx_floor_prevents_collapse_to_tie():
    # Two units both worst in A; one also worse in B. Without the floor both
    # geometric means are 0 and tie; with it they must differ.
    df = pd.DataFrame([_unit(log_income=0, poverty_absolute=100),
                       _unit(log_income=0, poverty_absolute=100, p_rate=50, u_rate=5)])
    k = kpx(df, BOUNDS)
    assert k.KPX.iloc[1] > k.KPX.iloc[0]


def test_kpx_missing_dimension_is_partial_and_renormalised():
    # Worst in A, B missing, best in C: I = sqrt(0.01 * 1) = 0.1 -> KPX 90
    df = pd.DataFrame([_unit(log_income=0, poverty_absolute=100, p_rate=np.nan, u_rate=np.nan)])
    k = kpx(df, BOUNDS)
    assert k.KPX.iloc[0] == pytest.approx(90.0)
    assert bool(k.partial.iloc[0]) is True


def test_kpx_clips_values_outside_frozen_bounds():
    # Poverty 150 is beyond the bound of 100: must score like 100, not below the floor
    a = kpx(pd.DataFrame([_unit(poverty_absolute=100)]), BOUNDS).KPX.iloc[0]
    b = kpx(pd.DataFrame([_unit(poverty_absolute=150)]), BOUNDS).KPX.iloc[0]
    assert a == pytest.approx(b)


# ---------- dirichlet_ranks
DIMS = pd.DataFrame({"A": [0.05, 0.5, 0.9, 0.95, 0.99],
                     "B": [0.05, 0.6, 0.8, 0.9, 0.99],
                     "C": [0.05, 0.4, 0.85, 0.97, 0.99]})


def test_worst_on_every_dimension_is_always_rank_one():
    r = dirichlet_ranks(DIMS, n=500)
    assert r.rank_p95.iloc[0] == 1 and r.share_top.iloc[0] == 1.0


def test_best_on_every_dimension_is_never_top():
    r = dirichlet_ranks(DIMS, n=500)
    assert r.share_top.iloc[4] == 0.0


def test_dirichlet_ranks_reproducible_with_seed():
    # Units that trade places depending on the weights, so the result really
    # depends on the random draws (a fixed seed must make it repeatable).
    swap = pd.DataFrame({"A": [0.2, 0.8, 0.5], "B": [0.8, 0.2, 0.5], "C": [0.5, 0.5, 0.45]})
    a = dirichlet_ranks(swap, n=200, seed=7, top_share=0.34)
    b = dirichlet_ranks(swap, n=200, seed=7, top_share=0.34)
    assert 0 < a.share_top.iloc[0] < 1  # randomness matters for this fixture
    pd.testing.assert_frame_equal(a, b)
