#!/usr/bin/env python3
"""Separate education, density and income: stratified grids + regressions holding the others fixed.

Writes data/processed/controls.json (used by build_viz.py) and prints tables.
"""
import json, pathlib
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
t = pd.read_csv(P / "towns_classgeo.csv")
t = t[t.gov_R2.notna() & t.pct_ba_plus.notna() & t.per_capita_income.notna() & (t.density > 0)].copy()
t["janoo"] = 1 - t.gov_R2
t["swing"] = t.gov_R2_24 - t.gov_R2
t["vs_ticket"] = -t.crossover
t["dem24"] = 1 - t.gov_R2_24
t["ticket24"] = 1 - t.env_R2_24
t["ba10"] = t.pct_ba_plus * 10          # per 10 points of college share
t["logden"] = np.log10(t.density)      # per 10x density
t["inc10"] = t.per_capita_income / 1e4  # per $10k
t["age10"] = t.median_age / 10
t["seas10"] = t.pct_seasonal_housing * 10
w = t.gov_total

def wq(col, k, weights=w):
    o = t[col].sort_values().index
    cw = weights[o].cumsum() / weights.sum()
    return pd.Series(np.ceil(cw * k).clip(1, k).astype(int), index=o).reindex(t.index)

# density: 3 groups by natural breaks used elsewhere (rural / small town / suburban+urban)
t["den3"] = pd.cut(t.density, [0, 50, 200, 1e9], labels=["Rural", "Small town", "Suburban/urban"]).astype(str)
t["ba3"] = wq("pct_ba_plus", 3).map({1: "Fewer grads", 2: "Middle", 3: "More grads"})
t["inc3"] = wq("per_capita_income", 3).map({1: "Lower income", 2: "Middle", 3: "Higher income"})

def cell(g):
    vw = g.gov_total
    a = lambda c: float(np.average(g[c], weights=vw))
    return {"towns": int(len(g)), "votes": int(vw.sum()), "janoo": a("janoo"), "swing": a("swing"), "vs_ticket": a("vs_ticket"),
            "ba": a("pct_ba_plus"), "inc": a("per_capita_income"), "den": float(g["pop"].sum() / g.land_sqmi.sum())}

grids = {}
for rk, ck in (("den3", "ba3"), ("inc3", "ba3"), ("den3", "inc3")):
    grids[f"{rk}_{ck}"] = {f"{r}|{c}": cell(g) for (r, c), g in t.groupby([rk, ck])}

out = {"grids": grids, "models": {}}
specs = {
    "Education only": "ba10",
    "Density only": "logden",
    "Income only": "inc10",
    "All three": "ba10 + logden + inc10",
    "All three + age, second homes": "ba10 + logden + inc10 + age10 + seas10",
}
for y, base in (("swing", ""), ("janoo", ""), ("vs_ticket", ""), ("swing", "dem24 + ")):
    key = y + ("_lean" if base else "")
    out["models"][key] = {}
    for name, rhs in specs.items():
        m = smf.wls(f"{y} ~ {base}{rhs}", t, weights=w).fit(cov_type="HC1")
        out["models"][key][name] = {v: {"b": float(m.params[v]), "lo": float(m.conf_int().loc[v, 0]), "hi": float(m.conf_int().loc[v, 1])}
                                    for v in ("ba10", "logden", "inc10", "age10", "seas10") if v in m.params}
        out["models"][key][name]["r2"] = float(m.rsquared)

(P / "controls.json").write_text(json.dumps(out, indent=1))
fmt = lambda d: "  ".join(f"{k}={100*v['b']:+.1f} [{100*v['lo']:+.1f},{100*v['hi']:+.1f}]" for k, v in d.items() if k != "r2") + f"  R2={d['r2']:.2f}"
for y, ms in out["models"].items():
    print(f"\n== {y} (points per: +10pt college | 10x density | +$10k income | +10yr age | +10pt second homes)")
    for n, d in ms.items():
        print(f"  {n:32s} {fmt(d)}")
for gname, g in grids.items():
    print(f"\n== grid {gname}")
    df = pd.DataFrame(g).T
    for m in ("janoo", "swing", "vs_ticket"):
        print(m); print((df[m].astype(float) * 100).round(1).unstack() if False else pd.Series((df[m].astype(float) * 100).round(1).values, index=pd.MultiIndex.from_tuples([tuple(k.split("|")) for k in df.index])).unstack().to_string())
    print("towns"); print(pd.Series(df.towns.values, index=pd.MultiIndex.from_tuples([tuple(k.split("|")) for k in df.index])).unstack().to_string())
