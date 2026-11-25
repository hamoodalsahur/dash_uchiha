"""The data dictionary must describe every column the dashboard reads, and nothing else.
Break caught: a new or renamed column in powerbi_tables/ with no documentation,
or a stale entry for a column that no longer exists."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TAGS = {"observed", "derived", "estimated", "modelled", "provisional", "backtest", "identifier", "label"}


def _dictionary():
    return pd.read_csv(ROOT / "data" / "data_dictionary.csv")


def test_every_dashboard_column_is_documented_exactly_once():
    dd = _dictionary()
    documented = list(zip(dd.table, dd.column))
    assert len(documented) == len(set(documented)), "duplicate entries"
    actual = {(f.name, c) for f in (ROOT / "powerbi_tables").glob("*.csv") for c in pd.read_csv(f, nrows=0).columns}
    assert set(documented) == actual, {"missing": actual - set(documented), "stale": set(documented) - actual}


def test_entries_are_complete_and_tagged():
    dd = _dictionary()
    for col in ("meaning", "unit", "source", "status_tag"):
        assert dd[col].notna().all() and (dd[col].astype(str).str.strip() != "").all(), col
    assert set(dd.status_tag) <= TAGS, set(dd.status_tag) - TAGS
