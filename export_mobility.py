"""Build the B40 -> M40 tables the Power BI dashboard reads (run after
download_mobility.py). Power BI only filters these rows; all maths is here.
Run: python export_mobility.py"""
from pathlib import Path

import numpy as np
import pandas as pd

from kantung.core import _read, DATA
from kantung.mobility import build_mobility, load_lines, load_penang_bands, scenario_grid

OUT = Path(__file__).parent / "powerbi_tables"
OUT.mkdir(exist_ok=True)

mob = build_mobility()
meta = dict(mob.attrs)
mob.insert(0, "district_id", mob.state + "|" + mob.dkey)
mob = mob.drop(columns=["state", "dkey", "src_note"])
mob["share_status"] = np.where(mob.share_below_m40_observed_low.notna(), "observed range + estimate", "estimate")
mob.to_csv(OUT / "fact_mobility.csv", index=False)

load_lines().to_csv(OUT / "fact_lines.csv", index=False)
scenario_grid().to_csv(OUT / "fact_scenarios.csv", index=False)

bands = load_penang_bands()
bands["district_id"] = np.where(bands.district.str.contains(r"\(state\)"), "Pulau Pinang|(state total)",
                                bands.state + "|" + bands.dkey)
bands[["district_id", "year", "income_concept", "band_lower_rm", "band_upper_rm", "household_share_pct", "source"]] \
    .to_csv(OUT / "fact_income_bands.csv", index=False)

w = _read(DATA / "formal_wages_state.parquet")
w = w.assign(month=pd.to_datetime(w.date).dt.strftime("%Y-%m-01"))[["state", "month", "wages_median", "employees"]]
w.to_csv(OUT / "fact_state_wages.csv", index=False)

# Numbers quoted in slides / report, for verification
y = mob[mob.year == 2024]
comp = y.income_growth_1924.notna()
print("inflation 2019-24 %/yr:", round(100 * meta["inflation_1924"], 2), "| M40 line growth %/yr:", round(100 * meta["line_growth_1924"], 2))
print("comparable districts 2019-24:", int(comp.sum()), "| grew slower than line:", int((y.income_growth_1924 < y.line_growth_1924).sum()))
print("catch-up 2019-24:", y.catch_up_status_1924.value_counts().to_dict())
print("median growth nominal / real %/yr:", round(100 * y.income_growth_1924.median(), 2), round(100 * y.income_growth_real_1924.median(), 2))
print("2024 districts with median below RM5,860:", int((y.income_median < 5860).sum()), "of", int(y.income_median.notna().sum()))
for yr in (2022, 2024):
    d = mob[mob.year == yr].dropna(subset=["share_below_m40", "households"])
    print(yr, "household-weighted share below line:", round(np.average(d.share_below_m40, weights=d.households), 3))
print("rows:", {f: sum(1 for _ in open(OUT / f)) - 1 for f in
                ("fact_mobility.csv", "fact_lines.csv", "fact_scenarios.csv", "fact_income_bands.csv", "fact_state_wages.csv")})
