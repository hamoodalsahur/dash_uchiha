"""Build every table the Power BI dashboard reads. Power BI only filters these
rows (Plan A: no scenario logic in DAX). Run: python3 export_powerbi.py"""
from pathlib import Path

import numpy as np
import pandas as pd

from kantung.core import SPLITS_2025, build_panel, dirichlet_ranks, fit_bounds, kpx, variance_split
from kantung.outputs import allocation_grid, map_to_2024, outlook_status, priority_list

OUT = Path(__file__).parent / "powerbi_tables"
OUT.mkdir(exist_ok=True)
REACHES = [round(x, 3) for x in np.arange(0.05, 0.601, 0.025)]

P = build_panel()
y22 = P[P.year == 2022].copy()
y24 = P[P.year == 2024].copy()

# KPX: P1/P99 bounds frozen on 2024 and applied to both years (comparable scores)
bounds = fit_bounds(y24, (0.01, 0.99))
for d in (y22, y24):
    k = kpx(d, bounds)
    for src, dst in (("A", "dim_A"), ("B", "dim_B"), ("C", "dim_C"), ("KPX", "KPX")):
        d[dst] = k[src].astype(float).to_numpy()
    d["partial"] = k["partial"].astype(bool).to_numpy()

# Weight stability on complete 2024 units
comp = y24[~y24.partial.astype(bool)]
st = dirichlet_ranks(comp[["dim_A", "dim_B", "dim_C"]].rename(columns=lambda c: c[-1]))
y24 = y24.join(st)
y24["tier"] = np.select([y24.share_top >= .9, y24.share_top >= .5], ["robust priority", "watch"], "not flagged")
y24.loc[y24.partial.astype(bool), "tier"] = "provisional"

# Outlook status on 2024 boundaries
y24["poverty_2022"] = map_to_2024(y24, y22.set_index(["state", "dkey"]), "poverty_absolute", SPLITS_2025).to_numpy()
key = y24.state + "|" + y24.dkey
y24["outlook"] = outlook_status(pd.Series(y24.poverty_2022.to_numpy(), index=key),
                                pd.Series(y24.poverty_absolute.to_numpy(), index=key)).to_numpy()

# Allocation grid: in-sample 2024 and backtest (2022 scores, 2024 outcomes)
def state_rate(d):
    g = d.dropna(subset=["poverty_absolute", "households"]).groupby("state")
    return g.apply(lambda x: np.average(x.poverty_absolute, weights=x.households), include_groups=False)

y24["s_district_2024"] = y24.poverty_absolute
y24["s_state_2024"] = y24.state.map(state_rate(y24))
y24["s_kpx_2024"] = y24.KPX
y24["s_district_2022"] = y24.poverty_2022
y24["s_state_2022"] = y24.state.map(state_rate(y22))
y24["s_kpx_2022"] = map_to_2024(y24, y22.set_index(["state", "dkey"]), "KPX", SPLITS_2025).to_numpy()
y24["s_persistent_first"] = y24.outlook.map({"persistent": 3, "emerging": 2}).fillna(0) * 1000 + y24.poverty_2022.fillna(0)

modes = {
    "In-sample 2024": {"District poverty": "s_district_2024", "State poverty": "s_state_2024", "KPX": "s_kpx_2024"},
    "Backtest 2022 to 2024": {"District poverty": "s_district_2022", "State poverty": "s_state_2022",
                              "KPX": "s_kpx_2022", "Persistent first": "s_persistent_first"},
}
grids = []
for mode, rules in modes.items():
    g = allocation_grid(y24, rules, "households", "poverty_absolute", REACHES, baseline="State poverty")
    grids.append(g.assign(mode=mode))
alloc = pd.concat(grids)
rand = pd.DataFrame([{"rule": "Random", "reach": r, "coverage": r, "efficiency": 1.0, "mode": m}
                     for r in REACHES for m in modes])
alloc = pd.concat([alloc, rand], ignore_index=True)

# Priority lists at three headline reach levels
pl = []
for mode, rules in modes.items():
    for name, col in rules.items():
        for r in (0.1, 0.2, 0.3):
            sel = priority_list(y24.set_index(key), col, "households", r)
            pl.append(pd.DataFrame({"district_id": sel.index, "selected_share": sel.to_numpy(),
                                    "rule": name, "reach": r, "mode": mode}))
plist = pd.concat(pl)
plist = plist[plist.selected_share > 0]

# Tables
y24["district_id"] = key
y22["district_id"] = y22.state + "|" + y22.dkey
dim = y24[["district_id", "state", "dkey", "src_note"]].assign(
    region=lambda d: np.where(d.state.isin(["Sabah", "W.P. Labuan"]), "Sabah & Labuan",
                     np.where(d.state == "Sarawak", "Sarawak", "Peninsular")),
    new_2024_district=lambda d: [(s, k) in SPLITS_2025 for s, k in zip(d.state, d.dkey)])
cols = ["district_id", "year", "poverty_absolute", "poverty_relative", "income_median", "p_rate", "u_rate",
        "piped_water", "electricity", "sanitation", "pop", "households", "dim_A", "dim_B", "dim_C", "KPX", "partial"]
fact = pd.concat([y22[cols], y24[cols + ["rank_p05", "rank_p50", "rank_p95", "share_top", "tier", "outlook", "poverty_2022"]]])
fact["households_status"] = "estimated"

headline = pd.DataFrame([
    {"metric": f"within_state_share_{v}_{w or 'unweighted'}_{y}", "value": variance_split(d, v, w)["within"]}
    for y, d in ((2022, y22), (2024, y24)) for v in ("poverty_absolute", "log_income") for w in (None, "households")])

dim.to_csv(OUT / "dim_district.csv", index=False)
fact.to_csv(OUT / "fact_district_year.csv", index=False)
alloc.to_csv(OUT / "fact_allocation.csv", index=False)
plist.to_csv(OUT / "fact_priority_list.csv", index=False)
headline.to_csv(OUT / "fact_headline.csv", index=False)

# Print the numbers the proposal quotes, for verification
b = alloc[(alloc["mode"] == "Backtest 2022 to 2024") & (alloc.reach == 0.2)].set_index("rule")
print("units 2024:", len(y24), "| robust:", (y24.tier == "robust priority").sum(), "| watch:", (y24.tier == "watch").sum(),
      "| provisional:", (y24.tier == "provisional").sum())
print("outlook counts:", y24.outlook.value_counts().to_dict())
print("backtest @20%:", b.coverage.round(3).to_dict(), "gain district:", round(b.loc["District poverty", "gain_vs_baseline"], 3))
print("poor households reached, district vs state @20%:", round(b.loc["District poverty", "poor_reached"]), round(b.loc["State poverty", "poor_reached"]))
print(headline.round(3).to_string(index=False))
print("rows:", {f.name: sum(1 for _ in open(f)) - 1 for f in OUT.glob("*.csv")})
