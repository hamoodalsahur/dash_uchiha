"""Tests for dashboard-facing outputs: outlook status, priority list, allocation grid.
Hand-derived expectations; fixture CV matches tests/test_core.py."""
import pandas as pd
import pytest

from kantung.outputs import allocation_grid, outlook_status, priority_list

CV = pd.DataFrame({"unit": ["A", "B", "C"], "rate": [50.0, 10.0, 10.0], "hh": [100.0, 100.0, 200.0]})


# ---------- outlook_status
# 5 units, top_share 0.4 -> top 2 each wave.
# prev top: u1 (30), u2 (20). cur top: u1 (28), u3 (25).
def test_outlook_status_classifies_each_case():
    prev = pd.Series({"u1": 30, "u2": 20, "u3": 5, "u4": 4, "u5": 1})
    cur = pd.Series({"u1": 28, "u2": 6, "u3": 25, "u4": 4, "u5": 1})
    s = outlook_status(prev, cur, top_share=0.4)
    assert s.to_dict() == {"u1": "persistent", "u2": "easing", "u3": "emerging",
                           "u4": "not flagged", "u5": "not flagged"}


def test_outlook_status_unit_without_history_is_marked():
    prev = pd.Series({"u1": 30, "u2": 20})
    cur = pd.Series({"u1": 28, "u2": 6, "new": 40})
    assert outlook_status(prev, cur, top_share=0.5)["new"] == "no history"


# ---------- priority_list: share of each unit selected at a reach
def test_priority_list_selects_top_unit_fully_and_ties_proportionally():
    # reach 50% = 200 of 400 hh: A fully, then 100 of the 300-hh tied B+C block = 1/3 each
    sel = priority_list(CV.set_index("unit"), "rate", "hh", 0.5)
    assert sel.to_dict() == pytest.approx({"A": 1.0, "B": 1 / 3, "C": 1 / 3})


def test_priority_list_selected_households_equal_reach():
    sel = priority_list(CV.set_index("unit"), "rate", "hh", 0.3)  # 120 hh
    assert (sel * CV.set_index("unit").hh).sum() == pytest.approx(120.0)


# ---------- allocation_grid: one row per rule x reach with planner metrics
def test_allocation_grid_metrics():
    units = CV.assign(state_score=[1.0, 1.0, 2.0])  # a rule that picks C first
    g = allocation_grid(units, {"district": "rate", "other": "state_score"}, "hh", "rate", [0.25])
    d = g.set_index("rule")
    # district rule at 25%: A fully -> 50 poor of 80; 100 hh selected, 50 poor
    assert d.loc["district", "coverage"] == pytest.approx(0.625)
    assert d.loc["district", "efficiency"] == pytest.approx(2.5)
    assert d.loc["district", "nonpoor_share"] == pytest.approx(0.5)
    assert d.loc["district", "poor_reached"] == pytest.approx(50.0)
    # other rule at 25%: half of C (100 of 200 hh, 10% poor) -> 10 poor of 80
    assert d.loc["other", "coverage"] == pytest.approx(10 / 80)
    assert d.loc["other", "nonpoor_share"] == pytest.approx(0.9)


def test_allocation_grid_gain_over_named_baseline():
    units = CV.assign(state_score=[1.0, 1.0, 2.0])
    g = allocation_grid(units, {"district": "rate", "other": "state_score"}, "hh", "rate", [0.25],
                        baseline="other").set_index("rule")
    assert g.loc["district", "gain_vs_baseline"] == pytest.approx(0.625 - 0.125)
    assert g.loc["other", "gain_vs_baseline"] == pytest.approx(0.0)


# ---------- map_to_2024: carry 2022 values onto 2024 boundaries
from kantung.outputs import map_to_2024


def test_unchanged_district_keeps_its_value_and_new_district_inherits_parent():
    prev = pd.DataFrame({"state": ["Sarawak", "Sabah", "Sabah"],
                         "dkey": ["simunjan", "beaufort", "papar"], "v": [20.0, 10.0, 4.0]}).set_index(["state", "dkey"])
    cur = pd.DataFrame({"state": ["Sarawak", "Sarawak", "Sabah"], "dkey": ["simunjan", "gedong", "membakut"]})
    splits = {("Sarawak", "gedong"): {"simunjan": 1.0}, ("Sabah", "membakut"): {"beaufort": 1.0, "papar": 3.0}}
    out = map_to_2024(cur, prev, "v", splits)
    # membakut = (10*1 + 4*3) / 4 = 5.5
    assert out.tolist() == pytest.approx([20.0, 20.0, 5.5])


def test_district_with_no_history_gets_nan():
    prev = pd.DataFrame({"state": ["A"], "dkey": ["x"], "v": [1.0]}).set_index(["state", "dkey"])
    cur = pd.DataFrame({"state": ["A"], "dkey": ["brand new"]})
    assert map_to_2024(cur, prev, "v", {}).isna().all()
