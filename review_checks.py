"""Run the checks raised by the two external reviews against real DOSM data."""
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

from kantung.core import (SPLITS_2025, build_panel, coverage, dirichlet_ranks,
                          fit_bounds, kpx, variance_split, district_key)

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)
P = build_panel()
y24, y22, y19 = (P[P.year == y].copy() for y in (2024, 2022, 2019))

print("== Panel coverage")
for y, d in ((2019, y19), (2022, y22), (2024, y24)):
    print(y, "units", len(d), "| poverty", d.poverty_absolute.notna().sum(), "| pop", d["pop"].notna().sum(),
          "| lfs", d.p_rate.notna().sum(), "| amenities", d.piped_water.notna().sum())
print("2024 units without population:", y24[y24["pop"].isna()][["state", "dkey"]].values.tolist())
print("2024 units without LFS:", y24[y24.p_rate.isna()][["state", "dkey", "poverty_absolute"]].values.tolist())

print("\n== Variance split (between-state share)")
for y, d in ((2022, y22), (2024, y24)):
    for col in ("poverty_absolute", "log_income"):
        u = variance_split(d, col); w = variance_split(d, col, "households")
        print(f"{y} {col:17s} unweighted between {u['between']:.2f} within {u['within']:.2f} | household-weighted between {w['between']:.2f} within {w['within']:.2f}")

print("\n== EPR identity check (EPR vs LFPR*(1-UR))")
d = y24.dropna(subset=["ep_ratio", "p_rate", "u_rate"])
gap = (d.ep_ratio - d.p_rate * (1 - d.u_rate / 100)).abs()
print("max abs gap (pp):", round(gap.max(), 2), "mean:", round(gap.mean(), 3))

print("\n== Spearman correlations 2024 (|r|>0.7 shown)")
cols = ["log_income", "poverty_absolute", "poverty_relative", "p_rate", "u_rate", "ep_ratio", "piped_water", "electricity", "sanitation"]
Cm = y24[cols].corr(method="spearman")
pairs = [(a, b, round(Cm.loc[a, b], 2)) for i, a in enumerate(cols) for b in cols[i + 1:] if abs(Cm.loc[a, b]) > 0.7]
print(pairs)

print("\n== Winsorising effect on extremes, 2024")
for col in ("poverty_absolute", "piped_water", "electricity"):
    s = y24[col].dropna(); p5, p95 = s.quantile([.05, .95])
    print(f"{col}: P5={p5:.1f} P95={p95:.1f}; clipped above P95: {(s > p95).sum()}, below P5: {(s < p5).sum()}")
print("Pitas poverty", y24.loc[y24.dkey == "pitas", "poverty_absolute"].values)

# ---------- KPX variants
ref = y24
base_b = fit_bounds(ref, (0.05, 0.95))
variants = {
    "geo_p5p95_floor": kpx(y24, base_b),
    "geo_p1p99_floor": kpx(y24, fit_bounds(ref, (0.01, 0.99))),
    "geo_raw_floor": kpx(y24, fit_bounds(ref, None)),
    "arith_p5p95": kpx(y24, base_b, agg="arith"),
    "geo_p5p95_nofloor": kpx(y24, base_b, floor=0.0),
}
print("\n== KPX variants vs base (Spearman; top-quintile overlap)")
base = variants["geo_p5p95_floor"]["KPX"]
k = int(np.ceil(0.2 * base.notna().sum()))
top = set(base.nlargest(k).index)
for name, v in variants.items():
    rho = spearmanr(base, v.KPX, nan_policy="omit")[0]
    ov = len(top & set(v.KPX.nlargest(k).index)) / k
    ties = v.KPX.round(6).duplicated(keep=False).sum()
    print(f"{name:20s} rho={rho:.3f} top20%-overlap={ov:.2f} tied-units={ties}")
y24["KPX"] = base
y24["partial"] = variants["geo_p5p95_floor"]["partial"]
print("partial (2-dimension) units:", int(y24.partial.sum()))

dims = variants["geo_p5p95_floor"][["A", "B", "C"]]
complete = dims.dropna()
st = dirichlet_ranks(complete)
print("\n== Dirichlet(5,5,5) x5000, seed 2026 (complete cases n=%d)" % len(complete))
print("robust priority (>=90% of draws in top 20%):", int((st.share_top >= .9).sum()),
      "| watch (50-90%):", int(((st.share_top >= .5) & (st.share_top < .9)).sum()))
print("median rank-interval width:", float((st.rank_p95 - st.rank_p05).median()))
show = y24.loc[st.sort_values("rank_p50").index[:8], ["state", "dkey", "poverty_absolute"]].join(st.round(2))
print(show.to_string())

# ---------- Targeting: in-sample and backtest
def state_rate(d, rate="poverty_absolute", w="households"):
    g = d.dropna(subset=[rate, w]).groupby("state")
    return g.apply(lambda x: np.average(x[rate], weights=x[w]), include_groups=False)

ev = y24.dropna(subset=["poverty_absolute", "households"]).copy()
ev["s_state24"] = ev.state.map(state_rate(ev))
ev["s_dist24"] = ev.poverty_absolute
print("\n== In-sample coverage 2024 (household denominator vs population proxy)")
for reach in (0.1, 0.2, 0.3):
    h = [coverage(ev, s, "households", "poverty_absolute", reach) for s in ("s_dist24", "s_state24")]
    p = [coverage(ev, s, "pop", "poverty_absolute", reach) for s in ("s_dist24", "s_state24")]
    print(f"reach {reach:.0%}: households dist {h[0]:.3f} state {h[1]:.3f} gain {h[0]-h[1]:+.3f} | population dist {p[0]:.3f} state {p[1]:.3f} gain {p[0]-p[1]:+.3f}")

# 2022 scores mapped to 2024 geography
s22 = y22.set_index(["state", "dkey"])
def score22(row, col):
    key = (row.state, row.dkey)
    if key in SPLITS_2025:
        par = SPLITS_2025[key]; tot = sum(par.values())
        vals = [(s22.loc[(row.state, p), col], wt) for p, wt in par.items() if (row.state, p) in s22.index]
        return np.nan if not vals else sum(v * w for v, w in vals) / sum(w for _, w in vals)
    return s22.loc[key, col] if key in s22.index else np.nan

ev["s_dist22"] = ev.apply(lambda r: score22(r, "poverty_absolute"), axis=1)
st22 = state_rate(y22)
ev["s_state22"] = ev.state.map(st22)
k22 = kpx(y22, fit_bounds(y22, (0.05, 0.95)))
y22["KPX"] = k22.KPX
s22 = y22.set_index(["state", "dkey"])
ev["s_kpx22"] = ev.apply(lambda r: score22(r, "KPX"), axis=1)
print("2024 units with a 2022 score:", ev.s_dist22.notna().sum(), "of", len(ev),
      "| missing:", ev[ev.s_dist22.isna()][["state", "dkey"]].values.tolist())

bt = ev.dropna(subset=["s_dist22", "s_state22", "s_kpx22"])
print("\n== Backtest: rank on 2022, evaluate on 2024 households (n=%d)" % len(bt))
rows = []
for reach in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5):
    r = {"reach": reach}
    for s in ("s_dist22", "s_state22", "s_kpx22", "s_dist24", "s_state24"):
        r[s] = coverage(bt, s, "households", "poverty_absolute", reach)
    rows.append(r)
BT = pd.DataFrame(rows).round(3); print(BT.to_string(index=False))

# cluster bootstrap over districts within states for gain at 20%
rng = np.random.default_rng(2026); gains = []
for _ in range(1000):
    samp = bt.groupby("state", group_keys=False).apply(lambda g: g.sample(len(g), replace=True, random_state=rng.integers(1e9)))
    samp = samp.reset_index(drop=True)
    gains.append(coverage(samp, "s_dist22", "households", "poverty_absolute", .2) - coverage(samp, "s_state22", "households", "poverty_absolute", .2))
print("backtest gain at 20%% reach: %.3f, 95%% bootstrap interval [%.3f, %.3f]" % (BT.loc[BT.reach == .2, "s_dist22"].iloc[0] - BT.loc[BT.reach == .2, "s_state22"].iloc[0], *np.percentile(gains, [2.5, 97.5])))
poor_hh = (bt.households * bt.poverty_absolute / 100)
print("estimated poor households in backtest set: %.0f; 1pp of coverage = %.0f households" % (poor_hh.sum(), poor_hh.sum() / 100))

# ---------- Risk outlook: predict 2024 from 2019/2022
s19 = y19.set_index(["state", "dkey"])
def hist(row, frame, col):
    key = (row.state, row.dkey)
    if key in SPLITS_2025:
        par = SPLITS_2025[key]
        vals = [(frame.loc[(row.state, p), col], wt) for p, wt in par.items() if (row.state, p) in frame.index]
        return np.nan if not vals else sum(v * w for v, w in vals) / sum(w for _, w in vals)
    return frame.loc[key, col] if key in frame.index else np.nan
s22 = y22.set_index(["state", "dkey"])
ev["p19"] = ev.apply(lambda r: hist(r, s19, "poverty_absolute"), axis=1)
ev["p22"] = ev.apply(lambda r: hist(r, s22, "poverty_absolute"), axis=1)
f = ev.dropna(subset=["p19", "p22"]).copy()
f["persist"] = f.p22
f["trend"] = (f.p22 + (f.p22 - f.p19) * 2 / 3).clip(0, 100)
f["damped"] = (f.p22 + 0.5 * (f.p22 - f.p19) * 2 / 3).clip(0, 100)
f["state22"] = f.state.map(st22)
print("\n== Risk outlook holdout: predict 2024 absolute poverty (n=%d)" % len(f))
act = f.poverty_absolute
kq = int(np.ceil(.2 * len(f))); topact = set(act.nlargest(kq).index)
for m in ("persist", "trend", "damped", "state22"):
    e = f[m] - act
    hit = len(topact & set(f[m].nlargest(kq).index)) / kq
    print(f"{m:8s} MAE {e.abs().mean():.2f}pp RMSE {np.sqrt((e**2).mean()):.2f}pp hh-weighted MAE {np.average(e.abs(), weights=f.households):.2f}pp top-20% recall {hit:.2f}")
ch = f.poverty_absolute - f.p22
print("corr(change 22->24, level 22) = %.2f  (negative = regression to the mean)" % np.corrcoef(ch, f.p22)[0, 1])
print("national-ish (hh-weighted) poverty 2019/2022/2024: %.2f / %.2f / %.2f" % tuple(np.average(f[c], weights=f.households) for c in ("p19", "p22", "poverty_absolute")))

# ---------- Factors associated with poverty (state fixed effects)
m = y24.dropna(subset=["poverty_absolute", "p_rate", "u_rate", "piped_water", "electricity", "dependency"]).copy()
n = len(m); yv = m.poverty_absolute / 100
m["lp"] = np.log(((yv * (n - 1) + .5) / n) / (1 - (yv * (n - 1) + .5) / n))
for c in ("p_rate", "u_rate", "piped_water", "electricity", "dependency"):
    m[c + "_z"] = (m[c] - m[c].mean()) / m[c].std()
fe = smf.ols("lp ~ p_rate_z + u_rate_z + piped_water_z + electricity_z + dependency_z + C(state)", m).fit(
    cov_type="cluster", cov_kwds={"groups": m.state})
print("\n== Factors associated with poverty, 2024, state FE, cluster SE by state (n=%d, states=%d)" % (n, m.state.nunique()))
print(fe.summary2().tables[1].loc[[c for c in fe.params.index if c.endswith("_z")], ["Coef.", "[0.025", "0.975]"]].round(3))
pooled = smf.ols("lp ~ p_rate_z + u_rate_z + piped_water_z + electricity_z + dependency_z", m).fit()
print("pooled (between+within) R2 %.2f | FE within-model R2 %.2f" % (pooled.rsquared, fe.rsquared))

# exports for downstream use
y24.to_csv("/home/claude/kantung/out_panel_2024.csv", index=False)
BT.to_csv("/home/claude/kantung/out_backtest.csv", index=False)
