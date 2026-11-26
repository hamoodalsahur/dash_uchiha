"""B40 -> M40 layer: how far each district is from the middle-income line,
whether it is catching up, and what growth would close the gap.

Describes districts, not households. Nothing here follows a family over time:
Malaysia has no public household panel. Share-below-line figures are estimates
(lognormal from each district's median and mean income), checked against the
published Penang income-band table and against the 40% national total.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

from kantung.core import DATA, SPLITS_2025, _read, build_panel, district_key

# Published national lines (DOSM Household Income Survey reports / technical
# notes), gross monthly household income, RM. Percentile minimums differ by a
# few ringgit through rounding, so the official figure is used where published.
OFFICIAL = {
    ("m40_entry", 2019): 4850, ("m40_entry", 2022): 5250, ("m40_entry", 2024): 5860,
    ("near_m40_floor", 2024): 3820, ("t20_entry", 2024): 12680,
}
PERCENTILE_FOR = {"near_m40_floor": 21, "m40_entry": 41, "t20_entry": 81}
TARGET_YEAR = 2030
BASE_YEAR = 2024
LEVEL_BAND = 0.0025  # |annual change in log(income / line)| below this = "about level"
GINI_BAND = 0.02     # district Gini moves a lot between waves; smaller changes = "no clear change"


# ---------- arithmetic ----------

def required_growth(y0: float, t0: float, line_growth: float, years: int) -> float:
    """Annual income growth needed for income y0 to meet a line that starts at
    t0 and grows `line_growth` a year, after `years` years. Fractions, not %."""
    if years <= 0 or y0 <= 0 or t0 <= 0 or line_growth <= -1:
        return float("nan")
    return (t0 * (1 + line_growth) ** years / y0) ** (1 / years) - 1


def years_to_cross(y0: float, t0: float, growth: float, line_growth: float) -> int | None:
    """Whole years until income growing at `growth` reaches a line growing at
    `line_growth`. 0 if already at or above; None if it never does."""
    if y0 >= t0:
        return 0
    if growth <= line_growth:
        return None
    n = math.ceil(math.log(t0 / y0) / math.log((1 + growth) / (1 + line_growth)))
    while y0 * (1 + growth) ** n < t0 * (1 + line_growth) ** n:  # guard float edge
        n += 1
    return n


def annual_growth(start, end, years, cpi_start=None, cpi_end=None):
    """Compound annual growth; real if both CPI levels are given."""
    ratio = np.asarray(end, float) / np.asarray(start, float)
    if cpi_start is not None and cpi_end is not None:
        ratio = ratio / (np.asarray(cpi_end, float) / np.asarray(cpi_start, float))
    return ratio ** (1 / years) - 1


def catch_up_status(change: pd.Series) -> pd.Series:
    """Label the annual change in log(income / line)."""
    return pd.Series(np.select([change > LEVEL_BAND, change < -LEVEL_BAND], ["closing", "falling behind"],
                               "about level"), index=change.index).where(change.notna())


# ---------- distribution estimates ----------

def share_below(median, mean, line):
    """Share of households below `line`, assuming lognormal income with the
    district's median and mean (sigma^2 = 2 ln(mean/median)). NaN if mean <= median."""
    median, mean, line = (np.asarray(x, float) for x in (median, mean, line))
    with np.errstate(invalid="ignore", divide="ignore"):
        sigma = np.sqrt(2 * np.log(mean / median))
        out = norm.cdf((np.log(line) - np.log(median)) / sigma)
    out = np.where(mean > median, out, np.nan)
    return float(out) if out.ndim == 0 else out


def band_bounds(bands: pd.DataFrame, line: float) -> tuple[float, float, float]:
    """Observed lower/upper bound (and a uniform-within-band interpolation) of
    the share of households below `line`, from a published income-band table."""
    lo_b = bands.band_lower_rm.to_numpy(float)
    hi_b = bands.band_upper_rm.to_numpy(float)
    p = bands.household_share_pct.to_numpy(float) / 100
    full = np.nan_to_num(hi_b, nan=np.inf) <= line
    part = (lo_b < line) & ~full
    lower = p[full].sum()
    upper = lower + p[part].sum()
    frac = np.where(part & np.isfinite(hi_b), (line - lo_b) / np.where(np.isfinite(hi_b), hi_b - lo_b, 1), 0)
    return float(lower), float(upper), float(lower + (p * frac).sum())


# ---------- loaders ----------

def load_lines() -> pd.DataFrame:
    """National and state income lines by year: geography, year, line, value_rm, source."""
    rows = []
    nat = _read(DATA / "hies_malaysia_percentile.parquet")
    st = _read(DATA / "hies_state_percentile.parquet")
    for geo_df, label in ((nat.assign(state="Malaysia"), "national"), (st, "state")):
        mins = geo_df[geo_df.variable == "minimum"]
        for line, pct in PERCENTILE_FOR.items():
            for _, r in mins[mins.percentile == pct].iterrows():
                official = OFFICIAL.get((line, int(r.year))) if r.state == "Malaysia" else None
                rows.append({"geography": r.state, "level": label, "year": int(r.year), "line": line,
                             "value_rm": official if official else float(r.income),
                             "source": "DOSM published line" if official else f"min income of percentile {pct}"})
    out = pd.DataFrame(rows)
    out["value_rm"] = out.value_rm.round().astype(int)
    return out.sort_values(["level", "geography", "line", "year"]).reset_index(drop=True)


def load_penang_bands() -> pd.DataFrame:
    b = pd.read_csv(DATA / "income_bands_penang_2024.csv")
    b["dkey"] = b.district.map(district_key)
    return b


def load_completion() -> pd.DataFrame:
    """Upper-secondary completion (%) by administrative district and year.

    MOE reports by District Education Office. Offices that match an
    administrative district by name map directly; a combined office such as
    'Kuala Muda/Yan' gives its value to each district it covers (flagged).
    Offices that split one district (e.g. Petaling Perdana/Utama, KL zones)
    are left out rather than averaged without cohort sizes.
    """
    c = _read(DATA / "completion_school_district.parquet")
    c = c[(c.district != "All Districts") & (c.stage == "secondary_upper")]
    rows = []
    for _, r in c.iterrows():
        parts = r.district.split("/")
        note = "direct match" if len(parts) == 1 else "shared education office"
        for part in parts:
            rows.append({"state": r.state, "dkey": district_key(part), "year": int(r.year),
                         "completion_upper_secondary": r.completion, "match_note": note})
    out = pd.DataFrame(rows)
    admin = build_panel()
    admin = set(zip(admin.state, admin.dkey))
    out = out[[(s, k) in admin for s, k in zip(out.state, out.dkey)]]
    return out.drop_duplicates(["state", "dkey", "year"]).reset_index(drop=True)


def _state_cpi_annual() -> pd.DataFrame:
    c = _read(DATA / "cpi_2d_state.parquet")
    c = c[c.division == "overall"]
    return c.groupby(["state", "year"])["index"].mean().rename("cpi").reset_index()


def _changed_keys() -> set:
    keys = set(SPLITS_2025)
    for (state, _), parents in SPLITS_2025.items():
        keys |= {(state, p) for p in parents}
    return keys


# ---------- the table ----------

def build_mobility(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """District-year table (2019, 2022, 2024) of gap, share below the line,
    growth and catch-up. Growth columns sit on the 2024 rows."""
    p = (panel if panel is not None else build_panel()).copy()
    keep = ["state", "dkey", "year", "income_median", "income_mean", "households", "dependency", "src_note"]
    p = p[keep]

    hd = _read(DATA / "hies_district.parquet")
    hd["dkey"] = hd.district.map(district_key)
    p = p.merge(hd.groupby(["state", "dkey", "year"])[["expenditure_mean"]].mean().reset_index(),
                on=["state", "dkey", "year"], how="left")
    gi = _read(DATA / "hh_inequality_district.parquet")
    gi["dkey"] = gi.district.map(district_key)
    p = p.merge(gi.groupby(["state", "dkey", "year"])[["gini"]].mean().reset_index(),
                on=["state", "dkey", "year"], how="left")

    lines = load_lines()
    nat = lines[lines.geography == "Malaysia"].pivot(index="year", columns="line", values="value_rm")
    stl = lines[(lines.level == "state") & (lines.line == "m40_entry")].set_index(["geography", "year"]).value_rm
    p["m40_line"] = p.year.map(nat["m40_entry"])
    p["near_m40_floor"] = p.year.map(nat["near_m40_floor"])
    p["state_m40_line"] = [stl.get((s, y), np.nan) for s, y in zip(p.state, p.year)]
    p["gap_rm"] = p.m40_line - p.income_median
    p["attainment"] = p.income_median / p.m40_line
    p["share_below_m40"] = share_below(p.income_median, p.income_mean, p.m40_line)
    p["share_near_m40"] = p.share_below_m40 - share_below(p.income_median, p.income_mean, p.near_m40_floor)
    p["expenditure_share"] = p.expenditure_mean / p.income_mean
    comp = load_completion().rename(columns={"match_note": "completion_match"})
    p = p.merge(comp, on=["state", "dkey", "year"], how="left")

    # Observed range from published income bands, where extracted (Penang 2024)
    bands = load_penang_bands()
    for dkey, b in bands.groupby("dkey"):
        lo, hi, _ = band_bounds(b, OFFICIAL[("m40_entry", 2024)])
        hit = (p.state == "Pulau Pinang") & (p.dkey == dkey) & (p.year == 2024)
        p.loc[hit, ["share_below_m40_observed_low", "share_below_m40_observed_high"]] = [lo, hi]
    p["boundary_changed"] = [(s, k) in _changed_keys() for s, k in zip(p.state, p.dkey)]

    # Growth and catch-up, on comparable boundaries only
    cpi = _state_cpi_annual().set_index(["state", "year"]).cpi
    wide = p.pivot_table(index=["state", "dkey"], columns="year", values="income_median")
    w = pd.DataFrame(index=wide.index)
    s = wide.index.get_level_values("state")
    for (a, b), tag in (((2019, 2024), "1924"), ((2022, 2024), "2224")):
        n = b - a
        cs, ce = [cpi.reindex(list(zip(s, [yr] * len(s)))).to_numpy() for yr in (a, b)]
        w[f"income_growth_{tag}"] = annual_growth(wide[a], wide[b], n)
        w[f"income_growth_real_{tag}"] = annual_growth(wide[a], wide[b], n, cs, ce)
        w[f"line_growth_{tag}"] = annual_growth(nat.loc[a, "m40_entry"], nat.loc[b, "m40_entry"], n)
        w[f"catch_up_{tag}"] = np.log((wide[b] / nat.loc[b, "m40_entry"]) / (wide[a] / nat.loc[a, "m40_entry"])) / n
        w[f"catch_up_status_{tag}"] = catch_up_status(w[f"catch_up_{tag}"])
    changed = [(st, k) in _changed_keys() for st, k in w.index]
    w.loc[changed, :] = np.nan
    w = w.reset_index().assign(year=BASE_YEAR)
    p = p.merge(w, on=["state", "dkey", "year"], how="left")

    g = p.pivot_table(index=["state", "dkey"], columns="year", values="gini")
    if 2022 in g and 2024 in g:
        d = (g[2024] - g[2022]).rename("gini_change_2224").reset_index().assign(year=BASE_YEAR)
        p = p.merge(d, on=["state", "dkey", "year"], how="left")
        p["gini_trend_2224"] = pd.Series(np.select([p.gini_change_2224 > GINI_BAND, p.gini_change_2224 < -GINI_BAND],
                                                   ["more unequal", "more equal"], "no clear change"),
                                         index=p.index).where(p.gini_change_2224.notna())

    # Growth needed to reach the line by 2030, three ways (2024 rows)
    cpi_nat = _state_cpi_annual().groupby("year").cpi.mean()
    infl = float(annual_growth(cpi_nat[2019], cpi_nat[2024], 5))
    line_g = float(annual_growth(nat.loc[2019, "m40_entry"], nat.loc[2024, "m40_entry"], 5))
    n = TARGET_YEAR - BASE_YEAR
    base = p.year == BASE_YEAR
    for label, h in (("fixed", 0.0), ("real", infl), ("moving", line_g)):
        p.loc[base, f"required_growth_2030_{label}"] = [
            required_growth(y, nat.loc[BASE_YEAR, "m40_entry"], h, n) if pd.notna(y) else np.nan
            for y in p.loc[base, "income_median"]]
    p.loc[base, "years_to_line_own_pace"] = [
        (years_to_cross(y, nat.loc[BASE_YEAR, "m40_entry"], gr, line_g) if pd.notna(y) and pd.notna(gr) else np.nan)
        for y, gr in zip(p.loc[base, "income_median"], p.loc[base, "income_growth_1924"])]
    p.attrs.update(inflation_1924=infl, line_growth_1924=line_g)
    return p.sort_values(["year", "state", "dkey"]).reset_index(drop=True)


def scenario_grid(start_incomes=(3000, 3500, 4000, 4500, 5000, 5500),
                  income_growth=(0.03, 0.05, 0.07, 0.10),
                  line_growth=(0.0, 0.02, 0.0385), years=range(BASE_YEAR, TARGET_YEAR + 1)) -> pd.DataFrame:
    """Preset income and line paths for the Power BI planner (no DAX maths)."""
    t0 = OFFICIAL[("m40_entry", BASE_YEAR)]
    rows = []
    for y0 in start_incomes:
        for g in income_growth:
            for h in line_growth:
                for yr in years:
                    k = yr - BASE_YEAR
                    inc, line = y0 * (1 + g) ** k, t0 * (1 + h) ** k
                    rows.append({"start_income_rm": y0, "income_growth_pct": round(100 * g, 2),
                                 "line_growth_pct": round(100 * h, 2), "year": yr,
                                 "income_rm": round(inc), "line_rm": round(line),
                                 "gap_rm": round(max(0.0, line - inc)), "reached": inc >= line,
                                 "required_growth_pct": round(100 * required_growth(y0, t0, h, TARGET_YEAR - BASE_YEAR), 2),
                                 "years_to_line": years_to_cross(y0, t0, g, h)})
    return pd.DataFrame(rows)
