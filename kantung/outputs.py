"""Dashboard-facing outputs: outlook status, priority lists, allocation grid."""
import math

import pandas as pd


def _top(s: pd.Series, top_share: float) -> set:
    s = s.dropna()
    return set(s.nlargest(math.ceil(top_share * len(s))).index)


def outlook_status(prev: pd.Series, cur: pd.Series, top_share: float = 0.2) -> pd.Series:
    """Label each current unit by whether it is in the worst `top_share` in the
    previous and current survey: persistent, emerging, easing, not flagged,
    or 'no history' when the unit has no previous value."""
    tp, tc = _top(prev, top_share), _top(cur, top_share)
    out = {}
    for u in cur.index:
        if u not in prev.index or pd.isna(prev.get(u)):
            out[u] = "no history"
        elif u in tp and u in tc:
            out[u] = "persistent"
        elif u in tc:
            out[u] = "emerging"
        elif u in tp:
            out[u] = "easing"
        else:
            out[u] = "not flagged"
    return pd.Series(out)


def priority_list(units: pd.DataFrame, score: str, weight: str, reach: float) -> pd.Series:
    """Share of each unit selected when units are taken in descending `score`
    order until `reach` of total `weight` is used. Tied units form one block;
    the marginal block is selected proportionally."""
    d = units.dropna(subset=[score, weight])
    target = reach * d[weight].sum()
    sel = pd.Series(0.0, index=d.index)
    used = 0.0
    for _, blk in reversed(list(d.groupby(score, sort=True))):
        bw = blk[weight].sum()
        frac = min(1.0, max(0.0, (target - used) / bw))
        sel[blk.index] = frac
        used += frac * bw
        if frac < 1.0:
            break
    return sel


def allocation_grid(units, rules, weight, rate, reaches, baseline=None) -> pd.DataFrame:
    """Planner metrics for each rule x reach: coverage of the poor, efficiency
    (coverage / reach), non-poor share of selected households, poor reached,
    and optionally the coverage gain over a baseline rule."""
    d = units.dropna(subset=[weight, rate])
    poor = d[weight] * d[rate] / 100
    rows = []
    for name, col in rules.items():
        for r in reaches:
            sel = priority_list(d, col, weight, r).reindex(d.index, fill_value=0.0)
            hh = (sel * d[weight]).sum()
            p = (sel * poor).sum()
            cov = p / poor.sum()
            rows.append({"rule": name, "reach": r, "coverage": cov,
                         "efficiency": cov / r if r else float("nan"),
                         "nonpoor_share": 1 - p / hh if hh else float("nan"),
                         "poor_reached": p})
    g = pd.DataFrame(rows)
    if baseline:
        base = g[g.rule == baseline].set_index("reach").coverage
        g["gain_vs_baseline"] = g.coverage - g.reach.map(base)
    return g


def map_to_2024(cur, prev, col, splits):
    """Value of `col` from `prev` (indexed by state, dkey) for each row of `cur`.
    Districts created after `prev` take the weighted mean of their parents per
    `splits`: {(state, child): {parent: weight}}. Unknown districts get NaN."""
    vals = []
    for state, dkey in zip(cur["state"], cur["dkey"]):
        parents = splits.get((state, dkey))
        if parents:
            pairs = [(prev.loc[(state, p), col], w) for p, w in parents.items() if (state, p) in prev.index]
            vals.append(sum(v * w for v, w in pairs) / sum(w for _, w in pairs) if pairs else float("nan"))
        else:
            vals.append(prev.loc[(state, dkey), col] if (state, dkey) in prev.index else float("nan"))
    return pd.Series(vals, index=cur.index, dtype=float)
