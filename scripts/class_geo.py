#!/usr/bin/env python3
"""Governor vote by education, income, and density, plus governor vote over time 2016-2026."""
import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
t = pd.read_csv(P / "towns.csv")
t = t[t.gov_R2.notna()].copy()  # drops Marlboro (governor return excluded; see analyze.py)
b = pd.DataFrame(json.loads((ROOT / "data/raw/needle_baseline.json").read_text()))
b["town"] = b.town.str.upper().str.replace(r"^ST\. ", "SAINT ", regex=True)
b.loc[b.town == "ESSEX", "town"] = "ESSEX TOWN"
t = t.merge(b[["town", "pd", "pr"]], on="town", how="left")

def tier(d):
    if d >= 1000: return "4 Urban (1000+/sq mi)"
    if d >= 200: return "3 Suburban / large town (200-1000)"
    if d >= 50: return "2 Small town (50-200)"
    return "1 Rural (<50)"
t["tier"] = t.density.map(tier)
w = t.gov_total
def wq(col, k=5):
    o = t[col].rank(method="first"); cw = w[o.sort_values().index].cumsum() / w.sum()
    q = pd.Series(np.ceil(cw * k).clip(1, k).astype(int), index=cw.index)
    return q.reindex(t.index)
t["ba_q"], t["inc_q"] = wq("pct_ba_plus"), wq("per_capita_income")

def summarize(g):
    s = lambda a, bb: g[a].sum() / (g[a].sum() + g[bb].sum())
    out = {"towns": len(g), "votes": int(g.gov_total.sum()),
           "janoo": 1 - s("gov_R", "gov_L"), "dem_gov_24": 1 - s("gov_R_24", "gov_L_24"),
           "dem_ticket_26": 1 - s("env_R", "env_L"), "dem_ticket_24": 1 - s("env_R_24", "env_L_24"),
           "harris_24": 1 - s("pres_R", "pres_L"), "biden_20": g.pd.sum() / (g.pd.sum() + g.pr.sum()),
           "turnout": g.ballots.sum() / g.reg.sum(),
           "ba": np.average(g.pct_ba_plus.dropna(), weights=g.gov_total[g.pct_ba_plus.notna()]), "inc": np.average(g.per_capita_income.dropna(), weights=g.gov_total[g.per_capita_income.notna()]),
           "density": g["pop"].sum() / g.land_sqmi.sum()}
    for y in ("16", "18", "20", "22"):
        out[f"dem_gov_{y}"] = 1 - np.average(t.loc[g.index, f"gov_R2_{y}"].dropna(), weights=g.gov_total[t.loc[g.index, f"gov_R2_{y}"].notna()])
    out["swing_to_dem"] = out["janoo"] - out["dem_gov_24"]
    out["janoo_vs_ticket"] = out["janoo"] - out["dem_ticket_26"]
    return pd.Series(out)

res = {}
for key, lab in [("tier", "Density tier"), ("ba_q", "College-degree quintile (1=lowest)"), ("inc_q", "Median income quintile (1=lowest)")]:
    s = t.groupby(key).apply(summarize, include_groups=False)
    res[key] = s
    print(f"\n=== {lab}")
    print(s[["towns", "votes", "ba", "inc", "density", "janoo", "dem_gov_24", "swing_to_dem", "dem_ticket_26", "janoo_vs_ticket", "turnout"]].round(3).to_string())
# education within density tier
print("\n=== Janoo swing (vs 2024 Dem) by density tier x BA tercile")
t["ba_t"] = wq("pct_ba_plus", 3)
x = t.groupby(["tier", "ba_t"]).apply(summarize, include_groups=False)
print(x[["towns", "janoo", "swing_to_dem", "janoo_vs_ticket"]].round(3).unstack().to_string())
print("\n=== Dem governor share over time by BA quintile")
print(res["ba_q"][["dem_gov_16", "dem_gov_18", "dem_gov_20", "dem_gov_22", "dem_gov_24", "janoo", "biden_20", "harris_24", "dem_ticket_24", "dem_ticket_26"]].round(3).to_string())
print("\n=== over time by density tier")
print(res["tier"][["dem_gov_16", "dem_gov_18", "dem_gov_20", "dem_gov_22", "dem_gov_24", "janoo", "biden_20", "harris_24", "dem_ticket_26"]].round(3).to_string())
t.to_csv(P / "towns_classgeo.csv", index=False)
pd.concat({k: v for k, v in res.items()}, names=["group", "bin"]).to_csv(P / "class_geo_summary.csv")
