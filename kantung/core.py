"""Kantung Atlas core pipeline: harmonise DOSM district tables and compute the
statistics the project relies on. Pure functions over pandas DataFrames so each
step can be unit-tested.

Data: OpenDOSM parquet files (CC BY 4.0) from storage.dosm.gov.my.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(os.environ.get("KANTUNG_DATA", Path(__file__).resolve().parent.parent / "data"))
RAW_STATE = RAW_DIST = DATA

FEDERAL_SINGLE = ["W.P. Kuala Lumpur", "W.P. Labuan", "W.P. Putrajaya", "Perlis"]

# Districts created after 2024 population boundaries: child -> {parent: share of
# parent's 2024 population that moved}. Inferred from population_district
# 2024 -> 2025 drops; shares sum of children ~= parent loss.
SPLITS_2025 = {
    ("Sarawak", "gedong"): {"simunjan": 1.0},
    ("Sarawak", "sebuyau"): {"simunjan": 1.0},
    ("Sarawak", "pantu"): {"sri aman": 1.0},
    ("Sarawak", "lingga"): {"sri aman": 1.0},
    ("Sarawak", "siburan"): {"serian": 1.0},
    ("Sabah", "membakut"): {"beaufort": 20.8, "papar": 33.7},
}


def district_key(name: str) -> str:
    """Normalise a district name so spelling variants across DOSM tables join.

    Handles: '&' vs 'dan', 'S.P.' abbreviations, 'Hulu'/'Ulu', bracketed
    old names, 'Tanjong'/'Tanjung', 'Highland(s)', case and spacing.
    Boundary changes are NOT handled here (see SPLITS_2025).
    """
    s = name.strip().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("&", " dan ")
    s = re.sub(r"\bs\.\s*p\.\s*", "seberang perai ", s)
    s = re.sub(r"\btanjong\b", "tanjung", s)
    s = re.sub(r"\bhighland\b", "highlands", s)
    s = re.sub(r"\bhulu\b", "ulu", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s == "ulu":  # Terengganu 2024 label
        s = "ulu terengganu"
    return s


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "date" in df:
        df["year"] = pd.to_datetime(df["date"]).dt.year
    return df


def _keyed(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dkey"] = df["district"].map(district_key)
    return df


def load_population() -> pd.DataFrame:
    """District population (thousands): total, citizen, dependency ratio."""
    p = _keyed(_read(RAW_DIST / "population_district.parquet"))
    p = p[p.sex == "both"]
    tot = p[(p.age == "overall") & (p.ethnicity == "overall")]
    nonc = p[(p.age == "overall") & (p.ethnicity == "other_noncitizen")]
    ages = p[(p.ethnicity == "overall") & (p.age != "overall")].copy()
    lo = ages.age.str.extract(r"^(\d+)")[0].astype(int)
    ages["band"] = np.where(lo < 15, "young", np.where(lo >= 65, "old", "work"))
    dep = ages.pivot_table(index=["state", "dkey", "year"], columns="band",
                           values="population", aggfunc="sum")
    dep["dependency"] = (dep.young + dep.old) / dep.work
    out = (tot.set_index(["state", "dkey", "year"])["population"].rename("pop")
           .to_frame()
           .join(nonc.set_index(["state", "dkey", "year"])["population"].rename("noncit"))
           .join(dep["dependency"]))
    out["pop_citizen"] = out["pop"] - out["noncit"].fillna(0)
    return out.reset_index()


def load_state_households() -> pd.DataFrame:
    h = _read(RAW_DIST / "hh_lq_state.parquet")
    return h[["state", "year", "households"]]


def build_panel() -> pd.DataFrame:
    """District-year panel for 2019, 2022, 2024 with all indicators.

    Single-district states/territories missing from 2024 district tables are
    filled from state tables and flagged in `src_note`.
    """
    inc = _keyed(_read(RAW_DIST / "hh_income_district.parquet"))
    pov = _keyed(_read(RAW_DIST / "hh_poverty_district.parquet"))
    lfs = _keyed(_read(RAW_DIST / "lfs_district.parquet"))
    am = _read(RAW_DIST / "hh_access_amenities.parquet")
    am = _keyed(am[am.district != "All Districts"])

    k = ["state", "dkey", "year"]
    panel = (pov.groupby(k)[["poverty_absolute", "poverty_relative"]].mean()
             .join(inc.groupby(k)[["income_median", "income_mean"]].mean(), how="outer")
             .join(lfs.groupby(k)[["p_rate", "u_rate", "ep_ratio"]].mean(), how="left")
             .join(am.groupby(k)[["piped_water", "electricity", "sanitation"]].mean(), how="left"))
    panel = panel.reset_index()
    panel = panel[panel.year.isin([2019, 2022, 2024])]
    panel["src_note"] = "district table"

    # Fill single-district units for 2024 from state tables
    sp = _read(RAW_STATE / "hh_poverty_state.parquet")
    hs = _read(RAW_STATE / "hies_state.parquet")
    lfs_s = _read(RAW_STATE / "lfs_state_sex.parquet")
    lfs_s = lfs_s[lfs_s.sex == "both"]
    rows = []
    for st in FEDERAL_SINGLE:
        dkey = district_key(st if st != "Perlis" else "Perlis")
        have = panel[(panel.state == st) & (panel.year == 2024)]
        if len(have):
            continue
        r = {"state": st, "dkey": dkey, "year": 2024, "src_note": "state table (single-district unit)"}
        a = sp[(sp.state == st) & (sp.year == 2024)]
        b = hs[(hs.state == st) & (hs.year == 2024)]
        c = lfs_s[(lfs_s.state == st) & (lfs_s.year == 2024)]
        if len(a):
            r.update(poverty_absolute=a.poverty_absolute.iloc[0], poverty_relative=a.poverty_relative.iloc[0])
        if len(b):
            r.update(income_median=b.income_median.iloc[0], income_mean=b.income_mean.iloc[0])
        if len(c):
            r.update(p_rate=c.p_rate.iloc[0], u_rate=c.u_rate.iloc[0], ep_ratio=c.ep_ratio.iloc[0])
        prev = am[(am.state == st) & (am.year == 2024)]
        if len(prev):
            r.update(prev[["piped_water", "electricity", "sanitation"]].mean().to_dict())
        rows.append(r)
    if rows:
        panel = pd.concat([panel, pd.DataFrame(rows)], ignore_index=True)

    # Population denominators. 2024 HIES uses post-split boundaries that only
    # appear in population_district from 2025, so 2024 uses 2025 population.
    pop = load_population()
    pop_year = {2019: 2020, 2022: 2022, 2024: 2025}
    panel["pop_year"] = panel.year.map(pop_year)
    panel = panel.merge(pop.rename(columns={"year": "pop_year"}), on=["state", "dkey", "pop_year"], how="left")

    # Households: district pop / state average household size (same pop year,
    # households for the survey year). Assumes uniform household size within a
    # state: a documented approximation.
    hh = load_state_households()
    st_pop = pop.groupby(["state", "year"])["pop"].sum().rename("state_pop").reset_index()
    hh = hh.merge(st_pop, on=["state", "year"], how="left")
    hh["hh_size"] = hh.state_pop * 1000 / hh.households
    panel = panel.merge(hh[["state", "year", "hh_size"]], on=["state", "year"], how="left")
    panel["households"] = panel["pop"] * 1000 / panel["hh_size"]
    panel["log_income"] = np.log(panel.income_median)
    return panel


def variance_split(df: pd.DataFrame, y: str, w: str | None = None, group: str = "state") -> dict:
    """Share of variance in `y` between groups (states) vs within.

    Unweighted (each district counts once) or weighted by column `w`.
    Returns {'between': share, 'within': share}.
    """
    d = df.dropna(subset=[y] + ([w] if w else []))
    wt = d[w].to_numpy(float) if w else np.ones(len(d))
    yv = d[y].to_numpy(float)
    mu = np.average(yv, weights=wt)
    sst = np.sum(wt * (yv - mu) ** 2)
    g = d.assign(_w=wt, _y=yv).groupby(group)
    gw = g["_w"].sum()
    gm = g.apply(lambda x: np.average(x["_y"], weights=x["_w"]), include_groups=False)
    ssb = np.sum(gw * (gm - mu) ** 2)
    return {"between": float(ssb / sst), "within": float(1 - ssb / sst)}


def coverage(units: pd.DataFrame, score: str, weight: str, rate: str, reach: float) -> float:
    """Share of the poor covered when units are selected in descending `score`
    order until `reach` share of total `weight` (e.g. households) is reached.

    Ties are handled as one block; the marginal block is partly selected
    (fraction applied uniformly to all units in the block, i.e. representative
    selection). `rate` is a percentage.
    """
    from kantung.outputs import priority_list

    d = units.dropna(subset=[score, weight, rate])
    poor = d[weight] * d[rate] / 100
    sel = priority_list(d, score, weight, reach)
    return float((sel * poor).sum() / poor.sum())


def _scale(x: pd.Series, lo: float, hi: float, higher_better: bool, floor: float) -> pd.Series:
    x = x.clip(lo, hi)
    r = (x - lo) / (hi - lo) if higher_better else (hi - x) / (hi - lo)
    return floor + (1 - floor) * r


DIMENSIONS = {
    "A": [("log_income", True), ("poverty_absolute", False)],
    "B": [("p_rate", True), ("u_rate", False)],
    "C": [("piped_water", True), ("electricity", True), ("sanitation", True)],
}


def fit_bounds(ref: pd.DataFrame, q: tuple[float, float] | None) -> dict:
    """Frozen normalisation bounds from a reference year."""
    b = {}
    for items in DIMENSIONS.values():
        for col, _ in items:
            s = ref[col].dropna()
            b[col] = (s.quantile(q[0]), s.quantile(q[1])) if q else (s.min(), s.max())
    return b


def kpx(df: pd.DataFrame, bounds: dict, weights=(1 / 3, 1 / 3, 1 / 3),
        floor: float = 0.01, agg: str = "geo") -> pd.DataFrame:
    """Kantung Priority Index. Dimension scores in [floor, 1] (higher = better);
    KPX = 100 * (1 - I), higher = more deprived. Needs >= 2 dimensions; rows
    with a missing dimension are flagged `partial`."""
    out = pd.DataFrame(index=df.index)
    for dim, items in DIMENSIONS.items():
        cols = [_scale(df[c], *bounds[c], hb, floor) for c, hb in items]
        out[dim] = pd.concat(cols, axis=1).mean(axis=1, skipna=True)
    w = np.asarray(weights, float)
    have = out[["A", "B", "C"]].notna()
    out["n_dims"] = have.sum(axis=1)
    ww = have.to_numpy() * w
    ww = ww / ww.sum(axis=1, keepdims=True)
    vals = out[["A", "B", "C"]].fillna(1).to_numpy()
    if agg == "geo":
        I = np.exp((ww * np.log(vals)).sum(axis=1))
    else:
        I = (ww * vals).sum(axis=1)
    out["I"] = I
    out["KPX"] = 100 * (1 - I)
    out.loc[out.n_dims < 2, "KPX"] = np.nan
    out["partial"] = out.n_dims < 3
    return out


def dirichlet_ranks(dims: pd.DataFrame, alpha=(5, 5, 5), n=5000, seed=2026,
                    top_share=0.2) -> pd.DataFrame:
    """Rank stability of KPX under random dimension weights ~ Dirichlet(alpha).
    Returns per-unit 5th/50th/95th percentile rank (1 = most deprived) and
    share of draws in the most-deprived `top_share`. This is weight stability,
    not a probability of true deprivation."""
    rng = np.random.default_rng(seed)
    W = rng.dirichlet(alpha, size=n)
    v = np.log(dims[["A", "B", "C"]].to_numpy())
    I = np.exp(v @ W.T)  # units x draws (complete cases only)
    ranks = I.argsort(axis=0).argsort(axis=0) + 1  # low I = rank 1 = most deprived
    k = int(np.ceil(top_share * len(dims)))
    return pd.DataFrame({
        "rank_p05": np.percentile(ranks, 5, axis=1),
        "rank_p50": np.percentile(ranks, 50, axis=1),
        "rank_p95": np.percentile(ranks, 95, axis=1),
        "share_top": (ranks <= k).mean(axis=1),
    }, index=dims.index)
